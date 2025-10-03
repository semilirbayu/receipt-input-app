"""
ColumnValidator service for validating column references and converting between formats.
"""
import re
from typing import Optional, Tuple


class ColumnValidator:
    """Validates column references and provides conversion utilities."""

    # Regex pattern for valid column references (A-ZZ)
    COLUMN_PATTERN = re.compile(r"^[A-Z]{1,2}$")

    # Maximum valid column index (ZZ = 701)
    MAX_COLUMN_INDEX = 701

    @staticmethod
    def validate(column_ref: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a single column reference.

        Args:
            column_ref: Column reference string (e.g., "A", "AA", "ZZ")

        Returns:
            Tuple of (is_valid, error_code)
            - (True, None) if valid
            - (False, "INVALID_COLUMN_FORMAT") if format is invalid
            - (False, "COLUMN_OUT_OF_RANGE") if beyond ZZ (index 701)
        """
        # Special case: 3+ uppercase letters should be OUT_OF_RANGE, not INVALID_FORMAT
        if len(column_ref) > 2 and column_ref.isupper() and column_ref.isalpha():
            return False, "COLUMN_OUT_OF_RANGE"

        # Check format with regex
        if not ColumnValidator.COLUMN_PATTERN.match(column_ref):
            return False, "INVALID_COLUMN_FORMAT"

        # Check range (must be within 0-701)
        index = ColumnValidator.to_index(column_ref)
        if index > ColumnValidator.MAX_COLUMN_INDEX:
            return False, "COLUMN_OUT_OF_RANGE"

        return True, None

    @staticmethod
    def to_index(column_ref: str) -> int:
        """
        Convert column reference to zero-based index.

        Args:
            column_ref: Column reference (e.g., "A", "AA", "ZZ")

        Returns:
            Zero-based index (A=0, B=1, ..., Z=25, AA=26, ..., ZZ=701)

        Algorithm:
            Single letter (A-Z):
                index = ord(letter) - ord('A')
            Double letter (AA-ZZ):
                first_index = ord(first) - ord('A') + 1  (A=1, B=2, ..., Z=26)
                second_index = ord(second) - ord('A')     (A=0, B=1, ..., Z=25)
                index = first_index * 26 + second_index
        """
        if len(column_ref) == 1:
            # Single letter: A=0, B=1, ..., Z=25
            return ord(column_ref) - ord('A')
        else:
            # Double letter: AA=26, AB=27, ..., ZZ=701
            first = ord(column_ref[0]) - ord('A') + 1  # A=1, B=2, ..., Z=26
            second = ord(column_ref[1]) - ord('A')      # A=0, B=1, ..., Z=25
            return first * 26 + second

    @staticmethod
    def from_index(index: int) -> str:
        """
        Convert zero-based index to column reference.

        Args:
            index: Zero-based index (0-701)

        Returns:
            Column reference (A, B, ..., Z, AA, AB, ..., ZZ)

        Algorithm:
            If index < 26: Single letter
                column = chr(ord('A') + index)
            Else: Double letter
                first_index = (index // 26) - 1
                second_index = index % 26
                column = chr(ord('A') + first_index) + chr(ord('A') + second_index)
        """
        if index < 26:
            # Single letter: 0=A, 1=B, ..., 25=Z
            return chr(ord('A') + index)
        else:
            # Double letter: 26=AA, 27=AB, ..., 701=ZZ
            first_index = (index // 26) - 1
            second_index = index % 26
            return chr(ord('A') + first_index) + chr(ord('A') + second_index)
