"""
ExtractedData model representing OCR-parsed data from a receipt.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid


@dataclass
class ExtractedData:
    """
    Represents OCR-parsed data from a receipt.

    Attributes:
        id: Unique identifier (UUID)
        receipt_id: Foreign key to Receipt
        transaction_date: Extracted date from receipt
        transaction_date_confidence: OCR confidence score (0.0-1.0)
        items: Semicolon-delimited list of items
        items_confidence: OCR confidence score (0.0-1.0)
        total_amount: Total receipt amount
        total_amount_confidence: OCR confidence score (0.0-1.0)
        raw_ocr_text: Full unprocessed OCR output (for debugging)
        extraction_timestamp: When OCR completed
    """

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

    # Constants
    MAX_ITEMS_LENGTH = 500

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate extracted data.

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
        """Convert to dictionary for API response."""
        return {
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "transaction_date_confidence": self.transaction_date_confidence,
            "items": self.items,
            "items_confidence": self.items_confidence,
            "total_amount": float(self.total_amount) if self.total_amount else None,
            "total_amount_confidence": self.total_amount_confidence
        }
