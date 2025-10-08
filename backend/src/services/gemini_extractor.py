"""
GeminiExtractorService - Receipt data extraction using Gemini Vision API.

Replaces traditional Tesseract OCR + regex parsing with LLM-based extraction.
Provides intelligent paraphrasing, language detection, and structured output.
"""
import google.generativeai as genai
from PIL import Image
import json
import os
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional
import logging

from backend.src.models.extracted_data import ExtractedData


# Configure logging
logger = logging.getLogger(__name__)


class GeminiExtractionError(Exception):
    """Custom exception for Gemini API extraction failures."""
    pass


class GeminiExtractorService:
    """
    Service for extracting receipt data using Gemini Vision API.

    Uses gemini-1.5-flash model for optimal speed/cost balance.
    Handles image processing, prompt engineering, and JSON parsing.
    """

    # Prompt template with JSON schema (from research.md)
    EXTRACTION_PROMPT = """Analyze this Indonesian/English receipt image and extract data in this exact JSON format:

{
  "transaction_date": "YYYY-MM-DD or null",
  "total_amount": 50000,
  "items": "Item 1; Item 2; Item 3",
  "currency": "IDR",
  "detected_language": "id",
  "confidence": {
    "date": 0.95,
    "amount": 0.98,
    "items": 0.85
  }
}

CRITICAL RULES:
1. Extract GRAND TOTAL only (ignore subtotals, tax lines, service charges)
2. For IDR amounts like "Rp 1.234.567", return numeric without separators: 1234567
3. Paraphrase items for clarity in the SAME language as the receipt:
   - Indonesian receipt → Indonesian paraphrased items (e.g., "Nsi Grng x2" → "Nasi Goreng (2 porsi)")
   - English receipt → English paraphrased items (e.g., "Chkn Wng x3" → "Chicken Wings (3 pieces)")
   - DO NOT translate between languages
4. Detect language: "id" for Indonesian, "en" for English
5. Reject future dates - return null if date is in the future
6. If field is unreadable, return null (better empty than wrong)
7. Confidence scores: 0.0 (unreadable) to 1.0 (certain)
8. For items: separate with semicolons, include quantities in parentheses
9. Currency: "IDR" for Indonesian Rupiah, "USD" for US Dollar, etc.

Return ONLY valid JSON, no markdown formatting or explanations."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize GeminiExtractorService.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set, extraction may fail")

        # Configure Gemini
        if self.api_key:
            genai.configure(api_key=self.api_key)

        # Initialize model (gemini-2.5-flash for speed/cost balance and vision)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def extract(self, image_path: str) -> ExtractedData:
        """
        Extract structured data from receipt image using Gemini Vision API.

        Args:
            image_path: Path to receipt image file

        Returns:
            ExtractedData object with parsed fields

        Raises:
            GeminiExtractionError: If API call fails or response invalid
        """
        try:
            # Load image
            image = Image.open(image_path)

            # Generate content with Gemini
            logger.info(f"Calling Gemini API for image: {image_path}")
            response = self.model.generate_content([self.EXTRACTION_PROMPT, image])

            # Parse JSON response
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                # Extract JSON from markdown code block
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
                response_text = response_text.replace("```json", "").replace("```", "").strip()

            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from Gemini: {response_text}")
                raise GeminiExtractionError(f"Failed to parse Gemini JSON response: {e}")

            # Convert to ExtractedData
            extracted = self._parse_gemini_response(data)

            logger.info(f"Successfully extracted data: {extracted.extraction_method}")
            return extracted

        except TimeoutError as e:
            logger.error(f"Gemini API timeout: {e}")
            raise GeminiExtractionError(f"Gemini API timeout: {e}")

        except Exception as e:
            # Check for rate limit error
            if hasattr(e, 'status_code') and e.status_code == 429:
                logger.error("Gemini API rate limit exceeded")
                raise GeminiExtractionError("Rate limit exceeded (429)")

            # Check for API downtime
            if hasattr(e, 'status_code') and e.status_code == 503:
                logger.error("Gemini API service unavailable")
                raise GeminiExtractionError("Gemini API service unavailable (503)")

            logger.error(f"Gemini extraction failed: {e}")
            raise GeminiExtractionError(f"Gemini extraction failed: {e}")

    def _parse_gemini_response(self, data: dict) -> ExtractedData:
        """
        Parse Gemini JSON response into ExtractedData object.

        Args:
            data: Parsed JSON dict from Gemini

        Returns:
            ExtractedData instance
        """
        # Parse transaction date
        transaction_date = None
        if data.get("transaction_date"):
            try:
                transaction_date = date.fromisoformat(data["transaction_date"])
            except (ValueError, TypeError):
                logger.warning(f"Invalid date format: {data.get('transaction_date')}")
                transaction_date = None

        # Parse total amount
        total_amount = None
        if data.get("total_amount") is not None:
            try:
                total_amount = Decimal(str(data["total_amount"]))
            except (ValueError, TypeError, InvalidOperation):
                logger.warning(f"Invalid amount format: {data.get('total_amount')}")
                total_amount = None

        # Extract confidence scores
        confidence = data.get("confidence", {})

        # Create ExtractedData
        extracted = ExtractedData(
            transaction_date=transaction_date,
            transaction_date_confidence=confidence.get("date", 0.0),
            items=data.get("items"),
            items_confidence=confidence.get("items", 0.0),
            total_amount=total_amount,
            total_amount_confidence=confidence.get("amount", 0.0),
            raw_ocr_text=json.dumps(data),  # Store full Gemini response
            extraction_method="gemini",
            detected_language=data.get("detected_language"),
            currency=data.get("currency"),
            paraphrased=True  # Gemini always paraphrases
        )

        return extracted
