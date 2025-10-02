"""
OCR service using pytesseract for receipt text extraction.
"""
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path
import time
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class OCRService:
    """Service for processing receipt images with OCR."""

    # Configuration
    PSM_MODE = 6  # Assume uniform block of text
    CONFIDENCE_THRESHOLD = 60
    TARGET_WIDTH = 1500

    @classmethod
    def preprocess_image(cls, image_path: str) -> Image.Image:
        """
        Preprocess image for better OCR results.

        Args:
            image_path: Path to image file

        Returns:
            Preprocessed PIL Image
        """
        img = Image.open(image_path)

        # Resize to target width maintaining aspect ratio
        if img.width > cls.TARGET_WIDTH:
            ratio = cls.TARGET_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((cls.TARGET_WIDTH, new_height), Image.Resampling.LANCZOS)

        # Convert to grayscale
        img = img.convert('L')

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)

        # Apply adaptive thresholding via PIL
        # Note: For true adaptive thresholding, use opencv
        img = img.point(lambda x: 0 if x < 128 else 255, '1')

        return img

    @classmethod
    def process_image(cls, file_path: str) -> Tuple[str, int]:
        """
        Extract text from receipt image using OCR.

        Args:
            file_path: Path to receipt image file

        Returns:
            Tuple of (raw_ocr_text, processing_time_ms)

        Raises:
            Exception: If OCR processing fails
        """
        start_time = time.time()

        try:
            # Preprocess image
            img = cls.preprocess_image(file_path)

            # Configure tesseract
            custom_config = f'--psm {cls.PSM_MODE}'

            # Extract text
            raw_text = pytesseract.image_to_string(
                img,
                config=custom_config
            )

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(f"OCR processing completed in {processing_time_ms}ms for {file_path}")

            # Check if processing time meets requirement
            if processing_time_ms > 5000:
                logger.warning(f"OCR processing exceeded 5 second target: {processing_time_ms}ms")

            return raw_text, processing_time_ms

        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            raise Exception("OCR_FAILED") from e
