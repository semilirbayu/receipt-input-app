"""
Parser service for extracting structured data from OCR text.
"""
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Tuple
from dateutil import parser as date_parser
import logging

logger = logging.getLogger(__name__)


class ParserService:
    """Service for parsing receipt data from OCR text."""

    # Date regex patterns (in priority order)
    DATE_PATTERNS = [
        (r'\d{4}-\d{2}-\d{2}', '%Y-%m-%d', 0.9),  # ISO 8601: 2025-09-28
        (r'\d{2}/\d{2}/\d{4}', '%m/%d/%Y', 0.9),  # US format: 09/28/2025
        (r'\d{2}-\d{2}-\d{4}', '%d-%m-%Y', 0.9),  # EU format: 28-09-2025
        (r'\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}', None, 0.9),  # Textual: 22 Sep 2025 or 22 September 2025
        (r'[A-Za-z]{3}\s+\d{1,2},?\s+\d{4}', None, 0.9),  # Textual: Jan 15, 2025
    ]

    # Item exclusion keywords
    EXCLUSION_KEYWORDS = {'subtotal', 'tax', 'total', 'amount', 'due', 'balance', 'change'}

    # Amount pattern
    AMOUNT_PATTERN = r'\$?\s*(\d+[,.]?\d*\.?\d{2})'

    @classmethod
    def extract_date(cls, ocr_text: str) -> Tuple[Optional[date], float]:
        """
        Extract transaction date from OCR text.

        Args:
            ocr_text: Raw OCR text

        Returns:
            Tuple of (extracted_date, confidence_score)
        """
        # Try regex patterns first
        for pattern, date_format, confidence in cls.DATE_PATTERNS:
            matches = re.search(pattern, ocr_text, re.IGNORECASE)
            if matches:
                try:
                    if date_format:
                        extracted_date = datetime.strptime(matches.group(), date_format).date()
                    else:
                        # Use dateutil for textual dates
                        extracted_date = date_parser.parse(matches.group(), fuzzy=True).date()

                    logger.info(f"Date extracted: {extracted_date} (confidence: {confidence})")
                    return extracted_date, confidence
                except (ValueError, date_parser.ParserError):
                    continue

        # Fallback: dateutil fuzzy parsing
        try:
            extracted_date = date_parser.parse(ocr_text, fuzzy=True).date()
            logger.info(f"Date extracted via fuzzy parsing: {extracted_date} (confidence: 0.7)")
            return extracted_date, 0.7
        except (ValueError, date_parser.ParserError):
            logger.warning("No date found in OCR text")
            return None, 0.0

    @classmethod
    def extract_items(cls, ocr_text: str) -> Tuple[Optional[str], float]:
        """
        Extract line items from OCR text.

        Args:
            ocr_text: Raw OCR text

        Returns:
            Tuple of (concatenated_items, confidence_score)
        """
        items = []
        lines = ocr_text.split('\n')

        # Enhanced patterns for international currencies
        item_amount_pattern = r'(?:Rp|USD|\$|€|£)?\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2,3})?'

        for line in lines:
            line_lower = line.lower().strip()
            original_line = line.strip()

            # Skip empty lines
            if not line_lower:
                continue

            # Skip lines with exclusion keywords
            if any(keyword in line_lower for keyword in cls.EXCLUSION_KEYWORDS):
                continue

            # Look for lines with quantity and amounts (x1, x2, etc. followed by price)
            # Also match lines with just amounts
            if re.search(r'x\d+', line_lower) or re.search(item_amount_pattern, line):
                # Keep the full line, preserving quantity and price information
                # Clean up excessive whitespace while keeping structure
                cleaned_line = ' '.join(original_line.split())

                # Skip if it's just a number or phone number-like pattern
                if re.match(r'^\d+$', cleaned_line) or len(cleaned_line.replace(' ', '').replace('.', '')) > 15:
                    continue

                items.append(cleaned_line)

        if not items:
            logger.warning("No items found in OCR text")
            return None, 0.0

        # Concatenate with semicolon-space delimiter
        concatenated = "; ".join(items)

        # Truncate to max length
        max_length = 500
        if len(concatenated) > max_length:
            concatenated = concatenated[:max_length]

        logger.info(f"Items extracted: {concatenated} (confidence: 0.85)")
        return concatenated, 0.85

    @classmethod
    def extract_total_amount(cls, ocr_text: str) -> Tuple[Optional[Decimal], float]:
        """
        Extract total amount from OCR text.

        Args:
            ocr_text: Raw OCR text

        Returns:
            Tuple of (total_amount, confidence_score)
        """
        # Enhanced pattern for international currencies
        # Matches: $15.95, Rp 300.150, 300,150, 15.95, etc.
        amount_patterns = [
            r'(?:Rp|USD|\$|€|£)?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',  # International format
            r'\$?\s*(\d+[,.]?\d*\.?\d{2})',  # Original US format
        ]

        # Look for total amount near "Total" keyword
        lines = ocr_text.split('\n')
        total_candidates = []

        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Check if line contains "total" keyword
            if 'total' in line_lower and 'subtotal' not in line_lower:
                # Extract amounts from this line and nearby lines (±1)
                search_lines = lines[max(0, i-1):min(len(lines), i+2)]
                for search_line in search_lines:
                    for pattern in amount_patterns:
                        for match in re.finditer(pattern, search_line):
                            try:
                                # Clean and parse amount
                                amount_str = match.group(1)
                                # Remove thousands separators (dots or commas)
                                # Detect decimal separator (last dot/comma)
                                if '.' in amount_str and ',' in amount_str:
                                    # Both present - last one is decimal
                                    if amount_str.rindex('.') > amount_str.rindex(','):
                                        amount_str = amount_str.replace(',', '')
                                    else:
                                        amount_str = amount_str.replace('.', '').replace(',', '.')
                                elif '.' in amount_str:
                                    # Check if dot is thousands separator (e.g., 300.150)
                                    parts = amount_str.split('.')
                                    if len(parts[-1]) == 3:  # Thousands separator
                                        amount_str = amount_str.replace('.', '')
                                    # else it's a decimal point
                                elif ',' in amount_str:
                                    # Comma - could be thousands or decimal
                                    parts = amount_str.split(',')
                                    if len(parts[-1]) == 2:  # Decimal
                                        amount_str = amount_str.replace(',', '.')
                                    else:  # Thousands separator
                                        amount_str = amount_str.replace(',', '')

                                amount_str = amount_str.replace(' ', '')

                                # Skip if looks like phone number (too many digits)
                                if len(amount_str.replace('.', '')) > 10:
                                    continue

                                amount = Decimal(amount_str)
                                total_candidates.append((amount, 0.95))  # High confidence
                            except (ValueError, ArithmeticError):
                                continue

        # If we found total candidates, return the largest
        if total_candidates:
            total_amount = max(total_candidates, key=lambda x: x[0])[0]
            logger.info(f"Total amount extracted near 'Total': {total_amount} (confidence: 0.95)")
            return total_amount, 0.95

        # Fallback: Find all amounts and return largest (excluding phone numbers)
        amounts = []
        for pattern in amount_patterns:
            for match in re.finditer(pattern, ocr_text):
                try:
                    amount_str = match.group(1).replace(',', '').replace(' ', '').replace('.', '')

                    # Skip if looks like phone number
                    if len(amount_str) > 10:
                        continue

                    # Re-parse with proper decimal handling
                    amount_str = match.group(1)
                    if '.' in amount_str:
                        parts = amount_str.split('.')
                        if len(parts[-1]) == 3:
                            amount_str = amount_str.replace('.', '')
                    amount_str = amount_str.replace(',', '').replace(' ', '')

                    amount = Decimal(amount_str)
                    amounts.append(amount)
                except (ValueError, ArithmeticError):
                    continue

        if not amounts:
            logger.warning("No amounts found in OCR text")
            return None, 0.0

        # Find largest amount (likely the total)
        total_amount = max(amounts)

        logger.info(f"Total amount extracted: {total_amount} (confidence: 0.75)")
        return total_amount, 0.75

    @classmethod
    def parse_receipt_data(cls, ocr_text: str) -> dict:
        """
        Parse all receipt data from OCR text.

        Args:
            ocr_text: Raw OCR text from tesseract

        Returns:
            Dictionary with extracted fields and confidence scores
        """
        transaction_date, date_conf = cls.extract_date(ocr_text)
        items, items_conf = cls.extract_items(ocr_text)
        total_amount, amount_conf = cls.extract_total_amount(ocr_text)

        return {
            "transaction_date": transaction_date,
            "transaction_date_confidence": date_conf,
            "items": items,
            "items_confidence": items_conf,
            "total_amount": total_amount,
            "total_amount_confidence": amount_conf
        }
