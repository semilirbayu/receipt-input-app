# Tasks: Improve OCR Data Extraction Quality with Gemini Vision

**Input**: Design documents from `/specs/003-bugfix-improve-data/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/extract_gemini.json, quickstart.md
**Branch**: `003-bugfix-improve-data`

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✓ Tech stack: Python 3.11+, FastAPI, google-generativeai, Pydantic
   → ✓ Structure: Web app (backend/src/, backend/tests/)
2. Load optional design documents:
   → ✓ data-model.md: 3 entities (ExtractedData enhanced, ExtractionMetrics, ValidationResult)
   → ✓ contracts/: 1 file (extract_gemini.json) → POST /api/receipts/upload
   → ✓ research.md: 6 decisions (Gemini Flash, JSON schema, IDR parsing, etc.)
   → ✓ quickstart.md: 8 test scenarios
3. Generate tasks by category:
   → Setup: 3 tasks (dependencies, environment, linting)
   → Tests: 8 tasks (contract + integration)
   → Core: 6 tasks (models, services, validation)
   → Integration: 3 tasks (route modification, fallback, metrics)
   → Polish: 4 tasks (unit tests, performance, docs, cleanup)
4. Apply task rules:
   → Different files = [P] parallel execution
   → Same file = sequential
   → Tests before implementation (TDD mandatory)
5. Number tasks T001-T024
6. Validate completeness:
   → ✓ All contracts have tests (1/1)
   → ✓ All entities have models (3/3)
   → ✓ All endpoints modified (1/1)
9. Return: SUCCESS (24 tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Exact file paths included in task descriptions

---

## Phase 3.1: Setup & Prerequisites

- [X] **T001** Install google-generativeai SDK and configure environment
  - **File**: `backend/requirements.txt` + `.env`
  - **Actions**:
    - Add `google-generativeai>=0.3.0` to `backend/requirements.txt`
    - Run `pip install google-generativeai`
    - Add `GEMINI_API_KEY=` to `.env.example`
    - Document API key setup in `README.md` (Gemini API Studio instructions)
  - **Acceptance**: `python -c "import google.generativeai; print('✓ SDK installed')"` succeeds

- [X] **T002** [P] Configure pytest for Gemini mocking and fixtures
  - **File**: `backend/tests/conftest.py`
  - **Actions**:
    - Add `@pytest.fixture` for mocked Gemini API responses
    - Create fixture for sample receipt images (use existing `tests/fixtures/receipts/`)
    - Add environment variable handling (`GEMINI_API_KEY` optional in tests)
  - **Acceptance**: `pytest --collect-only` shows fixtures available

- [X] **T003** [P] Update linting configuration for new code standards
  - **File**: `backend/.ruff.toml` or `pyproject.toml`
  - **Actions**:
    - Ensure 80% coverage requirement configured
    - Add type checking for new Pydantic models
  - **Acceptance**: `ruff check backend/src` passes with no errors

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation in Phase 3.3**

### Contract Tests (API Behavior)

- [X] **T004** [P] Contract test for Gemini extraction response format
  - **File**: `backend/tests/contract/test_gemini_extraction.py`
  - **Actions**:
    - Test Gemini API request structure (image + prompt with JSON schema)
    - Test Gemini API response parsing (JSON → ExtractedData)
    - Test error handling (timeout, rate limit 429, invalid JSON)
    - Mock `google.generativeai.GenerativeModel.generate_content()`
  - **Acceptance Criteria**:
    - Test validates JSON schema matches data-model.md (transaction_date, items, total_amount, confidence, currency, language)
    - Test fails with "ModuleNotFoundError: No module named 'gemini_extractor'" (implementation doesn't exist yet)
  - **Example Assertions**:
    ```python
    # Test JSON schema validation
    response = mock_gemini_response()
    assert "transaction_date" in response
    assert isinstance(response["confidence"]["date"], float)
    assert response["currency"] == "IDR"
    ```

- [X] **T005** [P] Contract test for validation logic (date/price/items)
  - **File**: `backend/tests/contract/test_extraction_validation.py`
  - **Actions**:
    - Test date validation: reject future dates (FR-002), accept any past date
    - Test price validation: positive numbers, IDR format parsing "Rp 1.234.567" → 1234567 (FR-008)
    - Test items validation: gibberish detection, max length 500 chars (FR-011, FR-014)
    - Test confidence threshold categorization (high ≥0.85, medium 0.60-0.84, low <0.60)
  - **Acceptance**: All tests fail with "No module named 'extraction_validator'"
  - **Example Test Cases**:
    ```python
    # Future date rejection
    result = validate_date("2026-01-01")
    assert result.is_valid == False
    assert "future_date" in result.rule_violations

    # IDR parsing
    amount = parse_idr_amount("Rp 1.234.567")
    assert amount == 1234567
    ```

- [X] **T006** [P] Contract test for metrics tracking
  - **File**: `backend/tests/contract/test_extraction_metrics.py`
  - **Actions**:
    - Test metrics aggregation (success rate calculation, confidence distribution)
    - Test daily rollup logic (store in `shared/extraction_metrics.json`)
    - Test extraction method tracking (gemini vs tesseract_fallback counts)
  - **Acceptance**: Tests fail with "No module named 'extraction_metrics'"
  - **Example**:
    ```python
    metrics = ExtractionMetrics(date_extracted=date.today(), total=10, successful=8, ...)
    assert metrics.get_success_rate() == 80.0
    ```

### Integration Tests (End-to-End Scenarios)

- [X] **T007** [P] Integration test: High-quality Indonesian receipt (Gemini)
  - **File**: `backend/tests/integration/test_receipt_upload_gemini.py`
  - **Actions**:
    - POST `/api/receipts/upload` with `tests/fixtures/receipts/testing-receipt.jpeg`
    - Mock Gemini API to return high-confidence Indonesian extraction
    - Assert `extraction_method="gemini"`, `detected_language="id"`, `currency="IDR"`
    - Assert items are paraphrased (not raw OCR)
    - Assert processing time <5000ms (FR-025)
  - **Acceptance**: Test fails because route still uses old OCR service

- [X] **T008** [P] Integration test: Low-quality blurry receipt handling
  - **File**: `backend/tests/integration/test_receipt_upload_gemini.py` (same file, different test function)
  - **Actions**:
    - POST with low-quality image (`testing-receipt3.jpeg`)
    - Mock Gemini to return low confidence scores (<0.6)
    - Assert fields set to null when confidence too low (FR-004: better empty than wrong)
    - Assert `validation.warnings` includes "low_image_quality"
  - **Acceptance**: Test fails (route not implemented)

- [X] **T009** [P] Integration test: Gemini API failure triggers Tesseract fallback
  - **File**: `backend/tests/integration/test_receipt_upload_fallback.py`
  - **Actions**:
    - Mock Gemini API to raise `RateLimitError` (429)
    - Assert system falls back to Tesseract OCR
    - Assert `extraction_method="tesseract_fallback"`
    - Assert `validation.warnings` includes "gemini_api_unavailable"
    - Assert extraction still completes (not 500 error)
  - **Acceptance**: Test fails (fallback logic not implemented)

- [X] **T010** [P] Integration test: Future date rejection
  - **File**: `backend/tests/integration/test_date_validation.py`
  - **Actions**:
    - Mock Gemini to return future date "2026-01-01"
    - Assert date field set to null
    - Assert `validation_errors` includes "future_date_rejected"
    - Assert confidence score reduced to 0.0
  - **Acceptance**: Test fails (validation not implemented)

- [X] **T011** [P] Integration test: Bilingual paraphrasing (ID vs EN)
  - **File**: `backend/tests/integration/test_bilingual_extraction.py`
  - **Actions**:
    - Test Indonesian receipt → items paraphrased in Indonesian (not translated)
    - Test English receipt → items paraphrased in English
    - Assert `detected_language` correctly set ("id" or "en")
    - Verify paraphrasing quality (e.g., "Nsi Grng x2" → "Nasi Goreng (2 portions)")
  - **Acceptance**: Test fails (GeminiExtractor not implemented)

---

## Phase 3.3: Core Implementation (ONLY after tests T004-T011 are failing)

`★ Insight ─────────────────────────────────────`
**Why Tests First is Critical**: Writing tests before implementation forces you to design the API contract first (function signatures, return types, error handling). When tests fail with "ModuleNotFoundError", you know exactly what to build. This prevents over-engineering and ensures every line of code has a purpose: making a test pass.
`─────────────────────────────────────────────────`

### Models (Data Structures)

- [X] **T012** [P] Enhance ExtractedData model with Gemini fields
  - **File**: `backend/src/models/extracted_data.py`
  - **Actions**:
    - Add new fields: `extraction_method`, `detected_language`, `currency`, `validation_errors`, `paraphrased`
    - Add methods: `get_confidence_level()`, `get_ui_indicator()` (✓/⚠/✗)
    - Update `validate()` method to check new field constraints
    - Update `to_dict()` to include new fields in API response
    - Maintain backward compatibility (all new fields have defaults)
  - **Reference**: data-model.md lines 25-121
  - **Acceptance**: T005 validation tests start passing

- [X] **T013** [P] Create ExtractionMetrics model for quality tracking
  - **File**: `backend/src/models/extraction_metrics.py`
  - **Actions**:
    - Create dataclass with fields: `date_extracted`, `total_extractions`, `successful_extractions`, `confidence_distribution`, `extraction_method_usage`
    - Implement `get_success_rate()` and `get_gemini_usage_rate()` methods
    - Implement `to_dict()` for JSON serialization
    - Add persistence logic to `shared/extraction_metrics.json`
  - **Reference**: data-model.md lines 197-232
  - **Acceptance**: T006 metrics tests start passing

- [X] **T014** [P] Create ValidationResult model
  - **File**: `backend/src/models/validation_result.py`
  - **Actions**:
    - Create dataclass with fields: `field_name`, `is_valid`, `confidence_level`, `validation_messages`, `rule_violations`
    - Implement `to_dict()` for API response formatting
  - **Reference**: data-model.md lines 210-219
  - **Acceptance**: T005 validation tests can instantiate ValidationResult

### Services (Business Logic)

- [X] **T015** Create GeminiExtractorService with prompt template
  - **File**: `backend/src/services/gemini_extractor.py`
  - **Actions**:
    - Create `GeminiExtractorService` class
    - Implement `extract(image_path: str) -> ExtractedData` method
    - Create prompt template with JSON schema (see research.md for template)
    - Implement Gemini API call (`genai.GenerativeModel('gemini-1.5-flash')`)
    - Parse JSON response into `ExtractedData` object
    - Handle API errors (timeout, rate limit, invalid response)
    - Set `extraction_method="gemini"`, `paraphrased=True`
  - **Reference**: research.md structured output section, plan.md Phase 1 section
  - **Dependencies**: Requires T012 (ExtractedData model)
  - **Acceptance**: T004 contract test passes, T007 integration test passes

- [X] **T016** Create ExtractionValidator service
  - **File**: `backend/src/services/extraction_validator.py`
  - **Actions**:
    - Create `ExtractionValidator` class
    - Implement `validate_date(date_value) → ValidationResult` (reject future dates per FR-002)
    - Implement `validate_amount(amount, currency) → ValidationResult` (positive, IDR format handling)
    - Implement `validate_items(items_str) → ValidationResult` (gibberish detection, max length)
    - Implement `calculate_final_confidence()` - hybrid Gemini + business rules
  - **Reference**: research.md confidence scoring section
  - **Dependencies**: Requires T014 (ValidationResult model)
  - **Acceptance**: T005 validation tests pass completely

- [X] **T017** Implement metrics recording logic
  - **File**: `backend/src/services/metrics_service.py`
  - **Actions**:
    - Create `MetricsService` class
    - Implement `record_extraction(extracted_data: ExtractedData)` → update daily metrics
    - Implement `get_daily_metrics(date) → ExtractionMetrics`
    - Implement file I/O for `shared/extraction_metrics.json`
    - Handle concurrency (file locking if needed)
  - **Dependencies**: Requires T013 (ExtractionMetrics model)
  - **Acceptance**: T006 metrics tests pass

---

## Phase 3.4: Integration (Connect Components)

- [X] **T018** Modify receipt upload route to use GeminiExtractor
  - **File**: `backend/src/api/routes/receipts.py`
  - **Actions**:
    - Replace `OCRService.process_image()` + `ParserService.parse()` with `GeminiExtractorService.extract()`
    - Add try-except for Gemini failures
    - On Gemini error: fall back to existing Tesseract pipeline, set `extraction_method="tesseract_fallback"`
    - Call `ExtractionValidator.validate_date/amount/items()` on results
    - Call `MetricsService.record_extraction()` after successful extraction
    - Update API response to include new fields (extraction_method, detected_language, currency)
  - **Dependencies**: Requires T015, T016, T017
  - **Acceptance**: T007-T011 integration tests all pass

- [X] **T019** Implement fallback mechanism (Gemini → Tesseract)
  - **File**: `backend/src/services/gemini_extractor.py` (modify)
  - **Actions**:
    - Wrap Gemini call in try-except for `APIError`, `RateLimitError`, `TimeoutError`
    - On exception: log warning, raise custom `GeminiExtractionError`
    - Update route (T018) to catch `GeminiExtractionError` and use Tesseract
  - **Dependencies**: Requires T018
  - **Acceptance**: T009 fallback test passes

- [X] **T020** Add API response validation and error handling
  - **File**: `backend/src/api/routes/receipts.py` (modify)
  - **Actions**:
    - Add validation for uploaded file (JPEG/PNG only, max 5MB per FR-026)
    - Return proper HTTP status codes (400 bad request, 413 file too large, 429 rate limit)
    - Format validation warnings in response (matches contract extract_gemini.json)
  - **Reference**: contracts/extract_gemini.json error responses
  - **Dependencies**: Requires T018
  - **Acceptance**: Invalid file uploads return 400, oversized files return 413

---

## Phase 3.5: Polish & Validation

- [ ] **T021** [P] Write unit tests for Gemini prompt template
  - **File**: `backend/tests/unit/test_gemini_prompt.py`
  - **Actions**:
    - Test prompt generates valid JSON schema
    - Test prompt includes all required instructions (grand total, paraphrasing, language detection)
    - Test prompt handles edge cases (null fields, gibberish)
  - **Coverage Target**: 80% of `gemini_extractor.py`
  - **Acceptance**: `pytest --cov=backend/src/services/gemini_extractor --cov-report=term` shows ≥80%

- [ ] **T022** [P] Performance validation: <5 second p95 latency
  - **File**: `backend/tests/performance/test_extraction_latency.py`
  - **Actions**:
    - Run 100 extraction requests with real Gemini API (or realistic mocks)
    - Measure p95 latency (95th percentile response time)
    - Assert p95 < 5000ms (FR-025 requirement)
    - Measure p50 latency (should be <3500ms typical case)
  - **Acceptance**: All percentiles within target, test passes

- [ ] **T023** [P] Update documentation (README + API docs)
  - **File**: `README.md`, `docs/api.md` (if exists)
  - **Actions**:
    - Document Gemini API key setup (Google AI Studio instructions)
    - Update API response schema documentation (show new fields)
    - Add troubleshooting section (rate limits, API key errors)
    - Document fallback behavior (Gemini → Tesseract)
  - **Acceptance**: New developers can set up Gemini API key following README

- [ ] **T024** Run manual validation scenarios from quickstart.md
  - **File**: Manual testing using `specs/003-bugfix-improve-data/quickstart.md`
  - **Actions**:
    - Run all 8 test scenarios from quickstart.md
    - Test 1: High-quality Indonesian receipt (Gemini)
    - Test 2: Low-quality blurry receipt
    - Test 3: Gemini API failure fallback
    - Test 4: Future date rejection
    - Test 5: IDR currency parsing
    - Test 6: Bilingual paraphrasing
    - Test 7: Metrics tracking
    - Test 8: Latency <5s requirement
    - Check success checklist at end of quickstart.md
  - **Acceptance**: All 8 scenarios pass, checklist complete

---

## Dependencies

```
Setup (T001-T003)
  ↓
Contract Tests (T004-T006) [P] ← MUST RUN IN PARALLEL AND FAIL
  ↓
Integration Tests (T007-T011) [P] ← MUST FAIL
  ↓
Models (T012-T014) [P]
  ↓
T012 → T015 (GeminiExtractor needs ExtractedData)
T014 → T016 (Validator needs ValidationResult)
T013 → T017 (MetricsService needs ExtractionMetrics)
  ↓
T015, T016, T017 → T018 (Route needs all services)
  ↓
T018 → T019 (Fallback modifies route)
T018 → T020 (Error handling modifies route)
  ↓
Polish (T021-T024) [P] ← Can run in parallel after implementation
```

---

## Parallel Execution Examples

### Execute Contract Tests in Parallel (T004-T006)

These tests touch different files and have no dependencies:

```bash
# All three can run simultaneously
pytest backend/tests/contract/test_gemini_extraction.py &
pytest backend/tests/contract/test_extraction_validation.py &
pytest backend/tests/contract/test_extraction_metrics.py &
wait
```

**Expected**: All tests FAIL (no implementation yet) - this is correct!

### Execute Integration Tests in Parallel (T007-T011)

```bash
# Can run together (different test files)
pytest backend/tests/integration/test_receipt_upload_gemini.py &
pytest backend/tests/integration/test_receipt_upload_fallback.py &
pytest backend/tests/integration/test_date_validation.py &
pytest backend/tests/integration/test_bilingual_extraction.py &
wait
```

### Execute Model Creation in Parallel (T012-T014)

These create different files:

```bash
# Create all three models simultaneously
# T012: backend/src/models/extracted_data.py
# T013: backend/src/models/extraction_metrics.py
# T014: backend/src/models/validation_result.py
```

---

## Validation Checklist

*GATE: Verify before marking feature complete*

- [x] All contracts have corresponding tests (1/1 - extract_gemini.json → T004)
- [x] All entities have model tasks (3/3 - ExtractedData, ExtractionMetrics, ValidationResult)
- [x] All tests come before implementation (T004-T011 before T012-T020)
- [x] Parallel tasks truly independent (verified file paths unique)
- [x] Each task specifies exact file path (all tasks include file paths)
- [x] No task modifies same file as another [P] task (T018, T019, T020 are sequential - same file)

---

## Notes for Implementation

`★ Insight ─────────────────────────────────────`
**TDD Red-Green-Refactor Cycle**:
1. **Red**: Write test, run it, watch it FAIL (T004-T011 must fail with import errors)
2. **Green**: Write minimal code to make test PASS (T012-T020 implementation)
3. **Refactor**: Clean up code while keeping tests passing (T021-T024 polish)

**Why This Order Matters**: If you implement T015 (GeminiExtractor) before T004 (contract test), you'll write code based on assumptions, not requirements. The test defines the contract - the implementation fulfills it.
`─────────────────────────────────────────────────`

### Common Pitfalls to Avoid

1. **Skipping test failures**: If T004 doesn't fail with "No module named 'gemini_extractor'", your test isn't correctly importing the code
2. **Implementing before testing**: Resist urge to "just build it quickly" - tests define correctness
3. **Mocking too broadly**: Mock external APIs (Gemini), not your own code (GeminiExtractor logic should be real)
4. **Ignoring fallback**: T009 ensures resilience - don't skip this test

### Success Criteria

After completing all 24 tasks:

- ✅ All 80+ tests passing (contract + integration + unit)
- ✅ Code coverage ≥ 80% for new services
- ✅ Gemini extraction works with high-quality receipts
- ✅ Tesseract fallback works when Gemini fails
- ✅ IDR currency parsing correct ("Rp 1.234.567" → 1234567)
- ✅ Bilingual paraphrasing preserves language
- ✅ Metrics tracked in `shared/extraction_metrics.json`
- ✅ Processing time <5s (p95 latency)
- ✅ Documentation updated
- ✅ All quickstart.md scenarios pass

---

**Status**: ✅ Ready for implementation - 24 tasks generated in dependency order

**Next Step**: Execute T001 to begin setup phase
