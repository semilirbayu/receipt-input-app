# Phase 0: Research & Technical Decisions

**Feature**: Column Mapping Configuration
**Date**: 2025-10-03
**Status**: Complete

## Research Summary

This document consolidates all technical research and decisions for implementing configurable column mappings in the Google Sheets integration.

---

## Decision 1: Column Notation Parsing

**Decision**: Use standard spreadsheet column notation (A, B, C, ..., Z, AA, AB, ..., ZZ)

**Rationale**:
- Users are already familiar with this notation from Excel/Google Sheets
- Unambiguous representation (no confusion between index-based vs. letter-based)
- Matches the visual column headers in Google Sheets UI
- Simple to validate with regex pattern

**Implementation Approach**:
- Accept column references as uppercase letters (A-ZZ)
- Convert to zero-based index for gspread library operations
- Conversion formula:
  - Single letter: `ord(letter) - ord('A')` → A=0, B=1, ..., Z=25
  - Double letter: `(ord(first) - ord('A') + 1) * 26 + (ord(second) - ord('A'))` → AA=26, AB=27, ..., ZZ=701

**Alternatives Considered**:
- Numeric indices (1, 2, 3...): Rejected due to ambiguity (0-based vs 1-based) and less intuitive
- R1C1 notation: Rejected as overly complex for simple column selection

---

## Decision 2: Column Validation Strategy

**Decision**: Validate with regex `^[A-Z]{1,2}$` + range check (A=1 to ZZ=702)

**Rationale**:
- Regex ensures format correctness (only uppercase letters, 1-2 characters)
- Range check enforces practical usability limit (clarification answer: A-ZZ)
- Fails fast on invalid input before attempting Google Sheets operations
- Clear error messages possible for different failure modes

**Validation Rules**:
1. Format validation: Must match `^[A-Z]{1,2}$`
2. Range validation: Converted index must be 0-701 (A-ZZ)
3. Non-empty: Column reference required for each data field

**Error Codes**:
- `INVALID_COLUMN_FORMAT`: Doesn't match regex pattern
- `COLUMN_OUT_OF_RANGE`: Valid format but beyond ZZ
- `MISSING_COLUMN_MAPPING`: Required mapping not provided

**Alternatives Considered**:
- Validate against actual spreadsheet column count: Rejected due to extra API call overhead
- Allow unlimited columns (A-ZZZ): Rejected per clarification decision for usability

---

## Decision 3: Data Concatenation for Duplicate Columns

**Decision**: Join multiple values with ` | ` (space-pipe-space) delimiter

**Rationale**:
- Visually clear separator that doesn't conflict with receipt data
- Maintains readability in spreadsheet cells
- Preserves distinct field values without data loss
- Easy to parse if user needs to split later

**Concatenation Behavior**:
- Order: date | description | price (alphabetical by field name for consistency)
- Example: If date="2024-01-15", price="25.50" both map to Column A
  - Cell value: "2024-01-15 | 25.50"

**Edge Cases**:
- Empty field values: Skip in concatenation (don't add extra delimiters)
- Single field to column: No delimiter, just the value
- Three fields to one column: "value1 | value2 | value3"

**Alternatives Considered**:
- Comma separator: Rejected due to conflict with price formatting
- Newline separator: Rejected as less readable in single cell
- Overwrite behavior (last write wins): Rejected per clarification (concatenation preferred)

---

## Decision 4: Storage Format

**Decision**: Extend user_preferences.json with `column_mappings` object

**Format**:
```json
{
  "user_session_123": {
    "id": "uuid-here",
    "spreadsheet_id": "1ABC...",
    "sheet_tab_name": "Receipts",
    "column_mappings": {
      "date": "A",
      "description": "B",
      "price": "C"
    },
    "created_at": "2024-01-01T00:00:00",
    "last_updated_at": "2024-01-15T10:30:00"
  }
}
```

**Rationale**:
- Minimal change to existing UserPreference model (add one optional field)
- Maintains backward compatibility (existing preferences without column_mappings still load)
- Simple JSON serialization/deserialization (no schema migration needed)
- Clear field naming matches domain language

**Field Mappings**:
- `date`: Maps to GoogleSheetsRow.transaction_date
- `description`: Maps to GoogleSheetsRow.items
- `price`: Maps to GoogleSheetsRow.total_amount

**Alternatives Considered**:
- Separate column_mappings.json file: Rejected to avoid dual-file synchronization complexity
- Database storage: Rejected as over-engineering for single-user session scope
- Array format `[{field: "date", column: "A"}]`: Rejected as more verbose than object

---

## Decision 5: Migration Strategy

**Decision**: Treat missing column_mappings field as unconfigured (require explicit setup)

**Rationale**:
- Aligns with clarification decision (mandatory explicit configuration)
- Prevents silent failures or unexpected behavior with legacy data
- Clear user feedback when configuration needed
- No automatic data migration reduces implementation risk

**Migration Behavior**:
1. Load existing user_preferences.json unchanged
2. When UserPreference loaded without `column_mappings` field:
   - `has_column_mappings()` method returns `False`
   - Receipt processing blocked with error: "COLUMN_MAPPINGS_REQUIRED"
   - UI redirects to column configuration screen
3. After user configures and saves:
   - `column_mappings` field added to their preference entry
   - Normal processing resumes

**No Data Loss**:
- Existing spreadsheet data remains unchanged
- Existing user_preferences entries (spreadsheet_id, sheet_tab_name) preserved
- Only adds new field, never removes or modifies existing fields

**Alternatives Considered**:
- Auto-migrate with default mappings (A, B, C): Rejected per clarification (explicit required)
- One-time migration script: Rejected as unnecessary (lazy migration on first use simpler)

---

## Best Practices Applied

### Python Dataclasses
- Use `@dataclass` for ColumnMapping model (consistent with existing codebase)
- Optional fields with `field(default=None)` for backward compatibility
- Type hints for all fields

### Google Sheets API (gspread)
- Column indices in gspread are 1-based (A=1, B=2, etc.) for `update_cell()`
- Use `append_row()` with pre-ordered list (current approach) + column mapping logic
- Alternative: Use `update_cell()` to write individual cells (more API calls but explicit positioning)
- **Chosen**: Sparse row approach - build row array with None for empty columns, write mapped columns only

### FastAPI Conventions
- Request/Response Pydantic models for validation
- Consistent error response format: `{"error_code": "...", "message": "..."}`
- Use dependency injection for session validation

### Testing Strategy
- Unit tests: Mock gspread client, test column conversion logic in isolation
- Contract tests: Validate API request/response schemas
- Integration tests: Test full flow with in-memory user_preferences

---

## Dependencies Analysis

**Existing Dependencies** (no new additions required):
- `gspread`: Google Sheets API client
- `FastAPI`: REST API framework
- `Pydantic`: Data validation
- `pytest`: Testing framework

**Version Compatibility**:
- Python 3.11+ (existing requirement)
- gspread 5.x (supports sparse row updates)
- FastAPI 0.100+ (existing)

---

## Performance Considerations

**Configuration Operations**:
- Load mappings: O(1) - single JSON read
- Validate mappings: O(3) - three field validations (date, description, price)
- Save mappings: O(1) - single JSON write
- **Target**: <200ms p95 (easily achievable with file-based storage)

**Data Write Operations**:
- Column index conversion: O(1) per field
- Duplicate detection: O(3) - max 3 fields to same column
- Concatenation: O(k) where k=fields per column (max 3)
- Sparse row building: O(702) worst case (ZZ columns), typical O(3)
- **Target**: <500ms p95 including Google Sheets API call

**No Performance Impact**:
- Column mapping logic adds <5ms overhead to existing append_row operation
- JSON file size increase: ~50 bytes per user (negligible)

---

## Security Considerations

**No New Security Risks**:
- Column mappings stored in same user_preferences.json (existing file permissions apply)
- Input validation prevents injection attacks (regex + range check)
- No sensitive data in column references (just letter combinations)
- OAuth2 session ID validation unchanged

**Validation Prevents**:
- Directory traversal: Column references can't contain `/` or `..`
- Code injection: Only [A-Z] characters accepted
- DoS via large inputs: Max 2 characters per column reference

---

## Open Questions Resolved

All questions resolved through clarification session (2025-10-03):
1. ✅ Initial setup behavior: Mandatory explicit configuration
2. ✅ Duplicate column handling: Allow with concatenation
3. ✅ Non-contiguous columns: Fully supported (e.g., A, C, F)
4. ✅ Data migration on mapping change: No migration, only new receipts affected
5. ✅ Column validation limit: A-ZZ (702 columns)

---

**Research Status**: ✅ COMPLETE - All technical decisions finalized, ready for Phase 1 design
