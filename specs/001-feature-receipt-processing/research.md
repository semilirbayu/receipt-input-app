# Phase 0: Research & Technical Decisions

**Feature**: Receipt Processing Web App
**Date**: 2025-10-01
**Status**: Complete

## Research Tasks

### 1. OCR Library Selection for Receipt Processing

**Decision**: pytesseract with Pillow preprocessing

**Rationale**:
- pytesseract wraps Tesseract OCR (maintained by Google), industry-standard open-source OCR engine
- Handles receipt text extraction well with preprocessing (contrast adjustment, grayscale conversion, thresholding)
- Meets <5 second performance requirement for typical receipt images (300-500KB)
- No per-request API costs (unlike cloud OCR services: Google Vision, AWS Textract)
- Suitable for small-scale deployment on Render or local servers

**Alternatives Considered**:
- **Google Cloud Vision API**: Higher accuracy (95%+ vs 85-90%) but adds external dependency, cost ($1.50/1000 images after free tier), and latency (network round-trip). Rejected because feature targets small businesses with cost sensitivity.
- **EasyOCR**: GPU-optimized, multi-language support. Rejected due to higher memory footprint (1.5GB+ model weights) unsuitable for lightweight Render deployment.
- **AWS Textract**: Excellent for structured document analysis but overkill for simple receipt text extraction. Rejected due to cost and AWS dependency.

**Implementation Notes**:
- Preprocess images using Pillow: resize to 1500px width, convert to grayscale, apply adaptive thresholading
- Use Tesseract PSM (Page Segmentation Mode) 6 (uniform text blocks) for receipt layout
- Set confidence threshold at 60% to flag low-quality extractions for manual review

---

### 2. Google Sheets Integration Pattern

**Decision**: gspread library with OAuth2 service account or user credentials

**Rationale**:
- gspread provides Pythonic wrapper for Google Sheets API v4
- Supports OAuth2 authorization code flow for user-specific sheet access (constitutional requirement)
- Handles token refresh automatically via google-auth library integration
- Supports atomic append operations (append_row) to avoid race conditions with concurrent users

**Alternatives Considered**:
- **pygsheets**: Similar feature set but less actively maintained (last update 2023 vs gspread 2024). Rejected for maintenance concerns.
- **Direct Google API client**: More control but requires manual OAuth flow implementation and token management. Rejected to reduce complexity.
- **CSV export + manual upload**: Violates core requirement for direct Google Sheets integration. Rejected.

**Implementation Notes**:
- Store OAuth2 tokens in encrypted session storage (server-side session with SECRET_KEY)
- Request minimum scopes: `https://www.googleapis.com/auth/spreadsheets` (read/write sheets only)
- Implement exponential backoff for rate limit handling (Google Sheets API: 100 requests/100 seconds/user)
- Cache spreadsheet metadata (sheet ID, tab name) in user preferences to avoid repeated lookups

---

### 3. FastAPI + Jinja2 Architecture Pattern

**Decision**: Monolithic FastAPI app serving both REST API and server-rendered templates

**Rationale**:
- Feature requires both API endpoints (upload, save) and user-facing HTML pages (upload form, review page)
- Jinja2 (FastAPI built-in template engine) supports responsive HTML generation without separate frontend framework
- Reduces deployment complexity: single process serving both backend logic and UI (vs separate React/Vue frontend)
- Meets responsive UI requirement via CSS media queries in templates
- Suitable for small-scale app with limited client-side interactivity

**Alternatives Considered**:
- **FastAPI + React SPA**: Better UX for complex interactions but requires separate build pipeline, CORS configuration, and increased deployment surface. Rejected as overkill for simple upload/review flow.
- **Flask + Jinja2**: Similar pattern but FastAPI offers async support (better for I/O-bound OCR/API operations) and automatic OpenAPI docs. Rejected in favor of FastAPI's modern async capabilities.
- **Django**: Full-featured framework with admin panel, ORM. Rejected due to heavier footprint and unnecessary features (no database needed).

**Implementation Notes**:
- Use FastAPI dependency injection for service layer (ocr_service, sheets_service) to enable unit testing with mocks
- Serve static assets (CSS, JS) via FastAPI StaticFiles middleware
- Implement CSRF protection for POST endpoints using `fastapi-csrf-protect` or manual token validation
- Use async route handlers for I/O-bound operations (file uploads, OCR processing, Google Sheets API calls)

---

### 4. Temporary File Storage Strategy

**Decision**: File system storage with 24-hour TTL cleanup via scheduled background task

**Rationale**:
- Meets security requirement SR-004 (24-hour retention) and SR-005 (automated cleanup)
- No database needed for transient data (simplifies architecture)
- File system I/O sufficient for expected scale (10-100 users, ~10-50 receipts/day)
- Background cleanup via APScheduler (Python library) runs daily at off-peak hours

**Alternatives Considered**:
- **S3/Cloud Storage**: More scalable but adds external dependency and cost ($0.023/GB/month). Rejected for local/small-scale deployment.
- **In-memory storage (Redis)**: Fast but loses data on restart and consumes RAM. Rejected because persistence not needed beyond 24 hours.
- **Database BLOB storage**: Requires database setup for transient data. Rejected to maintain simplicity (no DB in feature scope).

**Implementation Notes**:
- Store uploaded files in `shared/uploads/` with UUID-based filenames to prevent collisions
- Record upload timestamp in filename metadata (e.g., `{uuid}_{timestamp}.jpg`)
- APScheduler CronTrigger runs daily at 2 AM server time: scan directory, delete files older than 24 hours
- Implement graceful handling of missing files (if manually deleted or cleanup runs early)

---

### 5. Date Extraction Parsing Strategy

**Decision**: Regex-based pattern matching with dateutil fallback parser

**Rationale**:
- Receipts commonly use formats: MM/DD/YYYY, DD-MM-YYYY, YYYY-MM-DD, "Jan 15, 2025"
- Regex patterns match 80-90% of standardized formats quickly
- dateutil.parser.parse() handles ambiguous/natural language dates ("15th January 2025")
- Allows confidence scoring: regex match = high confidence, dateutil parse = medium confidence

**Alternatives Considered**:
- **LLM-based extraction** (GPT-4, Claude): Higher accuracy but adds API cost ($0.01-0.03/receipt) and latency (1-3s). Rejected due to cost and performance requirements.
- **Hardcoded format list**: Brittle, fails on regional variations. Rejected for lack of flexibility.
- **spaCy NER (Named Entity Recognition)**: Requires model training for date entities. Rejected as overkill for structured date parsing.

**Implementation Notes**:
- Apply regex patterns in priority order: ISO 8601 (YYYY-MM-DD), US format (MM/DD/YYYY), EU format (DD/MM/YYYY), textual ("Jan 15, 2025")
- If regex fails, pass OCR text to dateutil.parser.parse(fuzzy=True) to extract first date-like substring
- Flag extractions with confidence <70% for manual review (display warning icon in UI)
- Handle timezone-naive dates (receipts rarely include timezone) by assuming user's local timezone

---

### 6. Multi-Item Concatenation Format

**Decision**: Semicolon-space delimiter ("; ") for item list concatenation

**Rationale**:
- Meets FR-018 requirement (clarified in spec: concatenate multiple items to single string)
- Semicolon delimiter avoids collision with common receipt text (commas used in amounts, periods in abbreviations)
- Space after semicolon improves readability in Google Sheets cells
- Easy to split in spreadsheet formulas if user needs itemization later (e.g., SPLIT function)

**Alternatives Considered**:
- **Newline delimiter**: Breaks cell rendering in Google Sheets (shows as single line). Rejected.
- **Comma delimiter**: Conflicts with currency formatting ("$1,234.56"). Rejected.
- **Pipe delimiter ("|")**: Less readable. Rejected in favor of more conventional semicolon.

**Implementation Notes**:
- Extract line items from OCR text using pattern: amount + description (e.g., "$12.99 Coffee", "3x Sandwich $8.50")
- Filter out subtotals, tax lines, and total lines using heuristics (lines containing "subtotal", "tax", "total" keywords)
- Concatenate filtered items: `"; ".join(items)`
- Truncate concatenated string to 500 characters max (Google Sheets cell limit ~50K but practical readability limit)

---

### 7. OAuth2 Token Expiration Handling

**Decision**: Detect expiration before Google Sheets API calls, re-prompt for auth, discard unsaved data

**Rationale**:
- Meets FR-016 and FR-017 requirements (clarified in spec: immediate re-auth, discard data)
- Prevents partial save failures (data loss or inconsistent sheet state)
- Simplifies error handling by treating expired tokens as unrecoverable session state
- Forces user to complete auth flow before retrying operation (clear UX)

**Alternatives Considered**:
- **Auto-refresh token**: OAuth2 supports refresh tokens but Google tokens expire after 7 days if app not verified. Rejected because unverified app status likely for small-scale deployment.
- **Temporary save + retry**: Store extracted data in session, auto-retry after re-auth. Rejected to avoid stale data bugs (user might upload different receipt after re-auth).
- **Queue for later**: Save data to retry queue, process after auth restored. Rejected due to added complexity (requires persistence layer).

**Implementation Notes**:
- Check token expiry timestamp before every Google Sheets API call
- If expired or within 5 minutes of expiry, return 401 Unauthorized with error code "AUTH_EXPIRED"
- Frontend detects 401, displays modal: "Session expired. Please reconnect to Google Sheets."
- Clear client-side form data on auth redirect to prevent accidental stale submission
- Log expired token events for monitoring (detect frequent expiration indicating UX issue)

---

### 8. Error Code Format for Google Sheets Failures

**Decision**: "Error GS-{HTTP_CODE}: Unable to save data" format

**Rationale**:
- Meets FR-019 requirement (clarified in spec: structured error codes)
- HTTP status codes from Google Sheets API provide standard error categorization:
  - 403: Insufficient permissions
  - 423: Resource locked
  - 429: Quota/rate limit exceeded
  - 500: Server error
- Generic message ("Unable to save data") avoids exposing internal API details to users
- "GS-" prefix clarifies error source (Google Sheets) vs app errors

**Alternatives Considered**:
- **Custom app error codes**: More control but requires maintaining mapping table. Rejected to leverage standard HTTP semantics.
- **Full API error message**: Exposes Google API internals (confusing for users). Rejected.
- **No error codes**: Makes debugging harder for support. Rejected.

**Implementation Notes**:
- Catch `gspread.exceptions.APIError` and extract HTTP status code
- Map to user-friendly prefix: `f"Error GS-{status_code}: Unable to save data"`
- Log full API error response (including request ID) to server logs for debugging
- Display error code prominently in UI alert box with "Copy error code" button
- Document common error codes in help section: GS-403 (check permissions), GS-429 (try again later)

---

### 9. Responsive UI Breakpoints and Touch Target Sizing

**Decision**: Mobile-first CSS with breakpoints at 768px (tablet) and 1024px (desktop), 48x48px touch targets

**Rationale**:
- Aligns with constitutional principle II (Responsive UI)
- 768px and 1024px are standard breakpoints matching common device sizes (iPhone: 375-414px, iPad: 768-1024px, desktop: >1024px)
- 48x48px touch targets exceed WCAG minimum (44x44px) for better mobile usability
- Mobile-first approach ensures core functionality works on smallest screens, progressively enhanced for larger displays

**Alternatives Considered**:
- **Desktop-first**: Requires more CSS overrides for mobile. Rejected in favor of mobile-first per constitution.
- **Tailwind CSS/Bootstrap**: Pre-built responsive utilities but adds framework dependency. Rejected to keep frontend lightweight (vanilla CSS sufficient for simple layouts).
- **Single breakpoint (768px)**: Less granular control. Rejected to optimize for tablet landscape and desktop separately.

**Implementation Notes**:
- Base styles target mobile (<768px): single-column layout, full-width buttons, stacked forms
- Tablet breakpoint (768px-1023px): two-column layout for upload + preview, side-by-side buttons
- Desktop breakpoint (≥1024px): max-width 1200px centered container, drag-drop area 400x300px
- All interactive elements (buttons, file input, correction fields) styled with min-height 48px and min-width 48px
- Use relative units (rem, %) for scalability across zoom levels and accessibility settings

---

### 10. Testing Strategy and Coverage Targets

**Decision**: pytest with 80% unit test coverage, contract tests for API endpoints, integration tests for user flows

**Rationale**:
- Meets constitutional principle IV (Unit Testing with 80% coverage)
- pytest supports fixtures, parameterization, and async tests (FastAPI compatibility)
- Contract tests validate API request/response schemas (OpenAPI spec adherence)
- Integration tests verify end-to-end flows (upload → OCR → review → save) without mocking external services

**Alternatives Considered**:
- **unittest (stdlib)**: Less expressive fixture system. Rejected in favor of pytest's DX.
- **100% coverage target**: Diminishing returns for boilerplate code (e.g., Pydantic model definitions). Rejected; 80% balances quality and effort.
- **E2E tests only**: Misses unit-level edge cases and slower feedback. Rejected; pyramid approach (many unit, some integration, few E2E) preferred.

**Implementation Notes**:
- Unit tests: Mock pytesseract, gspread clients, file I/O to isolate business logic
- Contract tests: Use FastAPI TestClient to assert response schemas match OpenAPI definitions
- Integration tests: Use test Google Sheets (separate test spreadsheet) and sample receipt images
- Run tests in CI pipeline (GitHub Actions): unit tests on every commit, integration tests on PR merge
- Measure coverage via pytest-cov plugin: `pytest --cov=src --cov-report=term-missing --cov-fail-under=80`

---

## Research Summary

All technical decisions finalized. No NEEDS CLARIFICATION items remain. Key technologies:
- **Backend**: FastAPI + Jinja2 (Python 3.11+)
- **OCR**: pytesseract + Pillow
- **Integration**: gspread + google-auth (OAuth2)
- **Storage**: File system (24-hour TTL, APScheduler cleanup)
- **Testing**: pytest (80% coverage target)
- **Deployment**: uvicorn (local) or Render (production)

Ready to proceed to Phase 1 (Design & Contracts).
