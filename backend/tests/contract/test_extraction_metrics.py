"""
Contract tests for extraction metrics tracking.

These tests verify that ExtractionMetrics correctly:
1. Aggregates success rates (successful vs total extractions)
2. Tracks confidence distribution (low/medium/high counts)
3. Records extraction method usage (gemini vs tesseract_fallback)
4. Persists metrics to shared/extraction_metrics.json

Test must FAIL initially with "ModuleNotFoundError: No module named 'extraction_metrics'"
"""
import pytest
from datetime import date
import json
from pathlib import Path


class TestExtractionMetrics:
    """Contract tests for metrics aggregation and calculation."""

    def test_success_rate_calculation(self):
        """
        Verify success rate is correctly calculated as percentage.

        Success rate = (successful_extractions / total_extractions) * 100

        Expected to FAIL with: ModuleNotFoundError: No module named 'backend.src.models.extraction_metrics'
        """
        from backend.src.models.extraction_metrics import ExtractionMetrics

        metrics = ExtractionMetrics(
            date_extracted=date.today(),
            total_extractions=10,
            successful_extractions=8,
            failed_extractions=1,
            partial_extractions=1,
            confidence_distribution={"low": 2, "medium": 3, "high": 5},
            extraction_method_usage={"gemini": 9, "tesseract_fallback": 1}
        )

        success_rate = metrics.get_success_rate()

        assert success_rate == 80.0  # 8/10 * 100

    def test_success_rate_with_zero_extractions(self):
        """
        Success rate should be 0.0 when total_extractions is 0 (avoid division by zero).

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.models.extraction_metrics import ExtractionMetrics

        metrics = ExtractionMetrics(
            date_extracted=date.today(),
            total_extractions=0,
            successful_extractions=0,
            failed_extractions=0,
            partial_extractions=0,
            confidence_distribution={},
            extraction_method_usage={}
        )

        success_rate = metrics.get_success_rate()

        assert success_rate == 0.0

    def test_gemini_usage_rate_calculation(self):
        """
        Verify Gemini usage rate is correctly calculated as percentage.

        Gemini usage rate = (gemini_count / total_extractions) * 100

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.models.extraction_metrics import ExtractionMetrics

        metrics = ExtractionMetrics(
            date_extracted=date.today(),
            total_extractions=20,
            successful_extractions=18,
            failed_extractions=1,
            partial_extractions=1,
            confidence_distribution={"low": 3, "medium": 7, "high": 10},
            extraction_method_usage={"gemini": 18, "tesseract_fallback": 2}
        )

        gemini_rate = metrics.get_gemini_usage_rate()

        assert gemini_rate == 90.0  # 18/20 * 100

    def test_confidence_distribution_tracking(self):
        """
        Verify confidence distribution correctly tracks low/medium/high counts.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.models.extraction_metrics import ExtractionMetrics

        metrics = ExtractionMetrics(
            date_extracted=date.today(),
            total_extractions=15,
            successful_extractions=12,
            failed_extractions=2,
            partial_extractions=1,
            confidence_distribution={"low": 4, "medium": 6, "high": 5},
            extraction_method_usage={"gemini": 14, "tesseract_fallback": 1}
        )

        # Verify distribution
        assert metrics.confidence_distribution["low"] == 4
        assert metrics.confidence_distribution["medium"] == 6
        assert metrics.confidence_distribution["high"] == 5

        # Total should match
        total_in_distribution = sum(metrics.confidence_distribution.values())
        assert total_in_distribution == 15

    def test_extraction_method_usage_tracking(self):
        """
        Verify extraction method usage correctly tracks gemini vs tesseract_fallback.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.models.extraction_metrics import ExtractionMetrics

        metrics = ExtractionMetrics(
            date_extracted=date.today(),
            total_extractions=25,
            successful_extractions=23,
            failed_extractions=1,
            partial_extractions=1,
            confidence_distribution={"low": 2, "medium": 8, "high": 15},
            extraction_method_usage={"gemini": 23, "tesseract_fallback": 2}
        )

        # Verify method counts
        assert metrics.extraction_method_usage["gemini"] == 23
        assert metrics.extraction_method_usage["tesseract_fallback"] == 2

        # Total should match
        total_methods = sum(metrics.extraction_method_usage.values())
        assert total_methods == 25

    def test_metrics_to_dict_serialization(self):
        """
        Verify metrics can be serialized to dictionary for JSON storage.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.models.extraction_metrics import ExtractionMetrics

        metrics = ExtractionMetrics(
            date_extracted=date(2025, 10, 6),
            total_extractions=10,
            successful_extractions=8,
            failed_extractions=1,
            partial_extractions=1,
            confidence_distribution={"low": 2, "medium": 3, "high": 5},
            extraction_method_usage={"gemini": 9, "tesseract_fallback": 1}
        )

        metrics_dict = metrics.to_dict()

        # Verify required fields
        assert metrics_dict["date"] == "2025-10-06"
        assert metrics_dict["total"] == 10
        assert metrics_dict["successful"] == 8
        assert metrics_dict["failed"] == 1
        assert metrics_dict["partial"] == 1
        assert metrics_dict["success_rate"] == 80.0
        assert metrics_dict["gemini_usage_rate"] == 90.0
        assert metrics_dict["confidence_distribution"] == {"low": 2, "medium": 3, "high": 5}
        assert metrics_dict["extraction_methods"] == {"gemini": 9, "tesseract_fallback": 1}


class TestMetricsService:
    """Contract tests for metrics recording and persistence."""

    def test_record_extraction_updates_daily_metrics(self, tmp_path):
        """
        Verify recording extraction updates daily metrics in shared/extraction_metrics.json.

        Expected to FAIL with: ModuleNotFoundError: No module named 'backend.src.services.metrics_service'
        """
        from backend.src.services.metrics_service import MetricsService
        from backend.src.models.extracted_data import ExtractedData
        from decimal import Decimal

        # Create temporary metrics file
        metrics_file = tmp_path / "extraction_metrics.json"

        # Initialize service with custom storage path
        service = MetricsService(storage_path=metrics_file)

        # Create sample extracted data
        extracted = ExtractedData(
            receipt_id="test-123",
            transaction_date=date.today(),
            transaction_date_confidence=0.95,
            items="Test items",
            items_confidence=0.90,
            total_amount=Decimal("50000"),
            total_amount_confidence=0.98,
            extraction_method="gemini",
            detected_language="id",
            currency="IDR"
        )

        # Record extraction
        service.record_extraction(extracted)

        # Verify metrics file created
        assert metrics_file.exists()

        # Verify metrics updated
        with open(metrics_file, "r") as f:
            metrics_data = json.load(f)

        today_key = date.today().isoformat()
        assert today_key in metrics_data

        daily_metrics = metrics_data[today_key]
        assert daily_metrics["total_extractions"] == 1
        assert daily_metrics["successful_extractions"] == 1  # All 3 fields populated
        assert daily_metrics["extraction_method_usage"]["gemini"] == 1

    def test_get_daily_metrics_retrieves_correct_date(self, tmp_path):
        """
        Verify retrieving metrics for specific date.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.metrics_service import MetricsService
        from backend.src.models.extraction_metrics import ExtractionMetrics

        # Create temporary metrics file with test data
        metrics_file = tmp_path / "extraction_metrics.json"
        test_data = {
            "2025-10-06": {
                "date_extracted": "2025-10-06",
                "total_extractions": 5,
                "successful_extractions": 4,
                "failed_extractions": 0,
                "partial_extractions": 1,
                "confidence_distribution": {"low": 1, "medium": 2, "high": 2},
                "extraction_method_usage": {"gemini": 5, "tesseract_fallback": 0}
            }
        }

        with open(metrics_file, "w") as f:
            json.dump(test_data, f)

        # Initialize service
        service = MetricsService(storage_path=metrics_file)

        # Retrieve metrics
        metrics = service.get_daily_metrics(date(2025, 10, 6))

        # Verify
        assert isinstance(metrics, ExtractionMetrics)
        assert metrics.total_extractions == 5
        assert metrics.successful_extractions == 4

    def test_concurrent_metric_updates_file_locking(self, tmp_path):
        """
        Verify concurrent metric updates don't corrupt data (basic file locking).

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.metrics_service import MetricsService
        from backend.src.models.extracted_data import ExtractedData
        from decimal import Decimal

        metrics_file = tmp_path / "extraction_metrics.json"
        service = MetricsService(storage_path=metrics_file)

        # Simulate concurrent updates (in real scenario, would use threading)
        for i in range(5):
            extracted = ExtractedData(
                receipt_id=f"test-{i}",
                transaction_date=date.today(),
                transaction_date_confidence=0.90,
                items="Test items",
                items_confidence=0.85,
                total_amount=Decimal("10000"),
                total_amount_confidence=0.95,
                extraction_method="gemini",
                detected_language="id",
                currency="IDR"
            )
            service.record_extraction(extracted)

        # Verify all 5 extractions recorded
        with open(metrics_file, "r") as f:
            metrics_data = json.load(f)

        today_key = date.today().isoformat()
        assert metrics_data[today_key]["total_extractions"] == 5
