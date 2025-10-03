"""
Pytest fixtures shared across all test modules.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
from frontend.src.main import app
from backend.src.models.user_preference import UserPreference
from pathlib import Path
import json
import tempfile
import shutil


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing API endpoints.

    Note: Tests use session_id headers for authentication, which the endpoints
    support alongside browser session cookies for flexibility.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def setup_test_data(tmp_path, monkeypatch):
    """
    Set up test data for contract tests.
    Creates mock user preferences with different configurations.
    """
    # Create temporary storage directory
    test_storage = tmp_path / "shared"
    test_storage.mkdir()

    # Mock the storage file path
    monkeypatch.setattr(UserPreference, "STORAGE_FILE", test_storage / "user_preferences.json")

    # Create test user preferences
    test_prefs = {
        # User with configured column mappings
        "test-session-configured": {
            "id": "test-id-1",
            "spreadsheet_id": "1" * 44,
            "sheet_tab_name": "Sheet1",
            "column_mappings": {
                "date": "A",
                "description": "B",
                "price": "C"
            },
            "created_at": "2024-01-01T00:00:00",
            "last_updated_at": "2024-01-01T00:00:00"
        },
        # User without column mappings
        "test-session-unconfigured": {
            "id": "test-id-2",
            "spreadsheet_id": "2" * 44,
            "sheet_tab_name": "Sheet1",
            "created_at": "2024-01-01T00:00:00",
            "last_updated_at": "2024-01-01T00:00:00"
        },
        # User with duplicate column mappings
        "test-session-with-duplicates": {
            "id": "test-id-3",
            "spreadsheet_id": "3" * 44,
            "sheet_tab_name": "Sheet1",
            "column_mappings": {
                "date": "A",
                "description": "B",
                "price": "A"  # Duplicate
            },
            "created_at": "2024-01-01T00:00:00",
            "last_updated_at": "2024-01-01T00:00:00"
        },
        # User for valid POST test
        "test-session-valid": {
            "id": "test-id-4",
            "spreadsheet_id": "4" * 44,
            "sheet_tab_name": "Sheet1",
            "created_at": "2024-01-01T00:00:00",
            "last_updated_at": "2024-01-01T00:00:00"
        },
        # User for non-contiguous test
        "test-session-non-contiguous": {
            "id": "test-id-5",
            "spreadsheet_id": "5" * 44,
            "sheet_tab_name": "Sheet1",
            "created_at": "2024-01-01T00:00:00",
            "last_updated_at": "2024-01-01T00:00:00"
        },
        # User for duplicates test
        "test-session-duplicates": {
            "id": "test-id-6",
            "spreadsheet_id": "6" * 44,
            "sheet_tab_name": "Sheet1",
            "created_at": "2024-01-01T00:00:00",
            "last_updated_at": "2024-01-01T00:00:00"
        },
        # User for invalid format test
        "test-session-invalid": {
            "id": "test-id-7",
            "spreadsheet_id": "7" * 44,
            "sheet_tab_name": "Sheet1",
            "created_at": "2024-01-01T00:00:00",
            "last_updated_at": "2024-01-01T00:00:00"
        },
        # User for lowercase test
        "test-session-lowercase": {
            "id": "test-id-8",
            "spreadsheet_id": "8" * 44,
            "sheet_tab_name": "Sheet1",
            "created_at": "2024-01-01T00:00:00",
            "last_updated_at": "2024-01-01T00:00:00"
        },
        # User for out of range test
        "test-session-out-of-range": {
            "id": "test-id-9",
            "spreadsheet_id": "9" * 44,
            "sheet_tab_name": "Sheet1",
            "created_at": "2024-01-01T00:00:00",
            "last_updated_at": "2024-01-01T00:00:00"
        },
        # User for missing field test
        "test-session-missing": {
            "id": "test-id-10",
            "spreadsheet_id": "a" * 44,
            "sheet_tab_name": "Sheet1",
            "created_at": "2024-01-01T00:00:00",
            "last_updated_at": "2024-01-01T00:00:00"
        },
        # User for ZZ test
        "test-session-zz": {
            "id": "test-id-11",
            "spreadsheet_id": "b" * 44,
            "sheet_tab_name": "Sheet1",
            "created_at": "2024-01-01T00:00:00",
            "last_updated_at": "2024-01-01T00:00:00"
        }
    }

    # Write test preferences to file
    with open(test_storage / "user_preferences.json", "w") as f:
        json.dump(test_prefs, f, indent=2)

    yield

    # Cleanup (optional, tmp_path is auto-cleaned)
    # No explicit cleanup needed as tmp_path is automatically cleaned up
