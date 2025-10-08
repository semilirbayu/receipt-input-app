# Data Model: Enhanced Receipt Extraction

**Feature**: 003-bugfix-improve-data
**Date**: 2025-10-06
**Purpose**: Define data structures for Gemini Vision-based receipt extraction

---

## Overview

This feature enhances the existing `ExtractedData` model to support Gemini Vision API integration while maintaining backward compatibility. Three primary models are involved:

1. **ExtractedData** (enhanced) - Stores extraction results with new Gemini-specific fields
2. **ExtractionMetrics** (new) - Tracks quality metrics per FR-020
3. **ValidationResult** (new) - Represents field-level validation outcomes

---

## Entity: ExtractedData (Enhanced)

**Purpose**: Represents data extracted from a receipt image, supporting both Gemini and Tesseract extraction methods.

### Schema

```python
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
import uuid

@dataclass
class ExtractedData:
    """
    OCR-extracted receipt data with Gemini Vision support.

    Backward compatible with existing schema - adds optional fields
    for Gemini-specific metadata without breaking existing code.
    """

    # ==========================================
    # EXISTING FIELDS (preserved for compatibility)
    # ==========================================
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    receipt_id: str = ""
    transaction_date: Optional[date] = None
    transaction_date_confidence: float = 0.0  # 0.0-1.0 scale
    items: Optional[str] = None  # Semicolon-separated list
    items_confidence: float = 0.0
    total_amount: Optional[Decimal] = None
    total_amount_confidence: float = 0.0
    raw_ocr_text: str = ""  # Now stores Gemini JSON response if using Gemini
    extraction_timestamp: datetime = field(default_factory=datetime.utcnow)

    # ==========================================
    # NEW FIELDS (Gemini integration)
    # ==========================================
    extraction_method: str = "tesseract"  # "gemini" | "tesseract_fallback"
    detected_language: Optional[str] = None  # "en" | "id"
    currency: Optional[str] = None  # "IDR" | "USD" | etc.
    validation_errors: List[str] = field(default_factory=list)  # ["future_date_rejected", ...]
    paraphrased: bool = False  # True if items were AI-paraphrased

    # Constants
    MAX_ITEMS_LENGTH = 500
    CONFIDENCE_THRESHOLDS = {
        "high": 0.85,
        "medium": 0.60,
        "low": 0.0
    }

    def get_confidence_level(self, field: str) -> str:
        """
        Get UI-friendly confidence level for a field.

        Args:
            field: "date" | "items" | "amount"

        Returns:
            "high" | "medium" | "low"
        """
        conf_map = {
            "date": self.transaction_date_confidence,
            "items": self.items_confidence,
            "amount": self.total_amount_confidence
        }

        confidence = conf_map.get(field, 0.0)

        if confidence >= self.CONFIDENCE_THRESHOLDS["high"]:
            return "high"
        elif confidence >= self.CONFIDENCE_THRESHOLDS["medium"]:
            return "medium"
        else:
            return "low"

    def get_ui_indicator(self, field: str) -> str:
        """
        Get UI confidence indicator symbol (FR-019).

        Returns:
            "✓" (high) | "⚠" (medium) | "✗" (low)
        """
        level = self.get_confidence_level(field)
        return {"high": "✓", "medium": "⚠", "low": "✗"}[level]

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate extracted data (enhanced from original).

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Confidence scores must be in valid range
        for conf in [self.transaction_date_confidence, self.items_confidence, self.total_amount_confidence]:
            if not (0.0 <= conf <= 1.0):
                return False, "Invalid confidence score"

        # Total amount must be non-negative if present
        if self.total_amount is not None and self.total_amount < 0:
            return False, "Total amount must be positive or zero"

        # Items must be non-empty if present
        if self.items is not None and not self.items.strip():
            return False, "Items cannot be empty string"

        # Items length limit
        if self.items is not None and len(self.items) > self.MAX_ITEMS_LENGTH:
            return False, f"Items exceed {self.MAX_ITEMS_LENGTH} character limit"

        # At least one field must be non-null (original rule)
        if all(v is None for v in [self.transaction_date, self.items, self.total_amount]):
            return False, "At least one field must be extracted"

        # NEW: Validate extraction method
        if self.extraction_method not in ["gemini", "tesseract_fallback"]:
            return False, f"Invalid extraction_method: {self.extraction_method}"

        # NEW: Validate language code if present
        if self.detected_language and self.detected_language not in ["en", "id"]:
            return False, f"Invalid detected_language: {self.detected_language}"

        return True, None

    def to_dict(self) -> dict:
        """Convert to dictionary for API response (enhanced)."""
        return {
            # Original fields
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "transaction_date_confidence": self.transaction_date_confidence,
            "items": self.items,
            "items_confidence": self.items_confidence,
            "total_amount": float(self.total_amount) if self.total_amount else None,
            "total_amount_confidence": self.total_amount_confidence,

            # New Gemini fields
            "extraction_method": self.extraction_method,
            "detected_language": self.detected_language,
            "currency": self.currency,
            "paraphrased": self.paraphrased,

            # UI helpers
            "confidence_indicators": {
                "date": self.get_ui_indicator("date"),
                "items": self.get_ui_indicator("items"),
                "amount": self.get_ui_indicator("amount")
            }
        }
```

### Field Descriptions

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `id` | str | Yes | Unique identifier (UUID) | "550e8400-e29b-41d4-a716-446655440000" |
| `receipt_id` | str | Yes | Foreign key to Receipt | "receipt_001" |
| `transaction_date` | date? | No | Extracted transaction date | 2025-10-06 |
| `transaction_date_confidence` | float | Yes | Confidence score 0.0-1.0 | 0.95 |
| `items` | str? | No | Semicolon-separated items | "Nasi Goreng (2 portions); Es Teh Manis" |
| `items_confidence` | float | Yes | Confidence score 0.0-1.0 | 0.85 |
| `total_amount` | Decimal? | No | Total receipt amount (numeric) | 50000 (for Rp 50.000) |
| `total_amount_confidence` | float | Yes | Confidence score 0.0-1.0 | 0.98 |
| `raw_ocr_text` | str | Yes | Full Gemini JSON or Tesseract text | "{\\"date\\": \\"2025-10-06\\", ...}" |
| `extraction_timestamp` | datetime | Yes | When extraction completed | 2025-10-06T14:30:00Z |
| **`extraction_method`** | str | Yes | Method used | "gemini" or "tesseract_fallback" |
| **`detected_language`** | str? | No | Detected receipt language | "id" (Indonesian) or "en" (English) |
| **`currency`** | str? | No | Detected currency | "IDR", "USD" |
| **`validation_errors`** | List[str] | Yes | Business rule violations | ["future_date_rejected"] |
| **`paraphrased`** | bool | Yes | Items AI-paraphrased? | true (if Gemini paraphrased) |

### Business Rules

1. **Date Validation (FR-002)**:
   - Must reject future dates beyond tomorrow
   - Must accept any past date (no historical limit)
   - Invalid dates set to `null` with confidence = 0.0

2. **Amount Validation (FR-006)**:
   - Must be positive (>= 0.01)
   - Must be within reasonable range (0.01 to 999,999.99)
   - For IDR, periods are thousand-separators: "Rp 1.234.567" → 1234567

3. **Items Validation (FR-011, FR-014)**:
   - Must detect and reject gibberish (pattern-based + LLM)
   - Must sanitize: remove extra whitespace, OCR artifacts
   - Max length: 500 characters

4. **Confidence Thresholds (FR-016, FR-017)**:
   - High (≥0.85): Auto-fill, show ✓
   - Medium (0.60-0.84): Auto-fill, show ⚠, flag for review
   - Low (<0.60): Leave empty, show ✗, require manual input

### State Transitions

```
[Upload] → [Gemini Extract] → [Validate] → [Store]
                ↓ (on error)
         [Tesseract Fallback] → [Validate] → [Store]
```

---

## Entity: ExtractionMetrics (New)

**Purpose**: Track extraction quality metrics for monitoring and improvement analysis (FR-020).

### Schema

```python
from dataclasses import dataclass
from datetime import date
from typing import Dict

@dataclass
class ExtractionMetrics:
    """
    Daily aggregated metrics for extraction quality monitoring.

    Supports FR-020 requirement: track success rate and confidence distribution.
    """

    date_extracted: date  # Metrics aggregation date
    total_extractions: int  # Total receipts processed
    successful_extractions: int  # All 3 fields populated (date, items, amount)
    failed_extractions: int  # All 3 fields null
    partial_extractions: int  # Some fields populated, some null

    # Confidence distribution (counts per level)
    confidence_distribution: Dict[str, int]  # {"low": 5, "medium": 10, "high": 20}

    # Extraction method usage
    extraction_method_usage: Dict[str, int]  # {"gemini": 30, "tesseract_fallback": 5}

    def get_success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_extractions == 0:
            return 0.0
        return (self.successful_extractions / self.total_extractions) * 100

    def get_gemini_usage_rate(self) -> float:
        """Calculate percentage of extractions using Gemini (vs fallback)."""
        if self.total_extractions == 0:
            return 0.0
        gemini_count = self.extraction_method_usage.get("gemini", 0)
        return (gemini_count / self.total_extractions) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary for API/logging."""
        return {
            "date": self.date_extracted.isoformat(),
            "total": self.total_extractions,
            "successful": self.successful_extractions,
            "failed": self.failed_extractions,
            "partial": self.partial_extractions,
            "success_rate": round(self.get_success_rate(), 2),
            "confidence_distribution": self.confidence_distribution,
            "extraction_methods": self.extraction_method_usage,
            "gemini_usage_rate": round(self.get_gemini_usage_rate(), 2)
        }
```

### Storage

Metrics stored in JSON file: `shared/extraction_metrics.json`

```json
{
  "2025-10-06": {
    "date_extracted": "2025-10-06",
    "total_extractions": 35,
    "successful_extractions": 28,
    "failed_extractions": 2,
    "partial_extractions": 5,
    "confidence_distribution": {
      "low": 4,
      "medium": 12,
      "high": 19
    },
    "extraction_method_usage": {
      "gemini": 33,
      "tesseract_fallback": 2
    }
  }
}
```

---

## Entity: ValidationResult (New)

**Purpose**: Represent field-level validation outcomes for debugging and user feedback.

### Schema

```python
from dataclasses import dataclass
from typing import List

@dataclass
class ValidationResult:
    """
    Validation outcome for a single extracted field.

    Used for detailed feedback in API responses and debugging.
    """

    field_name: str  # "date" | "price" | "description"
    is_valid: bool  # Passed business rules?
    confidence_level: str  # "low" | "medium" | "high"
    validation_messages: List[str]  # Human-readable feedback
    rule_violations: List[str]  # Specific rule failures

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "field": self.field_name,
            "valid": self.is_valid,
            "confidence": self.confidence_level,
            "messages": self.validation_messages,
            "violations": self.rule_violations
        }
```

### Example Usage

```python
# Date validation
result = ValidationResult(
    field_name="date",
    is_valid=False,
    confidence_level="low",
    validation_messages=["Date appears to be in the future"],
    rule_violations=["future_date"]
)

# API response includes validation details
{
  "extracted_data": { ... },
  "validation": {
    "date": {
      "valid": false,
      "confidence": "low",
      "messages": ["Date appears to be in the future"],
      "violations": ["future_date"]
    }
  }
}
```

---

## Relationships

```
Receipt (existing)
  ↓ (1:1)
ExtractedData (enhanced)
  ↓ (aggregated daily)
ExtractionMetrics (new)

ExtractedData
  ↓ (validated by)
ValidationResult × 3 (date, price, items)
```

---

## Migration Strategy

### Backward Compatibility

**Existing code continues to work** because:
1. New fields have default values (`extraction_method="tesseract"`, `detected_language=None`)
2. `to_dict()` method maintains original field names
3. Validation rules are enhancements, not breaking changes

### Migration Steps

1. **Add new fields to `ExtractedData`** with defaults
2. **Update existing records** (optional - defaults handle old data gracefully)
3. **Create `ExtractionMetrics` storage** (new JSON file)
4. **Deploy Gemini integration** (Tesseract fallback ensures continuity)

No database migration needed (using JSON file storage per spec).

---

## Testing Requirements

### Unit Tests

1. **ExtractedData.validate()**:
   - Test confidence score validation (0.0-1.0 range)
   - Test amount validation (non-negative, reasonable range)
   - Test items validation (non-empty, max length)
   - Test new field validation (extraction_method, language code)

2. **ExtractionMetrics calculations**:
   - Test success_rate calculation
   - Test gemini_usage_rate calculation
   - Test confidence distribution aggregation

3. **ValidationResult**:
   - Test to_dict() serialization
   - Test field-level error tracking

### Integration Tests

1. **End-to-end extraction**:
   - Upload receipt → Extract with Gemini → Validate → Store → Retrieve
   - Verify all fields populated correctly
   - Verify metrics updated

2. **Fallback scenario**:
   - Mock Gemini failure → Tesseract fallback → `extraction_method="tesseract_fallback"`

---

## Summary

This data model design:

✅ **Maintains backward compatibility** - existing code unaffected
✅ **Supports Gemini integration** - new fields for language, currency, paraphrasing
✅ **Enables quality monitoring** - ExtractionMetrics tracks FR-020 requirements
✅ **Provides detailed validation** - ValidationResult for debugging and UX
✅ **Follows constitutional principles** - clear schema, type-safe, testable

**Next**: Generate API contracts and contract tests based on these models.
