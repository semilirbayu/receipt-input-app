"""
ColumnMappingConfiguration model for user's column mapping preferences.
"""
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List
from backend.src.services.column_validator import ColumnValidator


@dataclass
class ColumnMappingConfiguration:
    """
    Represents user's column mapping preferences for receipt data fields.

    Attributes:
        date_column: Column reference for transaction date (A-ZZ format)
        description_column: Column reference for items description (A-ZZ format)
        price_column: Column reference for total amount (A-ZZ format)
    """

    date_column: str
    description_column: str
    price_column: str

    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate all column references.

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if all fields are valid
            - (False, error_message) if any field is invalid

        Validation Rules:
            1. All three fields must be non-empty
            2. Each field must pass ColumnValidator.validate()
            3. Returns first validation error encountered
        """
        # Check all fields are non-empty
        if not self.date_column or not self.date_column.strip():
            return False, "date_column is required"

        if not self.description_column or not self.description_column.strip():
            return False, "description_column is required"

        if not self.price_column or not self.price_column.strip():
            return False, "price_column is required"

        # Validate date_column
        is_valid, error = ColumnValidator.validate(self.date_column)
        if not is_valid:
            return False, f"date_column: {error}"

        # Validate description_column
        is_valid, error = ColumnValidator.validate(self.description_column)
        if not is_valid:
            return False, f"description_column: {error}"

        # Validate price_column
        is_valid, error = ColumnValidator.validate(self.price_column)
        if not is_valid:
            return False, f"price_column: {error}"

        return True, None

    def to_dict(self) -> Dict[str, str]:
        """
        Convert to dictionary format for JSON serialization.

        Returns:
            Dictionary with keys: date, description, price
            Example: {"date": "A", "description": "B", "price": "C"}
        """
        return {
            "date": self.date_column,
            "description": self.description_column,
            "price": self.price_column
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ColumnMappingConfiguration":
        """
        Factory method to create instance from dictionary.

        Args:
            data: Dictionary with keys: date, description, price

        Returns:
            New ColumnMappingConfiguration instance
        """
        return cls(
            date_column=data["date"],
            description_column=data["description"],
            price_column=data["price"]
        )

    def get_column_index(self, column_ref: str) -> int:
        """
        Convert column reference to zero-based index.

        Args:
            column_ref: Column reference like "A" or "AA"

        Returns:
            Zero-based index (A=0, B=1, ..., ZZ=701)
        """
        return ColumnValidator.to_index(column_ref)

    def has_duplicates(self) -> bool:
        """
        Check if any columns are assigned to multiple fields.

        Returns:
            True if duplicates exist, False otherwise
        """
        columns = [self.date_column, self.description_column, self.price_column]
        return len(columns) != len(set(columns))

    def get_duplicate_columns(self) -> Dict[str, List[str]]:
        """
        Get mapping of duplicate columns to field names.

        Returns:
            Dictionary mapping column references to list of field names
            Example: {"A": ["date", "price"]} if both date and price map to column A
            Returns empty dict if no duplicates
        """
        column_to_fields = {}

        # Map each column to its field name(s)
        fields = [
            (self.date_column, "date"),
            (self.description_column, "description"),
            (self.price_column, "price")
        ]

        for column, field in fields:
            if column not in column_to_fields:
                column_to_fields[column] = []
            column_to_fields[column].append(field)

        # Filter to only columns with multiple fields (duplicates)
        duplicates = {
            column: field_list
            for column, field_list in column_to_fields.items()
            if len(field_list) > 1
        }

        return duplicates
