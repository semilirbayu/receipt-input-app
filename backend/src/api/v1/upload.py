"""
Upload endpoint for receipt image processing.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.src.models.receipt import Receipt
from backend.src.models.extracted_data import ExtractedData
from backend.src.services.ocr_service import OCRService
from backend.src.services.parser_service import ParserService
from backend.src.storage.temp_storage import TempStorageService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
storage_service = TempStorageService()


@router.post("/api/v1/upload")
async def upload_receipt(file: UploadFile = File(...)):
    """
    Upload receipt image for OCR processing.

    Args:
        file: Uploaded receipt image (JPG/PNG, max 5MB)

    Returns:
        JSON response with receipt_id, status, extracted_data, and processing_time_ms

    Raises:
        HTTPException: For validation or processing errors
    """
    # Read file content
    file_content = await file.read()

    # Create Receipt instance for validation
    receipt = Receipt.create(
        filename=file.filename or "unknown.jpg",
        file_size=len(file_content),
        file_type=file.content_type or "application/octet-stream",
        file_path=""  # Will be set after save
    )

    # Validate receipt
    is_valid, error_code = receipt.validate()
    if not is_valid:
        logger.warning(f"Upload validation failed: {error_code}")

        error_messages = {
            "FILE_TOO_LARGE": "File size exceeds 5MB limit",
            "INVALID_FORMAT": "Only JPG and PNG formats are supported",
            "MISSING_FILE": "No file provided in request"
        }

        raise HTTPException(
            status_code=400,
            detail={
                "error_code": error_code,
                "message": error_messages.get(error_code, "Invalid file")
            }
        )

    try:
        # Save file to temporary storage
        file_path = storage_service.save_file(file_content, receipt.filename)
        receipt.file_path = file_path

        # Mark as processing
        receipt.mark_processing()

        # Process with OCR
        raw_ocr_text, processing_time_ms = OCRService.process_image(file_path)

        # Parse extracted data
        parsed_data = ParserService.parse_receipt_data(raw_ocr_text)

        # Create ExtractedData instance
        extracted_data = ExtractedData.create(
            receipt_id=receipt.id,
            transaction_date=parsed_data["transaction_date"],
            transaction_date_confidence=parsed_data["transaction_date_confidence"],
            items=parsed_data["items"],
            items_confidence=parsed_data["items_confidence"],
            total_amount=parsed_data["total_amount"],
            total_amount_confidence=parsed_data["total_amount_confidence"],
            raw_ocr_text=raw_ocr_text
        )

        # Mark as completed
        receipt.mark_completed()

        # Return response
        return {
            "receipt_id": receipt.id,
            "status": "completed",
            "extracted_data": extracted_data.to_dict(),
            "processing_time_ms": processing_time_ms
        }

    except Exception as e:
        receipt.mark_failed()
        logger.error(f"OCR processing failed: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "OCR_FAILED",
                "message": "Unable to process image"
            }
        )
