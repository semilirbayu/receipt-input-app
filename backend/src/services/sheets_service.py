"""
Google Sheets service for appending receipt data.
"""
import gspread
from google.oauth2.credentials import Credentials
from backend.src.models.google_sheets_row import GoogleSheetsRow
from backend.src.models.user_preference import UserPreference
from datetime import datetime, timedelta
from typing import Tuple, Dict
import logging
import time

logger = logging.getLogger(__name__)


class SheetsService:
    """Service for Google Sheets integration."""

    @staticmethod
    def check_token_validity(token_expiry: datetime) -> Tuple[bool, str]:
        """
        Check if OAuth2 token is still valid.

        Args:
            token_expiry: Token expiration datetime

        Returns:
            Tuple of (is_valid, error_code)
        """
        now = datetime.utcnow()
        # Check if expired or within 5 minutes of expiry
        if token_expiry <= now or token_expiry <= (now + timedelta(minutes=5)):
            logger.warning(f"OAuth2 token expired or expiring soon: {token_expiry}")
            return False, "AUTH_EXPIRED"

        return True, ""

    @staticmethod
    def append_row(
        row_data: GoogleSheetsRow,
        user_pref: UserPreference,
        oauth_token: str,
        token_expiry: datetime
    ) -> Tuple[bool, Dict]:
        """
        Append row to Google Sheets.

        Args:
            row_data: GoogleSheetsRow instance with data to append
            user_pref: UserPreference with spreadsheet configuration
            oauth_token: OAuth2 access token
            token_expiry: Token expiration datetime

        Returns:
            Tuple of (success, response_dict)

        Raises:
            Exception: On Google Sheets API errors
        """
        # Check token validity
        is_valid, error_code = SheetsService.check_token_validity(token_expiry)
        if not is_valid:
            return False, {"error_code": error_code, "message": "Google Sheets authentication expired. Please reconnect."}

        # Validate row data
        is_valid, error_msg = row_data.validate()
        if not is_valid:
            return False, {"error_code": "INVALID_DATA", "message": error_msg}

        try:
            # Create credentials
            creds = Credentials(token=oauth_token)

            # Initialize gspread client
            client = gspread.authorize(creds)

            # Open spreadsheet and worksheet
            spreadsheet = client.open_by_key(user_pref.spreadsheet_id)
            worksheet = spreadsheet.worksheet(user_pref.sheet_tab_name)

            # Append row with exponential backoff for rate limiting
            max_retries = 3
            retry_delay = 1

            for attempt in range(max_retries):
                try:
                    worksheet.append_row(row_data.to_row())
                    break
                except gspread.exceptions.APIError as e:
                    if e.response.status_code == 429 and attempt < max_retries - 1:
                        # Rate limit exceeded, retry with backoff
                        logger.warning(f"Rate limit hit, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise

            # Get row number (approximate - last row + 1)
            row_number = len(worksheet.get_all_values()) + 1

            # Construct spreadsheet URL
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{user_pref.spreadsheet_id}/edit#gid=0"

            logger.info(f"Row appended successfully at row {row_number}")

            return True, {
                "success": True,
                "spreadsheet_url": spreadsheet_url,
                "row_number": row_number
            }

        except gspread.exceptions.APIError as e:
            # Extract HTTP status code and format error
            status_code = e.response.status_code
            error_code = f"GS-{status_code}"
            error_message = f"Error {error_code}: Unable to save data"

            logger.error(f"Google Sheets API error {status_code}: {e}")

            return False, {
                "error_code": error_code,
                "message": error_message
            }

        except Exception as e:
            logger.error(f"Unexpected error in sheets service: {e}")
            return False, {
                "error_code": "GS-500",
                "message": "Error GS-500: Unable to save data"
            }
