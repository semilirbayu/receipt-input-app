"""
Integration tests for receipt upload with Gemini Vision API.

T007: High-quality Indonesian receipt (Gemini extraction)
T008: Low-quality blurry receipt handling

These tests verify end-to-end flow: Upload → Extract (Gemini) → Validate → Response
Expected to FAIL initially because route still uses old OCR service.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
import json


class TestReceiptUploadGeminiIntegration:
    """Integration tests for Gemini-based receipt upload endpoint."""

    @pytest.mark.asyncio
    async def test_high_quality_indonesian_receipt_gemini_extraction(
        self,
        client: AsyncClient,
        sample_receipt_images,
        mock_gemini_high_quality_response,
        gemini_api_key_env
    ):
        """
        T007: POST /api/receipts/upload with high-quality Indonesian receipt.

        Expected behavior:
        - extraction_method="gemini"
        - detected_language="id"
        - currency="IDR"
        - items are paraphrased (not raw OCR)
        - processing time <5000ms (FR-025)

        Expected to FAIL with: Route still uses old OCR service, not Gemini
        """
        with patch('backend.src.services.gemini_extractor.GenerativeModel') as mock_model:
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_gemini_high_quality_response
            mock_model.return_value = mock_instance

            # Upload receipt
            with open(sample_receipt_images["high_quality"], "rb") as f:
                response = await client.post(
                    "/api/receipts/upload",
                    files={"file": ("receipt.jpeg", f, "image/jpeg")},
                    headers={"session_id": "test-session"}
                )

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Verify Gemini extraction
            extracted = data["extracted_data"]
            assert extracted["extraction_method"] == "gemini"
            assert extracted["detected_language"] == "id"
            assert extracted["currency"] == "IDR"
            assert extracted["paraphrased"] is True

            # Verify data quality
            assert extracted["transaction_date"] is not None
            assert extracted["items"] == "Nasi Goreng (2 porsi); Es Teh Manis"
            assert extracted["total_amount"] == 50000

            # Verify confidence indicators
            assert extracted["confidence_indicators"]["date"] == "✓"
            assert extracted["confidence_indicators"]["amount"] == "✓"

            # Verify processing time
            assert data["processing_time_ms"] < 5000

    @pytest.mark.asyncio
    async def test_low_quality_blurry_receipt_handling(
        self,
        client: AsyncClient,
        sample_receipt_images,
        mock_gemini_low_quality_response,
        gemini_api_key_env
    ):
        """
        T008: POST /api/receipts/upload with low-quality/blurry receipt.

        Expected behavior:
        - Low confidence scores (<0.6 for some fields)
        - Fields may be set to null when confidence too low (FR-004: better empty than wrong)
        - validation.warnings includes "low_image_quality"
        - Confidence indicators show "⚠" or "✗"

        Expected to FAIL with: Route not implemented for Gemini
        """
        with patch('backend.src.services.gemini_extractor.GenerativeModel') as mock_model:
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_gemini_low_quality_response
            mock_model.return_value = mock_instance

            # Upload blurry receipt
            with open(sample_receipt_images["low_quality"], "rb") as f:
                response = await client.post(
                    "/api/receipts/upload",
                    files={"file": ("receipt.jpeg", f, "image/jpeg")},
                    headers={"session_id": "test-session"}
                )

            # Verify response
            assert response.status_code == 200
            data = response.json()

            extracted = data["extracted_data"]

            # Verify low confidence handling
            assert extracted["transaction_date"] is None or extracted["transaction_date_confidence"] < 0.6
            assert extracted["items_confidence"] < 0.7
            assert extracted["total_amount_confidence"] < 0.85

            # Verify confidence indicators
            assert extracted["confidence_indicators"]["date"] in ["⚠", "✗"]
            assert extracted["confidence_indicators"]["items"] in ["⚠", "✗"]

            # Verify warnings
            assert "low_image_quality" in data["validation"]["warnings"] or \
                   "date_confidence_below_threshold" in data["validation"]["warnings"]

            # Still returns 200 (not error)
            assert response.status_code == 200
