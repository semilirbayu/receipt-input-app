"""
Contract tests for POST /api/v1/upload endpoint.
Validates API schema compliance with upload-api.yaml specification.
These tests MUST FAIL until the upload endpoint is implemented.
"""
import pytest
from httpx import AsyncClient
import yaml
from pathlib import Path
import io


@pytest.fixture
def upload_contract():
    """Load upload API contract specification."""
    contract_path = Path(__file__).parents[3] / "specs" / "001-feature-receipt-processing" / "contracts" / "upload-api.yaml"
    with open(contract_path) as f:
        return yaml.safe_load(f)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_upload_valid_file_returns_200_with_schema(client: AsyncClient, upload_contract):
    """Test valid multipart/form-data upload returns 200 with correct schema."""
    # Create a mock JPG file
    file_content = b"fake image content"
    files = {"file": ("receipt.jpg", io.BytesIO(file_content), "image/jpeg")}

    response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 200, "Expected 200 OK for valid upload"

    data = response.json()
    schema = upload_contract["paths"]["/api/v1/upload"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]

    # Validate response schema
    assert "receipt_id" in data, "Missing receipt_id field"
    assert "status" in data, "Missing status field"
    assert "extracted_data" in data, "Missing extracted_data field"

    # Validate field types
    assert isinstance(data["receipt_id"], str), "receipt_id must be string"
    assert data["status"] in ["completed", "failed"], "status must be 'completed' or 'failed'"

    # Validate extracted_data structure
    if data["extracted_data"] is not None:
        extracted = data["extracted_data"]
        if "transaction_date" in extracted and extracted["transaction_date"] is not None:
            assert isinstance(extracted["transaction_date"], str), "transaction_date must be string"
        if "items" in extracted and extracted["items"] is not None:
            assert isinstance(extracted["items"], str), "items must be string"
            assert len(extracted["items"]) <= 500, "items must be max 500 chars"
        if "total_amount" in extracted and extracted["total_amount"] is not None:
            assert isinstance(extracted["total_amount"], (int, float)), "total_amount must be number"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_upload_file_too_large_returns_400(client: AsyncClient):
    """Test file size >5MB returns 400 with FILE_TOO_LARGE error."""
    # Create a mock file >5MB
    large_content = b"x" * (5 * 1024 * 1024 + 1)  # 5MB + 1 byte
    files = {"file": ("large.jpg", io.BytesIO(large_content), "image/jpeg")}

    response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 400, "Expected 400 Bad Request for oversized file"

    data = response.json()
    assert data["error_code"] == "FILE_TOO_LARGE", "Expected FILE_TOO_LARGE error code"
    assert "message" in data, "Missing error message"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_upload_invalid_format_returns_400(client: AsyncClient):
    """Test invalid format (PDF) returns 400 with INVALID_FORMAT error."""
    file_content = b"%PDF-1.4 fake pdf content"
    files = {"file": ("receipt.pdf", io.BytesIO(file_content), "application/pdf")}

    response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 400, "Expected 400 Bad Request for invalid format"

    data = response.json()
    assert data["error_code"] == "INVALID_FORMAT", "Expected INVALID_FORMAT error code"
    assert "message" in data, "Missing error message"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_upload_missing_file_returns_400(client: AsyncClient):
    """Test missing file returns 400 with MISSING_FILE error."""
    response = await client.post("/api/v1/upload")

    assert response.status_code == 400, "Expected 400 Bad Request for missing file"

    data = response.json()
    assert data["error_code"] == "MISSING_FILE", "Expected MISSING_FILE error code"
    assert "message" in data, "Missing error message"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_upload_response_includes_processing_time(client: AsyncClient):
    """Test successful upload includes processing_time_ms in response."""
    file_content = b"fake image content"
    files = {"file": ("receipt.jpg", io.BytesIO(file_content), "image/jpeg")}

    response = await client.post("/api/v1/upload", files=files)

    if response.status_code == 200:
        data = response.json()
        assert "processing_time_ms" in data, "Missing processing_time_ms field"
        assert isinstance(data["processing_time_ms"], int), "processing_time_ms must be integer"
        assert data["processing_time_ms"] >= 0, "processing_time_ms must be non-negative"
