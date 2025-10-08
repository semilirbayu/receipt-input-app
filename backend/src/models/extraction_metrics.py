"""
ExtractionMetrics model for tracking extraction quality metrics.

Supports FR-020 requirement: track success rate and confidence distribution.
Stored in shared/extraction_metrics.json as daily aggregated metrics.
"""
from dataclasses import dataclass
from datetime import date
from typing import Dict


@dataclass
class ExtractionMetrics:
    """
    Daily aggregated metrics for extraction quality monitoring.

    Used to track and analyze extraction performance over time.
    Enables identification of quality trends and system improvements.

    Attributes:
        date_extracted: Metrics aggregation date
        total_extractions: Total receipts processed on this date
        successful_extractions: All 3 fields populated (date, items, amount)
        failed_extractions: All 3 fields null
        partial_extractions: Some fields populated, some null
        confidence_distribution: Counts per level {"low": 5, "medium": 10, "high": 20}
        extraction_method_usage: Method counts {"gemini": 30, "tesseract_fallback": 5}
    """

    date_extracted: date
    total_extractions: int
    successful_extractions: int
    failed_extractions: int
    partial_extractions: int
    confidence_distribution: Dict[str, int]  # {"low": X, "medium": Y, "high": Z}
    extraction_method_usage: Dict[str, int]  # {"gemini": X, "tesseract_fallback": Y}

    def get_success_rate(self) -> float:
        """
        Calculate success rate as percentage.

        Returns:
            Success rate (0.0-100.0), or 0.0 if no extractions
        """
        if self.total_extractions == 0:
            return 0.0
        return (self.successful_extractions / self.total_extractions) * 100

    def get_gemini_usage_rate(self) -> float:
        """
        Calculate percentage of extractions using Gemini (vs fallback).

        Returns:
            Gemini usage rate (0.0-100.0), or 0.0 if no extractions
        """
        if self.total_extractions == 0:
            return 0.0
        gemini_count = self.extraction_method_usage.get("gemini", 0)
        return (gemini_count / self.total_extractions) * 100

    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dict suitable for API responses and JSON storage
        """
        return {
            "date": self.date_extracted.isoformat(),
            "total": self.total_extractions,
            "successful": self.successful_extractions,
            "failed": self.failed_extractions,
            "partial": self.partial_extractions,
            "success_rate": round(self.get_success_rate(), 2),
            "confidence_distribution": self.confidence_distribution,
            "extraction_methods": self.extraction_method_usage,
            "gemini_usage_rate": round(self.get_gemini_usage_rate(), 2)
        }
