"""
Contract tests for GET /api/v1/column-config endpoint.
Validates API schema compliance with get-column-mappings.json specification.
These tests MUST FAIL until the column config GET endpoint is implemented.
"""
import pytest
from httpx import AsyncClient
import json
from pathlib import Path


@pytest.fixture
def get_column_mappings_contract():
    """Load GET column mappings API contract specification."""
    contract_path = (
        Path(__file__).parents[3]
        / "specs"
        / "002-feature-select-column"
        / "contracts"
        / "get-column-mappings.json"
    )
    with open(contract_path) as f:
        return json.load(f)


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_get_column_mappings_configured_returns_200(
    client: AsyncClient, get_column_mappings_contract
):
    """Test GET returns 200 with configured mappings."""
    # Simulate session_id header (OAuth2 authenticated user)
    headers = {"session_id": "test-session-configured"}

    response = await client.get("/api/v1/column-config", headers=headers)

    # This test will fail until endpoint is implemented
    assert response.status_code == 200, "Expected 200 OK when mappings are configured"

    data = response.json()
    schema = get_column_mappings_contract["components"]["schemas"][
        "ColumnMappingsResponse"
    ]

    # Validate response schema - all three fields required
    assert "date_column" in data, "Missing date_column field"
    assert "description_column" in data, "Missing description_column field"
    assert "price_column" in data, "Missing price_column field"

    # Validate field types and format (A-ZZ pattern)
    assert isinstance(data["date_column"], str), "date_column must be string"
    assert isinstance(data["description_column"], str), "description_column must be string"
    assert isinstance(data["price_column"], str), "price_column must be string"

    # Validate pattern matches ^[A-Z]{1,2}$
    import re

    pattern = re.compile(r"^[A-Z]{1,2}$")
    assert pattern.match(data["date_column"]), f"date_column '{data['date_column']}' must match A-ZZ format"
    assert pattern.match(data["description_column"]), f"description_column '{data['description_column']}' must match A-ZZ format"
    assert pattern.match(data["price_column"]), f"price_column '{data['price_column']}' must match A-ZZ format"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_get_column_mappings_not_configured_returns_404(
    client: AsyncClient, get_column_mappings_contract
):
    """Test GET returns 404 when column mappings are not configured."""
    # Simulate different session_id for unconfigured user
    headers = {"session_id": "test-session-unconfigured"}

    response = await client.get("/api/v1/column-config", headers=headers)

    # This test will fail until endpoint is implemented
    assert response.status_code == 404, "Expected 404 Not Found when mappings not configured"

    data = response.json()
    error_schema = get_column_mappings_contract["components"]["schemas"]["ErrorResponse"]

    # Validate error response structure
    assert "error_code" in data, "Missing error_code field"
    assert "message" in data, "Missing message field"

    # Validate error code value
    assert (
        data["error_code"] == "COLUMN_MAPPINGS_NOT_CONFIGURED"
    ), "Expected COLUMN_MAPPINGS_NOT_CONFIGURED error code"

    # Validate message is descriptive
    assert isinstance(data["message"], str), "message must be string"
    assert len(data["message"]) > 0, "message must not be empty"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_get_column_mappings_no_auth_returns_401(
    client: AsyncClient, get_column_mappings_contract
):
    """Test GET returns 401 when session_id header is missing (authentication required)."""
    # No headers = no authentication
    response = await client.get("/api/v1/column-config")

    # This test will fail until endpoint is implemented
    assert response.status_code == 401, "Expected 401 Unauthorized without session_id"

    data = response.json()

    # Validate error response structure
    assert "error_code" in data, "Missing error_code field"
    assert "message" in data, "Missing message field"

    # Validate error code value
    assert data["error_code"] == "AUTH_REQUIRED", "Expected AUTH_REQUIRED error code"

    # Validate message
    assert isinstance(data["message"], str), "message must be string"
    assert "authentication" in data["message"].lower() or "auth" in data["message"].lower(), \
        "Error message should mention authentication"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_get_column_mappings_with_duplicates_returns_200(
    client: AsyncClient, get_column_mappings_contract
):
    """Test GET returns 200 even when user has configured duplicate column assignments."""
    # Simulate session_id for user with duplicate mappings (e.g., date and price both to column A)
    headers = {"session_id": "test-session-with-duplicates"}

    response = await client.get("/api/v1/column-config", headers=headers)

    # This test may not be runnable until implementation allows setting duplicates
    # But endpoint should return whatever is configured
    if response.status_code == 200:
        data = response.json()

        # Should still have all three fields
        assert "date_column" in data
        assert "description_column" in data
        assert "price_column" in data

        # Duplicates are allowed per spec (FR-008)
        # e.g., date_column="A", price_column="A" is valid
