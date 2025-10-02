"""
Receipt data model representing uploaded receipt image file.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional
import uuid
import re


class ProcessingStatus(Enum):
    """Receipt processing status states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Receipt:
    """
    Represents an uploaded receipt image file.

    Attributes:
        id: Unique identifier (UUID)
        filename: Original uploaded filename
        file_path: Server file system path
        file_size: File size in bytes
        file_type: MIME type (image/jpeg or image/png)
        upload_timestamp: When the file was uploaded
        deletion_scheduled_at: When the file will be deleted (24 hours from upload)
        processing_status: Current processing state
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ""
    file_path: str = ""
    file_size: int = 0
    file_type: str = ""
    upload_timestamp: datetime = field(default_factory=datetime.utcnow)
    deletion_scheduled_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))
    processing_status: ProcessingStatus = ProcessingStatus.PENDING

    # Constants
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
    ALLOWED_TYPES = {"image/jpeg", "image/png"}

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.

        Args:
            filename: Original filename from upload

        Returns:
            Sanitized filename safe for storage
        """
        # Remove path traversal sequences
        filename = re.sub(r'\.\.[\\/]', '', filename)
        filename = filename.replace('/', '_').replace('\\', '_')

        # Keep only basename
        filename = Path(filename).name

        # Limit length
        if len(filename) > 255:
            name, ext = Path(filename).stem, Path(filename).suffix
            filename = name[:250] + ext

        return filename

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate receipt data.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.file_size > self.MAX_FILE_SIZE:
            return False, "FILE_TOO_LARGE"

        if self.file_type not in self.ALLOWED_TYPES:
            return False, "INVALID_FORMAT"

        if not self.filename:
            return False, "MISSING_FILE"

        return True, None

    def mark_processing(self) -> None:
        """Mark receipt as currently being processed."""
        self.processing_status = ProcessingStatus.PROCESSING

    def mark_completed(self) -> None:
        """Mark receipt processing as completed."""
        self.processing_status = ProcessingStatus.COMPLETED

    def mark_failed(self) -> None:
        """Mark receipt processing as failed."""
        self.processing_status = ProcessingStatus.FAILED

    @classmethod
    def create(cls, filename: str, file_size: int, file_type: str, file_path: str) -> "Receipt":
        """
        Factory method to create a new Receipt instance.

        Args:
            filename: Original uploaded filename
            file_size: File size in bytes
            file_type: MIME type
            file_path: Storage path

        Returns:
            New Receipt instance
        """
        sanitized_filename = cls.sanitize_filename(filename)

        return cls(
            filename=sanitized_filename,
            file_size=file_size,
            file_type=file_type,
            file_path=file_path
        )
