"""
Upload endpoint for receipt image processing.

Enhanced with Gemini Vision API integration and Tesseract fallback.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from backend.src.models.receipt import Receipt
from backend.src.models.extracted_data import ExtractedData
from backend.src.services.gemini_extractor import GeminiExtractorService, GeminiExtractionError
from backend.src.services.extraction_validator import ExtractionValidator
from backend.src.services.metrics_service import MetricsService
from backend.src.services.ocr_service import OCRService
from backend.src.services.parser_service import ParserService
from backend.src.storage.temp_storage import TempStorageService
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()
storage_service = TempStorageService()
gemini_service = GeminiExtractorService()
validator = ExtractionValidator()
metrics_service = MetricsService()


@router.post("/api/v1/upload")
async def upload_receipt(file: UploadFile = File(None)):
    """
    Upload receipt image for OCR processing.

    Args:
        file: Uploaded receipt image (JPG/PNG, max 5MB)

    Returns:
        JSON response with receipt_id, status, extracted_data, and processing_time_ms

    Raises:
        HTTPException: For validation or processing errors
    """
    # Check if file was provided
    if file is None or not file.filename:
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "MISSING_FILE",
                "message": "No file provided in request"
            }
        )

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

        return JSONResponse(
            status_code=400,
            content={
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

        # Start timing
        start_time = time.time()

        # Initialize warnings list
        warnings = []

        # Try Gemini extraction first
        extracted_data = None
        try:
            logger.info("Attempting Gemini extraction")
            extracted_data = gemini_service.extract(file_path)
            logger.info("Gemini extraction successful")

        except GeminiExtractionError as e:
            # Gemini failed - fall back to Tesseract
            logger.warning(f"Gemini extraction failed: {e}, falling back to Tesseract")
            warnings.append("gemini_api_unavailable")
            warnings.append("using_fallback_extraction")

            # Fallback to Tesseract + Parser
            raw_ocr_text, _ = OCRService.process_image(file_path)
            parsed_data = ParserService.parse_receipt_data(raw_ocr_text)

            # Create ExtractedData with tesseract_fallback method
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
            extracted_data.extraction_method = "tesseract_fallback"
            extracted_data.paraphrased = False

        # Validate extracted data
        date_validation = validator.validate_date(extracted_data.transaction_date)
        amount_validation = validator.validate_amount(
            extracted_data.total_amount,
            extracted_data.currency or "IDR"
        )
        items_validation = validator.validate_items(extracted_data.items)

        # Apply validation adjustments
        if not date_validation.is_valid:
            extracted_data.transaction_date = None
            extracted_data.transaction_date_confidence = 0.0
            warnings.extend(date_validation.validation_messages)

        if not amount_validation.is_valid:
            extracted_data.total_amount = None
            extracted_data.total_amount_confidence = 0.0
            warnings.extend(amount_validation.validation_messages)

        if not items_validation.is_valid:
            extracted_data.items = None
            extracted_data.items_confidence = 0.0
            warnings.extend(items_validation.validation_messages)

        # Check for low image quality
        avg_confidence = (
            extracted_data.transaction_date_confidence +
            extracted_data.items_confidence +
            extracted_data.total_amount_confidence
        ) / 3
        if avg_confidence < 0.6:
            warnings.append("low_image_quality")

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Record metrics
        try:
            metrics_service.record_extraction(extracted_data)
        except Exception as metrics_error:
            logger.error(f"Failed to record metrics: {metrics_error}")

        # Mark as completed
        receipt.mark_completed()

        # Build validation summary
        validation_summary = {
            "date_valid": date_validation.is_valid,
            "price_valid": amount_validation.is_valid,
            "items_valid": items_validation.is_valid,
            "warnings": warnings
        }

        # Return response
        return {
            "receipt_id": receipt.id,
            "extracted_data": extracted_data.to_dict(),
            "validation": validation_summary,
            "processing_time_ms": processing_time_ms
        }

    except Exception as e:
        receipt.mark_failed()
        logger.error(f"Receipt processing failed: {str(e)}")

        return JSONResponse(
            status_code=500,
            content={
                "error_code": "EXTRACTION_FAILED",
                "message": "Unable to extract data from receipt",
                "details": str(e)
            }
        )
