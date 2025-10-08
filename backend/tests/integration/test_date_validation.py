"""
Integration test for future date rejection.

T010: Future date rejection

Expected to FAIL initially because validation not implemented.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock


class TestDateValidationIntegration:
    """Integration tests for date validation in extraction flow."""

    @pytest.mark.asyncio
    async def test_future_date_rejection_in_extraction(
        self,
        client: AsyncClient,
        sample_receipt_images,
        mock_gemini_future_date_response,
        gemini_api_key_env
    ):
        """
        T010: Mock Gemini to return future date "2026-01-01".

        Expected behavior:
        - Date field set to null
        - validation_errors includes "future_date_rejected"
        - Confidence score reduced to 0.0
        - Confidence indicator shows "✗"

        Expected to FAIL with: Validation not implemented
        """
        with patch('backend.src.services.gemini_extractor.GenerativeModel') as mock_model:
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_gemini_future_date_response
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

            extracted = data["extracted_data"]

            # Verify future date rejected
            assert extracted["transaction_date"] is None
            assert extracted["transaction_date_confidence"] == 0.0
            assert extracted["confidence_indicators"]["date"] == "✗"

            # Verify validation errors
            validation = data["validation"]
            assert validation["date_valid"] is False
            # Check for validation error message
            assert any("future" in str(msg).lower() for msg in validation.get("warnings", []))
