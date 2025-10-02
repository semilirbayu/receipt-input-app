# Quickstart Guide: Receipt Processing Web App

**Feature**: Receipt Processing Web App
**Branch**: `001-feature-receipt-processing`
**Purpose**: Validate feature implementation through end-to-end user flow

---

## Prerequisites

1. **System Requirements**:
   - Python 3.11+ installed
   - Tesseract OCR installed (`brew install tesseract` on macOS or `apt-get install tesseract-ocr` on Linux)
   - Google Cloud project with Sheets API enabled and OAuth2 credentials configured

2. **Environment Setup**:
   ```bash
   # Clone repository and checkout feature branch
   git checkout 001-feature-receipt-processing

   # Install dependencies
   pip install -r requirements.txt

   # Set environment variables
   export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
   export GOOGLE_CLIENT_SECRET="your-client-secret"
   export SECRET_KEY="your-random-secret-key"
   export REDIRECT_URI="http://localhost:8000/api/v1/auth/callback"
   ```

3. **Test Assets**:
   - Sample receipt images available in `tests/fixtures/receipts/`
   - Test Google Spreadsheet created and accessible

---

## Quickstart Flow (Happy Path)

### Step 1: Start Application
```bash
# Start FastAPI server
uvicorn frontend.src.main:app --reload --port 8000

# Expected output:
# INFO:     Uvicorn running on http://localhost:8000
# INFO:     Application startup complete
```

**Validation**: Open browser to `http://localhost:8000`, homepage loads with "Upload Receipt" button.

---

### Step 2: Authenticate with Google Sheets
1. Click **"Connect to Google Sheets"** button on homepage
2. Redirected to Google OAuth2 consent screen
3. Select Google account and grant permissions for Google Sheets access
4. Redirected back to `/setup` page

**Validation**:
- Console logs: `INFO: OAuth2 callback successful, token acquired`
- Setup page displays: "Select your target spreadsheet"

---

### Step 3: Configure Spreadsheet Preferences
1. Enter **Spreadsheet ID** (from Google Sheets URL: `https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit`)
2. Enter **Sheet Tab Name** (e.g., "Expenses 2025")
3. Click **"Save Preferences"**

**Validation**:
- Success message: "Preferences saved. You can now upload receipts."
- Redirected to `/upload` page

---

### Step 4: Upload Receipt Image
1. On upload page, drag and drop a receipt image (JPG/PNG, <5MB) into the upload area
   **OR** click "Choose File" and select from file system
2. File uploads and OCR processing begins automatically

**Expected behavior**:
- Progress indicator shown (spinner/loading bar)
- Processing completes within 5 seconds
- Page automatically navigates to review page

**Validation**:
- Console logs:
  ```
  INFO: Receipt uploaded: receipt_id=a3bb189e-8bf9-3888-9912-ace4e6543002
  INFO: OCR processing started
  INFO: OCR processing completed in 3.2s
  ```
- Review page displays extracted data:
  - Transaction Date: `2025-09-28`
  - Items: `Coffee; Sandwich; Water`
  - Total Amount: `$24.50`

---

### Step 5: Review and Correct Extracted Data
1. Review auto-filled fields on review page
2. **Correct any errors**:
   - Click into "Transaction Date" field, change to correct date if wrong
   - Edit "Items" field to fix OCR mistakes (e.g., "Coffe" → "Coffee")
   - Update "Total Amount" if incorrect
3. Verify all required fields are non-empty

**Validation**:
- Edited fields update in real-time
- Form validation shows errors if fields left empty
- Confidence indicators (if <70%) display warning icons next to low-confidence fields

---

### Step 6: Save to Google Sheets
1. Click **"Save to Google Sheets"** button
2. System validates all fields (date, items, amount)
3. System checks OAuth2 token validity
4. Data appended to configured Google Sheets

**Expected behavior**:
- Success message: "Receipt saved successfully!"
- Link displayed: "View in Google Sheets" (opens spreadsheet in new tab)
- Receipt image deleted from server storage

**Validation**:
- Console logs:
  ```
  INFO: Token valid, proceeding with save
  INFO: Appending row to spreadsheet 1A2B3C4D5E6F... sheet 'Expenses 2025'
  INFO: Row appended at row number 42
  INFO: Receipt file deleted: uploads/a3bb189e-8bf9-3888-9912-ace4e6543002_1727539200.jpg
  ```
- Open Google Sheets, verify new row appended with:
  - Column A: `2025-09-28`
  - Column B: `Coffee; Sandwich; Water`
  - Column C: `24.50`
  - Column D: Timestamp (e.g., `2025-10-01T10:30:00Z`)

---

## Edge Case Tests

### Test 1: File Size Limit Enforcement (FR-002)
**Steps**:
1. Attempt to upload a 6MB image
2. Expected: Upload rejected with error "File size exceeds 5MB limit"

**Validation**: Error message displayed in red alert box, no file uploaded.

---

### Test 2: Invalid File Format (FR-001)
**Steps**:
1. Attempt to upload a PDF file
2. Expected: Upload rejected with error "Only JPG and PNG formats are supported"

**Validation**: Error message displayed, file input cleared.

---

### Test 3: OCR Failure Handling (FR-013)
**Steps**:
1. Upload a completely blank white image
2. OCR completes but returns no text
3. Review page displays empty fields with message: "OCR could not extract data. Please enter manually."

**Validation**:
- All fields editable
- Form allows manual entry
- Save button remains functional after manual completion

---

### Test 4: OAuth2 Token Expiration (FR-016, FR-017)
**Steps**:
1. Manually expire OAuth2 token (modify token timestamp in session or wait 7 days)
2. Complete upload and review flow
3. Click "Save to Google Sheets"
4. Expected: Error modal appears: "Session expired. Please reconnect to Google Sheets."
5. Click "Reconnect" button → redirects to OAuth2 login

**Validation**:
- Extracted data discarded (review page cleared)
- After re-authentication, user must re-upload receipt
- Console logs: `WARNING: OAuth2 token expired, prompting re-authentication`

---

### Test 5: Google Sheets Permission Error (FR-019)
**Steps**:
1. Change Google Sheets spreadsheet permissions to "View Only" (remove edit access)
2. Complete upload and review flow
3. Click "Save to Google Sheets"
4. Expected: Error displayed: "Error GS-403: Unable to save data"

**Validation**:
- Error code displayed prominently
- "Copy error code" button available
- Console logs: `ERROR: Google Sheets API error 403: Insufficient permissions`

---

### Test 6: Multi-Item Concatenation (FR-018)
**Steps**:
1. Upload receipt with multiple line items:
   ```
   Coffee         $4.50
   Sandwich       $8.00
   Water          $2.00
   Cookie         $3.00
   ```
2. OCR extracts items
3. Review page displays: "Coffee; Sandwich; Water; Cookie"
4. Save to Google Sheets

**Validation**:
- Google Sheets cell contains: `Coffee; Sandwich; Water; Cookie`
- Items separated by semicolon-space ("; ")
- No subtotal/tax/total lines included in concatenation

---

### Test 7: 24-Hour Image Retention (SR-004, SR-005)
**Steps**:
1. Upload receipt and save to Google Sheets
2. Verify file exists in `shared/uploads/` directory immediately after save
3. Manually run cleanup script or wait 24 hours
4. Verify file deleted automatically

**Validation**:
- Console logs after 24 hours: `INFO: Cleanup: Deleted 1 receipt file(s) older than 24 hours`
- File no longer exists in uploads directory

---

### Test 8: Mobile Browser Responsive UI (FR-009, FR-011, FR-015)
**Steps**:
1. Open app on mobile device (iOS Safari or Android Chrome)
2. Upload page displays touch-optimized UI:
   - Large touch target for file selection (48x48px minimum)
   - No drag-and-drop UI (replaced with "Tap to Select File" button)
3. Complete upload, review, and save flow on mobile

**Validation**:
- All buttons and input fields easily tappable
- No horizontal scrolling required
- Forms stack vertically on narrow screens (<768px)
- Text readable without zooming

---

## Performance Validation

### Test 9: OCR Processing Time (PR-001)
**Steps**:
1. Upload a typical receipt image (~500KB)
2. Measure time from upload completion to review page display

**Validation**:
- Processing time ≤ 5 seconds
- Console logs: `INFO: OCR processing completed in 3.2s` (or similar)

---

### Test 10: End-to-End Flow Duration (PR-002)
**Steps**:
1. Time complete flow: upload → review (10s user review) → save
2. Exclude user review time from measurement

**Validation**:
- Upload to OCR result: ≤ 5 seconds
- Save to Google Sheets: ≤ 5 seconds
- Total automated processing: ≤ 10 seconds

---

## Success Criteria

**Feature is considered validated if:**
- ✅ All 6 happy path steps complete without errors
- ✅ All 10 edge case/performance tests pass
- ✅ No console errors (except expected validation errors)
- ✅ Google Sheets contains correctly formatted receipt data
- ✅ Receipt images deleted after 24 hours
- ✅ Mobile browser UI functions correctly

**If any test fails**: Document failure, create bug ticket, fix implementation, and re-run quickstart.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: pytesseract` | Install dependencies: `pip install pytesseract` |
| `TesseractNotFoundError` | Install Tesseract OCR: `brew install tesseract` or `apt-get install tesseract-ocr` |
| OAuth2 redirect fails | Verify `REDIRECT_URI` matches Google Cloud Console OAuth2 settings |
| "Error GS-403" on save | Check Google Sheets permissions, ensure edit access granted |
| OCR returns empty results | Check image quality, ensure receipt text is visible and high-contrast |

---

**Quickstart Status**: Ready for implementation validation once `/tasks` and implementation phases complete.
