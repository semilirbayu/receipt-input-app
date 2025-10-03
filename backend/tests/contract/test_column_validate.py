"""
Contract tests for POST /api/v1/column-config/validate endpoint.
Validates API schema compliance with validate-column-reference.json specification.
These tests MUST FAIL until the column validate endpoint is implemented.
"""
import pytest
from httpx import AsyncClient
import json
from pathlib import Path


@pytest.fixture
def validate_column_contract():
    """Load validate column reference API contract specification."""
    contract_path = (
        Path(__file__).parents[3]
        / "specs"
        / "002-feature-select-column"
        / "contracts"
        / "validate-column-reference.json"
    )
    with open(contract_path) as f:
        return json.load(f)


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_validate_single_letter_valid_returns_200(
    client: AsyncClient, validate_column_contract
):
    """Test validate with single letter (A) returns 200 with valid=true and index."""
    payload = {"column": "A"}

    response = await client.post("/api/v1/column-config/validate", json=payload)

    # This test will fail until endpoint is implemented
    assert response.status_code == 200, "Expected 200 OK for validation request"

    data = response.json()
    schema = validate_column_contract["components"]["schemas"]["ValidationResponse"]

    # Validate response schema
    assert "valid" in data, "Missing valid field"
    assert "column" in data, "Missing column field"

    # Validate field values for valid column
    assert data["valid"] is True, "Column 'A' should be valid"
    assert data["column"] == "A", "Should echo back the column"
    assert "index" in data, "Should include index for valid column"
    assert data["index"] == 0, "Column A should have index 0"

    # Should NOT have error fields when valid
    assert "error_code" not in data or data.get("error_code") is None
    assert "message" not in data or data.get("message") is None


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_validate_double_letter_valid_returns_200(
    client: AsyncClient, validate_column_contract
):
    """Test validate with double letter (ZZ) returns 200 with valid=true and index=701."""
    payload = {"column": "ZZ"}

    response = await client.post("/api/v1/column-config/validate", json=payload)

    assert response.status_code == 200, "Expected 200 OK for validation request"

    data = response.json()

    # Validate ZZ is valid (maximum allowed column)
    assert data["valid"] is True, "Column 'ZZ' should be valid"
    assert data["column"] == "ZZ"
    assert "index" in data, "Should include index for valid column"
    assert data["index"] == 701, "Column ZZ should have index 701"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_validate_AA_returns_200_with_index_26(
    client: AsyncClient, validate_column_contract
):
    """Test validate with AA returns 200 with index=26."""
    payload = {"column": "AA"}

    response = await client.post("/api/v1/column-config/validate", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert data["column"] == "AA"
    assert data["index"] == 26, "Column AA should have index 26 (first double-letter column)"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_validate_invalid_format_A1_returns_200_with_valid_false(
    client: AsyncClient, validate_column_contract
):
    """Test validate with invalid format (A1) returns 200 with valid=false and error_code."""
    payload = {"column": "A1"}

    response = await client.post("/api/v1/column-config/validate", json=payload)

    assert response.status_code == 200, "Expected 200 OK (validation result, not error)"

    data = response.json()

    # Validate response indicates invalid
    assert data["valid"] is False, "Column 'A1' should be invalid"
    assert data["column"] == "A1", "Should echo back the column"

    # Should have error fields when invalid
    assert "error_code" in data, "Should include error_code for invalid column"
    assert data["error_code"] == "INVALID_COLUMN_FORMAT", "Expected INVALID_COLUMN_FORMAT"
    assert "message" in data, "Should include message for invalid column"
    assert isinstance(data["message"], str)

    # Should NOT have index field when invalid
    assert "index" not in data or data.get("index") is None


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_validate_lowercase_abc_returns_200_with_valid_false(
    client: AsyncClient, validate_column_contract
):
    """Test validate with lowercase (abc) returns 200 with valid=false and INVALID_COLUMN_FORMAT."""
    payload = {"column": "abc"}

    response = await client.post("/api/v1/column-config/validate", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert data["valid"] is False
    assert data["column"] == "abc"
    assert data["error_code"] == "INVALID_COLUMN_FORMAT"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_validate_out_of_range_AAA_returns_200_with_valid_false(
    client: AsyncClient, validate_column_contract
):
    """Test validate with out-of-range (AAA) returns 200 with valid=false and COLUMN_OUT_OF_RANGE."""
    payload = {"column": "AAA"}

    response = await client.post("/api/v1/column-config/validate", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert data["valid"] is False, "Column 'AAA' should be invalid (out of range)"
    assert data["column"] == "AAA"
    assert "error_code" in data
    assert data["error_code"] == "COLUMN_OUT_OF_RANGE", "Expected COLUMN_OUT_OF_RANGE"
    assert "message" in data
    assert "ZZ" in data["message"] or "range" in data["message"].lower()


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_validate_missing_column_field_returns_400(
    client: AsyncClient, validate_column_contract
):
    """Test validate with missing 'column' field returns 400."""
    payload = {}  # Missing 'column' field

    response = await client.post("/api/v1/column-config/validate", json=payload)

    assert response.status_code == 400, "Expected 400 Bad Request for missing field"

    data = response.json()
    error_schema = validate_column_contract["components"]["schemas"]["ErrorResponse"]

    # Validate error response structure
    assert "error_code" in data
    assert "message" in data
    assert data["error_code"] == "MISSING_COLUMN_FIELD", "Expected MISSING_COLUMN_FIELD"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_validate_Z_returns_200_with_index_25(
    client: AsyncClient, validate_column_contract
):
    """Test validate with Z returns 200 with index=25."""
    payload = {"column": "Z"}

    response = await client.post("/api/v1/column-config/validate", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert data["column"] == "Z"
    assert data["index"] == 25, "Column Z should have index 25"


@pytest.mark.contract
@pytest.mark.column_config
@pytest.mark.asyncio
async def test_validate_empty_string_returns_200_with_valid_false(
    client: AsyncClient, validate_column_contract
):
    """Test validate with empty string returns 200 with valid=false."""
    payload = {"column": ""}

    response = await client.post("/api/v1/column-config/validate", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert data["valid"] is False, "Empty string should be invalid"
    assert data["column"] == ""
    assert data["error_code"] == "INVALID_COLUMN_FORMAT"
