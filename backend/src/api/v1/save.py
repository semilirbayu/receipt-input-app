"""
Save endpoint for confirmed receipt data to Google Sheets.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
from backend.src.models.google_sheets_row import GoogleSheetsRow
from backend.src.models.user_preference import UserPreference
from backend.src.services.sheets_service import SheetsService
from backend.src.storage.temp_storage import TempStorageService
from dateutil import parser as date_parser
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
storage_service = TempStorageService()


class SaveRequest(BaseModel):
    """Request model for save endpoint."""
    receipt_id: str
    transaction_date: str
    items: str
    total_amount: float


@router.post("/api/v1/save")
async def save_receipt(request: Request, data: SaveRequest):
    """
    Save confirmed receipt data to Google Sheets.

    Args:
        request: FastAPI request object (for session access)
        data: SaveRequest with receipt data

    Returns:
        JSON response with success, spreadsheet_url, and row_number

    Raises:
        HTTPException: For validation or save errors
    """
    # Validate all fields present
    if not all([data.receipt_id, data.transaction_date, data.items, data.total_amount is not None]):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "MISSING_REQUIRED_FIELDS",
                "message": "All fields (transaction_date, items, total_amount) are required"
            }
        )

    # Validate and parse transaction_date
    try:
        parsed_date = date_parser.parse(data.transaction_date).date()
    except (ValueError, date_parser.ParserError):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_DATE",
                "message": "Transaction date must be a valid date"
            }
        )

    # Validate total_amount
    try:
        amount = Decimal(str(data.total_amount))
        if amount < 0:
            raise ValueError("Negative amount")
    except (ValueError, ArithmeticError):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_AMOUNT",
                "message": "Total amount must be a positive number"
            }
        )

    # Check authentication (session-based)
    # TODO: Implement proper session management
    session = request.session if hasattr(request, 'session') else {}
    oauth_token = session.get('oauth_token')
    token_expiry_str = session.get('token_expiry')
    user_session_id = session.get('user_id', 'default_user')

    if not oauth_token:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "NOT_AUTHENTICATED",
                "message": "Google Sheets authentication required"
            }
        )

    # Parse token expiry
    try:
        token_expiry = datetime.fromisoformat(token_expiry_str) if token_expiry_str else datetime.utcnow()
    except ValueError:
        token_expiry = datetime.utcnow()

    # Load user preferences
    user_pref = UserPreference.load_by_session_id(user_session_id)
    if not user_pref:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "NOT_AUTHENTICATED",
                "message": "Google Sheets configuration required"
            }
        )

    # Check if column mappings are configured
    if not user_pref.has_column_mappings():
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "COLUMN_MAPPINGS_REQUIRED",
                "message": "Please configure column mappings before processing receipts"
            }
        )

    # Construct GoogleSheetsRow
    sheets_row = GoogleSheetsRow.from_extracted_data(
        transaction_date=parsed_date,
        items=data.items,
        total_amount=amount
    )

    # Append to Google Sheets
    success, response = SheetsService.append_row(
        row_data=sheets_row,
        user_pref=user_pref,
        oauth_token=oauth_token,
        token_expiry=token_expiry
    )

    if not success:
        # Determine status code based on error
        error_code = response.get("error_code", "")

        if error_code == "AUTH_EXPIRED":
            status_code = 401
        elif error_code.startswith("GS-403"):
            status_code = 403
        elif error_code.startswith("GS-423"):
            status_code = 423
        elif error_code.startswith("GS-429"):
            status_code = 429
        else:
            status_code = 500

        raise HTTPException(status_code=status_code, detail=response)

    # Delete receipt file after successful save
    # Construct file path from receipt_id (simplified - in production use proper tracking)
    try:
        from pathlib import Path
        upload_dir = Path("shared/uploads")
        # Find file with receipt_id in name
        for file_path in upload_dir.glob(f"{data.receipt_id}*"):
            storage_service.delete_file(str(file_path))
            logger.info(f"Deleted receipt file after save: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to delete receipt file: {e}")

    return response
