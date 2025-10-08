# Feature Specification: Improve OCR Data Extraction Quality

**Feature Branch**: `003-bugfix-improve-data`
**Created**: 2025-10-06
**Status**: Draft
**Input**: User description: "bugfix improve data extraction - Currently, the quality of data extraction from uploaded photo files is still very unstable. Sometimes it fails to retrieve date data, incorrectly retrieves price data, and retrieves gibberish descriptions. I want the extracted date and price data to be valid, and the description data to be able to draw conclusions from the uploaded receipt photo, then written and, if necessary, paraphrased so that the description is clear."

## Execution Flow (main)
```
1. Parse user description from Input
   → ✓ Feature description provided: Improve OCR extraction quality
2. Extract key concepts from description
   → ✓ Actors: Users uploading receipts
   → ✓ Actions: Extract date, price, description from receipt images
   → ✓ Data: Transaction date, price amount, item descriptions
   → ✓ Constraints: Data must be valid, descriptions must be clear and paraphrased
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → ✓ Clear user flow identified: Upload → Extract → Validate → Display
5. Generate Functional Requirements
   → ✓ Each requirement testable and measurable
6. Identify Key Entities (if data involved)
   → ✓ ExtractedData entity with improved validation
7. Run Review Checklist
   → WARN: Some clarifications needed for implementation approach
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-10-06
- Q: When a receipt contains multiple total amounts (subtotal, tax, grand total), which value should the system extract as the "transaction price"? → A: Grand total (final amount including all taxes/fees)
- Q: What currency formats should the system support for price extraction? → A: IDR usually represented by Rp
- Q: How far back in history should the system accept receipt dates as valid? → A: No historical limit (accept any past date)
- Q: Should the system support receipts in languages other than English (e.g., Indonesian)? → A: Both English and Indonesian
- Q: What extraction quality metrics should the system track for monitoring and improvement? → A: Success rate + confidence distribution (low/medium/high counts)

**Implementation Context (discussed during clarification):**
- Volume: <1500 receipts/day (suitable for API-based solutions)
- Usage: Internal-first deployment (privacy/offline not blockers)
- Priority: Quality improvement over cost optimization at this stage

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story

As a user uploading receipt images, I need the system to accurately extract transaction dates, prices, and item descriptions so that I can review and save correct financial data to my spreadsheet without extensive manual corrections.

**Current Pain Points:**
- Date extraction often fails completely, leaving fields empty
- Price extraction returns incorrect values (wrong digits, decimal placement, or extra characters)
- Description extraction produces gibberish or unreadable text instead of clear item names
- Manual correction takes significant time due to poor initial extraction quality

**Desired Outcome:**
Users receive high-quality extracted data with:
- Valid, parseable dates in recognizable formats
- Accurate price amounts matching receipt totals
- Clear, readable descriptions that intelligently summarize receipt items

### Acceptance Scenarios

#### Scenario 1: Date Extraction Reliability
1. **Given** a receipt image with a visible transaction date
   **When** user uploads the receipt
   **Then** system extracts a valid date in recognizable format (e.g., "2025-10-06", "Oct 6, 2025")
   **And** date field is populated (not empty)
   **And** confidence indicator shows high confidence for valid dates

#### Scenario 2: Price Extraction Accuracy
1. **Given** a receipt image with clearly visible total amount
   **When** user uploads the receipt
   **Then** system extracts the correct numerical value including decimal places
   **And** price field contains only valid numeric characters (digits, decimal point, currency symbol if applicable)
   **And** extracted amount matches the receipt total within reasonable OCR tolerance

#### Scenario 3: Description Clarity and Intelligence
1. **Given** a receipt image with multiple item lines
   **When** user uploads the receipt
   **Then** system extracts item descriptions in readable text (no gibberish)
   **And** descriptions are intelligently paraphrased to remove OCR artifacts
   **And** descriptions provide clear summary of purchased items
   **And** multiple items are separated appropriately (e.g., semicolon-delimited)

#### Scenario 4: Low-Quality Image Handling
1. **Given** a receipt image with poor lighting or blur
   **When** user uploads the receipt
   **Then** system attempts extraction with best effort
   **And** confidence indicators accurately reflect uncertainty
   **And** invalid/unreliable data is flagged for user review
   **And** system does not populate fields with gibberish (better empty than wrong)

### Edge Cases

- **What happens when date is in non-standard format?** System should recognize multiple common date formats (MM/DD/YYYY, DD-MM-YYYY, written formats like "January 5, 2025")
- **What happens when receipt has multiple totals?** System should extract the grand total (final amount including all taxes and fees), not subtotals or intermediate amounts
- **What happens when receipt language is not English?** System must support both English and Indonesian language receipts with proper text extraction and paraphrasing in the detected language
- **What happens when description contains special characters or symbols?** System should sanitize and normalize text while preserving meaningful information
- **What happens when OCR confidence is very low across all fields?** System should indicate low confidence and potentially suggest re-upload with better image quality

---

## Requirements *(mandatory)*

### Functional Requirements

#### Date Extraction
- **FR-001**: System MUST extract transaction dates from receipt images with at least 80% success rate on clearly visible dates
- **FR-002**: System MUST validate extracted dates against reasonable date ranges (reject future dates beyond tomorrow, accept any past date without historical limit)
- **FR-003**: System MUST recognize multiple common date formats including MM/DD/YYYY, DD-MM-YYYY, YYYY-MM-DD, and written formats (e.g., "Jan 5, 2025")
- **FR-004**: System MUST prefer leaving date field empty rather than populating with invalid or gibberish data

#### Price Extraction
- **FR-005**: System MUST extract price amounts as valid numeric values with correct decimal placement
- **FR-006**: System MUST validate extracted prices are positive numbers within reasonable ranges (e.g., 0.01 to 999,999.99)
- **FR-007**: System MUST distinguish between total amount and other numerical values on receipt (subtotals, tax, item prices), prioritizing extraction of the grand total (final amount including all taxes/fees)
- **FR-008**: System MUST handle Indonesian Rupiah (IDR) currency format with "Rp" symbol recognition and proper digit grouping (e.g., "Rp 1.234.567")
- **FR-009**: System MUST strip non-numeric characters from price extraction (except decimal point and currency symbol)

#### Description Extraction and Enhancement
- **FR-010**: System MUST extract item descriptions from receipt in readable text format, supporting both English and Indonesian languages
- **FR-011**: System MUST detect and filter gibberish or unreadable extraction results
- **FR-012**: System MUST intelligently paraphrase descriptions to improve clarity while preserving meaning, respecting the source language (English or Indonesian)
- **FR-013**: System MUST combine multiple item lines into a structured format (e.g., semicolon-separated list)
- **FR-014**: System MUST sanitize extracted text by removing OCR artifacts, extra whitespace, and special characters that don't contribute to meaning
- **FR-015**: System MUST provide descriptions that are understandable without referring to original receipt image

#### Validation and Quality Control
- **FR-016**: System MUST assign confidence scores to each extracted field (date, price, items)
- **FR-017**: System MUST flag fields with low confidence for user review
- **FR-018**: System MUST provide validation feedback indicating which fields were successfully extracted vs. require manual input
- **FR-019**: System MUST maintain existing confidence indicator UI (✓/⚠/✗) with accurate reflection of extraction quality
- **FR-020**: System MUST log extraction quality metrics including per-field success rate (successful/failed/empty extractions) and confidence distribution (counts of low/medium/high confidence results) for monitoring and improvement analysis

#### User Experience
- **FR-021**: Users MUST see clearly which fields were auto-filled vs. need manual entry
- **FR-022**: Users MUST be able to easily correct any extraction errors
- **FR-023**: System MUST preserve user's manual corrections even if they differ from extracted values
- **FR-024**: System MUST maintain existing review workflow (upload → extract → review → save)

### Performance Requirements
- **FR-025**: Extraction quality improvements MUST NOT increase processing time beyond current <5 second target
- **FR-026**: System MUST handle receipt images up to 5MB without quality degradation

### Key Entities *(include if feature involves data)*

- **ExtractedData**: Represents data extracted from receipt image
  - Transaction date (must be valid date or null)
  - Price amount (must be positive numeric or null)
  - Item descriptions (must be readable text or null)
  - Confidence scores per field (0.0-1.0 scale)
  - Validation status per field (valid/invalid/empty)
  - Extraction method (gemini/tesseract_fallback)
  - Detected language (en/id)
  - Currency (IDR/USD)

- **ValidationResult**: Represents validation outcome for extracted data
  - Field name (date/price/items)
  - Is valid (boolean)
  - Confidence level (low/medium/high)
  - Validation messages (e.g., "Date format invalid", "Price contains non-numeric characters", "Items contain gibberish")

- **ExtractionMetrics**: Tracks daily extraction quality metrics (FR-020)
  - Date extracted (daily aggregation key)
  - Total extractions count
  - Successful extractions (all 3 fields populated)
  - Failed extractions (all 3 fields null)
  - Partial extractions (some fields populated)
  - Confidence distribution (counts: low/medium/high)
  - Extraction method usage (counts: gemini/tesseract_fallback)

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain (all 5 clarifications resolved)
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable (80% success rate, <5 second processing)
- [x] Scope is clearly bounded (focus on date/price/description quality)
- [x] Dependencies and assumptions identified (existing OCR workflow, confidence indicators)

**Outstanding Clarifications:**
All clarifications resolved (5/5 completed in Session 2025-10-06)

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted (date/price/description extraction quality)
- [x] Ambiguities marked (5 clarifications identified)
- [x] User scenarios defined (4 acceptance scenarios + edge cases)
- [x] Requirements generated (26 functional requirements)
- [x] Entities identified (ExtractedData, ValidationResult)
- [ ] Review checklist passed (pending clarifications)

---

## Notes for Planning Phase

This specification focuses on improving the **quality and reliability** of existing OCR data extraction, not adding new features. The planning phase should:

1. Analyze current extraction failure patterns to prioritize improvements
2. Research techniques for improving date/price/description parsing accuracy
3. Design validation rules for each data type
4. Define intelligent paraphrasing approach for descriptions
5. Establish quality metrics and testing approach for measuring improvement

**Success will be measured by:**
- Reduction in empty/null extraction results
- Increase in valid, parseable extracted data
- Decrease in gibberish descriptions
- User-reported improvement in extraction accuracy
- Reduction in time spent on manual corrections
