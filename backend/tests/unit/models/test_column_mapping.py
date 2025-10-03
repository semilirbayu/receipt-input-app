"""
Unit tests for ColumnMappingConfiguration model.
These tests MUST FAIL until the ColumnMappingConfiguration model is implemented.
"""
import pytest
from backend.src.models.column_mapping import ColumnMappingConfiguration


class TestColumnMappingConfigurationValidate:
    """Tests for ColumnMappingConfiguration.validate() method."""

    def test_validate_valid_config_ABC_returns_true(self):
        """Test validate with valid config (A, B, C) returns (True, None)."""
        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="B",
            price_column="C"
        )
        is_valid, error = config.validate()
        assert is_valid is True
        assert error is None

    def test_validate_with_missing_date_column_returns_false(self):
        """Test validate with empty date_column returns (False, error)."""
        config = ColumnMappingConfiguration(
            date_column="",
            description_column="B",
            price_column="C"
        )
        is_valid, error = config.validate()
        assert is_valid is False
        assert error is not None

    def test_validate_with_invalid_column_format_returns_false(self):
        """Test validate with invalid format (A1) returns (False, error)."""
        config = ColumnMappingConfiguration(
            date_column="A1",
            description_column="B",
            price_column="C"
        )
        is_valid, error = config.validate()
        assert is_valid is False
        assert "INVALID_COLUMN_FORMAT" in error

    def test_validate_with_out_of_range_column_returns_false(self):
        """Test validate with out-of-range column (AAA) returns (False, error)."""
        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="B",
            price_column="AAA"
        )
        is_valid, error = config.validate()
        assert is_valid is False
        assert "COLUMN_OUT_OF_RANGE" in error


class TestColumnMappingConfigurationToDict:
    """Tests for ColumnMappingConfiguration.to_dict() method."""

    def test_to_dict_returns_correct_format(self):
        """Test to_dict returns correct dictionary format."""
        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="B",
            price_column="C"
        )
        result = config.to_dict()

        assert result == {
            "date": "A",
            "description": "B",
            "price": "C"
        }

    def test_to_dict_with_non_contiguous_columns(self):
        """Test to_dict with non-contiguous columns (A, C, F)."""
        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="C",
            price_column="F"
        )
        result = config.to_dict()

        assert result == {
            "date": "A",
            "description": "C",
            "price": "F"
        }


class TestColumnMappingConfigurationFromDict:
    """Tests for ColumnMappingConfiguration.from_dict() method."""

    def test_from_dict_creates_valid_instance(self):
        """Test from_dict creates valid ColumnMappingConfiguration instance."""
        data = {
            "date": "A",
            "description": "B",
            "price": "C"
        }
        config = ColumnMappingConfiguration.from_dict(data)

        assert config.date_column == "A"
        assert config.description_column == "B"
        assert config.price_column == "C"

    def test_from_dict_with_double_letters(self):
        """Test from_dict with double letter columns (AA, AB, ZZ)."""
        data = {
            "date": "AA",
            "description": "AB",
            "price": "ZZ"
        }
        config = ColumnMappingConfiguration.from_dict(data)

        assert config.date_column == "AA"
        assert config.description_column == "AB"
        assert config.price_column == "ZZ"


class TestColumnMappingConfigurationGetColumnIndex:
    """Tests for ColumnMappingConfiguration.get_column_index() method."""

    def test_get_column_index_A_returns_0(self):
        """Test get_column_index('A') returns 0."""
        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="B",
            price_column="C"
        )
        index = config.get_column_index("A")
        assert index == 0

    def test_get_column_index_AA_returns_26(self):
        """Test get_column_index('AA') returns 26."""
        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="AA",
            price_column="C"
        )
        index = config.get_column_index("AA")
        assert index == 26

    def test_get_column_index_ZZ_returns_701(self):
        """Test get_column_index('ZZ') returns 701."""
        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="B",
            price_column="ZZ"
        )
        index = config.get_column_index("ZZ")
        assert index == 701


class TestColumnMappingConfigurationHasDuplicates:
    """Tests for ColumnMappingConfiguration.has_duplicates() method."""

    def test_has_duplicates_returns_false_for_unique_columns(self):
        """Test has_duplicates returns False for unique columns (A, B, C)."""
        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="B",
            price_column="C"
        )
        assert config.has_duplicates() is False

    def test_has_duplicates_returns_true_for_duplicate_columns(self):
        """Test has_duplicates returns True for duplicate columns (A, B, A)."""
        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="B",
            price_column="A"
        )
        assert config.has_duplicates() is True

    def test_has_duplicates_returns_true_for_all_same_columns(self):
        """Test has_duplicates returns True when all columns are the same (A, A, A)."""
        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="A",
            price_column="A"
        )
        assert config.has_duplicates() is True


class TestColumnMappingConfigurationGetDuplicateColumns:
    """Tests for ColumnMappingConfiguration.get_duplicate_columns() method."""

    def test_get_duplicate_columns_returns_empty_for_unique(self):
        """Test get_duplicate_columns returns empty dict for unique columns."""
        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="B",
            price_column="C"
        )
        duplicates = config.get_duplicate_columns()
        assert duplicates == {}

    def test_get_duplicate_columns_returns_correct_mapping_for_date_price_duplicate(self):
        """Test get_duplicate_columns returns correct mapping for (A, B, A)."""
        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="B",
            price_column="A"
        )
        duplicates = config.get_duplicate_columns()

        assert "A" in duplicates
        assert set(duplicates["A"]) == {"date", "price"}

    def test_get_duplicate_columns_returns_correct_mapping_for_all_same(self):
        """Test get_duplicate_columns for all same columns (A, A, A)."""
        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="A",
            price_column="A"
        )
        duplicates = config.get_duplicate_columns()

        assert "A" in duplicates
        assert set(duplicates["A"]) == {"date", "description", "price"}

    def test_get_duplicate_columns_with_multiple_duplicate_sets(self):
        """Test get_duplicate_columns with multiple duplicate sets (A, B, A, B would be impossible with 3 fields, so test A, A, B)."""
        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="A",
            price_column="B"
        )
        duplicates = config.get_duplicate_columns()

        assert "A" in duplicates
        assert set(duplicates["A"]) == {"date", "description"}
        assert "B" not in duplicates  # B is only used once
