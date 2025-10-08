# Gemini Vision API Integration Guide

This document provides technical details about the Gemini Vision API integration for receipt data extraction.

## Overview

The receipt processing app uses Google's Gemini 1.5 Flash model for intelligent receipt data extraction, replacing traditional Tesseract OCR for improved accuracy and intelligent paraphrasing.

## Architecture

```
Receipt Image Upload
        ↓
GeminiExtractorService
        ↓ (on API failure)
Tesseract Fallback
        ↓
ExtractionValidator
        ↓
ExtractedData + ValidationResult
```

### Key Components

1. **GeminiExtractorService** (`backend/src/services/gemini_extractor.py`)
   - Handles Gemini API calls
   - Implements structured prompt with JSON schema
   - Parses responses into `ExtractedData` objects
   - Error handling for API failures

2. **ExtractionValidator** (`backend/src/services/extraction_validator.py`)
   - Validates extracted dates (rejects future dates)
   - Validates amounts (positive numbers, IDR format handling)
   - Validates items (gibberish detection, max length)
   - Hybrid confidence scoring (Gemini + business rules)

3. **MetricsService** (`backend/src/services/metrics_service.py`)
   - Tracks extraction success rates
   - Monitors confidence distributions
   - Records extraction method usage (Gemini vs Tesseract)
   - Stores metrics in `shared/extraction_metrics.json`

## Gemini Prompt Engineering

### Prompt Structure

The extraction prompt includes:
- **JSON Schema**: Exact output format with required fields
- **Critical Rules**: Grand total extraction, IDR parsing, bilingual paraphrasing
- **Validation Constraints**: Future date rejection, null handling
- **Quality Requirements**: Confidence scoring, item formatting

### Example Prompt

```
Analyze this Indonesian/English receipt image and extract data in this exact JSON format:

{
  "transaction_date": "YYYY-MM-DD or null",
  "total_amount": 50000,
  "items": "Item 1; Item 2; Item 3",
  "currency": "IDR",
  "detected_language": "id",
  "confidence": {
    "date": 0.95,
    "amount": 0.98,
    "items": 0.85
  }
}

CRITICAL RULES:
1. Extract GRAND TOTAL only (ignore subtotals, tax lines)
2. For IDR amounts like "Rp 1.234.567", return numeric: 1234567
3. Paraphrase items in SAME language (no translation)
4. Detect language: "id" for Indonesian, "en" for English
5. Reject future dates - return null
6. If field unreadable, return null (better empty than wrong)
...
```

See `backend/src/services/gemini_extractor.py` for full prompt.

## API Configuration

### Environment Variables

```bash
# Required for Gemini extraction
GEMINI_API_KEY=your-api-key-from-google-ai-studio

# Optional (defaults shown)
GEMINI_MODEL=gemini-1.5-flash  # Model version
GEMINI_TIMEOUT=10              # API timeout in seconds
```

### Rate Limits (Free Tier)

- **15 requests per minute**
- **1,500 requests per day**
- When limits exceeded, automatic fallback to Tesseract

## Fallback Mechanism

### Trigger Conditions

The system falls back to Tesseract OCR when:
1. **Rate Limit (429)**: Gemini API quota exceeded
2. **Timeout**: API call exceeds timeout threshold
3. **Service Unavailable (503)**: Gemini API downtime
4. **API Key Invalid**: Missing or expired API key
5. **Network Errors**: Connection failures

### Implementation

```python
try:
    result = gemini_extractor.extract(image_path)
    # extraction_method = "gemini"
except GeminiExtractionError as e:
    logger.warning(f"Gemini extraction failed: {e}, falling back to Tesseract")
    result = tesseract_fallback.extract(image_path)
    # extraction_method = "tesseract_fallback"
```

## Response Schema

### ExtractedData Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `transaction_date` | `date \| null` | Transaction date (YYYY-MM-DD) | `"2025-10-06"` |
| `transaction_date_confidence` | `float` | Confidence score (0.0-1.0) | `0.95` |
| `items` | `str \| null` | Semicolon-delimited items | `"Nasi Goreng (2 porsi); Es Teh"` |
| `items_confidence` | `float` | Confidence score (0.0-1.0) | `0.92` |
| `total_amount` | `Decimal \| null` | Total amount (numeric) | `50000` |
| `total_amount_confidence` | `float` | Confidence score (0.0-1.0) | `0.98` |
| `extraction_method` | `str` | Method used | `"gemini"` or `"tesseract_fallback"` |
| `detected_language` | `str \| null` | Language code | `"id"` or `"en"` |
| `currency` | `str \| null` | Currency code | `"IDR"`, `"USD"` |
| `paraphrased` | `bool` | Items paraphrased? | `true` (Gemini), `false` (Tesseract) |
| `validation_errors` | `list[str]` | Validation warnings | `["future_date_rejected"]` |

### ValidationResult Fields

| Field | Type | Description |
|-------|------|-------------|
| `field_name` | `str` | Field being validated (`"date"`, `"price"`, `"items"`) |
| `is_valid` | `bool` | Validation passed? |
| `confidence_level` | `str` | `"high"` (≥0.85), `"medium"` (0.60-0.84), `"low"` (<0.60) |
| `validation_messages` | `list[str]` | Human-readable validation messages |
| `rule_violations` | `list[str]` | Specific rules violated |

## Validation Rules

### Date Validation (FR-002)

- **Reject future dates** beyond tomorrow
- **Accept any past date** (no historical limit)
- **Recognize multiple formats**: MM/DD/YYYY, DD-MM-YYYY, YYYY-MM-DD, written formats

### Price Validation (FR-006, FR-008)

- **Positive numbers only** (0.01 to 999,999.99)
- **IDR format handling**: "Rp 1.234.567" → 1234567
- **Strip non-numeric characters** except decimal point

### Items Validation (FR-011, FR-014)

- **Gibberish detection**: Reject unreadable text
- **Max length**: 500 characters
- **Sanitize**: Remove OCR artifacts, extra whitespace
- **Format**: Semicolon-separated with quantities in parentheses

## Confidence Scoring

### Gemini Confidence

Gemini returns per-field confidence (0.0-1.0):
- **≥0.85**: High confidence (✓ green indicator)
- **0.60-0.84**: Medium confidence (⚠ yellow indicator)
- **<0.60**: Low confidence (✗ red indicator)

### Hybrid Scoring

Business rules can reduce confidence:
- **Future date**: Confidence set to 0.0
- **Invalid amount**: Confidence set to 0.0
- **Gibberish items**: Confidence reduced by 0.3

## Performance

### Benchmarks (100 requests, mocked API)

| Metric | Value | Requirement |
|--------|-------|-------------|
| **P50 latency** | 1203ms | <3500ms ✅ |
| **P95 latency** | 1902ms | <5000ms ✅ |
| **P99 latency** | 1905ms | - |
| **Mean latency** | 1176ms | - |

Performance meets FR-025 requirement (<5 seconds).

### Real-World Latency

With live Gemini API (based on testing):
- **Typical**: 1-3 seconds
- **Peak load**: 3-5 seconds
- **Network issues**: 5-10 seconds (then fallback)

## Monitoring & Metrics

### Extraction Metrics Tracking

Metrics are tracked daily in `shared/extraction_metrics.json`:

```json
{
  "2025-10-06": {
    "total_extractions": 150,
    "successful_extractions": 142,
    "failed_extractions": 3,
    "partial_extractions": 5,
    "confidence_distribution": {
      "high": 128,
      "medium": 12,
      "low": 10
    },
    "extraction_method_usage": {
      "gemini": 145,
      "tesseract_fallback": 5
    }
  }
}
```

### Success Rate Calculation

```python
success_rate = (successful_extractions / total_extractions) * 100
# Target: >80% (FR-001)
```

### Gemini Usage Rate

```python
gemini_usage_rate = (gemini_count / total_extractions) * 100
# Monitors fallback frequency
```

## Error Handling

### Error Types

1. **GeminiExtractionError**: Base exception for all Gemini failures
2. **Rate Limit (429)**: Quota exceeded, triggers fallback
3. **Timeout**: API call exceeds threshold
4. **Invalid JSON**: Response parsing fails
5. **API Key Error**: Missing or invalid credentials

### Logging

```python
import logging
logger = logging.getLogger('backend.src.services.gemini_extractor')

# Levels:
logger.info("Successfully extracted data: gemini")
logger.warning("Invalid date format: future-date")
logger.error("Gemini API timeout: 10s exceeded")
```

## Testing

### Unit Tests

Run prompt template and parsing tests:

```bash
pytest backend/tests/unit/test_gemini_prompt.py -v
# Coverage target: 80% of gemini_extractor.py ✅ (achieved 100%)
```

### Performance Tests

Run latency validation:

```bash
# Mocked API (fast, no costs)
pytest backend/tests/performance/test_extraction_latency.py -v

# Live API (slow, incurs costs)
pytest backend/tests/performance/test_extraction_latency.py::test_p95_latency_with_real_gemini_api --run-live-api -v
```

### Contract Tests

Validate API contracts:

```bash
pytest backend/tests/contract/test_gemini_extraction.py -v
pytest backend/tests/contract/test_extraction_validation.py -v
pytest backend/tests/contract/test_extraction_metrics.py -v
```

### Integration Tests

End-to-end scenarios:

```bash
pytest backend/tests/integration/test_receipt_upload_gemini.py -v
pytest backend/tests/integration/test_receipt_upload_fallback.py -v
pytest backend/tests/integration/test_bilingual_extraction.py -v
```

## Troubleshooting

### Common Issues

#### 1. All extractions use `tesseract_fallback`

**Cause**: Gemini API key not configured or invalid

**Solution**:
```bash
# Check .env file
cat .env | grep GEMINI_API_KEY

# Verify key is valid at Google AI Studio
# https://makersuite.google.com/app/apikey

# Restart application after updating .env
```

#### 2. Rate limit errors (429)

**Cause**: Free tier quota exceeded (15/min or 1500/day)

**Solution**:
- Wait for quota reset (1 minute or 24 hours)
- Upgrade to paid tier for higher limits
- System automatically falls back to Tesseract

#### 3. Low confidence scores across all receipts

**Cause**: Poor image quality (blurry, low contrast, dark lighting)

**Solution**:
- Re-photograph receipts with better lighting
- Ensure text is sharp and high-contrast
- Use at least 1080p resolution images
- Hold camera steady to avoid motion blur

#### 4. Incorrect language detection

**Cause**: Mixed language receipts or unclear text

**Solution**:
- Gemini detects majority language
- For mixed receipts, items may be in dominant language
- Manual correction recommended for complex cases

## Best Practices

### Image Quality

For best extraction results:
- **Resolution**: Minimum 1080p (1920x1080)
- **Lighting**: Bright, even lighting without shadows
- **Focus**: Sharp text, no motion blur
- **Angle**: Straight-on, no perspective distortion
- **Format**: JPEG or PNG, <5MB

### API Key Security

- **Never commit** `.env` files to version control
- **Use environment variables** in production
- **Rotate keys** periodically
- **Monitor usage** via Google AI Studio console

### Performance Optimization

- **Image compression**: Resize large images before upload
- **Caching**: Consider caching frequent receipt patterns
- **Batch processing**: Use concurrent requests (respect rate limits)

## Future Enhancements

Potential improvements to the Gemini integration:

1. **Multi-page receipts**: Support for multi-image receipts
2. **Receipt categorization**: Auto-categorize by merchant type
3. **Expense splitting**: Detect shared expenses
4. **Tax extraction**: Separate tax amount from total
5. **Merchant detection**: Extract merchant name and logo

## References

- [Gemini API Documentation](https://ai.google.dev/docs)
- [Google AI Studio](https://makersuite.google.com/app/apikey)
- [Feature Spec: 003-bugfix-improve-data](../specs/003-bugfix-improve-data/spec.md)
- [Implementation Tasks](../specs/003-bugfix-improve-data/tasks.md)

## Support

For issues specific to Gemini integration:
1. Check logs: `tail -f logs/app.log` (if logging configured)
2. Verify API key: Test in Google AI Studio playground
3. Check metrics: Review `shared/extraction_metrics.json`
4. Review tests: Run relevant test suites to isolate issues
