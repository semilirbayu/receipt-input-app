# Phase 1: Data Model

**Feature**: Column Mapping Configuration
**Date**: 2025-10-03
**Status**: Complete

## Entity Relationship Overview

```
┌─────────────────────────────┐
│     UserPreference          │
├─────────────────────────────┤
│ - id: UUID                  │
│ - user_session_id: str      │
│ - spreadsheet_id: str       │
│ - sheet_tab_name: str       │
│ - column_mappings: dict     │◄──┐
│ - created_at: datetime      │   │ 1:1
│ - last_updated_at: datetime │   │
└─────────────────────────────┘   │
                                   │
                                   │
                  ┌────────────────┴──────────────────┐
                  │   ColumnMappingConfiguration      │
                  ├───────────────────────────────────┤
                  │ - date_column: str                │
                  │ - description_column: str         │
                  │ - price_column: str               │
                  ├───────────────────────────────────┤
                  │ + validate() → (bool, str)        │
                  │ + to_dict() → dict                │
                  │ + from_dict(dict) → Config        │
                  │ + get_column_index(col) → int     │
                  │ + has_duplicates() → bool         │
                  │ + get_duplicate_columns() → dict  │
                  └───────────────────────────────────┘
                           │
                           │ uses
                           ▼
                  ┌───────────────────────┐
                  │  ColumnValidator      │
                  ├───────────────────────┤
                  │ + validate(str) →     │
                  │   (bool, str)         │
                  │ + to_index(str) → int │
                  │ + from_index(int)     │
                  │   → str               │
                  └───────────────────────┘
```

---

## Entity: ColumnMappingConfiguration

**Purpose**: Represents the user's column mapping preferences for receipt data fields

**Attributes**:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| date_column | str | Yes | A-ZZ format | Column for transaction date |
| description_column | str | Yes | A-ZZ format | Column for items description |
| price_column | str | Yes | A-ZZ format | Column for total amount |

**Business Rules**:
1. All three fields must be configured (no partial configuration allowed)
2. Column references must be uppercase letters only
3. Column references must be within A-ZZ range (1-702)
4. Duplicate column assignments are allowed (triggers concatenation behavior)
5. Non-contiguous column assignments are allowed (e.g., A, C, F)

**State Transitions**:
```
┌──────────────┐
│ Unconfigured │ (UserPreference without column_mappings)
└──────┬───────┘
       │ User configures all 3 fields
       ▼
┌──────────────┐
│  Configured  │ (column_mappings present and validated)
└──────┬───────┘
       │ User updates any field
       ▼
┌──────────────┐
│   Modified   │ (existing mappings replaced, no migration)
└──────────────┘
```

**Methods**:

### `validate() -> tuple[bool, Optional[str]]`
Validates all column references.

**Returns**: `(True, None)` if valid, `(False, error_message)` if invalid

**Validation Steps**:
1. Check all three fields are non-empty
2. Validate each field with ColumnValidator
3. Return first validation error or success

### `to_dict() -> dict`
Converts to dictionary format for JSON serialization.

**Returns**:
```python
{
    "date": "A",
    "description": "B",
    "price": "C"
}
```

### `from_dict(data: dict) -> ColumnMappingConfiguration`
Factory method to create instance from dictionary.

**Parameters**: `data` - dict with keys: date, description, price

**Returns**: New ColumnMappingConfiguration instance

### `get_column_index(column_ref: str) -> int`
Converts column reference to zero-based index.

**Parameters**: `column_ref` - Column reference like "A" or "AA"

**Returns**: Zero-based index (A=0, B=1, ..., ZZ=701)

### `has_duplicates() -> bool`
Checks if any columns are assigned to multiple fields.

**Returns**: True if duplicates exist

### `get_duplicate_columns() -> dict[str, list[str]]`
Returns mapping of duplicate columns to field names.

**Returns**:
```python
{
    "A": ["date", "price"],  # Both fields map to column A
    "B": ["description", "price"]
}
```

---

## Entity: UserPreference (Modified)

**Changes to Existing Model**:

**New Field**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| column_mappings | Optional[dict] | No | None | Column mapping configuration |

**New Methods**:

### `has_column_mappings() -> bool`
Checks if user has configured column mappings.

**Returns**: True if column_mappings field exists and is valid

### `get_column_mappings() -> Optional[ColumnMappingConfiguration]`
Retrieves column mapping configuration.

**Returns**: ColumnMappingConfiguration instance or None if not configured

### `set_column_mappings(config: ColumnMappingConfiguration) -> None`
Saves column mapping configuration.

**Parameters**: `config` - Valid ColumnMappingConfiguration instance

**Side Effects**: Updates last_updated_at timestamp

**Storage Format Update**:
```json
{
  "user_session_id_here": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    "sheet_tab_name": "Receipts",
    "column_mappings": {
      "date": "A",
      "description": "B",
      "price": "F"
    },
    "created_at": "2025-01-01T10:00:00",
    "last_updated_at": "2025-01-15T14:30:00"
  }
}
```

---

## Service: ColumnValidator

**Purpose**: Validates column references and provides conversion utilities

**Methods**:

### `validate(column_ref: str) -> tuple[bool, Optional[str]]`
Validates a single column reference.

**Validation Rules**:
1. Must match regex `^[A-Z]{1,2}$`
2. Must convert to index 0-701 (A-ZZ range)

**Returns**: `(True, None)` or `(False, error_code)`

**Error Codes**:
- `INVALID_COLUMN_FORMAT`: Invalid format
- `COLUMN_OUT_OF_RANGE`: Beyond ZZ

### `to_index(column_ref: str) -> int`
Converts column reference to zero-based index.

**Algorithm**:
```python
if len(column_ref) == 1:
    return ord(column_ref) - ord('A')  # A=0, B=1, ..., Z=25
else:  # len == 2
    first = ord(column_ref[0]) - ord('A') + 1  # A=1, B=2, ..., Z=26
    second = ord(column_ref[1]) - ord('A')      # A=0, B=1, ..., Z=25
    return first * 26 + second                   # AA=26, AB=27, ..., ZZ=701
```

**Examples**:
- `to_index("A")` → 0
- `to_index("Z")` → 25
- `to_index("AA")` → 26
- `to_index("ZZ")` → 701

### `from_index(index: int) -> str`
Converts zero-based index to column reference.

**Algorithm**:
```python
if index < 26:  # A-Z
    return chr(ord('A') + index)
else:  # AA-ZZ
    first_index = (index // 26) - 1
    second_index = index % 26
    return chr(ord('A') + first_index) + chr(ord('A') + second_index)
```

---

## Service: SheetsService (Modified)

**Changes to Existing append_row Method**:

**New Behavior**:
1. Check if UserPreference has column_mappings configured
2. If not configured: Return error `(False, {"error_code": "COLUMN_MAPPINGS_REQUIRED"})`
3. If configured:
   - Build sparse row array based on column mappings
   - Handle duplicate column assignments with concatenation
   - Write to Google Sheets

**New Method**: `build_mapped_row(row_data: GoogleSheetsRow, mappings: ColumnMappingConfiguration) -> list`

**Purpose**: Converts GoogleSheetsRow to sparse array based on column mappings

**Algorithm**:
```python
def build_mapped_row(row_data, mappings):
    # Find max column index to determine array size
    max_index = max(
        mappings.get_column_index(mappings.date_column),
        mappings.get_column_index(mappings.description_column),
        mappings.get_column_index(mappings.price_column)
    )

    # Initialize sparse array with empty strings
    row = [''] * (max_index + 1)

    # Map of column index to field values
    column_values = {}

    # Collect values for each column
    date_idx = mappings.get_column_index(mappings.date_column)
    desc_idx = mappings.get_column_index(mappings.description_column)
    price_idx = mappings.get_column_index(mappings.price_column)

    # Add date value
    if date_idx not in column_values:
        column_values[date_idx] = []
    column_values[date_idx].append(row_data.transaction_date.strftime("%Y-%m-%d"))

    # Add description value
    if desc_idx not in column_values:
        column_values[desc_idx] = []
    column_values[desc_idx].append(row_data.items)

    # Add price value
    if price_idx not in column_values:
        column_values[price_idx] = []
    column_values[price_idx].append(str(float(row_data.total_amount)))

    # Write concatenated values to sparse array
    for col_idx, values in column_values.items():
        if len(values) == 1:
            row[col_idx] = values[0]
        else:
            row[col_idx] = ' | '.join(values)

    return row
```

**Example Outputs**:

*Scenario 1: No duplicates (A, B, F)*
```python
mappings = ColumnMappingConfiguration(
    date_column="A",
    description_column="B",
    price_column="F"
)
# Result: ['2024-01-15', 'Coffee; Bagel', '', '', '', '15.50']
#          A            B                C   D   E   F
```

*Scenario 2: Duplicates (A, B, A)*
```python
mappings = ColumnMappingConfiguration(
    date_column="A",
    description_column="B",
    price_column="A"  # Same as date
)
# Result: ['2024-01-15 | 15.50', 'Coffee; Bagel']
#          A                      B
```

---

## Data Flow Diagram

```
User Input (Column Config UI)
  │
  │ POST /api/v1/column-config
  ▼
┌─────────────────────────────┐
│ ColumnMappingConfiguration  │
│   .validate()               │
└────────────┬────────────────┘
             │ Valid
             ▼
┌─────────────────────────────┐
│    UserPreference           │
│ .set_column_mappings()      │
│ .save()                     │
└────────────┬────────────────┘
             │
             ▼
       user_preferences.json
       (persisted)


Receipt Processing Flow:
┌─────────────────────────────┐
│  GoogleSheetsRow            │
│  (date, items, price)       │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  UserPreference             │
│  .get_column_mappings()     │
└────────────┬────────────────┘
             │ Has mappings?
             ├─► No: Error COLUMN_MAPPINGS_REQUIRED
             │
             │ Yes
             ▼
┌─────────────────────────────┐
│  SheetsService              │
│  .build_mapped_row()        │
│  - Check duplicates         │
│  - Apply concatenation      │
│  - Build sparse array       │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  gspread.append_row()       │
│  → Google Sheets API        │
└─────────────────────────────┘
```

---

## Validation Rules Summary

**ColumnMappingConfiguration**:
- ✅ All fields required (date_column, description_column, price_column)
- ✅ Each field must match `^[A-Z]{1,2}$`
- ✅ Each field must convert to index 0-701
- ✅ Duplicates allowed (business rule from clarification)
- ✅ Non-contiguous assignments allowed

**UserPreference** (existing + new rules):
- ✅ Existing: spreadsheet_id must be 44 characters
- ✅ Existing: sheet_tab_name required, max 100 characters
- ✅ New: column_mappings optional (backward compatibility)
- ✅ New: If column_mappings present, must be valid ColumnMappingConfiguration

**Receipt Processing** (new gate):
- ✅ UserPreference must have column_mappings configured
- ✅ If missing: Block processing, return COLUMN_MAPPINGS_REQUIRED error

---

## Backward Compatibility

**Existing user_preferences.json Entries**:
- Entries without `column_mappings` field remain valid
- Loading succeeds, `get_column_mappings()` returns None
- `has_column_mappings()` returns False
- Receipt processing blocked until user configures mappings

**No Automatic Migration**:
- No default mappings applied
- User must explicitly configure via UI
- Preserves user intent (explicit configuration requirement from clarification)

**Data Safety**:
- Existing spreadsheet data unchanged
- New feature additive only (no deletions or modifications to existing fields)

---

**Data Model Status**: ✅ COMPLETE - All entities defined, ready for contract generation
