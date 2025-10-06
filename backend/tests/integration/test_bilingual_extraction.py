"""
Integration test for bilingual paraphrasing (ID vs EN).

T011: Bilingual paraphrasing

Expected to FAIL initially because GeminiExtractor not implemented.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock


class TestBilingualExtractionIntegration:
    """Integration tests for language-preserving paraphrasing."""

    @pytest.mark.asyncio
    async def test_indonesian_receipt_paraphrased_in_indonesian(
        self,
        client: AsyncClient,
        sample_receipt_images,
        mock_gemini_high_quality_response,
        gemini_api_key_env
    ):
        """
        T011: Test Indonesian receipt → items paraphrased in Indonesian (not translated).

        Expected:
        - Items paraphrased in Indonesian (e.g., "Nasi Goreng (2 porsi)")
        - NOT translated to English (e.g., "Fried Rice (2 portions)")
        - detected_language="id"

        Expected to FAIL with: GeminiExtractor not implemented
        """
        with patch('backend.src.services.gemini_extractor.GenerativeModel') as mock_model:
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_gemini_high_quality_response
            mock_model.return_value = mock_instance

            # Upload Indonesian receipt
            with open(sample_receipt_images["high_quality"], "rb") as f:
                response = await client.post(
                    "/api/receipts/upload",
                    files={"file": ("receipt.jpeg", f, "image/jpeg")},
                    headers={"session_id": "test-session"}
                )

            # Verify response
            assert response.status_code == 200
            data = response.json()

            extracted = data["extracted_data"]

            # Verify language detection
            assert extracted["detected_language"] == "id"

            # Verify paraphrasing in Indonesian (not English translation)
            items = extracted["items"]
            assert "Nasi Goreng" in items  # Indonesian term preserved
            assert "porsi" in items  # Indonesian word for "portions"
            assert "Fried Rice" not in items  # Not translated to English

    @pytest.mark.asyncio
    async def test_english_receipt_paraphrased_in_english(
        self,
        client: AsyncClient,
        sample_receipt_images,
        mock_gemini_english_receipt_response,
        gemini_api_key_env
    ):
        """
        Test English receipt → items paraphrased in English.

        Expected:
        - Items paraphrased in English (e.g., "Chicken Wings (3 pieces)")
        - detected_language="en"
        - currency="USD"

        Expected to FAIL with: GeminiExtractor not implemented
        """
        with patch('backend.src.services.gemini_extractor.GenerativeModel') as mock_model:
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_gemini_english_receipt_response
            mock_model.return_value = mock_instance

            # Upload English receipt
            with open(sample_receipt_images["english"], "rb") as f:
                response = await client.post(
                    "/api/receipts/upload",
                    files={"file": ("receipt.jpeg", f, "image/jpeg")},
                    headers={"session_id": "test-session"}
                )

            # Verify response
            assert response.status_code == 200
            data = response.json()

            extracted = data["extracted_data"]

            # Verify language detection
            assert extracted["detected_language"] == "en"
            assert extracted["currency"] == "USD"

            # Verify paraphrasing in English
            items = extracted["items"]
            assert "Chicken Wings" in items
            assert "pieces" in items  # English paraphrasing
            assert extracted["paraphrased"] is True
