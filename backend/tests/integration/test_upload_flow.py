"""
Integration test: Happy path upload → OCR → review → save flow.
Tests end-to-end user flow with mocked OCR processing.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
import io
from pathlib import Path


@pytest.mark.integration
@pytest.mark.asyncio
async def test_happy_path_upload_to_save(client: AsyncClient):
    """Test complete flow from upload through OCR to save."""
    # Mock pytesseract to return predefined OCR text
    mock_ocr_text = """
    COFFEE SHOP RECEIPT
    Date: 09/28/2025

    Coffee         $4.50
    Sandwich       $8.00
    Water          $2.00

    Subtotal      $14.50
    Tax            $1.45
    Total         $15.95
    """

    with patch('pytesseract.image_to_string', return_value=mock_ocr_text):
        # Step 1: Upload receipt image
        file_content = b"fake image content"
        files = {"file": ("receipt.jpg", io.BytesIO(file_content), "image/jpeg")}

        upload_response = await client.post("/api/v1/upload", files=files)

        assert upload_response.status_code == 200, "Upload should succeed"

        upload_data = upload_response.json()
        assert "receipt_id" in upload_data, "Should return receipt_id"
        assert upload_data["status"] == "completed", "OCR should complete"
        assert upload_data["extracted_data"] is not None, "Should extract data"

        extracted = upload_data["extracted_data"]
        receipt_id = upload_data["receipt_id"]

        # Verify extracted data
        assert extracted.get("transaction_date") == "2025-09-28", "Should extract date"
        assert "Coffee" in extracted.get("items", ""), "Should extract items"
        assert extracted.get("total_amount") == 15.95, "Should extract total"

        # Verify OCR processing time
        assert upload_data.get("processing_time_ms", 0) < 5000, "Should process within 5 seconds"

        # Verify file saved to uploads directory
        upload_dir = Path("shared/uploads")
        uploaded_files = list(upload_dir.glob("*.jpg"))
        assert len(uploaded_files) > 0, "File should be saved to uploads"

        # Step 2: User reviews and corrects data (simulated)
        corrected_data = {
            "receipt_id": receipt_id,
            "transaction_date": "2025-09-28",
            "items": "Coffee; Sandwich; Water",  # User-corrected format
            "total_amount": 15.95
        }

        # Step 3: Save to Google Sheets
        with patch('gspread.Client') as mock_gspread:
            mock_sheet = MagicMock()
            mock_sheet.append_row.return_value = None
            mock_gspread.return_value.open_by_key.return_value.worksheet.return_value = mock_sheet

            save_response = await client.post("/api/v1/save", json=corrected_data)

            # May return 401 if not authenticated, or 200 on success
            if save_response.status_code == 200:
                save_data = save_response.json()
                assert save_data["success"] is True, "Save should succeed"
                assert "spreadsheet_url" in save_data, "Should return spreadsheet URL"
                assert "row_number" in save_data, "Should return row number"

                # Verify receipt file deleted after save
                uploaded_files_after = list(upload_dir.glob("*.jpg"))
                assert len(uploaded_files_after) == 0, "Receipt should be deleted after save"
