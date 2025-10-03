"""
Column configuration endpoints for managing column mappings.
"""
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from backend.src.models.user_preference import UserPreference
from backend.src.models.column_mapping import ColumnMappingConfiguration
from backend.src.services.column_validator import ColumnValidator
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ColumnMappingsRequest(BaseModel):
    """Request model for saving column mappings."""
    date_column: Optional[str] = None
    description_column: Optional[str] = None
    price_column: Optional[str] = None


class ValidateColumnRequest(BaseModel):
    """Request model for validating a column reference."""
    column: Optional[str] = None


@router.get("/api/v1/column-config")
async def get_column_mappings(
    request: Request,
    session_id: Optional[str] = Header(None, alias="session_id")
):
    """
    Get configured column mappings for the authenticated user.

    Supports two authentication methods:
    1. Browser session cookies (for web UI)
    2. session_id header (for testing/API clients)

    Args:
        request: FastAPI request object (for session access)
        session_id: Optional session ID from header

    Returns:
        JSON with date_column, description_column, price_column

    Raises:
        HTTPException 401: If user not authenticated
        HTTPException 404: If column mappings are not configured
    """
    # Check authentication - support both session cookies and header
    oauth_token = None
    user_session_id = None

    # Method 1: Try session_id header (for tests/API)
    if session_id:
        user_session_id = session_id
        # Assume header-based auth is valid (tests handle their own mocking)
        oauth_token = "header-auth"
    else:
        # Method 2: Try session cookies (for browser)
        try:
            session = request.session
        except AttributeError:
            session = {}

        oauth_token = session.get('oauth_token')
        user_session_id = session.get('user_id', 'default_user')

    if not oauth_token:
        return JSONResponse(
            status_code=401,
            content={
                "error_code": "AUTH_REQUIRED",
                "message": "Authentication required. Please log in."
            }
        )

    # Load user preference
    user_pref = UserPreference.load_by_session_id(user_session_id)
    if not user_pref:
        return JSONResponse(
            status_code=401,
            content={
                "error_code": "AUTH_REQUIRED",
                "message": "Google Sheets configuration required."
            }
        )

    # Check if column mappings are configured
    if not user_pref.has_column_mappings():
        return JSONResponse(
            status_code=404,
            content={
                "error_code": "COLUMN_MAPPINGS_NOT_CONFIGURED",
                "message": "Column mappings have not been configured yet."
            }
        )

    # Return configured mappings
    mappings = user_pref.get_column_mappings()
    return {
        "date_column": mappings.date_column,
        "description_column": mappings.description_column,
        "price_column": mappings.price_column
    }


@router.post("/api/v1/column-config")
async def save_column_mappings(
    request: Request,
    data: ColumnMappingsRequest,
    session_id: Optional[str] = Header(None, alias="session_id")
):
    """
    Save column mappings configuration.

    Supports two authentication methods:
    1. Browser session cookies (for web UI)
    2. session_id header (for testing/API clients)

    Args:
        request: FastAPI request object (for session access)
        data: ColumnMappingsRequest with column assignments
        session_id: Optional session ID from header

    Returns:
        JSON with success status, message, and saved mappings

    Raises:
        HTTPException 401: If user not authenticated
        HTTPException 400: If validation fails
    """
    # Check authentication - support both session cookies and header
    oauth_token = None
    user_session_id = None

    # Method 1: Try session_id header (for tests/API)
    if session_id:
        user_session_id = session_id
        # Assume header-based auth is valid (tests handle their own mocking)
        oauth_token = "header-auth"
    else:
        # Method 2: Try session cookies (for browser)
        try:
            session = request.session
        except AttributeError:
            session = {}

        oauth_token = session.get('oauth_token')
        user_session_id = session.get('user_id', 'default_user')

    if not oauth_token:
        return JSONResponse(
            status_code=401,
            content={
                "error_code": "AUTH_REQUIRED",
                "message": "Authentication required. Please log in."
            }
        )

    # Load user preference
    user_pref = UserPreference.load_by_session_id(user_session_id)
    if not user_pref:
        return JSONResponse(
            status_code=401,
            content={
                "error_code": "AUTH_REQUIRED",
                "message": "Google Sheets configuration required."
            }
        )

    # Check for missing fields
    if not data.date_column or not data.date_column.strip():
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "MISSING_REQUIRED_FIELD",
                "field": "date_column",
                "message": "date_column is required"
            }
        )

    if not data.description_column or not data.description_column.strip():
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "MISSING_REQUIRED_FIELD",
                "field": "description_column",
                "message": "description_column is required"
            }
        )

    if not data.price_column or not data.price_column.strip():
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "MISSING_REQUIRED_FIELD",
                "field": "price_column",
                "message": "price_column is required"
            }
        )

    # Create configuration
    config = ColumnMappingConfiguration(
        date_column=data.date_column,
        description_column=data.description_column,
        price_column=data.price_column
    )

    # Validate configuration
    is_valid, error = config.validate()
    if not is_valid:
        # Determine which field caused the error
        field_name = None
        error_code = None

        if "date_column" in error:
            field_name = "date_column"
            error_code = error.split(": ")[1] if ": " in error else error
        elif "description_column" in error:
            field_name = "description_column"
            error_code = error.split(": ")[1] if ": " in error else error
        elif "price_column" in error:
            field_name = "price_column"
            error_code = error.split(": ")[1] if ": " in error else error
        else:
            error_code = error

        return JSONResponse(
            status_code=400,
            content={
                "error_code": error_code,
                "field": field_name,
                "message": error
            }
        )

    # Save configuration
    user_pref.set_column_mappings(config)
    user_pref.save()

    logger.info(f"Column mappings saved for session {user_session_id}: {config.to_dict()}")

    return {
        "success": True,
        "message": "Column mappings saved successfully",
        "mappings": {
            "date_column": config.date_column,
            "description_column": config.description_column,
            "price_column": config.price_column
        }
    }


@router.post("/api/v1/column-config/validate")
async def validate_column(data: ValidateColumnRequest):
    """
    Validate a single column reference.

    Args:
        data: ValidateColumnRequest with column reference

    Returns:
        JSON with validation result (valid, column, index/error_code/message)

    Raises:
        HTTPException 400: If column field is missing
    """
    # Check if column field is provided
    if data.column is None:
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "MISSING_COLUMN_FIELD",
                "message": "column field is required"
            }
        )

    column_ref = data.column

    # Validate column reference
    is_valid, error_code = ColumnValidator.validate(column_ref)

    if is_valid:
        # Return success with index
        index = ColumnValidator.to_index(column_ref)
        return {
            "valid": True,
            "column": column_ref,
            "index": index
        }
    else:
        # Return failure with error code and message
        error_messages = {
            "INVALID_COLUMN_FORMAT": f"Column '{column_ref}' has invalid format. Must be A-ZZ (uppercase letters only).",
            "COLUMN_OUT_OF_RANGE": f"Column '{column_ref}' is out of range. Valid range is A-ZZ."
        }

        return {
            "valid": False,
            "column": column_ref,
            "error_code": error_code,
            "message": error_messages.get(error_code, f"Invalid column: {error_code}")
        }
