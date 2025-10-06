# Implementation Plan: Improve OCR Data Extraction Quality

**Branch**: `003-bugfix-improve-data` | **Date**: 2025-10-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-bugfix-improve-data/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✓ Feature spec loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✓ All clarifications resolved in spec
   → ✓ Project Type: web (frontend + backend detected)
   → ✓ Structure Decision: Web application with backend API
3. Fill the Constitution Check section
   → ✓ Constitution loaded (v1.0.0)
4. Evaluate Constitution Check section
   → ✓ No violations detected
   → ✓ Progress Tracking: Initial Constitution Check PASS
5. Execute Phase 0 → research.md
   → ✓ Research completed for Gemini Vision API approach
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → ✓ Design artifacts generated
7. Re-evaluate Constitution Check section
   → ✓ No new violations
   → ✓ Progress Tracking: Post-Design Constitution Check PASS
8. Plan Phase 2 → Describe task generation approach
   → ✓ Task strategy documented
9. STOP - Ready for /tasks command
   → ✓ Plan complete
```

**IMPORTANT**: The /plan command STOPS at step 9. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

This feature improves the quality and reliability of receipt data extraction by replacing the current Tesseract OCR + regex parsing pipeline with Google Gemini Vision API. The primary goals are to achieve 80% success rate for date extraction, eliminate gibberish descriptions through intelligent paraphrasing, correctly extract grand totals from Indonesian receipts (IDR format with "Rp" symbol), and support bilingual receipts (English/Indonesian). The Gemini Vision approach natively handles intelligent paraphrasing (FR-012), gibberish detection (FR-011), and semantic understanding of receipt layouts, dramatically simplifying the codebase while improving extraction quality.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, google-generativeai (Gemini SDK), Pydantic, Pillow
**Storage**: JSON file-based persistence (existing), ExtractedData model (enhanced validation)
**Testing**: pytest with 80% code coverage requirement (contract tests for Gemini integration)
**Target Platform**: Linux server (web application)
**Project Type**: web - frontend (Jinja2 templates) + backend (FastAPI REST API)
**Performance Goals**: <5 second p95 for complete extraction (upload → Gemini API → validation → response)
**Constraints**: Gemini API rate limits (15 req/min free tier), <1500 receipts/day volume, maintain backward compatibility with existing ExtractedData schema
**Scale/Scope**: Single-user internal deployment initially, replacing ~350 lines of OCR+parsing code with ~100 lines of Gemini integration

**User-Provided Implementation Details**:
- Use Google Gemini Vision API as primary extraction method (replaces Tesseract OCR + regex parsing)
- Volume: <1500 receipts/day (within Gemini free tier limits)
- Usage: Internal-first deployment (privacy/offline not blockers)
- Priority: Quality improvement over cost optimization

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. RESTful API Design ✅
- **Status**: COMPLIANT
- **Evidence**: Existing `/api/receipts/upload` endpoint follows REST conventions; enhancement maintains same API contract with improved extraction quality
- **Changes**: No API signature changes; internal extraction service replacement is transparent to API consumers

### II. Responsive UI ✅
- **Status**: COMPLIANT (No UI changes)
- **Evidence**: Feature only modifies backend extraction service; existing responsive UI remains unchanged
- **Changes**: UI confidence indicators (✓/⚠/✗) continue to work with improved confidence scores from Gemini

### III. OAuth2 Authentication for Google Sheets ✅
- **Status**: COMPLIANT
- **Evidence**: Existing Google Sheets OAuth2 integration unchanged; Gemini API uses separate API key authentication (not OAuth2, but appropriate for service-to-service calls)
- **Changes**: New environment variable `GEMINI_API_KEY` for Gemini authentication

### IV. Unit Testing (NON-NEGOTIABLE) ✅
- **Status**: COMPLIANT
- **Evidence**: Will create unit tests for Gemini extraction service with mocked API responses
- **Testing Strategy**:
  - Contract tests for Gemini API request/response format
  - Unit tests for validation logic (date range, IDR format, gibberish detection)
  - Integration tests for complete extraction pipeline
  - Target: 80% coverage for new `GeminiExtractorService`
- **Changes**: Replace existing OCR/parser service tests with Gemini service tests

## Project Structure

### Documentation (this feature)
```
specs/003-bugfix-improve-data/
├── plan.md              # This file (/plan command output)
├── spec.md              # Feature specification (input)
├── research.md          # Phase 0 output - Gemini Vision API research
├── data-model.md        # Phase 1 output - Enhanced ExtractedData model
├── quickstart.md        # Phase 1 output - Testing guide for Gemini integration
└── contracts/           # Phase 1 output - API contracts for extraction endpoint
    └── extract_gemini.json  # OpenAPI schema for Gemini extraction
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── models/
│   │   ├── extracted_data.py          # [MODIFY] Enhanced validation for Gemini responses
│   │   └── extraction_metrics.py      # [NEW] Metrics tracking (FR-020)
│   ├── services/
│   │   ├── gemini_extractor.py        # [NEW] Gemini Vision API integration
│   │   ├── extraction_validator.py    # [NEW] Post-extraction validation
│   │   ├── ocr_service.py            # [DEPRECATE] Keep as fallback
│   │   └── parser_service.py         # [DEPRECATE] Keep as fallback
│   └── api/
│       └── routes/receipts.py        # [MODIFY] Route to use GeminiExtractor
└── tests/
    ├── contract/
    │   ├── test_gemini_extraction.py  # [NEW] Contract tests for Gemini API
    │   └── test_extraction_validation.py  # [NEW] Validation logic tests
    ├── integration/
    │   └── test_receipt_upload_gemini.py  # [NEW] End-to-end extraction tests
    └── unit/
        ├── test_gemini_extractor_unit.py  # [NEW] Unit tests with mocked API
        └── test_extraction_metrics.py     # [NEW] Metrics tracking tests

frontend/
├── src/
│   └── (no changes - UI remains unchanged)
└── tests/
    └── (no changes)
```

**Structure Decision**: Web application structure detected (backend/ + frontend/ directories exist). This feature modifies only backend extraction services while maintaining API compatibility, so frontend requires no changes. The existing ExtractedData model structure is preserved for backward compatibility.

## Phase 0: Outline & Research

### Research Tasks

1. **Gemini Vision API capabilities**:
   - Decision: Use `gemini-1.5-flash` model for cost/speed balance
   - Rationale: Flash model offers 15 req/min free tier, 2-4s latency, native vision+text understanding
   - Alternatives considered: gemini-1.5-pro (slower, costlier), Tesseract improvements (more code complexity)

2. **Structured output from Gemini**:
   - Decision: Use JSON schema in prompt for structured extraction
   - Rationale: Ensures consistent response format, enables type validation
   - Alternatives considered: Free-form text parsing (unreliable), function calling (overkill)

3. **IDR currency format handling**:
   - Decision: Prompt Gemini to normalize "Rp 1.234.567" to numeric value, preserve currency in metadata
   - Rationale: Gemini understands Indonesian currency conventions natively
   - Alternatives considered: Post-processing regex (defeats purpose of using LLM)

4. **Bilingual paraphrasing strategy**:
   - Decision: Prompt includes language detection + paraphrase-in-same-language instruction
   - Rationale: Preserves user's language preference, avoids translation artifacts
   - Alternatives considered: Always translate to English (loses context for Indonesian users)

5. **Fallback strategy for API failures**:
   - Decision: Keep existing Tesseract pipeline as graceful degradation
   - Rationale: Ensures 100% availability despite Gemini downtime/rate limits
   - Alternatives considered: Hard fail on API error (poor UX), queue for retry (adds complexity)

6. **Confidence scoring approach**:
   - Decision: Map Gemini's semantic confidence to 0.0-1.0 scale, validate against business rules
   - Rationale: Combines LLM's understanding with domain validation (e.g., future date rejection)
   - Alternatives considered: Trust Gemini blindly (risky), purely rule-based (defeats LLM advantage)

**Output**: research.md documenting these decisions in detail

## Phase 1: Design & Contracts

### 1. Data Model Design (`data-model.md`)

**Enhanced ExtractedData Model**:
```python
@dataclass
class ExtractedData:
    # Existing fields (preserved for backward compatibility)
    id: str
    receipt_id: str
    transaction_date: Optional[date]
    transaction_date_confidence: float
    items: Optional[str]  # Semicolon-separated
    items_confidence: float
    total_amount: Optional[Decimal]
    total_amount_confidence: float
    raw_ocr_text: str  # Now stores Gemini raw response
    extraction_timestamp: datetime

    # NEW fields for Gemini integration
    extraction_method: str  # "gemini" | "tesseract_fallback"
    detected_language: Optional[str]  # "en" | "id"
    currency: Optional[str]  # "IDR" | "USD"
    validation_errors: List[str]  # e.g., ["future_date_rejected"]
    paraphrased: bool  # True if items were paraphrased by Gemini
```

**New ExtractionMetrics Model** (FR-020):
```python
@dataclass
class ExtractionMetrics:
    date_extracted: date
    total_extractions: int
    successful_extractions: int  # All 3 fields populated
    failed_extractions: int  # All 3 fields null
    partial_extractions: int  # Some fields populated
    confidence_distribution: Dict[str, int]  # {"low": 5, "medium": 10, "high": 20}
    extraction_method_usage: Dict[str, int]  # {"gemini": 30, "tesseract_fallback": 5}
```

**ValidationResult Entity** (from spec):
```python
@dataclass
class ValidationResult:
    field_name: str  # "date" | "price" | "description"
    is_valid: bool
    confidence_level: str  # "low" | "medium" | "high"
    validation_messages: List[str]
    rule_violations: List[str]  # e.g., ["future_date", "negative_amount"]
```

### 2. API Contracts (`contracts/extract_gemini.json`)

**Endpoint**: `POST /api/receipts/upload` (no signature change)

**Request** (unchanged):
```json
{
  "file": "<multipart/form-data>",
  "user_id": "string"
}
```

**Response** (enhanced with new fields):
```json
{
  "receipt_id": "uuid",
  "extracted_data": {
    "transaction_date": "2025-10-06",
    "transaction_date_confidence": 0.95,
    "items": "Nasi Goreng (2 portions); Es Teh Manis",
    "items_confidence": 0.92,
    "total_amount": 50000,
    "total_amount_confidence": 0.98,
    "extraction_method": "gemini",
    "detected_language": "id",
    "currency": "IDR",
    "paraphrased": true
  },
  "validation": {
    "date_valid": true,
    "price_valid": true,
    "items_valid": true,
    "warnings": []
  },
  "processing_time_ms": 3200
}
```

**Error Responses** (new):
```json
{
  "error": "GEMINI_API_LIMIT_EXCEEDED",
  "message": "Rate limit reached, using fallback extraction",
  "extracted_data": { /* Tesseract fallback result */ },
  "extraction_method": "tesseract_fallback"
}
```

### 3. Contract Tests Generation

Tests to generate in `backend/tests/contract/`:

1. **test_gemini_extraction.py**:
   - Test Gemini API request format (image + prompt structure)
   - Test Gemini API response parsing (JSON schema validation)
   - Test error handling (API timeout, invalid response)

2. **test_extraction_validation.py**:
   - Test date validation (FR-002: reject future dates, accept any past date)
   - Test price validation (FR-006: positive numbers, reasonable ranges)
   - Test IDR format handling (FR-008: "Rp 1.234.567" parsing)
   - Test gibberish detection (FR-011: reject unreadable text)
   - Test confidence thresholds (low <0.6, medium 0.6-0.85, high >0.85)

3. **test_metrics_tracking.py**:
   - Test metrics aggregation (FR-020: success rate, confidence distribution)
   - Test daily rollup (store metrics per day)

### 4. Integration Test Scenarios

From user stories in spec → `quickstart.md`:

**Scenario 1: High-quality Indonesian receipt**
```
Given: testing-receipt.jpeg (clear IDR receipt)
When: POST /api/receipts/upload
Then:
  - transaction_date extracted with >0.9 confidence
  - total_amount correctly parsed (IDR format with periods)
  - items paraphrased in Indonesian
  - extraction_method = "gemini"
```

**Scenario 2: Low-quality blurry receipt**
```
Given: testing-receipt-blurry.jpeg
When: POST /api/receipts/upload
Then:
  - Gemini attempts extraction
  - Low confidence scores (<0.6) flagged
  - validation.warnings includes "low_image_quality"
  - Fields may be null (better empty than wrong per FR-004)
```

**Scenario 3: Gemini API failure**
```
Given: Mock Gemini API returns 503 error
When: POST /api/receipts/upload
Then:
  - System falls back to Tesseract OCR
  - extraction_method = "tesseract_fallback"
  - Response includes warning about degraded quality
```

### 5. Update CLAUDE.md

Run the update script to add Gemini Vision to active technologies:

```bash
.specify/scripts/bash/update-agent-context.sh claude
```

This will add to CLAUDE.md:
- Active Technologies: google-generativeai SDK, Gemini 1.5 Flash
- Commands: `export GEMINI_API_KEY=...`, test Gemini integration
- Recent Changes: 003-bugfix-improve-data - Replaced Tesseract with Gemini Vision API

**Output**:
- `data-model.md` with enhanced ExtractedData + new ExtractionMetrics models
- `contracts/extract_gemini.json` with OpenAPI schema
- Failing contract tests in `backend/tests/contract/`
- `quickstart.md` with 3 integration test scenarios
- Updated `CLAUDE.md` at repository root

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **Load baseline**: Start with `.specify/templates/tasks-template.md`

2. **Generate from contracts** (Phase 1 artifacts):
   - Contract test: `test_gemini_extraction.py` [P]
   - Contract test: `test_extraction_validation.py` [P]
   - Contract test: `test_metrics_tracking.py` [P]

3. **Generate from data model**:
   - Model: Create `gemini_extractor.py` with GeminiExtractorService class [P]
   - Model: Create `extraction_validator.py` with validation logic [P]
   - Model: Create `extraction_metrics.py` with metrics tracking [P]
   - Model: Enhance `extracted_data.py` with new fields

4. **Generate from integration scenarios** (quickstart.md):
   - Integration test: Scenario 1 (high-quality receipt)
   - Integration test: Scenario 2 (low-quality receipt)
   - Integration test: Scenario 3 (API failure fallback)

5. **Implementation tasks** (ordered by TDD):
   - Setup: Install `google-generativeai` SDK, configure API key
   - Setup: Create Gemini prompt template for structured extraction
   - Implement: GeminiExtractorService.extract() method (make contract tests pass)
   - Implement: ExtractionValidator.validate_date/price/items() (make validation tests pass)
   - Implement: ExtractionMetrics.record_extraction() (make metrics tests pass)
   - Refactor: Update receipt upload route to use GeminiExtractor
   - Refactor: Add fallback logic (Gemini → Tesseract on failure)
   - Test: Run integration tests from quickstart.md
   - Performance: Verify <5s p95 latency (FR-025)
   - Documentation: Add Gemini API setup to README

**Ordering Strategy**:
- **Parallel [P] tasks**: Contract tests, model files (independent)
- **Sequential dependencies**:
  1. Contract tests (define contracts)
  2. Model implementation (fulfill contracts)
  3. Integration tests (validate end-to-end)
  4. Performance validation (ensure <5s requirement)

**Estimated Output**: ~20 tasks in dependency order

**Example Task Sequence**:
```
1. [P] Write contract test for Gemini API request/response format
2. [P] Write contract test for date/price/items validation logic
3. [P] Write contract test for metrics tracking
4. Install google-generativeai SDK and configure GEMINI_API_KEY
5. Create GeminiExtractorService class with extract() method (stub)
6. Implement Gemini prompt template with JSON schema
7. Implement GeminiExtractorService.extract() - make test #1 pass
8. Create ExtractionValidator class with validation methods
9. Implement date validation (FR-002) - make test #2 pass
10. Implement price validation (FR-006, FR-008 IDR format) - make test #2 pass
... (continue through all 20 tasks)
```

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

No constitutional violations detected. All principles satisfied:
- RESTful API design maintained (no API changes)
- No UI changes required (responsive UI principle N/A)
- Separate authentication for Gemini API (service key, not OAuth2) is appropriate
- Unit testing strategy defined (80% coverage target, TDD approach)

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - approach described above)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (all 4 principles compliant)
- [x] Post-Design Constitution Check: PASS (no new violations)
- [x] All NEEDS CLARIFICATION resolved (5/5 from spec clarification session)
- [x] Complexity deviations documented (none - no violations)

---
*Based on Constitution v1.0.0 - See `/.specify/memory/constitution.md`*
