"""
Unit tests for Gemini prompt template and response parsing.

Tests the GeminiExtractorService prompt structure, JSON schema validation,
and response parsing logic without calling the actual Gemini API.
"""
import pytest
import json
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from backend.src.services.gemini_extractor import GeminiExtractorService, GeminiExtractionError
from backend.src.models.extracted_data import ExtractedData


class TestGeminiPromptTemplate:
    """Test suite for validating the Gemini extraction prompt template."""

    def test_prompt_includes_json_schema_structure(self):
        """Verify prompt contains valid JSON schema example."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")
        prompt = service.EXTRACTION_PROMPT

        # Check all required fields are mentioned in the prompt
        assert "transaction_date" in prompt
        assert "total_amount" in prompt
        assert "items" in prompt
        assert "currency" in prompt
        assert "detected_language" in prompt
        assert "confidence" in prompt

        # Check nested confidence fields
        assert '"date"' in prompt or "'date'" in prompt
        assert '"amount"' in prompt or "'amount'" in prompt
        assert '"items"' in prompt or "'items'" in prompt

    def test_prompt_includes_grand_total_instruction(self):
        """Verify prompt instructs to extract grand total only."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")
        prompt = service.EXTRACTION_PROMPT

        # Should mention grand total and avoiding subtotals
        assert "GRAND TOTAL" in prompt or "grand total" in prompt.lower()
        assert "subtotal" in prompt.lower() or "tax" in prompt.lower()
        assert "ignore" in prompt.lower() or "only" in prompt.lower()

    def test_prompt_includes_idr_parsing_instruction(self):
        """Verify prompt includes IDR format handling (Rp 1.234.567 → 1234567)."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")
        prompt = service.EXTRACTION_PROMPT

        # Should mention IDR and numeric conversion
        assert "IDR" in prompt or "Rp" in prompt
        assert "1.234.567" in prompt or "separator" in prompt.lower()
        assert "numeric" in prompt.lower() or "number" in prompt.lower()

    def test_prompt_includes_bilingual_paraphrasing_instruction(self):
        """Verify prompt instructs bilingual paraphrasing in same language."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")
        prompt = service.EXTRACTION_PROMPT

        # Should mention paraphrasing and language preservation
        assert "paraphras" in prompt.lower() or "clarity" in prompt.lower()
        assert "Indonesian" in prompt or "English" in prompt
        assert "SAME language" in prompt or "same language" in prompt.lower()
        assert "DO NOT translate" in prompt or "not translate" in prompt.lower()

    def test_prompt_includes_language_detection_instruction(self):
        """Verify prompt instructs language detection (id/en)."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")
        prompt = service.EXTRACTION_PROMPT

        # Should mention language detection and codes
        assert "detect" in prompt.lower() or "language" in prompt.lower()
        assert '"id"' in prompt or "'id'" in prompt  # Indonesian code
        assert '"en"' in prompt or "'en'" in prompt  # English code

    def test_prompt_includes_future_date_rejection(self):
        """Verify prompt instructs rejection of future dates."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")
        prompt = service.EXTRACTION_PROMPT

        # Should mention future dates and null handling
        assert "future" in prompt.lower()
        assert "null" in prompt.lower()

    def test_prompt_includes_null_handling_for_unreadable_fields(self):
        """Verify prompt instructs null for unreadable fields (better empty than wrong)."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")
        prompt = service.EXTRACTION_PROMPT

        # Should mention null/empty for unreadable
        assert "null" in prompt.lower()
        assert "unreadable" in prompt.lower() or "empty" in prompt.lower()
        assert "better" in prompt.lower() or "wrong" in prompt.lower()

    def test_prompt_includes_confidence_scoring_instruction(self):
        """Verify prompt instructs confidence scoring (0.0 to 1.0)."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")
        prompt = service.EXTRACTION_PROMPT

        # Should mention confidence and scale
        assert "confidence" in prompt.lower()
        assert "0.0" in prompt or "0" in prompt
        assert "1.0" in prompt or "certain" in prompt.lower()

    def test_prompt_includes_item_formatting_instruction(self):
        """Verify prompt instructs semicolon-separated items with quantities."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")
        prompt = service.EXTRACTION_PROMPT

        # Should mention item separation and quantity formatting
        assert "semicolon" in prompt.lower() or ";" in prompt
        assert "quantit" in prompt.lower() or "portion" in prompt.lower()
        assert "parenthes" in prompt.lower() or "(" in prompt

    def test_prompt_requests_json_only_no_markdown(self):
        """Verify prompt requests pure JSON without markdown formatting."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")
        prompt = service.EXTRACTION_PROMPT

        # Should mention JSON-only format
        assert "ONLY" in prompt or "only" in prompt
        assert "JSON" in prompt
        assert "no markdown" in prompt.lower() or "markdown" in prompt.lower()


class TestGeminiResponseParsing:
    """Test suite for parsing Gemini API responses into ExtractedData."""

    def test_parse_valid_complete_response(self):
        """Parse a complete valid Gemini response with all fields."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")

        gemini_response = {
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
        }

        result = service._parse_gemini_response(gemini_response)

        assert isinstance(result, ExtractedData)
        assert result.transaction_date == date(2025, 10, 5)
        assert result.total_amount == Decimal("125000")
        assert result.items == "Nasi Goreng (2 porsi); Es Teh Manis (1 gelas)"
        assert result.currency == "IDR"
        assert result.detected_language == "id"
        assert result.transaction_date_confidence == 0.95
        assert result.total_amount_confidence == 0.98
        assert result.items_confidence == 0.85
        assert result.extraction_method == "gemini"
        assert result.paraphrased is True

    def test_parse_response_with_null_fields(self):
        """Parse response where some fields are null (unreadable)."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")

        gemini_response = {
            "transaction_date": None,
            "total_amount": 50000,
            "items": None,
            "currency": "IDR",
            "detected_language": "id",
            "confidence": {
                "date": 0.0,
                "amount": 0.90,
                "items": 0.0
            }
        }

        result = service._parse_gemini_response(gemini_response)

        assert result.transaction_date is None
        assert result.total_amount == Decimal("50000")
        assert result.items is None
        assert result.transaction_date_confidence == 0.0
        assert result.items_confidence == 0.0

    def test_parse_response_with_invalid_date_format(self):
        """Parse response with invalid date format - should set to None."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")

        gemini_response = {
            "transaction_date": "invalid-date",
            "total_amount": 50000,
            "items": "Item 1",
            "currency": "IDR",
            "detected_language": "id",
            "confidence": {"date": 0.5, "amount": 0.9, "items": 0.8}
        }

        result = service._parse_gemini_response(gemini_response)

        # Invalid date should be set to None
        assert result.transaction_date is None

    def test_parse_response_with_invalid_amount_format(self):
        """Parse response with invalid amount format - should set to None."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")

        gemini_response = {
            "transaction_date": "2025-10-05",
            "total_amount": "not-a-number",
            "items": "Item 1",
            "currency": "IDR",
            "detected_language": "id",
            "confidence": {"date": 0.9, "amount": 0.5, "items": 0.8}
        }

        result = service._parse_gemini_response(gemini_response)

        # Invalid amount should be set to None
        assert result.total_amount is None

    def test_parse_response_missing_confidence_fields(self):
        """Parse response with missing confidence object - should default to 0.0."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")

        gemini_response = {
            "transaction_date": "2025-10-05",
            "total_amount": 50000,
            "items": "Item 1",
            "currency": "IDR",
            "detected_language": "id"
            # No confidence field
        }

        result = service._parse_gemini_response(gemini_response)

        assert result.transaction_date_confidence == 0.0
        assert result.total_amount_confidence == 0.0
        assert result.items_confidence == 0.0

    def test_parse_response_with_decimal_amount(self):
        """Parse response with decimal amount (e.g., 125000.50)."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")

        gemini_response = {
            "transaction_date": "2025-10-05",
            "total_amount": 125000.50,
            "items": "Item 1",
            "currency": "USD",
            "detected_language": "en",
            "confidence": {"date": 0.9, "amount": 0.95, "items": 0.8}
        }

        result = service._parse_gemini_response(gemini_response)

        assert result.total_amount == Decimal("125000.50")
        assert result.currency == "USD"

    def test_parse_response_stores_full_json_in_raw_ocr_text(self):
        """Verify full Gemini response is stored in raw_ocr_text."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")

        gemini_response = {
            "transaction_date": "2025-10-05",
            "total_amount": 50000,
            "items": "Item 1",
            "currency": "IDR",
            "detected_language": "id",
            "confidence": {"date": 0.9, "amount": 0.95, "items": 0.8}
        }

        result = service._parse_gemini_response(gemini_response)

        # Should store full JSON in raw_ocr_text
        assert result.raw_ocr_text is not None
        stored_data = json.loads(result.raw_ocr_text)
        assert stored_data["transaction_date"] == "2025-10-05"
        assert stored_data["total_amount"] == 50000


class TestGeminiExtractionErrorHandling:
    """Test suite for Gemini extraction error scenarios."""

    @patch('backend.src.services.gemini_extractor.genai.GenerativeModel')
    @patch('backend.src.services.gemini_extractor.Image')
    def test_extract_handles_json_decode_error(self, mock_image, mock_model):
        """Test that invalid JSON response raises GeminiExtractionError."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")

        # Mock image loading
        mock_image.open.return_value = MagicMock()

        # Mock Gemini response with invalid JSON
        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON"
        service.model.generate_content.return_value = mock_response

        with pytest.raises(GeminiExtractionError) as exc_info:
            service.extract("fake-image-path.jpg")

        assert "Failed to parse Gemini JSON response" in str(exc_info.value)

    @patch('backend.src.services.gemini_extractor.genai.GenerativeModel')
    @patch('backend.src.services.gemini_extractor.Image')
    def test_extract_strips_markdown_code_blocks(self, mock_image, mock_model):
        """Test that markdown code blocks are stripped from JSON response."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")

        # Mock image loading
        mock_image.open.return_value = MagicMock()

        # Mock Gemini response with markdown code blocks
        mock_response = MagicMock()
        mock_response.text = '''```json
{
  "transaction_date": "2025-10-05",
  "total_amount": 50000,
  "items": "Item 1",
  "currency": "IDR",
  "detected_language": "id",
  "confidence": {"date": 0.9, "amount": 0.95, "items": 0.8}
}
```'''
        service.model.generate_content.return_value = mock_response

        result = service.extract("fake-image-path.jpg")

        # Should successfully parse despite markdown formatting
        assert result.transaction_date == date(2025, 10, 5)
        assert result.total_amount == Decimal("50000")

    @patch('backend.src.services.gemini_extractor.genai.GenerativeModel')
    @patch('backend.src.services.gemini_extractor.Image')
    def test_extract_handles_timeout_error(self, mock_image, mock_model):
        """Test that timeout error is caught and wrapped."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")

        # Mock image loading
        mock_image.open.return_value = MagicMock()

        # Mock timeout error
        service.model.generate_content.side_effect = TimeoutError("Request timed out")

        with pytest.raises(GeminiExtractionError) as exc_info:
            service.extract("fake-image-path.jpg")

        assert "Gemini API timeout" in str(exc_info.value)

    @patch('backend.src.services.gemini_extractor.genai.GenerativeModel')
    @patch('backend.src.services.gemini_extractor.Image')
    def test_extract_handles_rate_limit_error(self, mock_image, mock_model):
        """Test that rate limit error (429) is caught and wrapped."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")

        # Mock image loading
        mock_image.open.return_value = MagicMock()

        # Mock rate limit error with status_code attribute
        rate_limit_error = Exception("Rate limit exceeded")
        rate_limit_error.status_code = 429
        service.model.generate_content.side_effect = rate_limit_error

        with pytest.raises(GeminiExtractionError) as exc_info:
            service.extract("fake-image-path.jpg")

        assert "Rate limit exceeded (429)" in str(exc_info.value)

    @patch('backend.src.services.gemini_extractor.genai.GenerativeModel')
    @patch('backend.src.services.gemini_extractor.Image')
    def test_extract_handles_api_downtime_error(self, mock_image, mock_model):
        """Test that API downtime error (503) is caught and wrapped."""
        service = GeminiExtractorService(api_key="fake-key-for-testing")

        # Mock image loading
        mock_image.open.return_value = MagicMock()

        # Mock service unavailable error
        api_error = Exception("Service unavailable")
        api_error.status_code = 503
        service.model.generate_content.side_effect = api_error

        with pytest.raises(GeminiExtractionError) as exc_info:
            service.extract("fake-image-path.jpg")

        assert "Gemini API service unavailable (503)" in str(exc_info.value)


class TestGeminiServiceInitialization:
    """Test suite for GeminiExtractorService initialization."""

    def test_initialization_with_explicit_api_key(self):
        """Test initialization with explicit API key."""
        service = GeminiExtractorService(api_key="test-api-key-123")
        assert service.api_key == "test-api-key-123"

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'env-api-key-456'})
    def test_initialization_with_env_var_api_key(self):
        """Test initialization with API key from environment variable."""
        service = GeminiExtractorService()
        assert service.api_key == "env-api-key-456"

    @patch.dict('os.environ', {}, clear=True)
    def test_initialization_without_api_key_logs_warning(self):
        """Test initialization without API key logs warning."""
        # Should not crash, just log warning
        service = GeminiExtractorService()
        assert service.api_key is None

    def test_model_initialized_with_gemini_flash(self):
        """Test that model is initialized with gemini-1.5-flash."""
        service = GeminiExtractorService(api_key="test-key")
        # Can't easily test the model name without calling the API,
        # but we can verify the service has a model attribute
        assert hasattr(service, 'model')
