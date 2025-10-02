# Phase 1: Data Model

**Feature**: Receipt Processing Web App
**Date**: 2025-10-01
**Status**: Complete

## Entity Definitions

### Receipt
Represents an uploaded receipt image file.

**Attributes**:
- `id` (UUID, primary identifier, auto-generated)
- `filename` (string, original uploaded filename, max 255 chars)
- `file_path` (string, server file system path, format: `uploads/{uuid}_{timestamp}.{ext}`)
- `file_size` (integer, bytes, max 5242880 = 5MB)
- `file_type` (enum, allowed: "image/jpeg", "image/png")
- `upload_timestamp` (datetime, ISO 8601 UTC, auto-set on upload)
- `deletion_scheduled_at` (datetime, ISO 8601 UTC, computed: upload_timestamp + 24 hours)
- `processing_status` (enum, values: "pending", "processing", "completed", "failed")

**Validation Rules**:
- `file_size` MUST be ≤ 5242880 bytes (5MB limit per FR-002)
- `file_type` MUST be "image/jpeg" or "image/png" (per FR-001)
- `filename` MUST be sanitized to remove path traversal sequences (e.g., "../")
- `id` MUST be unique and immutable

**Lifecycle**:
1. Created on file upload (status: "pending")
2. Status transitions: pending → processing → completed/failed
3. Deleted automatically 24 hours after `upload_timestamp` (per SR-004)

**Relationships**:
- One Receipt has one ExtractedData (1:1, optional until OCR completes)

---

### ExtractedData
Represents OCR-parsed data from a receipt.

**Attributes**:
- `id` (UUID, primary identifier, auto-generated)
- `receipt_id` (UUID, foreign key to Receipt.id)
- `transaction_date` (date, nullable, extracted date from receipt)
- `transaction_date_confidence` (float, range 0.0-1.0, OCR confidence score)
- `items` (string, semicolon-delimited list, max 500 chars, nullable)
- `items_confidence` (float, range 0.0-1.0, OCR confidence score)
- `total_amount` (decimal, precision 2, nullable, currency amount)
- `total_amount_confidence` (float, range 0.0-1.0, OCR confidence score)
- `raw_ocr_text` (text, full unprocessed OCR output, for debugging)
- `extraction_timestamp` (datetime, ISO 8601 UTC, auto-set on OCR completion)

**Validation Rules**:
- `transaction_date` MUST be valid date (parseable by dateutil.parser)
- `total_amount` MUST be positive or zero (negative amounts rejected)
- `items` MUST be non-empty string if present (no whitespace-only values)
- Confidence scores MUST be in range [0.0, 1.0]
- At least one of `transaction_date`, `items`, or `total_amount` MUST be non-null (reject completely empty extraction)

**State Transitions**:
- Created when OCR completes (all confidence fields set)
- Immutable after creation (updates create new ExtractedData record)
- User corrections overwrite fields but preserve original raw_ocr_text

**Relationships**:
- One ExtractedData belongs to one Receipt (1:1)

---

### UserPreference
Represents user's saved configuration for Google Sheets integration.

**Attributes**:
- `id` (UUID, primary identifier, auto-generated)
- `user_session_id` (string, OAuth2 session identifier, indexed)
- `spreadsheet_id` (string, Google Sheets spreadsheet ID from URL)
- `sheet_tab_name` (string, specific sheet tab name, max 100 chars)
- `last_updated_at` (datetime, ISO 8601 UTC, updated on preference change)
- `created_at` (datetime, ISO 8601 UTC, auto-set on first setup)

**Validation Rules**:
- `spreadsheet_id` MUST match Google Sheets ID format (alphanumeric, 44 chars)
- `sheet_tab_name` MUST be non-empty string
- `user_session_id` MUST be unique (one preference set per user session)

**Lifecycle**:
1. Created on first Google Sheets setup (user selects spreadsheet + tab)
2. Updated when user changes target spreadsheet/tab (per FR-012b)
3. Retained across sessions (no automatic deletion)

**Relationships**:
- One UserPreference belongs to one user session (1:1)
- No direct relationship to Receipt/ExtractedData (preferences used at save time)

---

### GoogleSheetsRow
Represents the data structure appended to Google Sheets (not stored in app database).

**Attributes** (column mapping):
- `Transaction Date` (date, ISO format YYYY-MM-DD)
- `Items` (string, semicolon-delimited)
- `Total Amount` (decimal, formatted as currency with 2 decimal places)
- `Uploaded At` (datetime, ISO 8601, timestamp when appended to sheet)

**Validation Rules**:
- All fields MUST be non-null (validated before append per FR-014)
- `Transaction Date` formatted as YYYY-MM-DD for Google Sheets date recognition
- `Total Amount` formatted as number (not string) for spreadsheet calculations

**Operation**:
- Appended via gspread `append_row()` method (atomic operation)
- No updates or deletes (append-only data model)

**Relationships**:
- Conceptually derived from ExtractedData (after user confirmation)
- No persistence in app (exists only in Google Sheets)

---

## Data Flow

### Upload Flow
```
User uploads image
  ↓
Receipt entity created (status: pending)
  ↓
File saved to file_path
  ↓
OCR triggered (status: processing)
  ↓
ExtractedData entity created (status: completed/failed)
  ↓
Data presented to user for review
```

### Correction Flow
```
User views ExtractedData
  ↓
User edits transaction_date, items, or total_amount fields
  ↓
Updated values validated (server-side)
  ↓
New ExtractedData record created (preserves original raw_ocr_text)
  ↓
Updated data shown in UI
```

### Save Flow
```
User confirms corrected data
  ↓
Validate all required fields present (per FR-014)
  ↓
Check OAuth2 token validity (per FR-016)
  ↓
Load UserPreference (spreadsheet_id, sheet_tab_name)
  ↓
Construct GoogleSheetsRow from ExtractedData
  ↓
Append row via gspread API
  ↓
Return success/failure response
  ↓
Delete Receipt file (24-hour TTL enforced)
```

---

## Entity Relationship Diagram

```
┌─────────────┐
│   Receipt   │
│─────────────│
│ id (PK)     │
│ filename    │
│ file_path   │──┐
│ file_size   │  │
│ file_type   │  │
│ timestamps  │  │
│ status      │  │
└─────────────┘  │
                 │ 1:1
                 ↓
         ┌───────────────┐
         │ ExtractedData │
         │───────────────│
         │ id (PK)       │
         │ receipt_id(FK)│
         │ transaction_  │
         │   date        │
         │ items         │
         │ total_amount  │
         │ confidences   │
         │ raw_ocr_text  │
         │ timestamp     │
         └───────────────┘
                 │
                 │ (no FK, used at save)
                 ↓
         ┌─────────────────┐
         │ UserPreference  │
         │─────────────────│
         │ id (PK)         │
         │ user_session_id │
         │ spreadsheet_id  │
         │ sheet_tab_name  │
         │ timestamps      │
         └─────────────────┘
                 │
                 │ (external, not persisted)
                 ↓
         ┌──────────────────┐
         │GoogleSheetsRow   │
         │──────────────────│
         │ Transaction Date │
         │ Items            │
         │ Total Amount     │
         │ Uploaded At      │
         └──────────────────┘
```

---

## Validation Summary

| Entity | Required Fields | Optional Fields | Computed Fields |
|--------|----------------|-----------------|-----------------|
| Receipt | id, file_path, file_size, file_type, upload_timestamp | filename | deletion_scheduled_at, processing_status |
| ExtractedData | id, receipt_id, extraction_timestamp | transaction_date, items, total_amount, confidences | (none) |
| UserPreference | id, user_session_id, spreadsheet_id, sheet_tab_name, created_at | (none) | last_updated_at |
| GoogleSheetsRow | Transaction Date, Items, Total Amount, Uploaded At | (none) | (none) |

---

## Storage Strategy

**Transient Data** (24-hour retention):
- Receipt files: File system at `shared/uploads/`
- ExtractedData records: In-memory session storage (not persisted to DB)

**Persistent Data** (retained across sessions):
- UserPreference: Lightweight persistent store (SQLite or JSON file)
- OAuth2 tokens: Encrypted session storage (server-side sessions with SECRET_KEY)

**External Persistence**:
- GoogleSheetsRow: Google Sheets (user's spreadsheet, append-only)

**Rationale**: No full database needed since receipt data is transient. UserPreference requires minimal persistence (lightweight SQLite sufficient). Keeps architecture simple per constitution.

---

## Data Model Status: ✅ Complete

All entities defined with validation rules, relationships, and lifecycle transitions. Ready for contract generation.
