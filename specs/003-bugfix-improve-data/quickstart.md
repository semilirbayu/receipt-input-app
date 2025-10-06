# Quickstart Guide: Gemini Vision Receipt Extraction

**Feature**: 003-bugfix-improve-data
**Purpose**: Test and validate the enhanced receipt extraction system
**Audience**: Developers, QA testers

---

## Prerequisites

### 1. Environment Setup

```bash
# Install dependencies
cd /Users/semilirbayu/Dev/Vibe\ Coding/receipt-input-app
pip install google-generativeai pytest pytest-asyncio

# Set Gemini API key
export GEMINI_API_KEY="your-api-key-here"

# Verify setup
python -c "import google.generativeai as genai; print('✓ Gemini SDK installed')"
```

### 2. Test Data

Use existing receipt fixtures in `tests/fixtures/receipts/`:
- `testing-receipt.jpeg` - High-quality Indonesian receipt
- `testing-receipt2.jpeg` - Medium quality
- `testing-receipt3.jpeg` - Low quality / blurry
- `testing-receipt4.jpeg` - English receipt (USD)
- `testing-receipt5.jpeg` - Edge case receipt

---

## Quick Validation Tests

### Test 1: High-Quality Indonesian Receipt (Gemini)

**Objective**: Verify Gemini extracts data with high confidence from clear IDR receipt

**Steps**:
```bash
# 1. Start backend server
cd backend
uvicorn src.main:app --reload

# 2. Upload test receipt
curl -X POST http://localhost:8000/api/receipts/upload \
  -F "file=@../tests/fixtures/receipts/testing-receipt.jpeg" \
  -H "Content-Type: multipart/form-data"
```

**Expected Response**:
```json
{
  "receipt_id": "<uuid>",
  "extracted_data": {
    "transaction_date": "2025-XX-XX",
    "transaction_date_confidence": ">= 0.85",
    "items": "<paraphrased Indonesian items>",
    "items_confidence": ">= 0.80",
    "total_amount": "<numeric IDR amount>",
    "total_amount_confidence": ">= 0.90",
    "extraction_method": "gemini",
    "detected_language": "id",
    "currency": "IDR",
    "paraphrased": true,
    "confidence_indicators": {
      "date": "✓",
      "items": "✓" or "⚠",
      "amount": "✓"
    }
  },
  "validation": {
    "date_valid": true,
    "price_valid": true,
    "items_valid": true,
    "warnings": []
  },
  "processing_time_ms": "< 5000"
}
```

**Success Criteria**:
- ✅ All 3 fields populated (date, items, amount)
- ✅ `extraction_method` = "gemini"
- ✅ `detected_language` = "id"
- ✅ `currency` = "IDR"
- ✅ Items are paraphrased (not raw OCR text)
- ✅ Processing time < 5 seconds
- ✅ At least 2 out of 3 confidence indicators show "✓"

---

### Test 2: Low-Quality Blurry Receipt

**Objective**: Verify system handles poor image quality gracefully (FR-004: better empty than wrong)

**Steps**:
```bash
curl -X POST http://localhost:8000/api/receipts/upload \
  -F "file=@../tests/fixtures/receipts/testing-receipt3.jpeg"
```

**Expected Response**:
```json
{
  "extracted_data": {
    "transaction_date": null,  // or low confidence
    "transaction_date_confidence": "< 0.60",
    "items": "<items or null>",
    "items_confidence": "< 0.70",
    "total_amount": "<amount or null>",
    "total_amount_confidence": "< 0.80",
    "extraction_method": "gemini",
    "confidence_indicators": {
      "date": "✗" or "⚠",
      "items": "⚠" or "✗",
      "amount": "⚠"
    }
  },
  "validation": {
    "warnings": ["low_image_quality"]
  }
}
```

**Success Criteria**:
- ✅ Low confidence scores accurately reflect image quality
- ✅ Null values for unreadable fields (not gibberish)
- ✅ Warning includes "low_image_quality"
- ✅ Response still returns 200 OK (not an error)

---

### Test 3: Gemini API Failure (Fallback to Tesseract)

**Objective**: Verify graceful degradation when Gemini API unavailable

**Steps**:
```bash
# 1. Simulate API failure by unsetting API key
unset GEMINI_API_KEY

# 2. Upload receipt
curl -X POST http://localhost:8000/api/receipts/upload \
  -F "file=@../tests/fixtures/receipts/testing-receipt.jpeg"

# 3. Restore API key
export GEMINI_API_KEY="your-api-key-here"
```

**Expected Response**:
```json
{
  "extracted_data": {
    "transaction_date": "<date>",
    "items": "<items (not paraphrased)>",
    "total_amount": "<amount>",
    "extraction_method": "tesseract_fallback",
    "detected_language": null,
    "paraphrased": false
  },
  "validation": {
    "warnings": ["gemini_api_unavailable", "using_fallback_extraction"]
  }
}
```

**Success Criteria**:
- ✅ `extraction_method` = "tesseract_fallback"
- ✅ Extraction still completes (not 500 error)
- ✅ Warning indicates fallback was used
- ✅ Items are NOT paraphrased (raw Tesseract output)

---

### Test 4: Date Validation (Future Date Rejection)

**Objective**: Verify FR-002 - system rejects future dates

**Steps**:
Create a test receipt with future date (manually edit test image or mock Gemini response):

```python
# In test file: backend/tests/integration/test_date_validation.py
def test_future_date_rejected():
    # Mock Gemini to return future date
    mock_response = {
        "transaction_date": "2026-01-01",  # Future date
        "total_amount": 50000,
        "items": "Test items"
    }

    # Validate
    validator = ExtractionValidator()
    result = validator.validate_date(mock_response["transaction_date"])

    assert result.is_valid == False
    assert "future_date" in result.rule_violations
```

**Success Criteria**:
- ✅ Future dates rejected (set to null or flagged invalid)
- ✅ Validation error includes "future_date" violation
- ✅ Confidence score reduced to 0.0

---

### Test 5: IDR Currency Format Parsing

**Objective**: Verify FR-008 - correct handling of "Rp 1.234.567" format

**Test Cases**:

| Input (on receipt) | Expected Output | Notes |
|-------------------|-----------------|-------|
| Rp 1.234.567 | 1234567 | Periods are thousand-separators |
| Rp 50.000 | 50000 | Standard Indonesian format |
| Rp 150.500 | 150500 | Not a decimal point |
| Rp 25000 | 25000 | Without separators |

**Steps**:
```python
# backend/tests/unit/test_idr_parsing.py
def test_idr_format_parsing():
    test_cases = [
        ("Rp 1.234.567", 1234567),
        ("Rp 50.000", 50000),
        ("Rp 150.500", 150500),
    ]

    for receipt_text, expected_amount in test_cases:
        result = GeminiExtractor.extract_amount(receipt_text)
        assert result == expected_amount
```

**Success Criteria**:
- ✅ All test cases parse correctly
- ✅ No decimal point misinterpretation (1.234.567 ≠ 1.23)
- ✅ Currency metadata preserved ("IDR")

---

### Test 6: Bilingual Paraphrasing

**Objective**: Verify FR-012 - paraphrasing respects source language

**Steps**:
```bash
# Test Indonesian receipt
curl -X POST http://localhost:8000/api/receipts/upload \
  -F "file=@../tests/fixtures/receipts/testing-receipt.jpeg"

# Verify items paraphrased in Indonesian (not translated to English)
# Expected: "Nasi Goreng (2 porsi)" NOT "Fried Rice (2 portions)"
```

**Success Criteria**:
- ✅ Indonesian receipts → Indonesian paraphrased items
- ✅ English receipts → English paraphrased items
- ✅ `detected_language` field correctly set
- ✅ No unwanted translation between languages

---

### Test 7: Metrics Tracking (FR-020)

**Objective**: Verify extraction quality metrics are logged

**Steps**:
```bash
# 1. Process multiple receipts
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/receipts/upload \
    -F "file=@../tests/fixtures/receipts/testing-receipt$i.jpeg"
done

# 2. Check metrics file
cat shared/extraction_metrics.json
```

**Expected Metrics**:
```json
{
  "2025-10-06": {
    "total_extractions": 5,
    "successful_extractions": 4,
    "failed_extractions": 0,
    "partial_extractions": 1,
    "confidence_distribution": {
      "low": 1,
      "medium": 2,
      "high": 2
    },
    "extraction_method_usage": {
      "gemini": 5,
      "tesseract_fallback": 0
    }
  }
}
```

**Success Criteria**:
- ✅ Metrics file exists at `shared/extraction_metrics.json`
- ✅ Counts match number of processed receipts
- ✅ Confidence distribution categorized (low/medium/high)
- ✅ Extraction method usage tracked

---

## Performance Validation

### Test 8: Latency Requirement (FR-025)

**Objective**: Verify <5 second p95 latency

**Steps**:
```bash
# Run load test (requires Apache Bench)
ab -n 100 -c 10 \
  -p test_receipt.jpeg \
  -T "multipart/form-data" \
  http://localhost:8000/api/receipts/upload

# Check p95 latency in results
```

**Success Criteria**:
- ✅ p95 latency < 5000ms
- ✅ p50 latency < 3500ms (typical case)
- ✅ No timeouts or 500 errors

---

## Automated Test Suite

### Running All Integration Tests

```bash
# Run all integration tests
cd backend
pytest tests/integration/test_receipt_upload_gemini.py -v

# Run with coverage
pytest tests/integration/ --cov=src/services/gemini_extractor --cov-report=html

# Expected output:
# ✓ test_high_quality_receipt_gemini_extraction
# ✓ test_low_quality_receipt_handling
# ✓ test_gemini_api_failure_fallback
# ✓ test_future_date_rejection
# ✓ test_idr_currency_parsing
# ✓ test_bilingual_paraphrasing
# ✓ test_metrics_tracking
# ✓ test_processing_time_under_5s
```

---

## Troubleshooting

### Issue: Gemini API Key Error

**Symptom**: `401 Unauthorized` or `GEMINI_API_KEY not found`

**Solution**:
```bash
# Check environment variable
echo $GEMINI_API_KEY

# If empty, set it:
export GEMINI_API_KEY="your-key-from-google-ai-studio"

# Restart server
```

### Issue: All Extractions Using Tesseract Fallback

**Symptom**: `extraction_method` always = "tesseract_fallback"

**Possible Causes**:
1. Gemini API key invalid
2. Rate limit exceeded (15 req/min on free tier)
3. Gemini API downtime

**Debug**:
```bash
# Check logs
tail -f backend/logs/app.log | grep "Gemini"

# Look for error messages like:
# "Gemini failed: RateLimitError, falling back to Tesseract"
```

### Issue: Low Confidence Scores

**Symptom**: All confidence indicators show "⚠" or "✗"

**Possible Causes**:
1. Poor image quality (blur, low resolution)
2. Non-receipt image uploaded
3. Receipt in unsupported language

**Debug**:
```bash
# Check validation warnings
jq '.validation.warnings' response.json

# Expected warnings:
# ["low_image_quality"] or ["unsupported_receipt_format"]
```

---

## Success Checklist

After running all tests, verify:

- [ ] ✅ Gemini extraction works for high-quality receipts
- [ ] ✅ Low-quality images handled gracefully (null fields, low confidence)
- [ ] ✅ Tesseract fallback activates on API failure
- [ ] ✅ Future dates rejected per FR-002
- [ ] ✅ IDR currency parsed correctly (periods as thousand-separators)
- [ ] ✅ Bilingual paraphrasing preserves source language
- [ ] ✅ Metrics tracked per FR-020 (success rate, confidence distribution)
- [ ] ✅ Processing time < 5 seconds (p95 latency)
- [ ] ✅ All integration tests passing
- [ ] ✅ Code coverage ≥ 80% for new services

---

## Next Steps

1. **Run `/tasks` command** to generate detailed implementation tasks
2. **Execute tasks** following TDD approach (tests first, then implementation)
3. **Monitor metrics** in `shared/extraction_metrics.json` after deployment
4. **Iterate on prompt engineering** if confidence scores consistently low

---

**Status**: ✅ Quickstart guide complete - ready for implementation phase
