"""
Contract tests for POST /api/v1/column-config endpoint.
Validates API schema compliance with save-column-mappings.json specification.
These tests MUST FAIL until the column config POST endpoint is implemented.
"""
import pytest
from httpx import AsyncClient
import json
from pathlib import Path


@pytest.fixture
def save_column_mappings_contract():
    """Load POST column mappings API contract specification."""
    contract_path = (
        Path(__file__).parents[3]
        / "specs"
        / "002-feature-select-column"
        / "contracts"
        / "save-column-mappings.json"
    )
    with open(contract_path) as f:
        return json.load(f)


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_post_column_mappings_valid_returns_200(
    client: AsyncClient, save_column_mappings_contract
):
    """Test POST with valid mappings returns 200 with success response."""
    headers = {"session_id": "test-session-valid"}
    payload = {
        "date_column": "A",
        "description_column": "B",
        "price_column": "C"
    }

    response = await client.post("/api/v1/column-config", headers=headers, json=payload)

    # This test will fail until endpoint is implemented
    assert response.status_code == 200, "Expected 200 OK for valid column mappings"

    data = response.json()
    schema = save_column_mappings_contract["components"]["schemas"]["SaveSuccessResponse"]

    # Validate response schema
    assert "success" in data, "Missing success field"
    assert "message" in data, "Missing message field"
    assert "mappings" in data, "Missing mappings field"

    # Validate field types and values
    assert data["success"] is True, "success must be true"
    assert isinstance(data["message"], str), "message must be string"
    assert isinstance(data["mappings"], dict), "mappings must be object"

    # Validate mappings echo back the input
    assert data["mappings"]["date_column"] == "A"
    assert data["mappings"]["description_column"] == "B"
    assert data["mappings"]["price_column"] == "C"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_post_column_mappings_non_contiguous_returns_200(
    client: AsyncClient, save_column_mappings_contract
):
    """Test POST with non-contiguous columns (A, C, F) returns 200."""
    headers = {"session_id": "test-session-non-contiguous"}
    payload = {
        "date_column": "A",
        "description_column": "C",
        "price_column": "F"
    }

    response = await client.post("/api/v1/column-config", headers=headers, json=payload)

    assert response.status_code == 200, "Expected 200 OK for non-contiguous columns"

    data = response.json()
    assert data["success"] is True
    assert data["mappings"]["date_column"] == "A"
    assert data["mappings"]["description_column"] == "C"
    assert data["mappings"]["price_column"] == "F"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_post_column_mappings_duplicates_returns_200(
    client: AsyncClient, save_column_mappings_contract
):
    """Test POST with duplicate columns (A, B, A) returns 200 - duplicates allowed per FR-008."""
    headers = {"session_id": "test-session-duplicates"}
    payload = {
        "date_column": "A",
        "description_column": "B",
        "price_column": "A"  # Duplicate of date_column
    }

    response = await client.post("/api/v1/column-config", headers=headers, json=payload)

    assert response.status_code == 200, "Expected 200 OK - duplicate columns allowed"

    data = response.json()
    assert data["success"] is True
    # System accepts duplicates, will concatenate values when writing


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_post_column_mappings_invalid_format_returns_400(
    client: AsyncClient, save_column_mappings_contract
):
    """Test POST with invalid format (A1, abc) returns 400 with INVALID_COLUMN_FORMAT."""
    headers = {"session_id": "test-session-invalid"}

    # Test case 1: Numeric character in column (A1)
    payload = {
        "date_column": "A1",
        "description_column": "B",
        "price_column": "C"
    }

    response = await client.post("/api/v1/column-config", headers=headers, json=payload)

    assert response.status_code == 400, "Expected 400 Bad Request for invalid format 'A1'"

    data = response.json()
    assert data["error_code"] == "INVALID_COLUMN_FORMAT", "Expected INVALID_COLUMN_FORMAT"
    assert "field" in data, "Should identify which field failed"
    assert data["field"] == "date_column", "Should identify date_column as invalid"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_post_column_mappings_lowercase_returns_400(
    client: AsyncClient, save_column_mappings_contract
):
    """Test POST with lowercase column (abc) returns 400 with INVALID_COLUMN_FORMAT."""
    headers = {"session_id": "test-session-lowercase"}
    payload = {
        "date_column": "A",
        "description_column": "abc",
        "price_column": "C"
    }

    response = await client.post("/api/v1/column-config", headers=headers, json=payload)

    assert response.status_code == 400, "Expected 400 Bad Request for lowercase 'abc'"

    data = response.json()
    assert data["error_code"] == "INVALID_COLUMN_FORMAT"
    assert data["field"] == "description_column"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_post_column_mappings_out_of_range_returns_400(
    client: AsyncClient, save_column_mappings_contract
):
    """Test POST with column beyond ZZ (AAA) returns 400 with COLUMN_OUT_OF_RANGE."""
    headers = {"session_id": "test-session-out-of-range"}
    payload = {
        "date_column": "A",
        "description_column": "B",
        "price_column": "AAA"  # Beyond ZZ (701) limit
    }

    response = await client.post("/api/v1/column-config", headers=headers, json=payload)

    assert response.status_code == 400, "Expected 400 Bad Request for out-of-range 'AAA'"

    data = response.json()
    assert data["error_code"] == "COLUMN_OUT_OF_RANGE", "Expected COLUMN_OUT_OF_RANGE"
    assert "field" in data
    assert data["field"] == "price_column"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_post_column_mappings_missing_field_returns_400(
    client: AsyncClient, save_column_mappings_contract
):
    """Test POST with missing required field returns 400 with MISSING_REQUIRED_FIELD."""
    headers = {"session_id": "test-session-missing"}
    payload = {
        "date_column": "A",
        "description_column": "B"
        # Missing price_column
    }

    response = await client.post("/api/v1/column-config", headers=headers, json=payload)

    assert response.status_code == 400, "Expected 400 Bad Request for missing field"

    data = response.json()
    assert data["error_code"] == "MISSING_REQUIRED_FIELD", "Expected MISSING_REQUIRED_FIELD"
    assert "field" in data
    assert data["field"] == "price_column", "Should identify missing field"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_post_column_mappings_no_auth_returns_401(
    client: AsyncClient, save_column_mappings_contract
):
    """Test POST without session_id header returns 401."""
    payload = {
        "date_column": "A",
        "description_column": "B",
        "price_column": "C"
    }

    response = await client.post("/api/v1/column-config", json=payload)

    assert response.status_code == 401, "Expected 401 Unauthorized without session_id"

    data = response.json()
    assert data["error_code"] == "AUTH_REQUIRED"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_post_column_mappings_ZZ_valid_returns_200(
    client: AsyncClient, save_column_mappings_contract
):
    """Test POST with ZZ (maximum valid column) returns 200."""
    headers = {"session_id": "test-session-zz"}
    payload = {
        "date_column": "A",
        "description_column": "B",
        "price_column": "ZZ"  # Maximum allowed column (index 701)
    }

    response = await client.post("/api/v1/column-config", headers=headers, json=payload)

    assert response.status_code == 200, "Expected 200 OK - ZZ is valid (within A-ZZ range)"

    data = response.json()
    assert data["success"] is True
    assert data["mappings"]["price_column"] == "ZZ"
