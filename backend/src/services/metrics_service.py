"""
MetricsService - Tracks extraction quality metrics for monitoring.

Implements FR-020: Track success rate and confidence distribution.
Stores daily aggregated metrics in shared/extraction_metrics.json.
"""
import json
from pathlib import Path
from datetime import date
from typing import Optional
import logging
import fcntl
import os

from backend.src.models.extraction_metrics import ExtractionMetrics
from backend.src.models.extracted_data import ExtractedData


# Configure logging
logger = logging.getLogger(__name__)


class MetricsService:
    """
    Service for recording and retrieving extraction quality metrics.

    Provides:
    - Daily metric aggregation
    - Success rate tracking
    - Confidence distribution analysis
    - Extraction method usage tracking
    - File-based persistence with locking for concurrency
    """

    DEFAULT_STORAGE_PATH = Path("shared/extraction_metrics.json")

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize MetricsService.

        Args:
            storage_path: Path to metrics JSON file (defaults to shared/extraction_metrics.json)
        """
        self.storage_path = storage_path or self.DEFAULT_STORAGE_PATH

        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize file if doesn't exist
        if not self.storage_path.exists():
            with open(self.storage_path, 'w') as f:
                json.dump({}, f)

    def record_extraction(self, extracted_data: ExtractedData) -> None:
        """
        Record extraction metrics for a single extraction.

        Updates daily metrics:
        - Increments total extractions
        - Classifies as successful/failed/partial
        - Updates confidence distribution
        - Tracks extraction method usage

        Args:
            extracted_data: ExtractedData instance to record
        """
        today = date.today().isoformat()

        # Determine extraction outcome
        is_successful = all([
            extracted_data.transaction_date is not None,
            extracted_data.items is not None,
            extracted_data.total_amount is not None
        ])

        is_failed = all([
            extracted_data.transaction_date is None,
            extracted_data.items is None,
            extracted_data.total_amount is None
        ])

        is_partial = not is_successful and not is_failed

        # Determine overall confidence level (use highest field confidence)
        max_confidence = max(
            extracted_data.transaction_date_confidence,
            extracted_data.items_confidence,
            extracted_data.total_amount_confidence
        )
        confidence_level = extracted_data.get_confidence_level("date")  # Uses same thresholds

        # Determine confidence category based on max confidence
        if max_confidence >= 0.85:
            confidence_category = "high"
        elif max_confidence >= 0.60:
            confidence_category = "medium"
        else:
            confidence_category = "low"

        # Update metrics with file locking
        self._update_metrics_file(
            date_key=today,
            is_successful=is_successful,
            is_failed=is_failed,
            is_partial=is_partial,
            confidence_category=confidence_category,
            extraction_method=extracted_data.extraction_method
        )

        logger.info(f"Recorded metrics for {today}: {extracted_data.extraction_method} extraction")

    def _update_metrics_file(
        self,
        date_key: str,
        is_successful: bool,
        is_failed: bool,
        is_partial: bool,
        confidence_category: str,
        extraction_method: str
    ) -> None:
        """
        Update metrics file with file locking for concurrency safety.

        Args:
            date_key: Date key (YYYY-MM-DD)
            is_successful: Whether extraction was successful
            is_failed: Whether extraction failed completely
            is_partial: Whether extraction was partial
            confidence_category: "low" | "medium" | "high"
            extraction_method: "gemini" | "tesseract_fallback"
        """
        # Use file locking to prevent concurrent write issues
        with open(self.storage_path, 'r+') as f:
            # Acquire exclusive lock
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)

            try:
                # Read current metrics
                f.seek(0)
                try:
                    all_metrics = json.load(f)
                except json.JSONDecodeError:
                    all_metrics = {}

                # Get or create daily metrics
                if date_key not in all_metrics:
                    all_metrics[date_key] = {
                        "date_extracted": date_key,
                        "total_extractions": 0,
                        "successful_extractions": 0,
                        "failed_extractions": 0,
                        "partial_extractions": 0,
                        "confidence_distribution": {"low": 0, "medium": 0, "high": 0},
                        "extraction_method_usage": {"gemini": 0, "tesseract_fallback": 0}
                    }

                daily = all_metrics[date_key]

                # Update counts
                daily["total_extractions"] += 1
                if is_successful:
                    daily["successful_extractions"] += 1
                elif is_failed:
                    daily["failed_extractions"] += 1
                elif is_partial:
                    daily["partial_extractions"] += 1

                # Update confidence distribution
                daily["confidence_distribution"][confidence_category] += 1

                # Update extraction method usage
                if extraction_method in daily["extraction_method_usage"]:
                    daily["extraction_method_usage"][extraction_method] += 1
                else:
                    daily["extraction_method_usage"][extraction_method] = 1

                # Write back to file
                f.seek(0)
                f.truncate()
                json.dump(all_metrics, f, indent=2)

            finally:
                # Release lock
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def get_daily_metrics(self, metric_date: date) -> Optional[ExtractionMetrics]:
        """
        Retrieve metrics for a specific date.

        Args:
            metric_date: Date to retrieve metrics for

        Returns:
            ExtractionMetrics instance, or None if no data for that date
        """
        date_key = metric_date.isoformat()

        with open(self.storage_path, 'r') as f:
            try:
                all_metrics = json.load(f)
            except json.JSONDecodeError:
                logger.warning("Failed to parse metrics file")
                return None

        if date_key not in all_metrics:
            logger.info(f"No metrics found for {date_key}")
            return None

        daily_data = all_metrics[date_key]

        # Convert to ExtractionMetrics
        metrics = ExtractionMetrics(
            date_extracted=metric_date,
            total_extractions=daily_data["total_extractions"],
            successful_extractions=daily_data["successful_extractions"],
            failed_extractions=daily_data["failed_extractions"],
            partial_extractions=daily_data["partial_extractions"],
            confidence_distribution=daily_data["confidence_distribution"],
            extraction_method_usage=daily_data["extraction_method_usage"]
        )

        return metrics
