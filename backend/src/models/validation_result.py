"""
ValidationResult model for field-level validation outcomes.

Used for detailed feedback in API responses and debugging.
Represents validation status for a single extracted field.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class ValidationResult:
    """
    Validation outcome for a single extracted field.

    Provides granular validation feedback for debugging and user communication.
    Used by ExtractionValidator to return field-level validation results.

    Attributes:
        field_name: Field being validated ("date" | "price" | "description" | "items")
        is_valid: Whether field passed all business rules
        confidence_level: Confidence category ("low" | "medium" | "high")
        validation_messages: Human-readable feedback for users
        rule_violations: Specific rule failure codes (e.g., ["future_date", "negative_amount"])
    """

    field_name: str
    is_valid: bool
    confidence_level: str  # "low" | "medium" | "high"
    validation_messages: List[str]
    rule_violations: List[str]

    def to_dict(self) -> dict:
        """
        Convert to dictionary for API response.

        Returns:
            Dict suitable for JSON API responses
        """
        return {
            "field": self.field_name,
            "valid": self.is_valid,
            "confidence": self.confidence_level,
            "messages": self.validation_messages,
            "violations": self.rule_violations
        }
