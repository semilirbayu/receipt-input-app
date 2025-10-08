# Research: Gemini Vision API for Receipt Extraction

**Feature**: 003-bugfix-improve-data
**Date**: 2025-10-06
**Context**: Replacing Tesseract OCR + regex parsing with Gemini Vision API

## Research Questions

### 1. Gemini Vision API Capabilities for Receipt OCR

**Question**: Can Gemini Vision API extract structured data from receipt images with sufficient accuracy for production use?

**Decision**: Use `gemini-1.5-flash` model for receipt data extraction

**Rationale**:
- **Native vision understanding**: Gemini processes images directly without separate OCR step, understanding context like "Total" vs "Subtotal" semantically
- **Structured output support**: Can request JSON-formatted responses with specific schema, eliminating need for regex parsing
- **Multilingual capability**: Handles English and Indonesian text natively (required per FR-010)
- **Cost/performance balance**: Flash model provides 2-4s latency (vs 6-8s for Pro), within our <5s requirement (FR-025)
- **Free tier suitability**: 15 requests/min, 1500 requests/day aligns with <1500 receipts/day volume from spec clarifications

**Alternatives Considered**:
1. **gemini-1.5-pro**:
   - Pros: Higher accuracy (~5-10% better on complex documents)
   - Cons: 2-3x slower (4-8s latency), more expensive ($0.00125 vs $0.000125 per image)
   - Rejected: Speed/cost trade-off not justified for receipt simplicity

2. **Improved Tesseract pipeline** (multi-pass OCR, adaptive preprocessing):
   - Pros: No API dependency, zero cost, offline-capable
   - Cons: Doesn't solve paraphrasing (FR-012) or gibberish detection (FR-011), requires ~350+ lines of complex code
   - Rejected: Can't meet "intelligent paraphrasing" requirement without LLM

3. **Azure Computer Vision + GPT-4V**:
   - Pros: Similar capabilities to Gemini
   - Cons: More expensive, separate OCR+LLM steps add latency, no Indonesian-optimized models
   - Rejected: Gemini's single-step processing is faster and cheaper

**Implementation Details**:
```python
import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content([prompt, image])
```

**Performance Benchmarks** (from Google documentation):
- Latency: 2-4s for typical receipt image (< 2MB)
- Accuracy: 85-95% on structured document extraction tasks
- Rate limits: 15 RPM (requests per minute) on free tier

---

### 2. Structured Output Format from Gemini

**Question**: How to ensure consistent, parseable responses from Gemini for receipt extraction?

**Decision**: Use JSON schema specification in prompt with explicit validation instructions

**Rationale**:
- **Prompt engineering**: Gemini responds well to structured output requests when schema is clearly defined in prompt
- **Type safety**: JSON schema enables Pydantic validation of response before database storage
- **Error handling**: Missing fields return `null` rather than causing parse errors
- **Confidence scores**: Can request per-field confidence as part of JSON structure

**Alternatives Considered**:
1. **Free-form text parsing**:
   - Pros: More flexible, allows conversational responses
   - Cons: Requires regex parsing (defeats purpose), unpredictable format
   - Rejected: Adds back the complexity we're removing

2. **Function calling API**:
   - Pros: Structured by design, type-validated by Gemini
   - Cons: Adds latency (+500ms), requires function definition boilerplate
   - Rejected: JSON-in-prompt achieves same result with less overhead

**Prompt Template** (simplified):
```
Analyze this Indonesian/English receipt image and extract data in this exact JSON format:

{
  "transaction_date": "YYYY-MM-DD or null",
  "total_amount": 50000,  // numeric only, no currency symbol
  "items": "Item 1; Item 2; Item 3",  // semicolon-separated, paraphrased
  "currency": "IDR",
  "detected_language": "id",
  "confidence": {
    "date": 0.95,  // 0.0-1.0
    "amount": 0.98,
    "items": 0.85
  }
}

Rules:
- Extract GRAND TOTAL only (ignore subtotals/tax lines)
- For IDR amounts like "Rp 1.234.567", return numeric: 1234567
- Paraphrase items for clarity (e.g., "Nsi Grng x2" → "Nasi Goreng (2 portions)")
- Reject future dates (return null)
- If field unreadable, return null (better empty than wrong)
```

**Validation Strategy**:
```python
# Parse response
data = json.loads(response.text)

# Pydantic validation
validated = ExtractedDataSchema(**data)

# Business rule validation
if validated.transaction_date and validated.transaction_date > date.today():
    validated.transaction_date = None  # Reject future dates per FR-002
```

---

### 3. IDR Currency Format Handling

**Question**: How to correctly parse Indonesian Rupiah amounts with period thousand-separators?

**Decision**: Prompt Gemini to normalize IDR format to pure numeric, preserve currency metadata separately

**Rationale**:
- **Native understanding**: Gemini knows "Rp 1.234.567" = 1,234,567 IDR without explicit rules
- **Avoids regex pitfalls**: No need for complex logic to distinguish thousand-separator periods from decimal points
- **Currency metadata**: Store "IDR" separately for future multi-currency support

**Example Transformations** (Gemini handles automatically):
| Receipt Text | Gemini Output | Database Storage |
|--------------|---------------|------------------|
| Rp 1.234.567 | 1234567 | Decimal(1234567), currency="IDR" |
| Rp 50.000 | 50000 | Decimal(50000), currency="IDR" |
| Rp 150.500 | 150500 | Decimal(150500), currency="IDR" |
| $15.50 | 15.50 | Decimal(15.50), currency="USD" |

**Alternatives Considered**:
1. **Post-processing regex**:
   - Pros: Full control over parsing logic
   - Cons: Defeats purpose of using LLM, reintroduces complexity
   - Rejected: Gemini handles this natively

2. **Store as string, parse on read**:
   - Pros: Preserves original format
   - Cons: Requires parsing every time data is used, error-prone
   - Rejected: Database should store normalized numeric values

**Edge Cases Handled**:
- Mixed currency on same receipt: Gemini detects dominant currency (usually IDR for Indonesian receipts)
- Ambiguous formats (e.g., "50.000" without "Rp"): Gemini infers from receipt context
- Handwritten amounts: Gemini vision model can read handwriting (Tesseract cannot)

---

### 4. Bilingual Paraphrasing Strategy

**Question**: How to paraphrase receipt items while preserving the original language (Indonesian or English)?

**Decision**: Prompt includes language detection + same-language paraphrasing instruction

**Rationale**:
- **User expectation**: Indonesian users expect Indonesian output, English users expect English
- **Context preservation**: Translation can lose meaning (e.g., "Nasi Goreng" → "Fried Rice" loses cultural specificity)
- **LLM capability**: Gemini can detect and maintain language consistency without separate detection step

**Prompt Instructions**:
```
1. Detect receipt language (Indonesian="id", English="en")
2. Paraphrase items in the SAME language:
   - Indonesian receipt → Indonesian paraphrased items
   - English receipt → English paraphrased items
3. Improve clarity while preserving meaning:
   - Fix OCR errors: "Nsi Grng" → "Nasi Goreng"
   - Expand abbreviations: "Teh Mns" → "Teh Manis"
   - Add quantity context: "x2" → "(2 portions)"
```

**Example Transformations**:
| OCR Output (Indonesian) | Paraphrased (Indonesian) |
|------------------------|--------------------------|
| Nsi Grng x2 | Nasi Goreng (2 portions) |
| Es Teh Mns | Es Teh Manis |
| Ayam Grg 1/2 | Ayam Goreng setengah porsi |

| OCR Output (English) | Paraphrased (English) |
|---------------------|----------------------|
| Chkn Wng x3 | Chicken Wings (3 pieces) |
| Iced Tea Lg | Iced Tea (Large) |

**Alternatives Considered**:
1. **Always translate to English**:
   - Pros: Simpler, single output language
   - Cons: Loses Indonesian cultural context, poor UX for Indonesian users
   - Rejected: Users expect their language preserved

2. **No paraphrasing, just OCR cleanup**:
   - Pros: Preserves exact item names
   - Cons: Doesn't meet FR-012 (intelligent paraphrasing requirement)
   - Rejected: Spec explicitly requires paraphrasing

---

### 5. Fallback Strategy for API Failures

**Question**: What happens when Gemini API is unavailable or exceeds rate limits?

**Decision**: Keep existing Tesseract + parser pipeline as graceful degradation fallback

**Rationale**:
- **High availability**: Ensures 100% uptime even if Gemini has outages
- **Rate limit handling**: Free tier has 15 req/min limit; fallback prevents user-facing errors
- **Code preservation**: Tesseract pipeline already exists and tested; minimal cost to maintain
- **User transparency**: Response includes `extraction_method` field so users know quality may be degraded

**Fallback Logic**:
```python
def extract_receipt_data(image_path: str) -> ExtractedData:
    try:
        # Try Gemini first (better quality)
        result = GeminiExtractor.extract(image_path)
        result.extraction_method = "gemini"
        return result

    except (APIError, RateLimitError, TimeoutError) as e:
        logger.warning(f"Gemini failed: {e}, falling back to Tesseract")

        # Fallback to Tesseract + parser
        ocr_text = OCRService.process_image(image_path)
        result = ParserService.parse_receipt_data(ocr_text)
        result.extraction_method = "tesseract_fallback"
        return result
```

**Error Scenarios**:
| Error Type | Gemini Behavior | Fallback Action | User Impact |
|------------|----------------|-----------------|-------------|
| Rate limit (429) | Request rejected | Use Tesseract | Lower quality, response includes warning |
| Timeout (>10s) | Request aborted | Use Tesseract | Slightly slower response |
| API downtime (503) | Connection failed | Use Tesseract | Lower quality, logged for monitoring |
| Invalid image | Returns null fields | Return null fields | Same behavior (no fallback needed) |

**Alternatives Considered**:
1. **Hard fail on Gemini error**:
   - Pros: Simpler code, forces investigation of failures
   - Cons: Poor user experience, breaks core functionality
   - Rejected: Availability is critical for production app

2. **Queue for retry**:
   - Pros: Eventually processes all with Gemini quality
   - Cons: Adds complexity (queue infrastructure), delays user feedback
   - Rejected: Real-time extraction required per FR-024 (existing workflow)

3. **Remove Tesseract entirely**:
   - Pros: Cleaner codebase, no maintenance burden
   - Cons: Single point of failure, vulnerable to API changes
   - Rejected: Fallback ensures reliability

---

### 6. Confidence Scoring Approach

**Question**: How to generate reliable confidence scores from Gemini responses?

**Decision**: Hybrid approach - Gemini's semantic confidence + business rule validation

**Rationale**:
- **Semantic confidence**: Gemini can assess "how confident am I this is a date?" based on context
- **Rule-based adjustment**: Reduce confidence if business rules violated (e.g., future date, negative amount)
- **User trust**: Confidence indicators (✓/⚠/✗) must accurately reflect reliability per FR-019

**Confidence Calculation**:
```python
def calculate_final_confidence(gemini_conf: float, field_value: Any, field_type: str) -> float:
    # Start with Gemini's semantic confidence
    confidence = gemini_conf

    # Apply business rule penalties
    if field_type == "date":
        if field_value > date.today() + timedelta(days=1):
            confidence = 0.0  # Future date invalid per FR-002
        elif field_value < date(1900, 1, 1):
            confidence *= 0.5  # Very old date suspicious

    elif field_type == "amount":
        if field_value < 0:
            confidence = 0.0  # Negative amount invalid per FR-006
        elif field_value > 999_999:
            confidence *= 0.7  # Unusually large amount

    elif field_type == "items":
        if detect_gibberish(field_value):
            confidence = 0.0  # Gibberish detected per FR-011
        elif len(field_value) < 3:
            confidence *= 0.6  # Very short items suspicious

    return confidence
```

**Confidence Thresholds** (for UI indicators):
- **High (✓)**: ≥ 0.85 - Auto-fill with high trust
- **Medium (⚠)**: 0.60-0.84 - Auto-fill but flag for review
- **Low (✗)**: < 0.60 - Leave empty, require manual input per FR-004

**Alternatives Considered**:
1. **Trust Gemini confidence blindly**:
   - Pros: Simpler, no extra logic needed
   - Cons: Gemini might be confident about semantically valid but business-rule-invalid data
   - Rejected: Domain validation necessary

2. **Purely rule-based confidence** (ignore Gemini scores):
   - Pros: Full control over scoring logic
   - Cons: Loses Gemini's semantic understanding (e.g., "date looks like phone number")
   - Rejected: Hybrid approach leverages both strengths

---

## Implementation Recommendations

### Phase 1 Priorities

1. **Set up Gemini API integration**:
   - Install `google-generativeai` SDK
   - Configure API key in environment variables
   - Create `GeminiExtractorService` class

2. **Design prompt template**:
   - JSON schema definition
   - Extraction rules (grand total, paraphrasing, language detection)
   - Edge case handling (null values, invalid dates)

3. **Implement validation layer**:
   - Date range validation (FR-002)
   - Amount validation (FR-006, FR-008)
   - Gibberish detection (FR-011)
   - Confidence score calculation

4. **Preserve fallback mechanism**:
   - Keep existing `OCRService` and `ParserService`
   - Add try-except logic in receipt upload route
   - Log fallback usage for monitoring

### Testing Strategy

1. **Contract tests**:
   - Mock Gemini API responses
   - Validate JSON schema parsing
   - Test error handling (timeout, rate limit, invalid response)

2. **Integration tests**:
   - Use real receipt images from `tests/fixtures/receipts/`
   - Test Indonesian receipts (IDR format, Indonesian language)
   - Test English receipts (USD format, English language)
   - Test low-quality images (blurry, poor lighting)

3. **Performance tests**:
   - Measure end-to-end latency (target <5s per FR-025)
   - Test rate limit handling (simulate 15+ req/min)
   - Compare Gemini vs Tesseract extraction quality

### Monitoring & Metrics

Track the following metrics per FR-020:
- **Extraction method distribution**: % Gemini vs % Tesseract fallback
- **Success rates**: % with all 3 fields populated
- **Confidence distribution**: Counts of low/medium/high confidence results
- **Fallback triggers**: Frequency of API errors by type (rate limit, timeout, etc.)

---

## Conclusion

Gemini Vision API provides a superior approach to receipt extraction compared to traditional OCR+parsing:

**Key Advantages**:
1. ✅ Natively handles paraphrasing (FR-012) and gibberish detection (FR-011)
2. ✅ Understands IDR currency format without complex regex (FR-008)
3. ✅ Bilingual support with language detection (FR-010)
4. ✅ Reduces codebase from ~350 lines to ~100 lines
5. ✅ Within performance budget (<5s per FR-025)
6. ✅ Within cost budget (free tier for <1500/day volume)

**Risk Mitigations**:
1. ✅ Tesseract fallback ensures high availability
2. ✅ Hybrid confidence scoring prevents blind trust in LLM
3. ✅ Business rule validation enforces domain constraints
4. ✅ Metrics tracking enables quality monitoring

**Next Steps**: Proceed to Phase 1 design (data models, contracts, tests)
