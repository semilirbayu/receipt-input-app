"""
Contract tests for extraction validation logic.

These tests verify that ExtractionValidator correctly validates:
1. Date validation: reject future dates (FR-002), accept any past date
2. Price validation: positive numbers, IDR format parsing "Rp 1.234.567" → 1234567 (FR-008)
3. Items validation: gibberish detection, max length 500 chars (FR-011, FR-014)
4. Confidence threshold categorization (high ≥0.85, medium 0.60-0.84, low <0.60)

Test must FAIL initially with "ModuleNotFoundError: No module named 'extraction_validator'"
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal


class TestDateValidation:
    """Contract tests for date validation rules."""

    def test_future_date_rejected(self):
        """
        FR-002: Future dates must be rejected (set to null with is_valid=False).

        Expected to FAIL with: ModuleNotFoundError: No module named 'backend.src.services.extraction_validator'
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()
        future_date = date.today() + timedelta(days=10)

        result = validator.validate_date(future_date)

        # Verify rejection
        assert result.is_valid == False
        assert "future_date" in result.rule_violations
        assert result.confidence_level == "low"
        assert len(result.validation_messages) > 0

    def test_tomorrow_date_rejected(self):
        """
        FR-002: Tomorrow's date should be rejected (edge case).

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()
        tomorrow = date.today() + timedelta(days=1)

        result = validator.validate_date(tomorrow)

        assert result.is_valid == False
        assert "future_date" in result.rule_violations

    def test_today_date_accepted(self):
        """
        Today's date should be accepted.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()
        today = date.today()

        result = validator.validate_date(today)

        assert result.is_valid == True
        assert len(result.rule_violations) == 0

    def test_past_date_accepted_no_historical_limit(self):
        """
        Any past date should be accepted (no historical limit per FR-002 clarification).

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()
        very_old_date = date(1950, 1, 1)

        result = validator.validate_date(very_old_date)

        assert result.is_valid == True
        assert "future_date" not in result.rule_violations


class TestAmountValidation:
    """Contract tests for price/amount validation rules."""

    def test_positive_amount_accepted(self):
        """
        FR-006: Positive amounts must be accepted.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()
        result = validator.validate_amount(Decimal("50000"), currency="IDR")

        assert result.is_valid == True
        assert len(result.rule_violations) == 0

    def test_zero_amount_rejected(self):
        """
        Zero amounts should be rejected.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()
        result = validator.validate_amount(Decimal("0"), currency="IDR")

        assert result.is_valid == False
        assert "invalid_amount" in result.rule_violations or "zero_amount" in result.rule_violations

    def test_negative_amount_rejected(self):
        """
        FR-006: Negative amounts must be rejected.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()
        result = validator.validate_amount(Decimal("-100"), currency="IDR")

        assert result.is_valid == False
        assert "negative_amount" in result.rule_violations or "invalid_amount" in result.rule_violations

    def test_idr_format_parsing_periods_as_thousand_separators(self):
        """
        FR-008: IDR format "Rp 1.234.567" should parse to 1234567.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import parse_idr_amount

        # Test cases for IDR parsing
        test_cases = [
            ("Rp 1.234.567", 1234567),
            ("Rp 50.000", 50000),
            ("Rp 150.500", 150500),
            ("Rp 25000", 25000),  # Without separators
            ("1.234.567", 1234567),  # Without "Rp" prefix
        ]

        for idr_text, expected_amount in test_cases:
            result = parse_idr_amount(idr_text)
            assert result == expected_amount, f"Failed to parse {idr_text}"

    def test_amount_within_reasonable_range(self):
        """
        Amounts should be within reasonable range (0.01 to 999,999.99).

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()

        # Very large amount
        result_large = validator.validate_amount(Decimal("1000000"), currency="IDR")
        assert result_large.is_valid == False
        assert "out_of_range" in result_large.rule_violations or "suspicious_amount" in result_large.rule_violations


class TestItemsValidation:
    """Contract tests for items field validation rules."""

    def test_valid_items_accepted(self):
        """
        Valid items string should be accepted.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()
        items = "Nasi Goreng (2 porsi); Es Teh Manis"

        result = validator.validate_items(items)

        assert result.is_valid == True
        assert len(result.rule_violations) == 0

    def test_gibberish_items_rejected(self):
        """
        FR-011: Gibberish text should be detected and rejected.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()
        gibberish = "asdfghjkl qwertyuiop zxcvbnm"

        result = validator.validate_items(gibberish)

        assert result.is_valid == False
        assert "gibberish_detected" in result.rule_violations

    def test_empty_items_rejected(self):
        """
        Empty or whitespace-only items should be rejected.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()

        result_empty = validator.validate_items("")
        assert result_empty.is_valid == False

        result_whitespace = validator.validate_items("   ")
        assert result_whitespace.is_valid == False

    def test_items_max_length_500_chars(self):
        """
        FR-014: Items exceeding 500 characters should be rejected.

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()
        long_items = "A" * 501  # 501 characters

        result = validator.validate_items(long_items)

        assert result.is_valid == False
        assert "max_length_exceeded" in result.rule_violations or "too_long" in result.rule_violations


class TestConfidenceScoring:
    """Contract tests for confidence score calculation and categorization."""

    def test_high_confidence_threshold(self):
        """
        FR-016: Confidence ≥0.85 should be categorized as "high".

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()

        # Test high confidence
        level = validator.categorize_confidence(0.95)
        assert level == "high"

        # Edge case: exactly 0.85
        level_edge = validator.categorize_confidence(0.85)
        assert level_edge == "high"

    def test_medium_confidence_threshold(self):
        """
        FR-017: Confidence 0.60-0.84 should be categorized as "medium".

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()

        # Test medium confidence
        level = validator.categorize_confidence(0.75)
        assert level == "medium"

        # Edge case: exactly 0.60
        level_edge_low = validator.categorize_confidence(0.60)
        assert level_edge_low == "medium"

        # Edge case: 0.84
        level_edge_high = validator.categorize_confidence(0.84)
        assert level_edge_high == "medium"

    def test_low_confidence_threshold(self):
        """
        Confidence <0.60 should be categorized as "low".

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator

        validator = ExtractionValidator()

        # Test low confidence
        level = validator.categorize_confidence(0.45)
        assert level == "low"

        # Edge case: exactly 0.59
        level_edge = validator.categorize_confidence(0.59)
        assert level_edge == "low"

    def test_hybrid_confidence_calculation_gemini_plus_business_rules(self):
        """
        Confidence scoring should combine Gemini confidence + business rule penalties.

        Example: Future date with Gemini confidence 0.90 → final confidence 0.0 (rule violation).

        Expected to FAIL with: ModuleNotFoundError
        """
        from backend.src.services.extraction_validator import ExtractionValidator
        from datetime import date, timedelta

        validator = ExtractionValidator()
        future_date = date.today() + timedelta(days=10)

        # Gemini says high confidence, but business rule rejects
        final_confidence = validator.calculate_final_confidence(
            gemini_confidence=0.90,
            field_value=future_date,
            field_type="date"
        )

        # Final confidence should be 0.0 due to future date violation
        assert final_confidence == 0.0
