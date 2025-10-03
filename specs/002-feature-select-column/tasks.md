# Tasks: Column Mapping Configuration

**Input**: Design documents from `/specs/002-feature-select-column/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md
**Feature Branch**: `002-feature-select-column`

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
   → Extract: Python 3.11+, FastAPI, gspread, Pydantic
   → Structure: web (backend/src/, frontend/src/)
2. Load optional design documents: ✓
   → data-model.md: 4 entities extracted
   → contracts/: 3 contract files found
   → research.md: 5 technical decisions loaded
   → quickstart.md: 9 test scenarios identified
3. Generate tasks by category:
   → Setup: Dependencies, testing configuration
   → Tests: 3 contract tests, 4 unit test files, 2 integration tests
   → Core: 4 models/services, 3 API endpoints
   → Integration: Frontend UI, existing code modifications
   → Polish: End-to-end validation, coverage check
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file modifications = sequential
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001-T030)
6. Dependencies validated
7. Parallel execution examples included
8. Task completeness validated:
   ✓ All 3 contracts have tests
   ✓ All 4 entities have model/service tasks
   ✓ All endpoints implemented
9. Return: SUCCESS (30 tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `backend/src/` for source, `backend/tests/` for tests
- **Frontend**: `frontend/src/` for source
- **Shared**: `shared/` for JSON storage
- Paths are absolute from repository root

---

## Phase 3.1: Setup & Configuration

- [x] **T001** Install dependencies for column validation: Ensure pydantic is in requirements.txt (already present from plan.md)

- [x] **T002** [P] Create test directory structure:
  - `backend/tests/unit/models/` (if not exists)
  - `backend/tests/unit/services/` (if not exists)
  - `backend/tests/contract/` (if not exists)
  - `backend/tests/integration/` (if not exists)

- [x] **T003** [P] Configure pytest markers for new test categories in `pytest.ini`:
  - Add marker: `contract: Contract tests for API endpoints`
  - Add marker: `column_config: Column mapping configuration tests`

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (API Endpoint Validation)

- [x] **T004** [P] Contract test GET /api/v1/column-config in `backend/tests/contract/test_column_config_get.py`:
  - Test 200: Returns configured mappings (date_column, description_column, price_column)
  - Test 404: Returns COLUMN_MAPPINGS_NOT_CONFIGURED when not set
  - Test 401: Returns AUTH_REQUIRED without session_id header
  - Validate response schema against `contracts/get-column-mappings.json`
  - **Must fail** (endpoint doesn't exist yet)

- [x] **T005** [P] Contract test POST /api/v1/column-config in `backend/tests/contract/test_column_config_post.py`:
  - Test 200: Saves valid mappings and returns success
  - Test 400: INVALID_COLUMN_FORMAT for invalid formats (A1, abc, AAA)
  - Test 400: COLUMN_OUT_OF_RANGE for columns beyond ZZ
  - Test 400: MISSING_REQUIRED_FIELD when fields missing
  - Test 401: AUTH_REQUIRED without session_id
  - Test duplicate columns allowed (A, B, A) returns 200
  - Test non-contiguous columns (A, C, F) returns 200
  - Validate request/response schemas against `contracts/save-column-mappings.json`
  - **Must fail** (endpoint doesn't exist yet)

- [x] **T006** [P] Contract test POST /api/v1/column-config/validate in `backend/tests/contract/test_column_validate.py`:
  - Test 200: Valid single letter (A) returns `{valid: true, index: 0}`
  - Test 200: Valid double letter (ZZ) returns `{valid: true, index: 701}`
  - Test 200: Invalid format (A1) returns `{valid: false, error_code: INVALID_COLUMN_FORMAT}`
  - Test 200: Out of range (AAA) returns `{valid: false, error_code: COLUMN_OUT_OF_RANGE}`
  - Test 400: Missing column field
  - Validate schemas against `contracts/validate-column-reference.json`
  - **Must fail** (endpoint doesn't exist yet)

### Unit Tests (Core Logic Validation)

- [x] **T007** [P] Unit tests for ColumnValidator in `backend/tests/unit/services/test_column_validator.py`:
  - Test `validate("A")` returns `(True, None)`
  - Test `validate("ZZ")` returns `(True, None)`
  - Test `validate("A1")` returns `(False, "INVALID_COLUMN_FORMAT")`
  - Test `validate("abc")` returns `(False, "INVALID_COLUMN_FORMAT")` (lowercase)
  - Test `validate("AAA")` returns `(False, "COLUMN_OUT_OF_RANGE")`
  - Test `to_index("A")` returns 0
  - Test `to_index("Z")` returns 25
  - Test `to_index("AA")` returns 26
  - Test `to_index("AB")` returns 27
  - Test `to_index("ZZ")` returns 701
  - Test `from_index(0)` returns "A"
  - Test `from_index(25)` returns "Z"
  - Test `from_index(26)` returns "AA"
  - Test `from_index(701)` returns "ZZ"
  - **Must fail** (service doesn't exist yet)

- [x] **T008** [P] Unit tests for ColumnMappingConfiguration in `backend/tests/unit/models/test_column_mapping.py`:
  - Test `validate()` returns `(True, None)` for valid config (A, B, C)
  - Test `validate()` returns `(False, error)` when field missing
  - Test `validate()` returns `(False, error)` for invalid column format
  - Test `to_dict()` returns `{date: "A", description: "B", price: "C"}`
  - Test `from_dict(data)` creates valid instance
  - Test `get_column_index("A")` returns 0
  - Test `has_duplicates()` returns False for (A, B, C)
  - Test `has_duplicates()` returns True for (A, B, A)
  - Test `get_duplicate_columns()` returns `{A: [date, price]}` for (A, B, A)
  - **Must fail** (model doesn't exist yet)

- [x] **T009** [P] Unit tests for UserPreference.column_mappings in `backend/tests/unit/models/test_user_preference.py`:
  - Test `has_column_mappings()` returns False when field missing
  - Test `has_column_mappings()` returns True when field exists
  - Test `get_column_mappings()` returns None when not configured
  - Test `get_column_mappings()` returns ColumnMappingConfiguration when configured
  - Test `set_column_mappings(config)` saves config to dict
  - Test `save()` persists column_mappings to JSON file
  - Test `load_by_session_id()` loads preference without column_mappings (backward compat)
  - Test `load_by_session_id()` loads preference with column_mappings
  - **Must fail** (new methods don't exist yet)

- [x] **T010** [P] Unit tests for SheetsService.build_mapped_row() in `backend/tests/unit/services/test_sheets_service.py`:
  - Test no duplicates (A, B, F) returns sparse row: `['2024-01-15', 'Coffee', '', '', '', '15.50']`
  - Test with duplicates (A, B, A) returns: `['2024-01-15 | 15.50', 'Coffee']`
  - Test non-contiguous (A, C, Z) returns row with empty strings in gaps
  - Test max column index calculation: (A, B, ZZ) creates 702-element array
  - Test concatenation order is consistent (alphabetical by field name)
  - Mock GoogleSheetsRow data, test with ColumnMappingConfiguration
  - **Must fail** (method doesn't exist yet)

### Integration Tests

- [ ] **T011** [P] Integration test: Configuration workflow in `backend/tests/integration/test_column_config_workflow.py`:
  - Test unconfigured state: GET returns 404
  - Test save configuration: POST with valid data returns 200
  - Test retrieve after save: GET returns saved mappings
  - Test update configuration: POST overwrites existing mappings
  - Test invalid save: POST with invalid format returns 400
  - Use in-memory user_preferences (mock file I/O)
  - **Must fail** (endpoints don't exist yet)

- [ ] **T012** [P] Integration test: Receipt processing with mappings in `backend/tests/integration/test_receipt_with_mappings.py`:
  - Test processing blocked without mappings: Returns COLUMN_MAPPINGS_REQUIRED
  - Test data written to correct columns after configuration
  - Test duplicate column concatenation in actual append_row call
  - Test non-contiguous columns leave gaps in row data
  - Test existing data unchanged when mappings updated (simulate 2 receipts with different mappings)
  - Mock gspread API, verify append_row() calls
  - **Must fail** (integration not implemented yet)

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Backend Models & Services

- [ ] **T013** [P] Implement ColumnValidator service in `backend/src/services/column_validator.py`:
  - Create ColumnValidator class (no need for dataclass, pure utility class)
  - Implement `validate(column_ref: str) -> tuple[bool, Optional[str]]`:
    - Regex pattern: `^[A-Z]{1,2}$`
    - Range check: 0-701 (A-ZZ)
    - Return error codes: INVALID_COLUMN_FORMAT, COLUMN_OUT_OF_RANGE
  - Implement `to_index(column_ref: str) -> int`:
    - Single letter: `ord(column) - ord('A')`
    - Double letter: `(ord(first) - ord('A') + 1) * 26 + (ord(second) - ord('A'))`
  - Implement `from_index(index: int) -> str`:
    - Reverse conversion: index < 26 → single letter, else → double letter
  - **Verify**: T007 tests now pass

- [ ] **T014** [P] Implement ColumnMappingConfiguration model in `backend/src/models/column_mapping.py`:
  - Create @dataclass ColumnMappingConfiguration
  - Fields: date_column: str, description_column: str, price_column: str
  - Implement `validate() -> tuple[bool, Optional[str]]`:
    - Check all fields non-empty
    - Validate each with ColumnValidator.validate()
  - Implement `to_dict() -> dict` (serialize to JSON format)
  - Implement `from_dict(data: dict) -> ColumnMappingConfiguration` (classmethod)
  - Implement `get_column_index(column_ref: str) -> int` (delegate to ColumnValidator)
  - Implement `has_duplicates() -> bool` (check if any columns repeat)
  - Implement `get_duplicate_columns() -> dict[str, list[str]]` (group fields by column)
  - **Verify**: T008 tests now pass

- [ ] **T015** Modify UserPreference model in `backend/src/models/user_preference.py`:
  - Add field: `column_mappings: Optional[dict] = None`
  - Implement `has_column_mappings() -> bool` (check if field exists and valid)
  - Implement `get_column_mappings() -> Optional[ColumnMappingConfiguration]`:
    - Return None if not configured
    - Use ColumnMappingConfiguration.from_dict() if exists
  - Implement `set_column_mappings(config: ColumnMappingConfiguration) -> None`:
    - Store config.to_dict() in column_mappings field
    - Update last_updated_at
  - Modify `save()`: Include column_mappings in JSON serialization
  - Modify `load_by_session_id()`: Handle missing column_mappings field (backward compat)
  - **Verify**: T009 tests now pass
  - **Dependencies**: Requires T014 (ColumnMappingConfiguration)

- [ ] **T016** Modify SheetsService in `backend/src/services/sheets_service.py`:
  - Import ColumnMappingConfiguration from models
  - Implement `build_mapped_row(row_data: GoogleSheetsRow, mappings: ColumnMappingConfiguration) -> list`:
    - Calculate max_index from all three column mappings
    - Initialize sparse row: `[''] * (max_index + 1)`
    - Create column_values dict mapping index → list of values
    - Collect values for each field (date, description, price)
    - Handle duplicates: Join with ` | ` delimiter
    - Return sparse row array
  - Modify `append_row()` method:
    - Add parameter check: `if not user_pref.has_column_mappings()` → return error
    - Get mappings: `mappings = user_pref.get_column_mappings()`
    - Build mapped row: `row = self.build_mapped_row(row_data, mappings)`
    - Replace `worksheet.append_row(row_data.to_row())` with `worksheet.append_row(row)`
  - **Verify**: T010 tests now pass, T012 integration test passes
  - **Dependencies**: Requires T014, T015

### Backend API Endpoints

- [ ] **T017** Create column_config.py API module in `backend/src/api/v1/column_config.py`:
  - Import FastAPI, UserPreference, ColumnMappingConfiguration, ColumnValidator
  - Create APIRouter for `/api/v1/column-config` endpoints
  - Implement GET `/api/v1/column-config`:
    - Extract session_id from header
    - Load UserPreference by session_id
    - If not found or no auth: Return 401
    - If no column_mappings: Return 404 with COLUMN_MAPPINGS_NOT_CONFIGURED
    - Return 200 with mappings dict
  - Implement POST `/api/v1/column-config`:
    - Extract session_id from header
    - Parse request body (date_column, description_column, price_column)
    - Create ColumnMappingConfiguration from body
    - Validate config: If invalid, return 400 with error
    - Load UserPreference by session_id
    - Call user_pref.set_column_mappings(config)
    - Save user_pref
    - Return 200 with success message and mappings
  - Implement POST `/api/v1/column-config/validate`:
    - Parse request body: {column: str}
    - Validate with ColumnValidator.validate()
    - If valid: Return 200 with `{valid: true, column, index}`
    - If invalid: Return 200 with `{valid: false, column, error_code, message}`
    - If missing field: Return 400
  - **Verify**: T004, T005, T006 contract tests now pass
  - **Dependencies**: Requires T013, T014, T015

- [ ] **T018** Register column_config router in backend main app:
  - Open `backend/src/api/v1/__init__.py` or main FastAPI app file
  - Import column_config router from `backend/src/api/v1/column_config`
  - Register router: `app.include_router(column_config.router)`
  - **Verify**: Endpoints accessible at /api/v1/column-config
  - **Dependencies**: Requires T017

- [ ] **T019** Modify save.py receipt processing endpoint in `backend/src/api/v1/save.py`:
  - Add check before processing receipt:
    ```python
    if not user_pref.has_column_mappings():
        return {
            "error_code": "COLUMN_MAPPINGS_REQUIRED",
            "message": "Please configure column mappings before processing receipts"
        }, 400
    ```
  - Pass user_pref (with mappings) to SheetsService.append_row()
  - **Verify**: Receipt processing blocked without configuration (T011, T012 tests)
  - **Dependencies**: Requires T015, T016

---

## Phase 3.4: Frontend Implementation

- [ ] **T020** [P] Create column configuration page template in `frontend/src/templates/column_config.html`:
  - Extend base.html template
  - Create form with 3 input fields:
    - Date column (text input, placeholder "A")
    - Description column (text input, placeholder "B")
    - Price column (text input, placeholder "C")
  - Add error message display areas for each field
  - Add success message display area
  - Submit button "Save Configuration"
  - Mobile-responsive layout (use existing CSS grid/flexbox)
  - Include validation hints (A-ZZ format)
  - **Verify**: Template renders without errors

- [ ] **T021** [P] Create column configuration JavaScript in `frontend/src/static/js/column_config.js`:
  - Implement real-time validation:
    - On input blur, call POST /api/v1/column-config/validate
    - Display green checkmark or red X based on response
    - Show error message if invalid
  - Implement form submission:
    - Prevent default form submit
    - Gather all 3 field values
    - POST to /api/v1/column-config with JSON body
    - On success: Show success message, redirect to upload page
    - On error: Display field-specific validation errors
  - Handle session_id from existing session management (check existing upload.js pattern)
  - **Verify**: Real-time validation works, form submission saves config

- [ ] **T022** Add column config link to setup.html in `frontend/src/templates/setup.html`:
  - Add "Configure Columns" button/link after spreadsheet configuration
  - Link to `/column-config` route (needs T023)
  - Show current mapping status if configured
  - **Verify**: Link navigates to column config page

- [ ] **T023** Add column config route to frontend app in `frontend/src/main.py`:
  - Import column_config.html template
  - Add route: `@app.get("/column-config")`
  - Render column_config.html template
  - Pass current mappings if available (call GET /api/v1/column-config)
  - **Verify**: /column-config route accessible, template renders
  - **Dependencies**: Requires T017, T020

- [ ] **T024** Update CSS styling in `frontend/src/static/css/styles.css`:
  - Add styles for `.column-config-form` class
  - Style validation states: `.field-valid`, `.field-invalid`
  - Style error messages: `.field-error`
  - Add mobile breakpoint adjustments for column config form
  - Ensure touch-friendly input fields (min-height: 44px)
  - **Verify**: Form looks good on mobile and desktop

---

## Phase 3.5: Integration & Polish

- [ ] **T025** End-to-end test: Run quickstart.md Step 1-3 manually:
  - Step 1: Verify unconfigured state blocks processing
  - Step 2: Configure mappings (A, B, F)
  - Step 3: Process receipt and verify in Google Sheets
  - **Verify**: Data in columns A, B, F as expected
  - **Dependencies**: All previous tasks complete

- [ ] **T026** [P] End-to-end test: Run quickstart.md Step 4 (modify mappings):
  - Change mappings to (C, D, E)
  - Process new receipt
  - **Verify**: Row 1 unchanged (A, B, F), Row 2 uses (C, D, E)

- [ ] **T027** [P] End-to-end test: Run quickstart.md Step 5 (duplicate columns):
  - Set mappings to (A, B, A)
  - Process receipt
  - **Verify**: Column A contains concatenated value "date | price"

- [ ] **T028** [P] End-to-end test: Run quickstart.md Step 6-9 (validation & edge cases):
  - Test invalid formats (A1, abc, AAA)
  - Test validation API directly
  - Test GET endpoint before/after configuration
  - Test non-contiguous columns (A, C, Z)
  - **Verify**: All edge cases handled correctly

- [ ] **T029** Run unit test coverage check:
  - Execute: `pytest --cov=backend/src --cov-report=term-missing`
  - **Verify**: ≥80% coverage for new modules (column_mapping.py, column_validator.py)
  - **Verify**: UserPreference, SheetsService updated code covered
  - If <80%: Add missing unit tests

- [ ] **T030** Final verification against functional requirements:
  - FR-001 to FR-016: Verify all requirements met
  - Run all tests: `pytest backend/tests/`
  - Check no regressions in existing functionality
  - Verify backward compatibility: Load old user_preferences.json
  - **Verify**: All 16 functional requirements validated
  - **Dependencies**: All tasks complete

---

## Dependencies

**Critical Path**:
```
Setup (T001-T003)
  ↓
Contract Tests [P] (T004-T006) + Unit Tests [P] (T007-T010) + Integration Tests [P] (T011-T012)
  ↓
Core Services [P] (T013-T014)
  ↓
UserPreference (T015) → SheetsService (T016)
  ↓
API Endpoints (T017) → Register Router (T018) + Modify save.py (T019)
  ↓
Frontend [P] (T020-T024)
  ↓
E2E Tests (T025-T028) → Coverage (T029) → Final Verification (T030)
```

**Blocking Relationships**:
- T015 blocks T016 (SheetsService needs UserPreference.get_column_mappings())
- T014 blocks T015 (UserPreference needs ColumnMappingConfiguration)
- T013, T014, T015 block T017 (API needs all models/services)
- T017 blocks T018, T023 (Router registration, frontend routes need API)
- T015, T016 block T019 (save.py needs updated models)
- All implementation blocks E2E tests (T025-T028)

**Parallel Opportunities**:
- T004-T006: All 3 contract tests (different files)
- T007-T010: All 4 unit test files (different files)
- T011-T012: Both integration tests (different files)
- T013-T014: ColumnValidator + ColumnMappingConfiguration (different files)
- T020-T021: HTML template + JavaScript (different files)
- T025-T028: E2E test scenarios (can run concurrently with test spreadsheet)

---

## Parallel Execution Examples

### Launch all contract tests together:
```python
# T004-T006 in parallel
Task(
    description="Contract test GET column-config",
    prompt="Write contract tests for GET /api/v1/column-config in backend/tests/contract/test_column_config_get.py. Test 200 with valid mappings, 404 when not configured, 401 without auth. Validate against contracts/get-column-mappings.json schema. Tests must fail initially.",
    subagent_type="general-purpose"
)
Task(
    description="Contract test POST column-config",
    prompt="Write contract tests for POST /api/v1/column-config in backend/tests/contract/test_column_config_post.py. Test 200 success, 400 validation errors (format/range), 401 auth, duplicate columns allowed, non-contiguous allowed. Validate against contracts/save-column-mappings.json. Must fail initially.",
    subagent_type="general-purpose"
)
Task(
    description="Contract test POST validate",
    prompt="Write contract tests for POST /api/v1/column-config/validate in backend/tests/contract/test_column_validate.py. Test valid columns return index, invalid format/range return errors. Validate against contracts/validate-column-reference.json. Must fail.",
    subagent_type="general-purpose"
)
```

### Launch all unit test files together:
```python
# T007-T010 in parallel
Task(
    description="Unit test ColumnValidator",
    prompt="Write unit tests for ColumnValidator in backend/tests/unit/services/test_column_validator.py. Test validate() with A-ZZ formats, to_index() conversions (A=0, ZZ=701), from_index() reverse. Must fail initially.",
    subagent_type="general-purpose"
)
Task(
    description="Unit test ColumnMappingConfiguration",
    prompt="Write unit tests for ColumnMappingConfiguration in backend/tests/unit/models/test_column_mapping.py. Test validate(), to_dict(), from_dict(), has_duplicates(), get_duplicate_columns(). Must fail.",
    subagent_type="general-purpose"
)
Task(
    description="Unit test UserPreference mappings",
    prompt="Write unit tests for UserPreference column_mappings methods in backend/tests/unit/models/test_user_preference.py. Test has_column_mappings(), get/set, save/load with backward compatibility. Must fail.",
    subagent_type="general-purpose"
)
Task(
    description="Unit test SheetsService build_mapped_row",
    prompt="Write unit tests for SheetsService.build_mapped_row() in backend/tests/unit/services/test_sheets_service.py. Test sparse rows, duplicates concatenation, non-contiguous columns. Mock GoogleSheetsRow. Must fail.",
    subagent_type="general-purpose"
)
```

### Launch core models/services together:
```python
# T013-T014 in parallel (different files, no dependencies between them)
Task(
    description="Implement ColumnValidator",
    prompt="Implement ColumnValidator service in backend/src/services/column_validator.py. Methods: validate(regex + range), to_index(A=0,ZZ=701), from_index(reverse). Verify T007 tests pass.",
    subagent_type="general-purpose"
)
Task(
    description="Implement ColumnMappingConfiguration",
    prompt="Implement ColumnMappingConfiguration model in backend/src/models/column_mapping.py. @dataclass with 3 fields, validate(), to_dict(), from_dict(), has_duplicates(), get_duplicate_columns(). Verify T008 tests pass.",
    subagent_type="general-purpose"
)
```

### Launch frontend tasks together:
```python
# T020-T021 in parallel
Task(
    description="Create column config HTML",
    prompt="Create column_config.html in frontend/src/templates/. Form with 3 inputs (date, description, price), error displays, mobile-responsive. Extends base.html. Verify renders.",
    subagent_type="general-purpose"
)
Task(
    description="Create column config JavaScript",
    prompt="Create column_config.js in frontend/src/static/js/. Real-time validation via /validate endpoint, form submission to /column-config POST. Handle session_id. Verify validation and save work.",
    subagent_type="general-purpose"
)
```

---

## Notes

- **[P] tasks** = different files, no dependencies, can run in parallel
- **TDD critical**: Verify all tests T004-T012 fail before implementing T013-T019
- **Backward compatibility**: T015 must handle user_preferences.json without column_mappings field
- **Coverage target**: 80%+ for new code (T029 verification)
- **Constitution compliance**: RESTful API, responsive UI, OAuth2, unit testing enforced
- Commit after each task for clear git history
- Avoid: Implementing before tests, modifying same file in parallel tasks

---

## Validation Checklist
*GATE: Verified during task generation*

- [x] All 3 contracts have corresponding tests (T004-T006)
- [x] All 4 entities have model/service tasks (T013-T016)
- [x] All tests come before implementation (T004-T012 before T013-T019)
- [x] Parallel tasks truly independent (different files verified)
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task
- [x] TDD enforced (Phase 3.2 must complete before 3.3)
- [x] 80% coverage requirement included (T029)
- [x] E2E validation against functional requirements (T030)

---

**Tasks Status**: ✅ READY - 30 tasks generated, dependency-ordered, ready for execution
