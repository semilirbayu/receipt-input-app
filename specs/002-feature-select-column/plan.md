# Implementation Plan: Column Mapping Configuration

**Branch**: `002-feature-select-column` | **Date**: 2025-10-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-feature-select-column/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
This feature enables users to configure custom column mappings for Google Sheets integration, allowing them to specify which spreadsheet columns receive receipt data fields (date, description, price). The implementation extends the existing UserPreference model to persist column mapping configurations and modifies the SheetsService to write data according to user-specified column assignments. Users must explicitly configure all mappings before processing receipts, with validation ensuring column references stay within the practical A-ZZ range (702 columns).

## Technical Context
**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Jinja2, gspread, Pydantic
**Storage**: JSON file-based persistence (shared/user_preferences.json)
**Testing**: pytest with 80% code coverage requirement
**Target Platform**: Linux server (web application)
**Project Type**: web - frontend (Jinja2 templates) + backend (FastAPI REST API)
**Performance Goals**: <200ms p95 for configuration save/load operations
**Constraints**: Must maintain backward compatibility with existing user_preferences.json structure
**Scale/Scope**: Single-user session storage, <10 configuration operations per session

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. RESTful API Design ✅
**Status**: COMPLIANT
- New endpoints will follow REST conventions with JSON payloads
- HTTP verbs used semantically (GET for retrieval, POST/PUT for configuration updates)
- Proper status codes (200 success, 400 validation errors, 401 auth errors)
- API versioning via `/api/v1/` maintained

### II. Responsive UI ✅
**Status**: COMPLIANT
- Column mapping configuration UI will be added to existing setup.html template
- Mobile-first design approach maintained with existing responsive CSS framework
- Configuration form will adapt to mobile/desktop viewports
- Touch-friendly input fields for column selection

### III. OAuth2 Authentication for Google Sheets ✅
**Status**: COMPLIANT
- Column mapping configuration accessed only after OAuth2 authentication
- Existing OAuth2 flow unchanged
- Column mappings tied to user session ID from OAuth2

### IV. Unit Testing (NON-NEGOTIABLE) ✅
**Status**: COMPLIANT
- Unit tests required for:
  - ColumnMappingConfiguration model (validation, persistence, retrieval)
  - Column validation logic (A-ZZ range checking, duplicate detection)
  - Data concatenation logic for duplicate column assignments
  - Updated SheetsService methods
- Target: 80%+ code coverage for all new modules
- Mock Google Sheets API interactions in unit tests

### Additional Standards ✅
**Error Handling**: Validation errors return consistent JSON format with clear error codes
**Input Validation**: Column references validated against A-ZZ range before persistence
**Security**: No new security concerns; configuration stored in existing secure session storage

## Project Structure

### Documentation (this feature)
```
specs/002-feature-select-column/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   ├── get-column-mappings.json
│   ├── save-column-mappings.json
│   └── validate-column-reference.json
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── models/
│   │   ├── user_preference.py          # MODIFIED: Add column_mappings field
│   │   └── column_mapping.py           # NEW: Column mapping data structure
│   ├── services/
│   │   ├── sheets_service.py           # MODIFIED: Apply column mappings when writing
│   │   └── column_validator.py         # NEW: Validate column references (A-ZZ)
│   └── api/
│       └── v1/
│           ├── column_config.py        # NEW: Column mapping configuration endpoints
│           └── save.py                 # MODIFIED: Check mappings before processing
└── tests/
    ├── unit/
    │   ├── models/
    │   │   ├── test_user_preference.py # MODIFIED: Add column mapping tests
    │   │   └── test_column_mapping.py  # NEW: Column mapping model tests
    │   └── services/
    │       ├── test_sheets_service.py  # MODIFIED: Test column mapping application
    │       └── test_column_validator.py # NEW: Column validation tests
    └── contract/
        └── test_column_config_api.py   # NEW: API contract tests

frontend/
├── src/
│   ├── templates/
│   │   ├── setup.html                  # MODIFIED: Add column mapping configuration UI
│   │   └── column_config.html          # NEW: Dedicated column configuration page
│   └── static/
│       ├── js/
│       │   └── column_config.js        # NEW: Column mapping client-side logic
│       └── css/
│           └── styles.css              # MODIFIED: Add column config styling
```

**Structure Decision**: Web application structure selected based on existing backend/ and frontend/ directories. Backend uses FastAPI with JSON file persistence; frontend uses Jinja2 templates with vanilla JavaScript. Column mapping configuration extends existing UserPreference model and setup workflow.

## Phase 0: Outline & Research

**Research completed - No unknowns remain after clarification session.**

All technical decisions are clear from existing codebase analysis:
1. **Column Notation Parsing**: Standard spreadsheet notation (A, B, ..., Z, AA, AB, ..., ZZ)
2. **Validation Strategy**: Regex pattern `^[A-Z]{1,2}$` with range check (A=1 to ZZ=702)
3. **Data Concatenation**: Join multiple values with ` | ` delimiter when mapping to same column
4. **Storage Format**: Extend user_preferences.json with `column_mappings` object: `{"date": "A", "description": "B", "price": "C"}`
5. **Migration Strategy**: Existing user_preferences.json entries without column_mappings field treated as unconfigured (require explicit setup)

**Output**: research.md documenting these decisions with rationale

## Phase 1: Design & Contracts

**Completed**: All design artifacts generated

### Data Model (`data-model.md`)
- **ColumnMappingConfiguration**: New entity with date_column, description_column, price_column
- **UserPreference**: Extended with optional column_mappings field
- **ColumnValidator**: New service for validation and conversion logic
- **SheetsService**: Modified append_row() and new build_mapped_row() method

### API Contracts (`contracts/*.json`)
1. **GET /api/v1/column-config**: Retrieve column mappings
   - 200: Returns configured mappings
   - 404: Not configured yet
   - 401: Authentication required

2. **POST /api/v1/column-config**: Save column mappings
   - 200: Saved successfully
   - 400: Validation errors (invalid format, out of range)
   - 401: Authentication required

3. **POST /api/v1/column-config/validate**: Validate single column
   - 200: Returns validation result with index if valid
   - 400: Missing column field

### Quickstart Tests (`quickstart.md`)
End-to-end validation scenarios:
- Happy path: Configure → Process → Verify in Google Sheets
- Edge cases: Duplicates, non-contiguous, validation errors
- State transitions: Unconfigured → Configured → Modified
- Backward compatibility: Existing data unchanged

### Agent Context Update
- CLAUDE.md updated with Python 3.11+, FastAPI, gspread, Pydantic
- JSON file persistence approach documented

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

### From Contracts (API Tests First)
1. **Contract Test: GET /api/v1/column-config**
   - Test 404 when not configured
   - Test 200 with valid mappings
   - Test 401 without authentication
   - [P] Can run in parallel

2. **Contract Test: POST /api/v1/column-config**
   - Test 200 on successful save
   - Test 400 validation errors (format, range)
   - Test 401 without authentication
   - [P] Can run in parallel

3. **Contract Test: POST /api/v1/column-config/validate**
   - Test valid columns return index
   - Test invalid format returns error
   - Test out of range returns error
   - [P] Can run in parallel

### From Data Model (Unit Tests + Implementation)
4. **Unit Test: ColumnValidator**
   - Test validate() with valid/invalid formats
   - Test to_index() conversion (A=0, ZZ=701)
   - Test from_index() reverse conversion
   - [P] Can run in parallel

5. **Implement: ColumnValidator Service**
   - Regex validation pattern
   - Index conversion algorithms
   - Error code generation

6. **Unit Test: ColumnMappingConfiguration**
   - Test validation with all fields
   - Test to_dict() / from_dict()
   - Test has_duplicates() detection
   - Test get_duplicate_columns() grouping
   - [P] Can run in parallel with #4

7. **Implement: ColumnMappingConfiguration Model**
   - Dataclass with three string fields
   - Validation method using ColumnValidator
   - Serialization methods

8. **Unit Test: UserPreference (Extended)**
   - Test has_column_mappings() method
   - Test get_column_mappings() returns config
   - Test set_column_mappings() and save
   - Test backward compatibility (load without field)

9. **Modify: UserPreference Model**
   - Add optional column_mappings dict field
   - Add three new methods
   - Update save() to serialize mappings
   - Update load_by_session_id() to handle missing field

10. **Unit Test: SheetsService.build_mapped_row()**
    - Test no duplicates: sparse row with correct indices
    - Test with duplicates: concatenation with " | "
    - Test non-contiguous: empty strings in gaps
    - Test max column index calculation

11. **Modify: SheetsService**
    - Implement build_mapped_row() method
    - Modify append_row() to check mappings
    - Return COLUMN_MAPPINGS_REQUIRED error if missing
    - Apply mappings via build_mapped_row()

### From User Stories (Integration Tests)
12. **Integration Test: Configuration Workflow**
    - Test unconfigured state blocks processing
    - Test save configuration succeeds
    - Test retrieve configuration returns saved values
    - Test update configuration overwrites

13. **Integration Test: Receipt Processing with Mappings**
    - Test data written to correct columns
    - Test duplicate column concatenation
    - Test non-contiguous columns leave gaps
    - Test existing data unchanged after mapping update

### API Implementation
14. **Implement: GET /api/v1/column-config Endpoint**
    - Load UserPreference by session ID
    - Check has_column_mappings()
    - Return 404 or 200 with mappings

15. **Implement: POST /api/v1/column-config Endpoint**
    - Parse request body
    - Validate with ColumnMappingConfiguration
    - Save to UserPreference
    - Return success or validation errors

16. **Implement: POST /api/v1/column-config/validate Endpoint**
    - Parse column reference from body
    - Validate with ColumnValidator
    - Return validation result with index

### Frontend Implementation
17. **Create: column_config.html Template**
    - Form with three input fields (date, description, price)
    - Client-side validation UI
    - Error message display areas
    - Mobile-responsive layout

18. **Create: column_config.js**
    - Real-time validation via /validate endpoint
    - Form submission to /column-config
    - Error handling and display
    - Success redirect to upload page

19. **Modify: setup.html Template**
    - Add "Configure Columns" button/link
    - Link to column_config.html page

20. **Modify: save.py (Receipt Processing Endpoint)**
    - Check user has_column_mappings() before processing
    - Return COLUMN_MAPPINGS_REQUIRED error if missing
    - Pass mappings to SheetsService

### CSS Styling
21. **Modify: styles.css**
    - Column configuration form styling
    - Validation error state styling
    - Mobile breakpoint adjustments

### Integration & E2E Tests
22. **Integration Test: Full User Journey**
    - Setup → Configure Columns → Upload → Process → Verify
    - Tests quickstart.md scenario 1-5
    - Validates all functional requirements

**Ordering Strategy**:
- Tests before implementation (TDD)
- Contract tests [P] first (can run in parallel)
- Unit tests [P] for models/services (independent)
- Implementation tasks after corresponding tests
- Integration tests after all units implemented
- Frontend last (depends on backend APIs)

**Estimated Output**: ~22 numbered, dependency-ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No constitutional violations identified*

All constitutional principles complied with:
- RESTful API design followed
- Responsive UI maintained
- OAuth2 authentication integrated
- Unit testing with 80% coverage requirement
- Error handling consistent
- Input validation enforced

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved (5 clarifications documented)
- [x] Complexity deviations documented (None - full compliance)

**Artifacts Generated**:
- [x] plan.md (this file)
- [x] research.md (Phase 0)
- [x] data-model.md (Phase 1)
- [x] contracts/get-column-mappings.json (Phase 1)
- [x] contracts/save-column-mappings.json (Phase 1)
- [x] contracts/validate-column-reference.json (Phase 1)
- [x] quickstart.md (Phase 1)
- [x] CLAUDE.md updated (Phase 1)
- [x] tasks.md (Phase 3) - 30 implementation tasks

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
