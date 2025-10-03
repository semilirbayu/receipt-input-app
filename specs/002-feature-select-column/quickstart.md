# Quickstart: Column Mapping Configuration

**Feature**: Column Mapping Configuration
**Purpose**: Validate that column mapping feature works end-to-end
**Estimated Time**: 10 minutes

## Prerequisites

- [ ] Development environment set up
- [ ] Backend server running (`uvicorn frontend.src.main:app`)
- [ ] Google OAuth2 configured
- [ ] Test Google Spreadsheet accessible

## Test Scenario: Happy Path

### Step 1: Initial Setup - Verify Unconfigured State

**Action**: Try to process a receipt without configuring column mappings

**Expected Behavior**:
```
1. Navigate to upload page
2. Upload test receipt image
3. Review extracted data
4. Click "Save to Google Sheets"
5. System blocks operation
6. Error displayed: "Please configure column mappings first"
7. Redirected to column configuration page
```

**Verification**:
- [ ] Receipt processing is blocked
- [ ] Clear error message displayed
- [ ] User redirected to configuration UI

---

### Step 2: Configure Column Mappings

**Action**: Set up column mappings

**Steps**:
```
1. On column configuration page:
   - Date column: Enter "A"
   - Description column: Enter "B"
   - Price column: Enter "F"
2. Click "Save Configuration"
```

**Expected API Call**:
```http
POST /api/v1/column-config
Content-Type: application/json
session_id: <user_session_id>

{
  "date_column": "A",
  "description_column": "B",
  "price_column": "F"
}
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Column mappings saved successfully",
  "mappings": {
    "date_column": "A",
    "description_column": "B",
    "price_column": "F"
  }
}
```

**Verification**:
- [ ] Configuration saved without errors
- [ ] Success message displayed
- [ ] User can proceed to receipt processing

---

### Step 3: Process Receipt with Configured Mappings

**Action**: Upload and save a receipt

**Steps**:
```
1. Navigate to upload page
2. Upload test receipt (receipt_test_001.jpg)
3. Review extracted data:
   - Date: 2024-01-15
   - Description: Coffee; Bagel
   - Price: 15.50
4. Click "Save to Google Sheets"
```

**Expected Behavior**:
```
1. System retrieves column mappings (A, B, F)
2. Builds sparse row:
   ["2024-01-15", "Coffee; Bagel", "", "", "", "15.50"]
    A              B                C   D   E   F
3. Appends row to Google Sheets
4. Success message with spreadsheet link
```

**Verification in Google Sheets**:
- [ ] New row appended
- [ ] Date in column A: "2024-01-15"
- [ ] Description in column B: "Coffee; Bagel"
- [ ] Columns C, D, E are empty
- [ ] Price in column F: "15.50"

---

### Step 4: Modify Column Mappings

**Action**: Change column mappings and verify existing data unchanged

**Steps**:
```
1. Go to column configuration page
2. Update mappings:
   - Date column: "C"
   - Description column: "D"
   - Price column: "E"
3. Save configuration
4. Process new receipt (receipt_test_002.jpg)
   - Date: 2024-01-16
   - Description: Lunch
   - Price: 25.00
```

**Expected API Call**:
```http
POST /api/v1/column-config
Content-Type: application/json
session_id: <user_session_id>

{
  "date_column": "C",
  "description_column": "D",
  "price_column": "E"
}
```

**Expected Behavior**:
```
1. Old mapping (A, B, F) remains in row 1
2. New mapping (C, D, E) applied to row 2:
   ["", "", "2024-01-16", "Lunch", "25.00"]
    A   B   C            D        E
```

**Verification in Google Sheets**:
- [ ] Row 1 unchanged: Date in A, Description in B, Price in F
- [ ] Row 2 uses new mappings: Date in C, Description in D, Price in E
- [ ] Columns adapt to new structure

---

### Step 5: Test Duplicate Column Assignment

**Action**: Assign multiple fields to the same column

**Steps**:
```
1. Go to column configuration page
2. Set mappings:
   - Date column: "A"
   - Description column: "B"
   - Price column: "A"  ← Same as date
3. Save configuration
4. Process receipt (receipt_test_003.jpg)
   - Date: 2024-01-17
   - Description: Dinner
   - Price: 45.00
```

**Expected Behavior**:
```
1. System detects duplicate assignment (A)
2. Concatenates values with " | " delimiter
3. Appends row:
   ["2024-01-17 | 45.00", "Dinner"]
    A                      B
```

**Verification in Google Sheets**:
- [ ] Column A contains: "2024-01-17 | 45.00"
- [ ] Column B contains: "Dinner"
- [ ] No errors or data loss

---

## Test Scenario: Validation Edge Cases

### Test 6: Invalid Column Format

**Action**: Try to save invalid column reference

**Steps**:
```
1. Column configuration page
2. Enter invalid formats:
   - Date column: "A1" (contains number)
   - Description column: "abc" (lowercase)
   - Price column: "AAA" (out of range)
3. Click "Save Configuration"
```

**Expected Behavior**:
```
Each invalid input shows error:
- "A1": "Column must be uppercase letters only (A-ZZ)"
- "abc": "Column must be uppercase letters only (A-ZZ)"
- "AAA": "Column exceeds maximum range. Must be between A and ZZ."
```

**Verification**:
- [ ] Save blocked
- [ ] Field-specific error messages displayed
- [ ] User can correct and retry

---

### Test 7: Real-time Validation

**Action**: Test live validation API

**API Call**:
```http
POST /api/v1/column-config/validate
Content-Type: application/json

{"column": "ZZ"}
```

**Expected Response**:
```json
{
  "valid": true,
  "column": "ZZ",
  "index": 701
}
```

**API Call (Invalid)**:
```http
POST /api/v1/column-config/validate
Content-Type: application/json

{"column": "ZZZ"}
```

**Expected Response**:
```json
{
  "valid": false,
  "column": "ZZZ",
  "error_code": "COLUMN_OUT_OF_RANGE",
  "message": "Column exceeds maximum range. Must be between A and ZZ."
}
```

**Verification**:
- [ ] Valid columns return index
- [ ] Invalid columns return error codes
- [ ] UI can use for real-time feedback

---

### Test 8: Retrieve Existing Mappings

**Action**: Check GET endpoint returns saved configuration

**API Call**:
```http
GET /api/v1/column-config
session_id: <user_session_id>
```

**Expected Response** (if configured):
```json
{
  "date_column": "A",
  "description_column": "B",
  "price_column": "F"
}
```

**Expected Response** (if not configured):
```http
HTTP 404 Not Found

{
  "error_code": "COLUMN_MAPPINGS_NOT_CONFIGURED",
  "message": "Column mappings have not been configured. Please set up your column preferences."
}
```

**Verification**:
- [ ] Configured state returns 200 with mappings
- [ ] Unconfigured state returns 404 with clear message
- [ ] UI can check configuration status

---

## Test Scenario: Non-Contiguous Columns

### Test 9: Sparse Column Layout

**Action**: Use non-sequential columns

**Steps**:
```
1. Configure mappings:
   - Date: "A"
   - Description: "C"
   - Price: "Z"
2. Process receipt
```

**Expected Google Sheets Row**:
```
["2024-01-15", "", "Coffee", "", ..., "", "15.50"]
 A              B   C         D    ...  Y   Z
```

**Verification**:
- [ ] Data written to correct non-contiguous columns
- [ ] Intermediate columns remain empty
- [ ] No errors or data misalignment

---

## Success Criteria

**All checks must pass:**

### Functional Requirements
- [ ] FR-001: Column assignments configurable (including non-contiguous)
- [ ] FR-002: Standard notation (A-ZZ) accepted
- [ ] FR-003: Mappings persist between sessions
- [ ] FR-004: Mappings applied when writing data
- [ ] FR-005: Mappings viewable via GET endpoint
- [ ] FR-006: Mappings modifiable via POST endpoint
- [ ] FR-007: Validation enforces A-ZZ range
- [ ] FR-008: Duplicate columns allowed
- [ ] FR-009: Explicit configuration required
- [ ] FR-011: Processing blocked without configuration
- [ ] FR-012: Clear prompt displayed when unconfigured
- [ ] FR-013: Concatenation works for duplicate columns
- [ ] FR-014: Existing data not migrated
- [ ] FR-015: New mappings apply only to new receipts
- [ ] FR-016: Invalid columns rejected with error

### User Acceptance Scenarios
- [ ] Scenario 1: Configuration saves and persists
- [ ] Scenario 2: Data written to configured columns
- [ ] Scenario 3: Mappings viewable and updatable
- [ ] Scenario 4: Receipt processing blocked without configuration
- [ ] Scenario 5: Existing data unchanged after mapping update

### Edge Cases
- [ ] Duplicate column assignment: Concatenation works
- [ ] Non-contiguous columns: Sparse row built correctly
- [ ] Invalid format: Validation errors displayed
- [ ] Out of range: ZZZ rejected, ZZ accepted
- [ ] Missing configuration: Processing blocked with clear message

---

## Cleanup

After testing:
1. Delete test rows from Google Spreadsheet
2. Reset column mappings if needed
3. Clear test receipts from upload directory

---

## Troubleshooting

**Issue**: Configuration saves but data still goes to wrong columns
- **Check**: Verify user_preferences.json has column_mappings field
- **Fix**: Ensure SheetsService.build_mapped_row() is called

**Issue**: Validation API returns 500 error
- **Check**: ColumnValidator regex pattern
- **Fix**: Ensure pattern is `^[A-Z]{1,2}$`

**Issue**: Concatenation not working
- **Check**: Duplicate detection logic in build_mapped_row()
- **Fix**: Verify column index comparison (not string comparison)

**Issue**: Existing data migrated after mapping change
- **Check**: SheetsService.append_row() should only affect new rows
- **Fix**: Ensure no UPDATE operations triggered on mapping save

---

**Quickstart Status**: ✅ READY - All test scenarios defined, validation criteria clear
