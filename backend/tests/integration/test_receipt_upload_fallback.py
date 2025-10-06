"""
Integration test for Gemini API failure triggering Tesseract fallback.

T009: Gemini API failure triggers Tesseract fallback

Expected to FAIL initially because fallback logic not implemented.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock


class TestGeminiFallbackMechanism:
    """Integration tests for fallback from Gemini to Tesseract."""

    @pytest.mark.asyncio
    async def test_gemini_rate_limit_triggers_tesseract_fallback(
        self,
        client: AsyncClient,
        sample_receipt_images,
        gemini_api_key_env
    ):
        """
        T009: Mock Gemini API to raise RateLimitError (429).

        Expected behavior:
        - System falls back to Tesseract OCR
        - extraction_method="tesseract_fallback"
        - validation.warnings includes "gemini_api_unavailable"
        - Extraction still completes (not 500 error)

        Expected to FAIL with: Fallback logic not implemented
        """
        # Mock Gemini to raise rate limit error
        with patch('backend.src.services.gemini_extractor.GenerativeModel') as mock_model:
            mock_instance = MagicMock()

            # Simulate 429 rate limit error
            rate_limit_error = Exception("429 Resource Exhausted")
            rate_limit_error.status_code = 429
            mock_instance.generate_content.side_effect = rate_limit_error
            mock_model.return_value = mock_instance

            # Upload receipt
            with open(sample_receipt_images["high_quality"], "rb") as f:
                response = await client.post(
                    "/api/receipts/upload",
                    files={"file": ("receipt.jpeg", f, "image/jpeg")},
                    headers={"session_id": "test-session"}
                )

            # Verify fallback behavior
            assert response.status_code == 200
            data = response.json()

            # Verify Tesseract fallback used
            extracted = data["extracted_data"]
            assert extracted["extraction_method"] == "tesseract_fallback"
            assert extracted["paraphrased"] is False  # Tesseract doesn't paraphrase
            assert extracted["detected_language"] is None  # Tesseract doesn't detect language

            # Verify warnings
            assert "gemini_api_unavailable" in data["validation"]["warnings"] or \
                   "using_fallback_extraction" in data["validation"]["warnings"]

            # Verify extraction still completed
            assert extracted["transaction_date"] is not None or \
                   extracted["items"] is not None or \
                   extracted["total_amount"] is not None

    @pytest.mark.asyncio
    async def test_gemini_timeout_triggers_fallback(
        self,
        client: AsyncClient,
        sample_receipt_images,
        gemini_api_key_env
    ):
        """
        Test Gemini API timeout triggers Tesseract fallback.

        Expected to FAIL with: Fallback logic not implemented
        """
        with patch('backend.src.services.gemini_extractor.GenerativeModel') as mock_model:
            mock_instance = MagicMock()
            mock_instance.generate_content.side_effect = TimeoutError("API timeout")
            mock_model.return_value = mock_instance

            # Upload receipt
            with open(sample_receipt_images["high_quality"], "rb") as f:
                response = await client.post(
                    "/api/receipts/upload",
                    files={"file": ("receipt.jpeg", f, "image/jpeg")},
                    headers={"session_id": "test-session"}
                )

            # Verify fallback
            assert response.status_code == 200
            data = response.json()
            assert data["extracted_data"]["extraction_method"] == "tesseract_fallback"

    @pytest.mark.asyncio
    async def test_gemini_api_downtime_triggers_fallback(
        self,
        client: AsyncClient,
        sample_receipt_images,
        gemini_api_key_env
    ):
        """
        Test Gemini API service downtime (503) triggers fallback.

        Expected to FAIL with: Fallback logic not implemented
        """
        with patch('backend.src.services.gemini_extractor.GenerativeModel') as mock_model:
            mock_instance = MagicMock()
            api_error = Exception("503 Service Unavailable")
            api_error.status_code = 503
            mock_instance.generate_content.side_effect = api_error
            mock_model.return_value = mock_instance

            # Upload receipt
            with open(sample_receipt_images["high_quality"], "rb") as f:
                response = await client.post(
                    "/api/receipts/upload",
                    files={"file": ("receipt.jpeg", f, "image/jpeg")},
                    headers={"session_id": "test-session"}
                )

            # Verify fallback
            assert response.status_code == 200
            data = response.json()
            assert data["extracted_data"]["extraction_method"] == "tesseract_fallback"
