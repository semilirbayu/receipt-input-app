# Implementation Plan: Receipt Processing Web App

**Branch**: `001-feature-receipt-processing` | **Date**: 2025-10-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-feature-receipt-processing/spec.md`

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
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 8. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Receipt Processing Web App enables freelancers and small businesses to upload receipt images, extract purchase data via OCR, manually correct extracted fields, and save confirmed data to Google Sheets. Built with Python FastAPI backend, Jinja2 templated frontend, pytesseract OCR processing, and Google Sheets API integration via gspread. The system enforces 5MB file size limits, completes OCR within 5 seconds, and provides responsive UI for mobile and desktop browsers.

## Technical Context
**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Jinja2, pytesseract, Pillow, gspread, google-auth
**Storage**: File system (temporary 24-hour retention), Google Sheets (external persistence)
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux/macOS server (local uvicorn or Render deployment)
**Project Type**: Web (backend + frontend)
**Performance Goals**: OCR processing <5 seconds, total upload-to-save <10 seconds
**Constraints**: <5MB image uploads, mobile/desktop browser compatibility (Chrome, Safari, Firefox)
**Scale/Scope**: Single-user or small team usage (10-100 users), lightweight deployment

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Check (Before Phase 0)
| Principle | Status | Notes |
|-----------|--------|-------|
| **I. RESTful API Design** | ✅ PASS | Backend will use FastAPI with JSON REST endpoints: POST /api/v1/upload, POST /api/v1/save, GET /api/v1/auth/callback |
| **II. Responsive UI** | ✅ PASS | Jinja2 templates will implement mobile-first responsive design with CSS media queries, drag-and-drop for desktop, touch for mobile |
| **III. OAuth2 Authentication** | ✅ PASS | Google Sheets integration uses OAuth2 authorization code flow via google-auth library |
| **IV. Unit Testing** | ✅ PASS | pytest unit tests required for OCR module, data parser, Google Sheets connector, with 80%+ coverage target |

**Initial Result**: All constitutional principles satisfied. No violations to document.

### Post-Design Check (After Phase 1)
| Principle | Status | Verification |
|-----------|--------|--------------|
| **I. RESTful API Design** | ✅ PASS | Contracts define RESTful endpoints with proper HTTP verbs (GET, POST), JSON payloads, semantic resource URIs (/api/v1/upload, /api/v1/save, /api/v1/auth/*), and appropriate status codes (2xx, 4xx, 5xx). API versioned via /v1/ path. |
| **II. Responsive UI** | ✅ PASS | Quickstart validates mobile-first design with touch targets (48x48px), breakpoints (768px, 1024px), and mobile browser testing (iOS Safari, Android Chrome). No horizontal scrolling enforced. |
| **III. OAuth2 Authentication** | ✅ PASS | Auth contract implements OAuth2 authorization code flow (/auth/login, /auth/callback) with token refresh handling. Research confirms google-auth library integration. |
| **IV. Unit Testing** | ✅ PASS | Project structure includes test directories (contract/, integration/, unit/) with specific test files for all services. Research confirms pytest with 80% coverage target and contract tests for API schema validation. |

**Post-Design Result**: All constitutional principles remain satisfied after design phase. No violations detected. Ready to proceed to Phase 2.

## Project Structure

### Documentation (this feature)
```
specs/001-feature-receipt-processing/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── upload.py        # POST /api/v1/upload
│   │   │   ├── save.py          # POST /api/v1/save
│   │   │   └── auth.py          # OAuth2 callback endpoints
│   │   └── middleware/
│   │       └── file_validation.py
│   ├── services/
│   │   ├── ocr_service.py       # pytesseract + Pillow
│   │   ├── parser_service.py    # Extract date, items, total
│   │   ├── sheets_service.py    # gspread integration
│   │   └── cleanup_service.py   # 24-hour image deletion
│   ├── models/
│   │   ├── receipt.py           # Receipt data model
│   │   ├── extracted_data.py    # OCR result model
│   │   └── user_preference.py   # Spreadsheet settings
│   └── storage/
│       └── temp_storage.py      # File system operations
└── tests/
    ├── contract/
    │   ├── test_upload_contract.py
    │   ├── test_save_contract.py
    │   └── test_auth_contract.py
    ├── integration/
    │   ├── test_upload_flow.py
    │   ├── test_correction_flow.py
    │   └── test_save_flow.py
    └── unit/
        ├── test_ocr_service.py
        ├── test_parser_service.py
        ├── test_sheets_service.py
        └── test_cleanup_service.py

frontend/
├── src/
│   ├── templates/
│   │   ├── base.html            # Jinja2 base layout
│   │   ├── upload.html          # Upload + drag-drop UI
│   │   └── review.html          # OCR result review/correction
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css       # Responsive styles
│   │   └── js/
│   │       ├── upload.js        # Drag-drop + file handling
│   │       └── review.js        # Correction form logic
│   └── main.py                  # FastAPI app entry point
└── tests/
    └── e2e/
        └── test_user_flows.py

shared/
└── uploads/                     # Temporary image storage (24-hour TTL)
```

**Structure Decision**: Web application structure selected (backend + frontend) because feature requires both server-side OCR/API processing and browser-based user interface. FastAPI serves both REST API endpoints and Jinja2-rendered HTML templates from a unified backend process.

## Phase 0: Outline & Research

**Status**: ✅ Complete

**Output**: [research.md](./research.md)

All technical decisions documented including:
- OCR library selection (pytesseract + Pillow preprocessing)
- Google Sheets integration pattern (gspread + OAuth2)
- FastAPI + Jinja2 architecture
- Temporary file storage strategy (24-hour TTL with APScheduler)
- Date extraction parsing (regex + dateutil fallback)
- Multi-item concatenation format (semicolon-space delimiter)
- OAuth2 token expiration handling
- Error code format for Google Sheets failures
- Responsive UI breakpoints (768px, 1024px, 48x48px touch targets)
- Testing strategy (pytest, 80% coverage, contract tests)

All NEEDS CLARIFICATION items resolved. Ready for Phase 1.

## Phase 1: Design & Contracts

**Status**: ✅ Complete

**Outputs**:
- [data-model.md](./data-model.md) - Entities: Receipt, ExtractedData, UserPreference, GoogleSheetsRow
- [contracts/upload-api.yaml](./contracts/upload-api.yaml) - POST /api/v1/upload endpoint
- [contracts/save-api.yaml](./contracts/save-api.yaml) - POST /api/v1/save endpoint
- [contracts/auth-api.yaml](./contracts/auth-api.yaml) - OAuth2 flow endpoints
- [quickstart.md](./quickstart.md) - End-to-end validation flow with 10 test scenarios
- [CLAUDE.md](../../CLAUDE.md) - Agent context file (repository root)

**Contract Test Files** (to be created in implementation):
- `backend/tests/contract/test_upload_contract.py` - Validates upload API schema
- `backend/tests/contract/test_save_contract.py` - Validates save API schema
- `backend/tests/contract/test_auth_contract.py` - Validates auth API schema

**Integration Test Scenarios** (from quickstart):
- Happy path: Upload → OCR → Review → Save
- Edge cases: File size limit, invalid format, OCR failure, token expiration, permissions error, multi-item, 24-hour retention, mobile UI
- Performance: OCR <5s, end-to-end <10s

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base template
2. Generate tasks from Phase 1 design artifacts:
   - **From contracts/** (3 API contracts):
     - Each endpoint → contract test task [P]
     - Each endpoint → implementation task
   - **From data-model.md** (4 entities):
     - Each entity → model creation task [P]
     - Validation logic for each entity
   - **From quickstart.md** (10 test scenarios):
     - Happy path → integration test task
     - Each edge case → integration test task
   - **From research.md** (10 technical decisions):
     - Core services: ocr_service, parser_service, sheets_service, cleanup_service [P]
     - Middleware: file_validation [P]
     - Storage: temp_storage [P]
     - Frontend templates: base.html, upload.html, review.html [P]
     - Frontend JS: upload.js, review.js [P]
     - Static CSS: styles.css (responsive breakpoints)
     - FastAPI main app: routing, middleware, startup/shutdown
     - Environment setup: requirements.txt, .env.example, README

**Task Ordering Strategy**:
- **Phase 1: Setup & Infrastructure** (parallel where possible)
  - Project scaffolding (directories, requirements.txt)
  - Environment configuration (.env, OAuth2 setup docs)
  - Contract test files (fail initially, no implementation)
- **Phase 2: Data Models** (parallel tasks marked [P])
  - Create Receipt, ExtractedData, UserPreference models
  - Validation logic per entity
  - Unit tests for models
- **Phase 3: Core Services** (parallel tasks marked [P])
  - ocr_service.py (pytesseract + Pillow)
  - parser_service.py (date, items, total extraction)
  - temp_storage.py (file save/delete operations)
  - Unit tests for each service (mocked dependencies)
- **Phase 4: Integration Services** (depends on Phase 3)
  - sheets_service.py (gspread + OAuth2)
  - cleanup_service.py (APScheduler + temp_storage)
  - Unit tests with mocked Google Sheets API
- **Phase 5: API Endpoints** (depends on Phase 2-4)
  - POST /api/v1/upload (file validation + OCR trigger)
  - POST /api/v1/save (validation + sheets append)
  - GET /api/v1/auth/login (OAuth2 redirect)
  - GET /api/v1/auth/callback (token exchange)
  - POST /api/v1/auth/setup (save preferences)
  - GET /api/v1/auth/status (check auth state)
  - Middleware: file_validation, CSRF protection
  - Contract tests should now pass
- **Phase 6: Frontend** (parallel tasks marked [P])
  - Jinja2 templates (base, upload, review)
  - JavaScript (upload.js with drag-drop, review.js with form validation)
  - CSS (responsive styles with breakpoints)
  - Static file serving (FastAPI StaticFiles)
- **Phase 7: Integration Tests** (depends on all prior phases)
  - Happy path flow test (upload → OCR → review → save)
  - Edge case tests (10 scenarios from quickstart)
  - Performance validation (OCR <5s, total <10s)
- **Phase 8: Deployment & Documentation**
  - README.md with setup instructions
  - Deployment configuration (Render or uvicorn local)
  - OAuth2 setup guide (Google Cloud Console steps)
  - Run quickstart validation

**Parallelization Markers**:
- Tasks marked [P] can run in parallel (independent files/modules)
- Non-[P] tasks have dependencies on prior phase completion

**Estimated Task Count**: 35-40 tasks

**Dependency Graph**:
```
Setup (1-3) → Models (4-9) [P] → Services (10-20) [P] → Endpoints (21-28) → Frontend (29-34) [P] → Integration Tests (35-38) → Deployment (39-40)
```

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan. The /tasks command will generate tasks.md with numbered tasks following this strategy.

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

No violations detected. This section is intentionally empty.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (N/A - no violations)

**Artifacts Generated**:
- [x] plan.md (this file)
- [x] research.md (10 technical decisions)
- [x] data-model.md (4 entities with relationships)
- [x] contracts/upload-api.yaml (OpenAPI 3.0)
- [x] contracts/save-api.yaml (OpenAPI 3.0)
- [x] contracts/auth-api.yaml (OpenAPI 3.0)
- [x] quickstart.md (10 test scenarios)
- [x] CLAUDE.md (agent context file)

---

**Planning Complete**: Ready for `/tasks` command to generate tasks.md

*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*