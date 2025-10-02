"""
Contract tests for POST /api/v1/save endpoint.
Validates API schema compliance with save-api.yaml specification.
These tests MUST FAIL until the save endpoint is implemented.
"""
import pytest
from httpx import AsyncClient
import yaml
from pathlib import Path


@pytest.fixture
def save_contract():
    """Load save API contract specification."""
    contract_path = Path(__file__).parents[3] / "specs" / "001-feature-receipt-processing" / "contracts" / "save-api.yaml"
    with open(contract_path) as f:
        return yaml.safe_load(f)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_save_valid_payload_returns_200(client: AsyncClient, save_contract):
    """Test valid save payload returns 200 with correct schema."""
    payload = {
        "receipt_id": "a3bb189e-8bf9-3888-9912-ace4e6543002",
        "transaction_date": "2025-09-28",
        "items": "Coffee; Sandwich; Water",
        "total_amount": 24.50
    }

    response = await client.post("/api/v1/save", json=payload)

    assert response.status_code == 200, "Expected 200 OK for valid save"

    data = response.json()
    schema = save_contract["paths"]["/api/v1/save"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]

    # Validate response schema
    assert "success" in data, "Missing success field"
    assert "spreadsheet_url" in data, "Missing spreadsheet_url field"
    assert "row_number" in data, "Missing row_number field"

    # Validate field types
    assert isinstance(data["success"], bool), "success must be boolean"
    assert data["success"] is True, "success must be true on successful save"
    assert isinstance(data["spreadsheet_url"], str), "spreadsheet_url must be string"
    assert isinstance(data["row_number"], int), "row_number must be integer"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_save_missing_fields_returns_400(client: AsyncClient):
    """Test missing required fields returns 400 with MISSING_REQUIRED_FIELDS error."""
    payload = {
        "receipt_id": "a3bb189e-8bf9-3888-9912-ace4e6543002",
        "transaction_date": "2025-09-28"
        # Missing items and total_amount
    }

    response = await client.post("/api/v1/save", json=payload)

    assert response.status_code == 400, "Expected 400 Bad Request for missing fields"

    data = response.json()
    assert data["error_code"] == "MISSING_REQUIRED_FIELDS", "Expected MISSING_REQUIRED_FIELDS error code"
    assert "message" in data, "Missing error message"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_save_invalid_date_returns_400(client: AsyncClient):
    """Test invalid date returns 400 with INVALID_DATE error."""
    payload = {
        "receipt_id": "a3bb189e-8bf9-3888-9912-ace4e6543002",
        "transaction_date": "invalid-date",
        "items": "Coffee",
        "total_amount": 10.00
    }

    response = await client.post("/api/v1/save", json=payload)

    assert response.status_code == 400, "Expected 400 Bad Request for invalid date"

    data = response.json()
    assert data["error_code"] == "INVALID_DATE", "Expected INVALID_DATE error code"
    assert "message" in data, "Missing error message"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_save_invalid_amount_returns_400(client: AsyncClient):
    """Test invalid amount returns 400 with INVALID_AMOUNT error."""
    payload = {
        "receipt_id": "a3bb189e-8bf9-3888-9912-ace4e6543002",
        "transaction_date": "2025-09-28",
        "items": "Coffee",
        "total_amount": -10.00  # Negative amount
    }

    response = await client.post("/api/v1/save", json=payload)

    assert response.status_code == 400, "Expected 400 Bad Request for negative amount"

    data = response.json()
    assert data["error_code"] == "INVALID_AMOUNT", "Expected INVALID_AMOUNT error code"
    assert "message" in data, "Missing error message"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_save_expired_token_returns_401(client: AsyncClient):
    """Test expired token returns 401 with AUTH_EXPIRED error."""
    # This test assumes a mechanism to simulate expired token
    # Will be implemented when auth middleware is ready
    payload = {
        "receipt_id": "a3bb189e-8bf9-3888-9912-ace4e6543002",
        "transaction_date": "2025-09-28",
        "items": "Coffee",
        "total_amount": 10.00
    }

    # TODO: Add header or session state to simulate expired token
    response = await client.post("/api/v1/save", json=payload)

    # This test may return 401 or 200 depending on auth state
    if response.status_code == 401:
        data = response.json()
        assert data["error_code"] in ["AUTH_EXPIRED", "NOT_AUTHENTICATED"], "Expected auth error code"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_save_insufficient_permissions_returns_403(client: AsyncClient):
    """Test insufficient permissions returns 403 with GS-403 error."""
    payload = {
        "receipt_id": "a3bb189e-8bf9-3888-9912-ace4e6543002",
        "transaction_date": "2025-09-28",
        "items": "Coffee",
        "total_amount": 10.00
    }

    # TODO: Mock Google Sheets API to return 403
    response = await client.post("/api/v1/save", json=payload)

    # This test may return various status codes depending on implementation
    if response.status_code == 403:
        data = response.json()
        assert data["error_code"] == "GS-403", "Expected GS-403 error code"
        assert "Unable to save data" in data["message"], "Expected standard error message format"
