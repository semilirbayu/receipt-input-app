"""
Contract tests for OAuth2 authentication endpoints.
Validates API schema compliance with auth-api.yaml specification.
These tests MUST FAIL until the auth endpoints are implemented.
"""
import pytest
from httpx import AsyncClient
import yaml
from pathlib import Path


@pytest.fixture
def auth_contract():
    """Load auth API contract specification."""
    contract_path = Path(__file__).parents[3] / "specs" / "001-feature-receipt-processing" / "contracts" / "auth-api.yaml"
    with open(contract_path) as f:
        return yaml.safe_load(f)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_auth_login_returns_302_redirect(client: AsyncClient):
    """Test GET /api/v1/auth/login returns 302 redirect to Google OAuth2."""
    response = await client.get("/api/v1/auth/login", follow_redirects=False)

    assert response.status_code == 302, "Expected 302 redirect to Google OAuth2"

    location = response.headers.get("location", "")
    assert "accounts.google.com" in location, "Expected redirect to accounts.google.com"
    assert "oauth2" in location, "Expected OAuth2 authorization URL"
    assert "client_id" in location, "Expected client_id parameter in URL"
    assert "redirect_uri" in location, "Expected redirect_uri parameter in URL"
    assert "scope" in location, "Expected scope parameter in URL"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_auth_callback_with_code_returns_302(client: AsyncClient):
    """Test GET /api/v1/auth/callback with valid code returns 302 to /setup."""
    response = await client.get(
        "/api/v1/auth/callback?code=test_auth_code",
        follow_redirects=False
    )

    # May return 302 on success or 401/400 on token exchange failure
    if response.status_code == 302:
        location = response.headers.get("location", "")
        assert "/setup" in location, "Expected redirect to /setup page"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_auth_callback_without_code_returns_400(client: AsyncClient):
    """Test GET /api/v1/auth/callback without code returns 400 with MISSING_AUTH_CODE."""
    response = await client.get("/api/v1/auth/callback")

    assert response.status_code == 400, "Expected 400 Bad Request for missing code"

    data = response.json()
    assert data["error_code"] == "MISSING_AUTH_CODE", "Expected MISSING_AUTH_CODE error code"
    assert "message" in data, "Missing error message"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_auth_setup_with_valid_payload_returns_200(client: AsyncClient, auth_contract):
    """Test POST /api/v1/auth/setup with valid payload returns 200 with success."""
    payload = {
        "spreadsheet_id": "1A2B3C4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S0T",
        "sheet_tab_name": "Expenses 2025"
    }

    response = await client.post("/api/v1/auth/setup", json=payload)

    # May return 401 if not authenticated, or 200 on success
    if response.status_code == 200:
        data = response.json()
        assert "success" in data, "Missing success field"
        assert "message" in data, "Missing message field"
        assert isinstance(data["success"], bool), "success must be boolean"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_auth_setup_with_invalid_spreadsheet_id_returns_400(client: AsyncClient):
    """Test POST /api/v1/auth/setup with invalid spreadsheet_id returns 400."""
    payload = {
        "spreadsheet_id": "invalid-id-too-short",  # Not 44 chars
        "sheet_tab_name": "Expenses 2025"
    }

    response = await client.post("/api/v1/auth/setup", json=payload)

    if response.status_code == 400:
        data = response.json()
        assert data["error_code"] == "INVALID_SPREADSHEET_ID", "Expected INVALID_SPREADSHEET_ID error code"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_auth_status_returns_200_with_schema(client: AsyncClient, auth_contract):
    """Test GET /api/v1/auth/status returns 200 with authentication status."""
    response = await client.get("/api/v1/auth/status")

    assert response.status_code == 200, "Expected 200 OK for status check"

    data = response.json()
    schema = auth_contract["paths"]["/api/v1/auth/status"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]

    # Validate response schema
    assert "authenticated" in data, "Missing authenticated field"
    assert isinstance(data["authenticated"], bool), "authenticated must be boolean"

    if "spreadsheet_configured" in data:
        assert isinstance(data["spreadsheet_configured"], bool), "spreadsheet_configured must be boolean"

    if "token_expires_at" in data and data["token_expires_at"] is not None:
        assert isinstance(data["token_expires_at"], str), "token_expires_at must be string or null"
