"""
ExtractedData model representing OCR-parsed data from a receipt.

Enhanced to support Gemini Vision API integration with backward compatibility.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
import uuid


@dataclass
class ExtractedData:
    """
    Represents OCR-parsed data from a receipt with Gemini Vision support.

    Backward compatible - new fields have defaults that preserve existing behavior.

    Original Attributes:
        id: Unique identifier (UUID)
        receipt_id: Foreign key to Receipt
        transaction_date: Extracted date from receipt
        transaction_date_confidence: OCR confidence score (0.0-1.0)
        items: Semicolon-delimited list of items
        items_confidence: OCR confidence score (0.0-1.0)
        total_amount: Total receipt amount
        total_amount_confidence: OCR confidence score (0.0-1.0)
        raw_ocr_text: Full unprocessed OCR output (Gemini JSON response if using Gemini)
        extraction_timestamp: When OCR completed

    New Gemini Attributes:
        extraction_method: "gemini" or "tesseract_fallback"
        detected_language: "id" (Indonesian) or "en" (English) or None
        currency: "IDR", "USD", etc. or None
        validation_errors: List of business rule violations (e.g., ["future_date_rejected"])
        paraphrased: True if items were AI-paraphrased for clarity
    """

    # ==========================================
    # EXISTING FIELDS (preserved for compatibility)
    # ==========================================
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    receipt_id: str = ""
    transaction_date: Optional[date] = None
    transaction_date_confidence: float = 0.0
    items: Optional[str] = None
    items_confidence: float = 0.0
    total_amount: Optional[Decimal] = None
    total_amount_confidence: float = 0.0
    raw_ocr_text: str = ""
    extraction_timestamp: datetime = field(default_factory=datetime.utcnow)

    # ==========================================
    # NEW FIELDS (Gemini integration)
    # ==========================================
    extraction_method: str = "tesseract"  # Default to tesseract for backward compatibility
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

        Args:
            field: "date" | "items" | "amount"

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

        # Total amount must be non-negative
        if self.total_amount is not None and self.total_amount < 0:
            return False, "Total amount must be positive or zero"

        # Items must be non-empty if present
        if self.items is not None and not self.items.strip():
            return False, "Items cannot be empty string"

        # Items length limit
        if self.items is not None and len(self.items) > self.MAX_ITEMS_LENGTH:
            return False, f"Items exceed {self.MAX_ITEMS_LENGTH} character limit"

        # At least one field must be non-null
        if all(v is None for v in [self.transaction_date, self.items, self.total_amount]):
            return False, "At least one field must be extracted"

        # NEW: Validate extraction method
        if self.extraction_method not in ["gemini", "tesseract", "tesseract_fallback"]:
            return False, f"Invalid extraction_method: {self.extraction_method}"

        # NEW: Validate language code if present
        if self.detected_language and self.detected_language not in ["en", "id"]:
            return False, f"Invalid detected_language: {self.detected_language}"

        return True, None

    @classmethod
    def create(
        cls,
        receipt_id: str,
        transaction_date: Optional[date] = None,
        transaction_date_confidence: float = 0.0,
        items: Optional[str] = None,
        items_confidence: float = 0.0,
        total_amount: Optional[Decimal] = None,
        total_amount_confidence: float = 0.0,
        raw_ocr_text: str = ""
    ) -> "ExtractedData":
        """
        Factory method to create a new ExtractedData instance.

        Args:
            receipt_id: Associated receipt ID
            transaction_date: Extracted date
            transaction_date_confidence: Confidence score for date
            items: Extracted items string
            items_confidence: Confidence score for items
            total_amount: Extracted total amount
            total_amount_confidence: Confidence score for amount
            raw_ocr_text: Raw OCR output

        Returns:
            New ExtractedData instance
        """
        return cls(
            receipt_id=receipt_id,
            transaction_date=transaction_date,
            transaction_date_confidence=transaction_date_confidence,
            items=items,
            items_confidence=items_confidence,
            total_amount=total_amount,
            total_amount_confidence=total_amount_confidence,
            raw_ocr_text=raw_ocr_text
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API response (enhanced with Gemini fields)."""
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
