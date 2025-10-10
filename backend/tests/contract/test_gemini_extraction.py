"""
Contract tests for Gemini Vision API extraction response format.

These tests verify that the GeminiExtractorService correctly:
1. Sends properly formatted requests to Gemini API
2. Parses JSON responses into ExtractedData objects
3. Handles API errors (timeout, rate limit, invalid JSON)

Test must FAIL initially with "ModuleNotFoundError: No module named 'gemini_extractor'"
This proves we're testing the implementation that doesn't exist yet (TDD Red phase).
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import date
from decimal import Decimal


class TestGeminiExtractionResponseFormat:
    """Contract tests for Gemini API response parsing."""

    def test_gemini_request_structure_includes_image_and_json_schema(
        self, mock_gemini_high_quality_response
    ):
        """
        Verify Gemini API request includes image + prompt with JSON schema.

        Expected to FAIL with: ModuleNotFoundError: No module named 'backend.src.services.gemini_extractor'
        """
        # This import will fail - that's expected!
        from backend.src.services.gemini_extractor import GeminiExtractorService

        with patch('google.generativeai.GenerativeModel') as mock_model, \
             patch('PIL.Image.open') as mock_image:
            # Mock image loading
            mock_image.return_value = MagicMock()

            # Mock the generate_content method
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_gemini_high_quality_response
            mock_model.return_value = mock_instance

            # Create service and extract
            service = GeminiExtractorService(api_key="test-key")
            service.extract("fake-image-path.jpg")

            # Verify request was made with correct structure
            mock_instance.generate_content.assert_called_once()
            call_args = mock_instance.generate_content.call_args[0]

            # Should be called with [prompt, image]
            assert len(call_args) >= 1, "Should include prompt in request"

    def test_gemini_response_parsing_to_extracted_data(
        self, mock_gemini_high_quality_response
    ):
        """
        Verify Gemini JSON response correctly parsed into ExtractedData.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.gemini_extractor import GeminiExtractorService
        from backend.src.models.extracted_data import ExtractedData

        with patch('google.generativeai.GenerativeModel') as mock_model, \
             patch('PIL.Image.open') as mock_image:
            # Mock image loading
            mock_image.return_value = MagicMock()

            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_gemini_high_quality_response
            mock_model.return_value = mock_instance

            service = GeminiExtractorService(api_key="test-key")
            result = service.extract("fake-image-path.jpg")

            # Verify result is ExtractedData instance
            assert isinstance(result, ExtractedData)

            # Verify JSON schema fields are correctly parsed
            response_data = json.loads(mock_gemini_high_quality_response.text)
            assert result.transaction_date == date.fromisoformat(response_data["transaction_date"])
            assert result.total_amount == Decimal(str(response_data["total_amount"]))
            assert result.items == response_data["items"]

            # Verify Gemini-specific fields
            assert result.extraction_method == "gemini"
            assert result.detected_language == response_data["detected_language"]
            assert result.currency == response_data["currency"]

            # Verify confidence scores
            assert result.transaction_date_confidence == response_data["confidence"]["date"]
            assert result.total_amount_confidence == response_data["confidence"]["amount"]
            assert result.items_confidence == response_data["confidence"]["items"]

    def test_gemini_api_timeout_error_handling(self):
        """
        Verify timeout errors are properly handled.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.gemini_extractor import GeminiExtractorService, GeminiExtractionError

        with patch('google.generativeai.GenerativeModel') as mock_model, \
             patch('PIL.Image.open') as mock_image:
            # Mock image loading
            mock_image.return_value = MagicMock()

            mock_instance = MagicMock()
            # Simulate timeout
            mock_instance.generate_content.side_effect = TimeoutError("API timeout")
            mock_model.return_value = mock_instance

            service = GeminiExtractorService(api_key="test-key")

            # Should raise custom exception
            with pytest.raises(GeminiExtractionError) as exc_info:
                service.extract("fake-image-path.jpg")

            assert "timeout" in str(exc_info.value).lower()

    def test_gemini_api_rate_limit_error_handling(self):
        """
        Verify rate limit (429) errors are properly handled.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.gemini_extractor import GeminiExtractorService, GeminiExtractionError

        with patch('google.generativeai.GenerativeModel') as mock_model, \
             patch('PIL.Image.open') as mock_image:
            # Mock image loading
            mock_image.return_value = MagicMock()

            mock_instance = MagicMock()
            # Simulate rate limit error
            from google.generativeai.types import GenerationConfig
            rate_limit_error = Exception("429 Rate Limit Exceeded")
            rate_limit_error.status_code = 429
            mock_instance.generate_content.side_effect = rate_limit_error
            mock_model.return_value = mock_instance

            service = GeminiExtractorService(api_key="test-key")

            # Should raise custom exception
            with pytest.raises(GeminiExtractionError) as exc_info:
                service.extract("fake-image-path.jpg")

            assert "rate limit" in str(exc_info.value).lower() or "429" in str(exc_info.value)

    def test_gemini_invalid_json_response_handling(self):
        """
        Verify invalid JSON responses are handled gracefully.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.gemini_extractor import GeminiExtractorService, GeminiExtractionError

        with patch('google.generativeai.GenerativeModel') as mock_model, \
             patch('PIL.Image.open') as mock_image:
            # Mock image loading
            mock_image.return_value = MagicMock()

            mock_instance = MagicMock()
            # Return invalid JSON
            mock_response = MagicMock()
            mock_response.text = "This is not valid JSON"
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance

            service = GeminiExtractorService(api_key="test-key")

            # Should raise custom exception
            with pytest.raises(GeminiExtractionError) as exc_info:
                service.extract("fake-image-path.jpg")

            assert "json" in str(exc_info.value).lower() or "parse" in str(exc_info.value).lower()

    def test_json_schema_validation_all_required_fields(
        self, mock_gemini_high_quality_response
    ):
        """
        Verify JSON schema includes all required fields per data-model.md.

        Required fields:
        - transaction_date
        - items
        - total_amount
        - currency
        - detected_language
        - confidence (with date, amount, items sub-fields)

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.gemini_extractor import GeminiExtractorService

        with patch('google.generativeai.GenerativeModel') as mock_model, \
             patch('PIL.Image.open') as mock_image:
            # Mock image loading
            mock_image.return_value = MagicMock()

            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_gemini_high_quality_response
            mock_model.return_value = mock_instance

            service = GeminiExtractorService(api_key="test-key")
            result = service.extract("fake-image-path.jpg")

            # Verify all required fields are present
            response_data = json.loads(mock_gemini_high_quality_response.text)
            assert "transaction_date" in response_data
            assert "items" in response_data
            assert "total_amount" in response_data
            assert "currency" in response_data
            assert "detected_language" in response_data
            assert "confidence" in response_data

            # Verify confidence sub-fields
            assert "date" in response_data["confidence"]
            assert "amount" in response_data["confidence"]
            assert "items" in response_data["confidence"]

            # Verify confidence values are floats in 0.0-1.0 range
            assert isinstance(response_data["confidence"]["date"], float)
            assert 0.0 <= response_data["confidence"]["date"] <= 1.0
            assert isinstance(response_data["confidence"]["amount"], float)
            assert 0.0 <= response_data["confidence"]["amount"] <= 1.0
            assert isinstance(response_data["confidence"]["items"], float)
            assert 0.0 <= response_data["confidence"]["items"] <= 1.0
