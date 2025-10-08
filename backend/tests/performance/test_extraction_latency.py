"""
Performance tests for receipt extraction latency.

Validates that extraction processing meets the <5 second p95 latency requirement (FR-025).
Can run with either real Gemini API or realistic mocks.
"""
import pytest
import time
import statistics
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from backend.src.services.gemini_extractor import GeminiExtractorService


class TestExtractionLatency:
    """Test suite for validating extraction performance requirements."""

    @pytest.fixture
    def sample_receipt_image(self):
        """Get path to a sample receipt image for testing."""
        # Use existing test fixture
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "receipts"

        # Try to find any valid receipt image
        for image_file in ["testing-receipt.jpeg", "testing-receipt.jpg", "sample-receipt.jpg"]:
            image_path = fixtures_path / image_file
            if image_path.exists():
                return str(image_path)

        # If no fixture found, use a mock path (will need mocking)
        return "fake-receipt-for-performance-test.jpg"

    @pytest.fixture
    def mock_gemini_response(self):
        """Create a realistic mock Gemini response for performance testing."""
        mock_response = MagicMock()
        mock_response.text = '''{
            "transaction_date": "2025-10-05",
            "total_amount": 125000,
            "items": "Nasi Goreng (2 porsi); Es Teh Manis (1 gelas)",
            "currency": "IDR",
            "detected_language": "id",
            "confidence": {
                "date": 0.95,
                "amount": 0.98,
                "items": 0.85
            }
        }'''
        return mock_response

    @patch('backend.src.services.gemini_extractor.genai.GenerativeModel')
    @patch('backend.src.services.gemini_extractor.Image')
    def test_p95_latency_under_5_seconds_with_mocks(
        self, mock_image, mock_model, sample_receipt_image, mock_gemini_response
    ):
        """
        Test that p95 latency is under 5000ms using mocked Gemini API.

        Requirement: FR-025 - Processing time must not exceed 5 seconds.
        """
        # Mock image loading
        mock_image.open.return_value = MagicMock()

        # Create service and mock API with realistic delay
        service = GeminiExtractorService(api_key="fake-key-for-testing")

        def mock_generate_with_delay(*args, **kwargs):
            """Simulate realistic API latency (500ms-2000ms)."""
            time.sleep(0.5 + (hash(str(time.time())) % 15) / 10)  # 500ms-2000ms
            return mock_gemini_response

        service.model.generate_content = mock_generate_with_delay

        # Run 100 extraction requests
        latencies = []
        num_requests = 100

        print(f"\nRunning {num_requests} extraction requests...")
        for i in range(num_requests):
            start_time = time.time()
            try:
                result = service.extract(sample_receipt_image)
                latency_ms = (time.time() - start_time) * 1000
                latencies.append(latency_ms)

                if (i + 1) % 20 == 0:
                    print(f"Completed {i + 1}/{num_requests} requests...")
            except Exception as e:
                pytest.fail(f"Extraction failed on request {i + 1}: {e}")

        # Calculate percentiles
        latencies.sort()
        p50 = statistics.median(latencies)
        p95_index = int(len(latencies) * 0.95)
        p95 = latencies[p95_index]
        p99_index = int(len(latencies) * 0.99)
        p99 = latencies[p99_index]
        mean = statistics.mean(latencies)

        # Print performance metrics
        print(f"\n{'='*60}")
        print(f"Performance Test Results ({num_requests} requests)")
        print(f"{'='*60}")
        print(f"Mean latency:   {mean:.2f}ms")
        print(f"P50 latency:    {p50:.2f}ms")
        print(f"P95 latency:    {p95:.2f}ms")
        print(f"P99 latency:    {p99:.2f}ms")
        print(f"Min latency:    {min(latencies):.2f}ms")
        print(f"Max latency:    {max(latencies):.2f}ms")
        print(f"{'='*60}")

        # Assert requirements
        assert p95 < 5000, (
            f"P95 latency ({p95:.2f}ms) exceeds 5000ms requirement (FR-025)"
        )

        # Additional assertion for typical case
        assert p50 < 3500, (
            f"P50 latency ({p50:.2f}ms) should be under 3500ms for typical cases"
        )

    @patch('backend.src.services.gemini_extractor.genai.GenerativeModel')
    @patch('backend.src.services.gemini_extractor.Image')
    def test_single_extraction_latency(
        self, mock_image, mock_model, sample_receipt_image, mock_gemini_response
    ):
        """
        Test that a single extraction completes within reasonable time.

        This is a faster smoke test for CI/CD pipelines.
        """
        # Mock image loading
        mock_image.open.return_value = MagicMock()

        # Create service
        service = GeminiExtractorService(api_key="fake-key-for-testing")

        # Mock API with realistic delay
        def mock_generate_with_delay(*args, **kwargs):
            time.sleep(1.0)  # Simulate 1 second API call
            return mock_gemini_response

        service.model.generate_content = mock_generate_with_delay

        # Measure single extraction
        start_time = time.time()
        result = service.extract(sample_receipt_image)
        latency_ms = (time.time() - start_time) * 1000

        print(f"\nSingle extraction latency: {latency_ms:.2f}ms")

        # Should complete well under 5 seconds
        assert latency_ms < 5000, (
            f"Single extraction took {latency_ms:.2f}ms, exceeds 5000ms limit"
        )

        # Verify extraction succeeded
        assert result.extraction_method == "gemini"
        assert result.transaction_date is not None

    @pytest.mark.skipif(
        "not config.getoption('--run-live-api')",
        reason="Only run with --run-live-api flag (requires real Gemini API key)"
    )
    def test_p95_latency_with_real_gemini_api(self, sample_receipt_image):
        """
        Test p95 latency with real Gemini API.

        WARNING: This test makes real API calls and incurs costs.
        Only run manually with: pytest --run-live-api -k test_p95_latency_with_real

        Requires GEMINI_API_KEY environment variable.
        """
        service = GeminiExtractorService()  # Uses env var

        if not service.api_key:
            pytest.skip("GEMINI_API_KEY not set, skipping live API test")

        # Run 20 requests (fewer than mock test to reduce costs)
        latencies = []
        num_requests = 20

        print(f"\nRunning {num_requests} LIVE API requests...")
        for i in range(num_requests):
            start_time = time.time()
            try:
                result = service.extract(sample_receipt_image)
                latency_ms = (time.time() - start_time) * 1000
                latencies.append(latency_ms)

                print(f"Request {i + 1}/{num_requests}: {latency_ms:.2f}ms")

                # Rate limiting: wait 100ms between requests
                time.sleep(0.1)
            except Exception as e:
                print(f"Warning: Request {i + 1} failed: {e}")
                continue

        if len(latencies) < 10:
            pytest.skip(f"Too many failures ({num_requests - len(latencies)}), cannot measure latency")

        # Calculate percentiles
        latencies.sort()
        p50 = statistics.median(latencies)
        p95_index = int(len(latencies) * 0.95)
        p95 = latencies[p95_index]
        mean = statistics.mean(latencies)

        # Print performance metrics
        print(f"\n{'='*60}")
        print(f"LIVE API Performance Results ({len(latencies)} successful requests)")
        print(f"{'='*60}")
        print(f"Mean latency:   {mean:.2f}ms")
        print(f"P50 latency:    {p50:.2f}ms")
        print(f"P95 latency:    {p95:.2f}ms")
        print(f"Min latency:    {min(latencies):.2f}ms")
        print(f"Max latency:    {max(latencies):.2f}ms")
        print(f"{'='*60}")

        # Assert requirement
        assert p95 < 5000, (
            f"LIVE API P95 latency ({p95:.2f}ms) exceeds 5000ms requirement"
        )


def pytest_addoption(parser):
    """Add custom command-line option for live API tests."""
    parser.addoption(
        "--run-live-api",
        action="store_true",
        default=False,
        help="Run tests that make real Gemini API calls (incurs costs)"
    )


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "live_api: mark test as making real API calls (deselect with '-m \"not live_api\"')"
    )
