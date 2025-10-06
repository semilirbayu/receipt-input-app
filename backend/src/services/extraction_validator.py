"""
ExtractionValidator - Business rule validation for extracted receipt data.

Validates dates, amounts, and items according to functional requirements.
Implements hybrid confidence scoring (Gemini confidence + business rules).
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
import re
import logging

from backend.src.models.validation_result import ValidationResult


# Configure logging
logger = logging.getLogger(__name__)


def parse_idr_amount(idr_text: str) -> int:
    """
    Parse Indonesian Rupiah format to numeric value.

    Handles formats like:
    - "Rp 1.234.567" → 1234567
    - "Rp 50.000" → 50000
    - "1.234.567" → 1234567 (without Rp prefix)

    Args:
        idr_text: IDR amount string

    Returns:
        Numeric amount as integer
    """
    # Remove "Rp" prefix and whitespace
    cleaned = idr_text.replace("Rp", "").replace(" ", "").strip()

    # Remove period separators (Indonesian thousand separators)
    cleaned = cleaned.replace(".", "")

    try:
        return int(cleaned)
    except ValueError:
        logger.warning(f"Failed to parse IDR amount: {idr_text}")
        return 0


class ExtractionValidator:
    """
    Validator for extracted receipt data with business rule enforcement.

    Implements:
    - FR-002: Future date rejection
    - FR-006: Positive amount validation
    - FR-008: IDR currency format handling
    - FR-011: Gibberish detection
    - FR-014: Items max length validation
    - FR-016/FR-017: Confidence thresholds
    """

    # Confidence thresholds (matches ExtractedData.CONFIDENCE_THRESHOLDS)
    CONFIDENCE_HIGH = 0.85
    CONFIDENCE_MEDIUM = 0.60

    # Amount validation limits
    MIN_AMOUNT = Decimal("0.01")
    MAX_AMOUNT = Decimal("999999.99")

    # Items validation
    MAX_ITEMS_LENGTH = 500

    def validate_date(self, date_value: Any) -> ValidationResult:
        """
        Validate transaction date (FR-002: reject future dates).

        Args:
            date_value: Date to validate (can be date object or None)

        Returns:
            ValidationResult with validation outcome
        """
        violations = []
        messages = []
        is_valid = True

        if date_value is None:
            return ValidationResult(
                field_name="date",
                is_valid=False,
                confidence_level="low",
                validation_messages=["Date not extracted"],
                rule_violations=["missing_date"]
            )

        # Check if future date (FR-002)
        if date_value > date.today():
            violations.append("future_date")
            messages.append("Date appears to be in the future")
            is_valid = False
            confidence = "low"
        else:
            confidence = "high"

        return ValidationResult(
            field_name="date",
            is_valid=is_valid,
            confidence_level=confidence,
            validation_messages=messages,
            rule_violations=violations
        )

    def validate_amount(self, amount: Decimal, currency: str = "IDR") -> ValidationResult:
        """
        Validate transaction amount (FR-006: positive, reasonable range).

        Args:
            amount: Amount to validate
            currency: Currency code

        Returns:
            ValidationResult with validation outcome
        """
        violations = []
        messages = []
        is_valid = True
        confidence = "high"

        if amount is None:
            return ValidationResult(
                field_name="amount",
                is_valid=False,
                confidence_level="low",
                validation_messages=["Amount not extracted"],
                rule_violations=["missing_amount"]
            )

        # Check if zero or negative (FR-006)
        if amount <= 0:
            violations.append("negative_amount" if amount < 0 else "zero_amount")
            messages.append("Amount must be positive")
            is_valid = False
            confidence = "low"

        # Check reasonable range
        elif amount > self.MAX_AMOUNT:
            violations.append("out_of_range")
            messages.append(f"Amount exceeds reasonable limit ({self.MAX_AMOUNT})")
            is_valid = False
            confidence = "low"

        return ValidationResult(
            field_name="amount",
            is_valid=is_valid,
            confidence_level=confidence,
            validation_messages=messages,
            rule_violations=violations
        )

    def validate_items(self, items: str) -> ValidationResult:
        """
        Validate items field (FR-011: gibberish detection, FR-014: max length).

        Args:
            items: Items string to validate

        Returns:
            ValidationResult with validation outcome
        """
        violations = []
        messages = []
        is_valid = True
        confidence = "high"

        if items is None or not items.strip():
            return ValidationResult(
                field_name="items",
                is_valid=False,
                confidence_level="low",
                validation_messages=["Items not extracted"],
                rule_violations=["missing_items"]
            )

        # Check max length (FR-014)
        if len(items) > self.MAX_ITEMS_LENGTH:
            violations.append("max_length_exceeded")
            messages.append(f"Items exceed {self.MAX_ITEMS_LENGTH} character limit")
            is_valid = False
            confidence = "low"

        # Gibberish detection (FR-011) - simple heuristic
        if self._is_gibberish(items):
            violations.append("gibberish_detected")
            messages.append("Items appear to be gibberish")
            is_valid = False
            confidence = "low"

        return ValidationResult(
            field_name="items",
            is_valid=is_valid,
            confidence_level=confidence,
            validation_messages=messages,
            rule_violations=violations
        )

    def _is_gibberish(self, text: str) -> bool:
        """
        Detect gibberish text using simple heuristics.

        Checks for:
        - Very low vowel ratio
        - Excessive consonant clusters
        - Random character sequences

        Args:
            text: Text to analyze

        Returns:
            True if likely gibberish, False otherwise
        """
        # Remove punctuation and whitespace
        cleaned = re.sub(r'[^a-zA-Z]', '', text.lower())

        if len(cleaned) < 5:
            return False  # Too short to determine

        # Count vowels
        vowels = sum(1 for c in cleaned if c in 'aeiou')
        vowel_ratio = vowels / len(cleaned)

        # Very low vowel ratio indicates gibberish
        if vowel_ratio < 0.15:
            return True

        # Check for excessive consonant clusters (4+ consonants in a row)
        consonant_clusters = re.findall(r'[^aeiou]{4,}', cleaned)
        if len(consonant_clusters) > 2:
            return True

        return False

    def categorize_confidence(self, confidence_score: float) -> str:
        """
        Categorize confidence score into high/medium/low (FR-016, FR-017).

        Args:
            confidence_score: Score from 0.0 to 1.0

        Returns:
            "high" | "medium" | "low"
        """
        if confidence_score >= self.CONFIDENCE_HIGH:
            return "high"
        elif confidence_score >= self.CONFIDENCE_MEDIUM:
            return "medium"
        else:
            return "low"

    def calculate_final_confidence(
        self,
        gemini_confidence: float,
        field_value: Any,
        field_type: str
    ) -> float:
        """
        Calculate final confidence score combining Gemini confidence + business rules.

        Hybrid approach: Start with Gemini's semantic confidence, then apply
        business rule penalties for violations.

        Args:
            gemini_confidence: Gemini's confidence score (0.0-1.0)
            field_value: The extracted value
            field_type: "date" | "amount" | "items"

        Returns:
            Final confidence score (0.0-1.0)
        """
        confidence = gemini_confidence

        if field_type == "date" and field_value is not None:
            # Future date penalty (FR-002)
            if field_value > date.today() + timedelta(days=1):
                confidence = 0.0  # Future date invalid

        elif field_type == "amount" and field_value is not None:
            # Negative/zero amount penalty (FR-006)
            if field_value <= 0:
                confidence = 0.0  # Invalid amount

            # Out of range penalty
            elif field_value > self.MAX_AMOUNT:
                confidence *= 0.7  # Suspicious amount

        elif field_type == "items" and field_value is not None:
            # Gibberish penalty (FR-011)
            if self._is_gibberish(field_value):
                confidence = 0.0  # Gibberish detected

            # Very short items penalty
            elif len(field_value) < 3:
                confidence *= 0.6  # Suspiciously short

        return max(0.0, min(1.0, confidence))  # Clamp to [0.0, 1.0]
