"""
Unit tests for ColumnValidator service.
These tests MUST FAIL until the ColumnValidator service is implemented.
"""
import pytest
from backend.src.services.column_validator import ColumnValidator


class TestColumnValidatorValidate:
    """Tests for ColumnValidator.validate() method."""

    def test_validate_single_letter_A_returns_true(self):
        """Test validate with 'A' returns (True, None)."""
        is_valid, error = ColumnValidator.validate("A")
        assert is_valid is True
        assert error is None

    def test_validate_single_letter_Z_returns_true(self):
        """Test validate with 'Z' returns (True, None)."""
        is_valid, error = ColumnValidator.validate("Z")
        assert is_valid is True
        assert error is None

    def test_validate_double_letter_ZZ_returns_true(self):
        """Test validate with 'ZZ' returns (True, None)."""
        is_valid, error = ColumnValidator.validate("ZZ")
        assert is_valid is True
        assert error is None

    def test_validate_double_letter_AA_returns_true(self):
        """Test validate with 'AA' returns (True, None)."""
        is_valid, error = ColumnValidator.validate("AA")
        assert is_valid is True
        assert error is None

    def test_validate_numeric_A1_returns_false(self):
        """Test validate with 'A1' returns (False, 'INVALID_COLUMN_FORMAT')."""
        is_valid, error = ColumnValidator.validate("A1")
        assert is_valid is False
        assert error == "INVALID_COLUMN_FORMAT"

    def test_validate_lowercase_abc_returns_false(self):
        """Test validate with 'abc' returns (False, 'INVALID_COLUMN_FORMAT')."""
        is_valid, error = ColumnValidator.validate("abc")
        assert is_valid is False
        assert error == "INVALID_COLUMN_FORMAT"

    def test_validate_triple_letter_AAA_returns_false(self):
        """Test validate with 'AAA' returns (False, 'COLUMN_OUT_OF_RANGE')."""
        is_valid, error = ColumnValidator.validate("AAA")
        assert is_valid is False
        assert error == "COLUMN_OUT_OF_RANGE"

    def test_validate_empty_string_returns_false(self):
        """Test validate with empty string returns (False, 'INVALID_COLUMN_FORMAT')."""
        is_valid, error = ColumnValidator.validate("")
        assert is_valid is False
        assert error == "INVALID_COLUMN_FORMAT"


class TestColumnValidatorToIndex:
    """Tests for ColumnValidator.to_index() method."""

    def test_to_index_A_returns_0(self):
        """Test to_index('A') returns 0."""
        index = ColumnValidator.to_index("A")
        assert index == 0

    def test_to_index_Z_returns_25(self):
        """Test to_index('Z') returns 25."""
        index = ColumnValidator.to_index("Z")
        assert index == 25

    def test_to_index_AA_returns_26(self):
        """Test to_index('AA') returns 26."""
        index = ColumnValidator.to_index("AA")
        assert index == 26

    def test_to_index_AB_returns_27(self):
        """Test to_index('AB') returns 27."""
        index = ColumnValidator.to_index("AB")
        assert index == 27

    def test_to_index_ZZ_returns_701(self):
        """Test to_index('ZZ') returns 701."""
        index = ColumnValidator.to_index("ZZ")
        assert index == 701

    def test_to_index_B_returns_1(self):
        """Test to_index('B') returns 1."""
        index = ColumnValidator.to_index("B")
        assert index == 1

    def test_to_index_AZ_returns_51(self):
        """Test to_index('AZ') returns 51."""
        index = ColumnValidator.to_index("AZ")
        assert index == 51


class TestColumnValidatorFromIndex:
    """Tests for ColumnValidator.from_index() method."""

    def test_from_index_0_returns_A(self):
        """Test from_index(0) returns 'A'."""
        column = ColumnValidator.from_index(0)
        assert column == "A"

    def test_from_index_25_returns_Z(self):
        """Test from_index(25) returns 'Z'."""
        column = ColumnValidator.from_index(25)
        assert column == "Z"

    def test_from_index_26_returns_AA(self):
        """Test from_index(26) returns 'AA'."""
        column = ColumnValidator.from_index(26)
        assert column == "AA"

    def test_from_index_27_returns_AB(self):
        """Test from_index(27) returns 'AB'."""
        column = ColumnValidator.from_index(27)
        assert column == "AB"

    def test_from_index_701_returns_ZZ(self):
        """Test from_index(701) returns 'ZZ'."""
        column = ColumnValidator.from_index(701)
        assert column == "ZZ"

    def test_from_index_1_returns_B(self):
        """Test from_index(1) returns 'B'."""
        column = ColumnValidator.from_index(1)
        assert column == "B"

    def test_from_index_51_returns_AZ(self):
        """Test from_index(51) returns 'AZ'."""
        column = ColumnValidator.from_index(51)
        assert column == "AZ"
