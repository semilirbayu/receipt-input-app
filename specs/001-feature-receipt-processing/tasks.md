# Tasks: Receipt Processing Web App

**Input**: Design documents from `/specs/001-feature-receipt-processing/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Python 3.11+, FastAPI, Jinja2, pytesseract, Pillow, gspread, google-auth
   → Structure: backend/ (API + templates), frontend/ (static assets), shared/ (uploads)
2. Load design documents:
   → data-model.md: 4 entities (Receipt, ExtractedData, UserPreference, GoogleSheetsRow)
   → contracts/: 3 API contracts (upload-api.yaml, save-api.yaml, auth-api.yaml)
   → research.md: 10 technical decisions
   → quickstart.md: 10 test scenarios
3. Generate tasks by category:
   → Setup: project init, dependencies, environment
   → Tests: 3 contract tests, 10 integration tests
   → Core: 4 models, 6 services, 6 API endpoints, 3 templates, 2 JS modules
   → Integration: middleware, cleanup scheduler, static files
   → Polish: unit tests, documentation, quickstart validation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Total tasks: 43 tasks
6. Dependencies: Setup → Tests → Models → Services → Endpoints → Frontend → Integration → Polish
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `backend/src/` for source code, `backend/tests/` for tests
- **Frontend**: `frontend/src/` for templates and entry point, `frontend/static/` for CSS/JS
- **Shared**: `shared/uploads/` for temporary file storage

---

## Phase 3.1: Setup

- [ ] **T001** Create project directory structure per implementation plan
  - Create `backend/src/api/v1/`, `backend/src/services/`, `backend/src/models/`, `backend/src/storage/`, `backend/src/api/middleware/`
  - Create `backend/tests/contract/`, `backend/tests/integration/`, `backend/tests/unit/`
  - Create `frontend/src/templates/`, `frontend/src/static/css/`, `frontend/src/static/js/`
  - Create `shared/uploads/` (temporary storage)
  - Create `tests/fixtures/receipts/` (sample images)

- [ ] **T002** Initialize Python project with dependencies
  - Create `requirements.txt` with: fastapi, uvicorn, jinja2, pytesseract, Pillow, gspread, google-auth, python-multipart, apscheduler, pytest, pytest-asyncio, pytest-cov
  - Create `pyproject.toml` with Python 3.11+ requirement
  - Create `.gitignore` for `*.pyc`, `__pycache__/`, `shared/uploads/*`, `.env`

- [ ] **T003** [P] Create environment configuration template
  - Create `.env.example` with placeholders:
    - `GOOGLE_CLIENT_ID`
    - `GOOGLE_CLIENT_SECRET`
    - `SECRET_KEY`
    - `REDIRECT_URI`
    - `UPLOAD_DIR=shared/uploads`
    - `MAX_FILE_SIZE_MB=5`
  - Document required OAuth2 setup in comments

- [ ] **T004** [P] Configure pytest and coverage tools
  - Create `pytest.ini` with test discovery patterns
  - Configure coverage report settings (80% threshold)
  - Add coverage exclusions for `__init__.py`, test files

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (API Schema Validation)

- [ ] **T005** [P] Contract test POST /api/v1/upload in `backend/tests/contract/test_upload_contract.py`
  - Load contract from `specs/001-feature-receipt-processing/contracts/upload-api.yaml`
  - Test valid multipart/form-data upload returns 200 with receipt_id, status, extracted_data
  - Test file size >5MB returns 400 with FILE_TOO_LARGE
  - Test invalid format (PDF) returns 400 with INVALID_FORMAT
  - Test missing file returns 400 with MISSING_FILE
  - Validate response schema matches OpenAPI spec

- [ ] **T006** [P] Contract test POST /api/v1/save in `backend/tests/contract/test_save_contract.py`
  - Load contract from `specs/001-feature-receipt-processing/contracts/save-api.yaml`
  - Test valid save payload returns 200 with success, spreadsheet_url, row_number
  - Test missing required fields returns 400 with MISSING_REQUIRED_FIELDS
  - Test invalid date returns 400 with INVALID_DATE
  - Test invalid amount returns 400 with INVALID_AMOUNT
  - Test expired token returns 401 with AUTH_EXPIRED
  - Test insufficient permissions returns 403 with GS-403
  - Validate response schema matches OpenAPI spec

- [ ] **T007** [P] Contract test OAuth2 endpoints in `backend/tests/contract/test_auth_contract.py`
  - Load contract from `specs/001-feature-receipt-processing/contracts/auth-api.yaml`
  - Test GET /api/v1/auth/login returns 302 redirect to Google OAuth2
  - Test GET /api/v1/auth/callback with valid code returns 302 to /setup
  - Test GET /api/v1/auth/callback without code returns 400 with MISSING_AUTH_CODE
  - Test POST /api/v1/auth/setup with valid payload returns 200 with success
  - Test POST /api/v1/auth/setup with invalid spreadsheet_id returns 400
  - Test GET /api/v1/auth/status returns 200 with authenticated, spreadsheet_configured, token_expires_at
  - Validate response schema matches OpenAPI spec

### Integration Tests (User Flows)

- [ ] **T008** [P] Integration test: Happy path upload → OCR → review → save in `backend/tests/integration/test_upload_flow.py`
  - Upload sample receipt image from `tests/fixtures/receipts/sample_receipt.jpg`
  - Verify OCR processing completes within 5 seconds
  - Verify extracted_data contains transaction_date, items, total_amount with confidence scores
  - Verify receipt file saved to `shared/uploads/` with UUID filename
  - Mock pytesseract with predefined OCR text output

- [ ] **T009** [P] Integration test: File size limit enforcement in `backend/tests/integration/test_file_size_limit.py`
  - Create mock 6MB image file
  - Attempt upload via POST /api/v1/upload
  - Verify 400 response with FILE_TOO_LARGE error code
  - Verify no file saved to uploads directory

- [ ] **T010** [P] Integration test: Invalid file format rejection in `backend/tests/integration/test_invalid_format.py`
  - Create mock PDF file
  - Attempt upload via POST /api/v1/upload
  - Verify 400 response with INVALID_FORMAT error code
  - Verify no file saved to uploads directory

- [ ] **T011** [P] Integration test: OCR failure handling in `backend/tests/integration/test_ocr_failure.py`
  - Upload blank white image
  - Verify OCR completes but returns empty extracted_data (all fields null)
  - Verify 200 response with status="completed" but extracted_data is null
  - Verify UI flow allows manual data entry

- [ ] **T012** [P] Integration test: OAuth2 token expiration in `backend/tests/integration/test_token_expiration.py`
  - Mock OAuth2 token with past expiry timestamp
  - Complete upload and review flow
  - Attempt POST /api/v1/save
  - Verify 401 response with AUTH_EXPIRED error code
  - Verify extracted data discarded (session cleared)

- [ ] **T013** [P] Integration test: Google Sheets permission error in `backend/tests/integration/test_sheets_permission_error.py`
  - Mock gspread API to raise 403 Forbidden error
  - Complete upload and review flow
  - Attempt POST /api/v1/save
  - Verify 403 response with "Error GS-403: Unable to save data"
  - Verify error code displayed in response

- [ ] **T014** [P] Integration test: Multi-item concatenation in `backend/tests/integration/test_multi_item_extraction.py`
  - Upload receipt with 4 line items (Coffee, Sandwich, Water, Cookie)
  - Verify extracted items concatenated as "Coffee; Sandwich; Water; Cookie"
  - Verify semicolon-space delimiter ("; ") used
  - Verify subtotal/tax/total lines excluded from item list

- [ ] **T015** [P] Integration test: 24-hour image retention in `backend/tests/integration/test_image_retention.py`
  - Upload receipt and verify file saved to `shared/uploads/`
  - Mock file timestamp to 25 hours ago
  - Trigger cleanup scheduler manually
  - Verify file deleted from uploads directory
  - Verify files <24 hours old remain untouched

- [ ] **T016** [P] Integration test: Correction flow in `backend/tests/integration/test_correction_flow.py`
  - Upload receipt with OCR extraction
  - Submit corrected data via review form (modify date, items, amount)
  - Verify corrected data saved to Google Sheets (not original OCR data)
  - Verify original raw_ocr_text preserved for debugging

- [ ] **T017** [P] Integration test: Save flow end-to-end in `backend/tests/integration/test_save_flow.py`
  - Mock authenticated session with UserPreference (spreadsheet_id, sheet_tab_name)
  - Mock gspread to capture append_row() call
  - Submit corrected data via POST /api/v1/save
  - Verify row appended with: Transaction Date (YYYY-MM-DD), Items (semicolon-delimited), Total Amount (decimal), Uploaded At (ISO 8601)
  - Verify response includes spreadsheet_url and row_number
  - Verify receipt file deleted after successful save

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models

- [ ] **T018** [P] Receipt model in `backend/src/models/receipt.py`
  - Define Receipt class with fields: id (UUID), filename, file_path, file_size, file_type, upload_timestamp, deletion_scheduled_at, processing_status
  - Add validation: file_size ≤ 5MB, file_type in ["image/jpeg", "image/png"], filename sanitized
  - Implement lifecycle methods: create(), mark_processing(), mark_completed(), mark_failed()
  - Add computed field: deletion_scheduled_at = upload_timestamp + 24 hours

- [ ] **T019** [P] ExtractedData model in `backend/src/models/extracted_data.py`
  - Define ExtractedData class with fields: id (UUID), receipt_id (FK), transaction_date, transaction_date_confidence, items, items_confidence, total_amount, total_amount_confidence, raw_ocr_text, extraction_timestamp
  - Add validation: confidence scores in [0.0, 1.0], total_amount ≥ 0, items non-empty if present, at least one field non-null
  - Implement immutability: no updates after creation (corrections create new record)
  - Link to Receipt via receipt_id foreign key

- [ ] **T020** [P] UserPreference model in `backend/src/models/user_preference.py`
  - Define UserPreference class with fields: id (UUID), user_session_id, spreadsheet_id, sheet_tab_name, last_updated_at, created_at
  - Add validation: spreadsheet_id 44 chars alphanumeric, sheet_tab_name non-empty max 100 chars, user_session_id unique
  - Implement persistence: save(), load_by_session_id(), update()
  - Use lightweight storage (SQLite or JSON file)

- [ ] **T021** [P] GoogleSheetsRow structure in `backend/src/models/google_sheets_row.py`
  - Define GoogleSheetsRow dataclass with fields: transaction_date (date), items (str), total_amount (decimal), uploaded_at (datetime)
  - Add validation: all fields non-null, transaction_date formatted as YYYY-MM-DD, total_amount formatted as number
  - Implement to_row() method: return list for gspread append_row()
  - Add from_extracted_data() factory method

### Core Services

- [ ] **T022** [P] OCR service in `backend/src/services/ocr_service.py`
  - Implement process_image() function: accepts file_path, returns raw OCR text
  - Add Pillow preprocessing: resize to 1500px width, grayscale conversion, adaptive thresholding
  - Configure pytesseract: PSM mode 6 (uniform text blocks), confidence threshold 60%
  - Add error handling: raise OCR_FAILED if tesseract process fails
  - Add timing: log processing duration, enforce <5 second target

- [ ] **T023** [P] Parser service in `backend/src/services/parser_service.py`
  - Implement parse_receipt_data() function: accepts raw OCR text, returns ExtractedData fields
  - Add date extraction: regex patterns (YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY, "Jan 15, 2025"), dateutil fallback
  - Add item extraction: detect line items with amounts, filter out subtotal/tax/total lines, concatenate with "; " delimiter, truncate to 500 chars
  - Add amount extraction: find largest numeric value with currency symbol, parse to decimal
  - Return confidence scores: regex match = 0.9, dateutil parse = 0.7, no match = 0.0

- [ ] **T024** [P] Temporary storage service in `backend/src/storage/temp_storage.py`
  - Implement save_file() function: accepts uploaded file, returns file_path with UUID_{timestamp} filename
  - Implement delete_file() function: accepts file_path, deletes from file system
  - Implement list_old_files() function: scans uploads directory, returns files older than 24 hours
  - Add error handling: graceful handling of missing files, permission errors
  - Add validation: ensure files saved to `shared/uploads/` only (prevent path traversal)

- [ ] **T025** Google Sheets service in `backend/src/services/sheets_service.py`
  - Implement append_row() function: accepts GoogleSheetsRow, UserPreference, OAuth2 token, appends to Google Sheets
  - Add gspread client initialization with OAuth2 credentials
  - Add exponential backoff for rate limiting (100 requests/100 seconds/user)
  - Add error handling: catch APIError, extract HTTP status code, format as "Error GS-{code}: Unable to save data"
  - Add token validation: check expiry before API call, raise AUTH_EXPIRED if expired or within 5 minutes
  - Return spreadsheet_url and row_number on success

- [ ] **T026** Cleanup service in `backend/src/services/cleanup_service.py`
  - Implement schedule_cleanup() function: configures APScheduler with CronTrigger (daily at 2 AM)
  - Implement cleanup_task() function: calls temp_storage.list_old_files(), deletes each file, logs count
  - Add error handling: log errors but don't crash scheduler
  - Add startup registration: called from FastAPI lifespan event

### API Endpoints

- [ ] **T027** POST /api/v1/upload endpoint in `backend/src/api/v1/upload.py`
  - Accept multipart/form-data file upload
  - Validate file size ≤ 5MB (return 400 FILE_TOO_LARGE if exceeded)
  - Validate file type JPG/PNG (return 400 INVALID_FORMAT if invalid)
  - Save file via temp_storage.save_file()
  - Create Receipt model (status: pending)
  - Trigger OCR: call ocr_service.process_image() → parser_service.parse_receipt_data()
  - Create ExtractedData model linked to Receipt
  - Return 200 with receipt_id, status, extracted_data, processing_time_ms
  - Add error handling: return 500 OCR_FAILED on processing errors

- [ ] **T028** POST /api/v1/save endpoint in `backend/src/api/v1/save.py`
  - Accept JSON payload: receipt_id, transaction_date, items, total_amount
  - Validate all fields present (return 400 MISSING_REQUIRED_FIELDS)
  - Validate transaction_date is valid date (return 400 INVALID_DATE)
  - Validate total_amount ≥ 0 (return 400 INVALID_AMOUNT)
  - Load UserPreference from session (return 401 NOT_AUTHENTICATED if missing)
  - Check OAuth2 token validity (return 401 AUTH_EXPIRED if expired)
  - Construct GoogleSheetsRow from payload
  - Call sheets_service.append_row()
  - Delete receipt file via temp_storage.delete_file()
  - Return 200 with success, spreadsheet_url, row_number
  - Add error handling: catch gspread APIError, return 403/423/429/500 with GS-{code} format

- [ ] **T029** GET /api/v1/auth/login endpoint in `backend/src/api/v1/auth.py`
  - Generate Google OAuth2 authorization URL using google-auth library
  - Include scopes: https://www.googleapis.com/auth/spreadsheets
  - Include redirect_uri from environment variable
  - Return 302 redirect to Google consent screen
  - Add error handling: return 500 if URL generation fails

- [ ] **T030** GET /api/v1/auth/callback endpoint in `backend/src/api/v1/auth.py`
  - Accept query parameter: code (authorization code)
  - Exchange code for OAuth2 token via google-auth library
  - Store token in server-side session (encrypted with SECRET_KEY)
  - Extract token expiry timestamp
  - Return 302 redirect to /setup page
  - Add error handling: return 400 MISSING_AUTH_CODE if code missing, 401 AUTH_FAILED if exchange fails

- [ ] **T031** POST /api/v1/auth/setup endpoint in `backend/src/api/v1/auth.py`
  - Accept JSON payload: spreadsheet_id, sheet_tab_name
  - Validate spreadsheet_id 44 chars (return 400 INVALID_SPREADSHEET_ID)
  - Validate sheet_tab_name non-empty (return 400 INVALID_SHEET_NAME)
  - Create UserPreference linked to session
  - Save to persistent storage
  - Return 200 with success, message
  - Add error handling: return 401 NOT_AUTHENTICATED if no OAuth2 token in session

- [ ] **T032** GET /api/v1/auth/status endpoint in `backend/src/api/v1/auth.py`
  - Check session for OAuth2 token
  - Check UserPreference existence
  - Return 200 with: authenticated (bool), spreadsheet_configured (bool), token_expires_at (datetime or null)

### Middleware

- [ ] **T033** File validation middleware in `backend/src/api/middleware/file_validation.py`
  - Implement validate_file_upload() middleware function
  - Check Content-Length header ≤ 5MB before reading request body
  - Check Content-Type header for multipart/form-data
  - Sanitize uploaded filename (remove path traversal sequences)
  - Return 400 with appropriate error code if validation fails
  - Attach to POST /api/v1/upload route

---

## Phase 3.4: Frontend

### Templates (Jinja2)

- [ ] **T034** [P] Base template in `frontend/src/templates/base.html`
  - Create HTML boilerplate with <!DOCTYPE html>, <head>, <body>
  - Add viewport meta tag for mobile responsiveness
  - Link to `static/css/styles.css`
  - Define content block for page-specific content
  - Add navigation: "Upload Receipt" link, "Connect to Google Sheets" button (conditional on auth status)
  - Add footer with copyright, help link

- [ ] **T035** [P] Upload page template in `frontend/src/templates/upload.html`
  - Extend base.html
  - Add drag-and-drop upload area (desktop: 400x300px, mobile: full-width button)
  - Add file input with accept="image/jpeg,image/png"
  - Add progress indicator (spinner/loading bar) hidden by default
  - Add error message container for validation errors
  - Link to `static/js/upload.js`
  - Add responsive styles: mobile (<768px) shows "Tap to Select File" button, desktop (≥768px) shows drag-drop area

- [ ] **T036** [P] Review page template in `frontend/src/templates/review.html`
  - Extend base.html
  - Display uploaded receipt image thumbnail (max 300px width)
  - Add editable form fields: transaction_date (date input), items (textarea, max 500 chars), total_amount (number input, step 0.01)
  - Display confidence scores as icons (high: ✓, medium: ⚠, low: ✗)
  - Add "Save to Google Sheets" button (disabled until all fields non-empty)
  - Add "Discard and Upload New" button
  - Link to `static/js/review.js`
  - Add form validation: highlight empty required fields in red

### Static Assets

- [ ] **T037** [P] Responsive CSS in `frontend/src/static/css/styles.css`
  - Implement mobile-first base styles: single-column layout, full-width buttons, stacked forms
  - Add breakpoint 768px (tablet): two-column layout for upload + preview, side-by-side buttons
  - Add breakpoint 1024px (desktop): max-width 1200px centered container, drag-drop area 400x300px
  - Style all interactive elements: min-height 48px, min-width 48px (WCAG touch target size)
  - Add button styles: primary (blue), secondary (gray), danger (red)
  - Add form styles: input borders, focus states, error states (red border + message)
  - Add alert styles: success (green), error (red), warning (yellow)
  - Use relative units (rem, %) for scalability

- [ ] **T038** [P] Upload interaction JS in `frontend/src/static/js/upload.js`
  - Implement drag-and-drop event handlers: dragover, dragleave, drop
  - Implement file input change handler
  - Validate file size ≤ 5MB client-side (show error if exceeded)
  - Validate file type JPG/PNG client-side (show error if invalid)
  - Submit file via FormData to POST /api/v1/upload
  - Show progress indicator during upload/OCR
  - Handle response: redirect to review page on success, show error alert on failure
  - Add touch detection: hide drag-drop UI on mobile (<768px), show file input button only

- [ ] **T039** [P] Review correction JS in `frontend/src/static/js/review.js`
  - Pre-fill form fields with extracted_data from backend
  - Implement real-time form validation: check all fields non-empty, enable/disable Save button
  - Implement "Save to Google Sheets" button click: submit corrected data via POST /api/v1/save
  - Handle 200 response: show success message, display "View in Google Sheets" link with spreadsheet_url
  - Handle 401 response: show modal "Session expired. Please reconnect to Google Sheets." with "Reconnect" button → redirect to /api/v1/auth/login
  - Handle 403/423/429/500 responses: show error alert with error code, add "Copy error code" button
  - Implement "Discard and Upload New" button: redirect to upload page, clear session data

### FastAPI App Entry Point

- [ ] **T040** FastAPI main app in `frontend/src/main.py`
  - Initialize FastAPI app with title "Receipt Processing Web App"
  - Configure Jinja2Templates with directory `frontend/src/templates`
  - Configure StaticFiles at `/static` → `frontend/src/static`
  - Mount API routes from `backend.src.api.v1.*`
  - Add CORS middleware (allow all origins for local development, restrict in production)
  - Add session middleware with SECRET_KEY from environment
  - Register cleanup scheduler on startup via lifespan event
  - Add root route `/` → render upload.html
  - Add `/setup` route → render setup page (spreadsheet configuration form)
  - Add `/review/{receipt_id}` route → render review.html with extracted data

---

## Phase 3.5: Integration

- [ ] **T041** Integrate cleanup scheduler with FastAPI app
  - Import cleanup_service.schedule_cleanup() in main.py
  - Call schedule_cleanup() in lifespan startup event
  - Verify scheduler starts on app startup
  - Add graceful shutdown: stop scheduler on app shutdown

- [ ] **T042** Add logging configuration
  - Configure Python logging: INFO level for app logs, WARNING for library logs
  - Add structured log format: timestamp, level, module, message
  - Log key events: upload start/complete, OCR start/complete, save start/complete, cleanup execution, token expiration, API errors
  - Write logs to stdout (for Render/cloud deployment) and `logs/app.log` (for local development)

---

## Phase 3.6: Polish

- [ ] **T043** [P] Unit test: OCR service in `backend/tests/unit/test_ocr_service.py`
  - Mock pytesseract.image_to_string()
  - Test preprocessing: verify resize, grayscale, thresholding applied
  - Test PSM mode 6 configuration
  - Test confidence threshold 60%
  - Test error handling: OCR_FAILED raised on pytesseract exceptions
  - Test performance: verify processing time logged

- [ ] **T044** [P] Unit test: Parser service in `backend/tests/unit/test_parser_service.py`
  - Test date extraction: regex patterns (YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY), dateutil fallback
  - Test item extraction: multi-item concatenation, semicolon-space delimiter, subtotal/tax exclusion, 500 char truncation
  - Test amount extraction: find largest numeric value, parse currency symbols
  - Test confidence scoring: regex = 0.9, dateutil = 0.7, no match = 0.0
  - Test edge cases: empty OCR text, malformed dates, no amounts found

- [ ] **T045** [P] Unit test: Sheets service in `backend/tests/unit/test_sheets_service.py`
  - Mock gspread client
  - Test append_row() success: verify append_row() called with correct data
  - Test token validation: verify AUTH_EXPIRED raised if token expired
  - Test error handling: verify GS-403, GS-423, GS-429, GS-500 errors formatted correctly
  - Test exponential backoff: verify retry logic on rate limit errors
  - Test return values: spreadsheet_url, row_number

- [ ] **T046** [P] Unit test: Cleanup service in `backend/tests/unit/test_cleanup_service.py`
  - Mock APScheduler
  - Test schedule_cleanup(): verify CronTrigger configured for 2 AM daily
  - Test cleanup_task(): mock temp_storage.list_old_files(), verify delete_file() called for each
  - Test error handling: verify errors logged but don't crash scheduler
  - Test edge case: no old files found (verify no errors)

- [ ] **T047** [P] Unit test: Models validation in `backend/tests/unit/test_models.py`
  - Test Receipt validation: file_size ≤ 5MB, file_type in ["image/jpeg", "image/png"], filename sanitized
  - Test ExtractedData validation: confidence in [0.0, 1.0], total_amount ≥ 0, at least one field non-null
  - Test UserPreference validation: spreadsheet_id 44 chars, sheet_tab_name non-empty
  - Test GoogleSheetsRow validation: all fields non-null, date formatted as YYYY-MM-DD

- [ ] **T048** Performance validation: OCR processing time
  - Upload 10 sample receipts (varying sizes 100KB-5MB)
  - Measure processing time from upload completion to review page display
  - Verify all receipts processed within 5 seconds
  - Log results to `performance_report.txt`

- [ ] **T049** Performance validation: End-to-end flow duration
  - Automate full flow: upload → review (no user delay) → save
  - Measure total automated processing time (exclude user review)
  - Verify upload to OCR result ≤ 5 seconds
  - Verify save to Google Sheets ≤ 5 seconds
  - Verify total ≤ 10 seconds
  - Log results to `performance_report.txt`

- [ ] **T050** Run pytest with coverage report
  - Execute: `pytest --cov=backend/src --cov=frontend/src --cov-report=term-missing --cov-fail-under=80`
  - Verify 80%+ coverage achieved
  - Review uncovered lines, add tests if critical paths missed
  - Generate HTML coverage report: `--cov-report=html`

- [ ] **T051** Create README.md documentation
  - Add project overview, features, tech stack
  - Add prerequisites: Python 3.11+, Tesseract OCR, Google Cloud OAuth2 setup
  - Add setup instructions: clone, install dependencies, configure .env, run uvicorn
  - Add OAuth2 configuration guide: Google Cloud Console steps, enable Sheets API, create credentials
  - Add usage guide: connect to Google Sheets, upload receipt, review/correct, save
  - Add troubleshooting section: common errors (TesseractNotFoundError, OAuth2 redirect fails, GS-403)
  - Add testing instructions: run pytest, run quickstart validation
  - Add deployment guide: Render or uvicorn local

- [ ] **T052** Execute quickstart validation from `specs/001-feature-receipt-processing/quickstart.md`
  - Start FastAPI server: `uvicorn frontend.src.main:app --reload --port 8000`
  - Run all 6 happy path steps manually
  - Run all 10 edge case/performance tests
  - Document results: ✅ pass or ❌ fail for each test
  - If any test fails: create bug ticket, fix implementation, re-run quickstart
  - Update Progress Tracking in plan.md: mark Phase 5 validation complete

- [ ] **T053** Final code review and cleanup
  - Remove commented-out code, debug print statements
  - Verify no hardcoded secrets (check .env usage)
  - Run linter: `ruff check .` (fix any issues)
  - Run formatter: `ruff format .`
  - Verify all imports used (remove unused)
  - Verify no duplication (refactor if found)
  - Verify constitutional principles satisfied: RESTful API, responsive UI, OAuth2, unit tests

---

## Dependencies

**Phase Dependencies**:
- Phase 3.1 (Setup) → Phase 3.2 (Tests)
- Phase 3.2 (Tests) → Phase 3.3 (Core Implementation)
- Phase 3.3 (Core Implementation) → Phase 3.4 (Frontend)
- Phase 3.4 (Frontend) → Phase 3.5 (Integration)
- Phase 3.5 (Integration) → Phase 3.6 (Polish)

**Task Dependencies**:
- T001-T004 (Setup) must complete before T005-T017 (Tests)
- T005-T017 (Tests) must complete and FAIL before T018-T033 (Implementation)
- T018-T021 (Models) must complete before T025 (Sheets service uses models)
- T022-T024 (OCR/Parser/Storage services) must complete before T027 (Upload endpoint uses them)
- T025 (Sheets service) must complete before T028 (Save endpoint uses it)
- T029-T032 (Auth endpoints) must complete before T028 (Save endpoint checks auth)
- T033 (Middleware) must complete before T027 (Upload endpoint uses middleware)
- T034 (Base template) must complete before T035-T036 (other templates extend it)
- T040 (Main app) must complete before T041 (Integration depends on app)
- T001-T042 (All implementation) must complete before T043-T053 (Polish/validation)

**Blocking Tasks** (must complete sequentially):
- T001 → T002-T004 (directory structure before file creation)
- T005-T007 → T008-T017 (contract tests before integration tests)
- T018-T021 → T022-T026 (models before services)
- T022-T026 → T027-T032 (services before endpoints)
- T034 → T035-T036 (base template before child templates)
- T040 → T041 (main app before integration)

---

## Parallel Execution Examples

### Example 1: Contract Tests (T005-T007)
```bash
# All contract tests can run in parallel (different files, no dependencies)
Task: "Contract test POST /api/v1/upload in backend/tests/contract/test_upload_contract.py"
Task: "Contract test POST /api/v1/save in backend/tests/contract/test_save_contract.py"
Task: "Contract test OAuth2 endpoints in backend/tests/contract/test_auth_contract.py"
```

### Example 2: Integration Tests (T008-T017)
```bash
# All integration tests can run in parallel (independent scenarios, different files)
Task: "Integration test: Happy path upload → OCR → review → save in backend/tests/integration/test_upload_flow.py"
Task: "Integration test: File size limit enforcement in backend/tests/integration/test_file_size_limit.py"
Task: "Integration test: Invalid file format rejection in backend/tests/integration/test_invalid_format.py"
Task: "Integration test: OCR failure handling in backend/tests/integration/test_ocr_failure.py"
Task: "Integration test: OAuth2 token expiration in backend/tests/integration/test_token_expiration.py"
Task: "Integration test: Google Sheets permission error in backend/tests/integration/test_sheets_permission_error.py"
Task: "Integration test: Multi-item concatenation in backend/tests/integration/test_multi_item_extraction.py"
Task: "Integration test: 24-hour image retention in backend/tests/integration/test_image_retention.py"
Task: "Integration test: Correction flow in backend/tests/integration/test_correction_flow.py"
Task: "Integration test: Save flow end-to-end in backend/tests/integration/test_save_flow.py"
```

### Example 3: Data Models (T018-T021)
```bash
# All models can be created in parallel (different files, no cross-dependencies)
Task: "Receipt model in backend/src/models/receipt.py"
Task: "ExtractedData model in backend/src/models/extracted_data.py"
Task: "UserPreference model in backend/src/models/user_preference.py"
Task: "GoogleSheetsRow structure in backend/src/models/google_sheets_row.py"
```

### Example 4: Core Services (T022-T024)
```bash
# OCR, Parser, and Storage services can be built in parallel (different files)
Task: "OCR service in backend/src/services/ocr_service.py"
Task: "Parser service in backend/src/services/parser_service.py"
Task: "Temporary storage service in backend/src/storage/temp_storage.py"
```

### Example 5: Frontend Templates (T034-T036)
```bash
# After base template (T034) completes, child templates can run in parallel
Task: "Upload page template in frontend/src/templates/upload.html"
Task: "Review page template in frontend/src/templates/review.html"
```

### Example 6: Frontend Static Assets (T037-T039)
```bash
# CSS and JS files can be created in parallel (different files)
Task: "Responsive CSS in frontend/src/static/css/styles.css"
Task: "Upload interaction JS in frontend/src/static/js/upload.js"
Task: "Review correction JS in frontend/src/static/js/review.js"
```

### Example 7: Unit Tests (T043-T047)
```bash
# All unit tests can run in parallel (different files, mocked dependencies)
Task: "Unit test: OCR service in backend/tests/unit/test_ocr_service.py"
Task: "Unit test: Parser service in backend/tests/unit/test_parser_service.py"
Task: "Unit test: Sheets service in backend/tests/unit/test_sheets_service.py"
Task: "Unit test: Cleanup service in backend/tests/unit/test_cleanup_service.py"
Task: "Unit test: Models validation in backend/tests/unit/test_models.py"
```

---

## Notes

- **[P] tasks** = different files, no dependencies, can run in parallel
- **Verify tests fail** before implementing (TDD requirement)
- **Commit after each task** for atomic progress tracking
- **Avoid**: vague tasks, same file conflicts, skipping tests

---

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - 3 contract files → 3 contract test tasks [P] (T005-T007)
   - 3 contracts × 2 endpoints avg → 6 endpoint implementation tasks (T027-T032)

2. **From Data Model**:
   - 4 entities → 4 model creation tasks [P] (T018-T021)
   - Relationships → service layer tasks (T025 sheets_service uses models)

3. **From User Stories**:
   - 10 quickstart scenarios → 10 integration tests [P] (T008-T017)
   - Quickstart validation → final validation task (T052)

4. **From Research**:
   - 10 technical decisions → setup tasks (T001-T004), service tasks (T022-T026)

5. **Ordering**:
   - Setup (T001-T004) → Tests (T005-T017) → Models (T018-T021) → Services (T022-T026) → Endpoints (T027-T033) → Frontend (T034-T040) → Integration (T041-T042) → Polish (T043-T053)

---

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (T005-T007 cover 3 contracts)
- [x] All entities have model tasks (T018-T021 cover 4 entities)
- [x] All tests come before implementation (Phase 3.2 before Phase 3.3)
- [x] Parallel tasks truly independent (all [P] tasks use different files)
- [x] Each task specifies exact file path (all tasks include file paths)
- [x] No task modifies same file as another [P] task (verified)

---

**Tasks Status**: ✅ Complete - 53 tasks generated, ready for execution

*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
