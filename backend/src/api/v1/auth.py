"""
OAuth2 authentication endpoints for Google Sheets integration.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from backend.src.models.user_preference import UserPreference
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# OAuth2 configuration
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/api/v1/auth/callback")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SetupRequest(BaseModel):
    """Request model for setup endpoint."""
    spreadsheet_id: str
    sheet_tab_name: str


@router.get("/api/v1/auth/login")
async def initiate_auth():
    """
    Initiate OAuth2 authorization flow.

    Returns:
        Redirect to Google OAuth2 consent screen
    """
    try:
        # Create flow instance
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )

        # Generate authorization URL
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )

        logger.info(f"Redirecting to Google OAuth2: {auth_url}")
        return RedirectResponse(url=auth_url, status_code=302)

    except Exception as e:
        logger.error(f"Failed to generate authorization URL: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "AUTH_INIT_FAILED",
                "message": "Failed to initiate authentication"
            }
        )


@router.get("/api/v1/auth/callback")
async def handle_callback(request: Request, code: str = None):
    """
    Handle OAuth2 callback from Google.

    Args:
        request: FastAPI request object
        code: Authorization code from Google

    Returns:
        Redirect to setup page
    """
    if not code:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "MISSING_AUTH_CODE",
                "message": "Authorization code not provided"
            }
        )

    try:
        # Exchange code for token
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )

        flow.fetch_token(code=code)
        creds = flow.credentials

        # Store token in session (encrypted)
        # TODO: Implement proper session management with SECRET_KEY encryption
        if hasattr(request, 'session'):
            request.session['oauth_token'] = creds.token
            request.session['token_expiry'] = creds.expiry.isoformat() if creds.expiry else None
            request.session['refresh_token'] = creds.refresh_token
            request.session['user_id'] = 'default_user'  # TODO: Extract from Google user info

        logger.info("OAuth2 callback successful, token acquired")

        return RedirectResponse(url="/setup", status_code=302)

    except Exception as e:
        logger.error(f"OAuth2 token exchange failed: {e}")
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "AUTH_FAILED",
                "message": "Failed to authenticate with Google"
            }
        )


@router.post("/api/v1/auth/setup")
async def save_preferences(request: Request, data: SetupRequest):
    """
    Save user's target spreadsheet and sheet tab preferences.

    Args:
        request: FastAPI request object
        data: SetupRequest with spreadsheet configuration

    Returns:
        JSON response with success message
    """
    # Check authentication
    session = request.session if hasattr(request, 'session') else {}
    if not session.get('oauth_token'):
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "NOT_AUTHENTICATED",
                "message": "Please authenticate with Google Sheets first"
            }
        )

    # Validate spreadsheet_id
    if len(data.spreadsheet_id) != 44:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_SPREADSHEET_ID",
                "message": "Spreadsheet ID must be 44 characters"
            }
        )

    # Validate sheet_tab_name
    if not data.sheet_tab_name or not data.sheet_tab_name.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_SHEET_NAME",
                "message": "Sheet tab name cannot be empty"
            }
        )

    # Create and save user preference
    user_session_id = session.get('user_id', 'default_user')
    user_pref = UserPreference.create(
        session_id=user_session_id,
        spreadsheet_id=data.spreadsheet_id,
        sheet_tab_name=data.sheet_tab_name
    )

    user_pref.save()

    logger.info(f"Preferences saved for user {user_session_id}")

    return {
        "success": True,
        "message": "Preferences saved. You can now upload receipts."
    }


@router.get("/api/v1/auth/status")
async def check_auth_status(request: Request):
    """
    Check current authentication status.

    Args:
        request: FastAPI request object

    Returns:
        JSON response with authentication status
    """
    session = request.session if hasattr(request, 'session') else {}

    authenticated = bool(session.get('oauth_token'))
    user_session_id = session.get('user_id', 'default_user')

    user_pref = UserPreference.load_by_session_id(user_session_id) if authenticated else None
    spreadsheet_configured = user_pref is not None

    token_expiry_str = session.get('token_expiry')

    return {
        "authenticated": authenticated,
        "spreadsheet_configured": spreadsheet_configured,
        "token_expires_at": token_expiry_str,
        "spreadsheet_id": user_pref.spreadsheet_id if user_pref else None,
        "sheet_tab_name": user_pref.sheet_tab_name if user_pref else None
    }


@router.post("/api/v1/auth/disconnect")
async def disconnect_spreadsheet(request: Request):
    """
    Disconnect from Google Sheets and clear all configuration.

    This endpoint clears:
    - OAuth session tokens
    - User preferences (spreadsheet ID, sheet tab, column mappings)

    Args:
        request: FastAPI request object

    Returns:
        JSON response with success message
    """
    session = request.session if hasattr(request, 'session') else {}
    user_session_id = session.get('user_id', 'default_user')

    # Delete user preferences file
    user_pref = UserPreference.load_by_session_id(user_session_id)
    if user_pref:
        user_pref.delete()
        logger.info(f"Deleted preferences for user {user_session_id}")

    # Clear session
    if hasattr(request, 'session'):
        request.session.clear()
        logger.info(f"Cleared session for user {user_session_id}")

    return {
        "success": True,
        "message": "Successfully disconnected from Google Sheets"
    }
