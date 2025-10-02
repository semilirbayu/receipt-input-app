"""
GoogleSheetsRow structure for data appended to Google Sheets.
"""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from backend.src.models.extracted_data import ExtractedData


@dataclass
class GoogleSheetsRow:
    """
    Represents the data structure appended to Google Sheets.

    Attributes:
        transaction_date: Transaction date (YYYY-MM-DD format)
        items: Semicolon-delimited list of items
        total_amount: Total receipt amount
        uploaded_at: Timestamp when appended to sheet
    """

    transaction_date: date
    items: str
    total_amount: Decimal
    uploaded_at: datetime

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate row data before appending to sheet.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.transaction_date is None:
            return False, "Transaction date is required"

        if not self.items or not self.items.strip():
            return False, "Items are required"

        if self.total_amount is None:
            return False, "Total amount is required"

        if self.total_amount < 0:
            return False, "Total amount must be non-negative"

        return True, None

    def to_row(self) -> List:
        """
        Convert to list format for gspread append_row().

        Returns:
            List of values matching Google Sheets column order
        """
        return [
            self.transaction_date.strftime("%Y-%m-%d"),
            self.items,
            float(self.total_amount),
            self.uploaded_at.isoformat()
        ]

    @classmethod
    def from_extracted_data(
        cls,
        transaction_date: date,
        items: str,
        total_amount: Decimal
    ) -> "GoogleSheetsRow":
        """
        Factory method to create GoogleSheetsRow from corrected data.

        Args:
            transaction_date: Confirmed transaction date
            items: Confirmed items string
            total_amount: Confirmed total amount

        Returns:
            New GoogleSheetsRow instance
        """
        return cls(
            transaction_date=transaction_date,
            items=items,
            total_amount=total_amount,
            uploaded_at=datetime.utcnow()
        )
