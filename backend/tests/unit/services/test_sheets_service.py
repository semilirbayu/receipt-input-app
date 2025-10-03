"""
Unit tests for SheetsService.build_mapped_row() method.
These tests MUST FAIL until the build_mapped_row method is implemented.
"""
import pytest
from datetime import date
from decimal import Decimal
from backend.src.services.sheets_service import SheetsService
from backend.src.models.google_sheets_row import GoogleSheetsRow
from backend.src.models.column_mapping import ColumnMappingConfiguration


class TestSheetsServiceBuildMappedRow:
    """Tests for SheetsService.build_mapped_row() method."""

    def test_build_mapped_row_no_duplicates_ABC(self):
        """Test build_mapped_row with no duplicates (A, B, C) returns sparse row."""
        row_data = GoogleSheetsRow.from_extracted_data(
            transaction_date=date(2024, 1, 15),
            items="Coffee; Bagel",
            total_amount=Decimal("15.50")
        )

        mappings = ColumnMappingConfiguration(
            date_column="A",
            description_column="B",
            price_column="C"
        )

        result = SheetsService.build_mapped_row(row_data, mappings)

        # Expected: ['2024-01-15', 'Coffee; Bagel', '15.5']
        assert len(result) == 3
        assert result[0] == "2024-01-15"
        assert result[1] == "Coffee; Bagel"
        assert result[2] == "15.5"

    def test_build_mapped_row_non_contiguous_ACF(self):
        """Test build_mapped_row with non-contiguous columns (A, C, F) returns row with empty strings in gaps."""
        row_data = GoogleSheetsRow.from_extracted_data(
            transaction_date=date(2024, 1, 15),
            items="Coffee",
            total_amount=Decimal("15.50")
        )

        mappings = ColumnMappingConfiguration(
            date_column="A",
            description_column="C",
            price_column="F"
        )

        result = SheetsService.build_mapped_row(row_data, mappings)

        # Expected: ['2024-01-15', '', 'Coffee', '', '', '15.5']
        #            A            B   C        D   E   F
        assert len(result) == 6
        assert result[0] == "2024-01-15"
        assert result[1] == ""
        assert result[2] == "Coffee"
        assert result[3] == ""
        assert result[4] == ""
        assert result[5] == "15.5"

    def test_build_mapped_row_with_duplicates_ABA(self):
        """Test build_mapped_row with duplicates (A, B, A) concatenates values with ' | '."""
        row_data = GoogleSheetsRow.from_extracted_data(
            transaction_date=date(2024, 1, 15),
            items="Coffee",
            total_amount=Decimal("15.50")
        )

        mappings = ColumnMappingConfiguration(
            date_column="A",
            description_column="B",
            price_column="A"
        )

        result = SheetsService.build_mapped_row(row_data, mappings)

        # Expected: ['2024-01-15 | 15.5', 'Coffee']
        #            A                     B
        assert len(result) == 2
        assert result[1] == "Coffee"
        # Check concatenation (order should be consistent)
        assert " | " in result[0]
        assert "2024-01-15" in result[0]
        assert "15.5" in result[0]

    def test_build_mapped_row_max_column_index_calculation(self):
        """Test build_mapped_row with (A, B, ZZ) creates 702-element array."""
        row_data = GoogleSheetsRow.from_extracted_data(
            transaction_date=date(2024, 1, 15),
            items="Coffee",
            total_amount=Decimal("15.50")
        )

        mappings = ColumnMappingConfiguration(
            date_column="A",
            description_column="B",
            price_column="ZZ"
        )

        result = SheetsService.build_mapped_row(row_data, mappings)

        # ZZ is index 701, so array should have 702 elements (0-701)
        assert len(result) == 702
        assert result[0] == "2024-01-15"
        assert result[1] == "Coffee"
        assert result[701] == "15.5"

        # All gaps should be empty strings
        for i in range(2, 701):
            assert result[i] == ""

    def test_build_mapped_row_concatenation_order_is_consistent(self):
        """Test concatenation order is consistent when multiple fields map to same column."""
        row_data = GoogleSheetsRow.from_extracted_data(
            transaction_date=date(2024, 1, 15),
            items="Coffee; Bagel",
            total_amount=Decimal("25.50")
        )

        # All three fields to column A
        mappings = ColumnMappingConfiguration(
            date_column="A",
            description_column="A",
            price_column="A"
        )

        result = SheetsService.build_mapped_row(row_data, mappings)

        # Expected: ['2024-01-15 | Coffee; Bagel | 25.5']
        assert len(result) == 1
        # All three values concatenated with ' | '
        assert result[0].count(" | ") == 2
        assert "2024-01-15" in result[0]
        assert "Coffee; Bagel" in result[0]
        assert "25.5" in result[0]

    def test_build_mapped_row_double_letter_columns(self):
        """Test build_mapped_row with double letter columns (AA, AB, AC)."""
        row_data = GoogleSheetsRow.from_extracted_data(
            transaction_date=date(2024, 1, 15),
            items="Coffee",
            total_amount=Decimal("15.50")
        )

        mappings = ColumnMappingConfiguration(
            date_column="AA",
            description_column="AB",
            price_column="AC"
        )

        result = SheetsService.build_mapped_row(row_data, mappings)

        # AA=26, AB=27, AC=28, so array should have 29 elements (0-28)
        assert len(result) == 29
        assert result[26] == "2024-01-15"
        assert result[27] == "Coffee"
        assert result[28] == "15.5"

        # First 26 elements should be empty
        for i in range(26):
            assert result[i] == ""
