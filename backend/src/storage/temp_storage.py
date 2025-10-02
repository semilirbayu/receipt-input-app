"""
Temporary storage service for receipt file management.
"""
from pathlib import Path
from typing import List
import uuid
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)


class TempStorageService:
    """Service for managing temporary receipt file storage."""

    def __init__(self, upload_dir: str = "shared/uploads"):
        """
        Initialize temp storage service.

        Args:
            upload_dir: Directory for temporary file storage
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_content: bytes, original_filename: str) -> str:
        """
        Save uploaded file with UUID-based filename.

        Args:
            file_content: File binary content
            original_filename: Original uploaded filename

        Returns:
            Path to saved file

        Raises:
            ValueError: If path traversal attempt detected
        """
        # Generate UUID filename
        file_uuid = str(uuid.uuid4())
        timestamp = int(datetime.utcnow().timestamp())
        extension = Path(original_filename).suffix

        filename = f"{file_uuid}_{timestamp}{extension}"
        file_path = self.upload_dir / filename

        # Ensure file is within upload directory (prevent path traversal)
        if not file_path.resolve().is_relative_to(self.upload_dir.resolve()):
            raise ValueError("Path traversal attempt detected")

        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)

        logger.info(f"File saved: {file_path}")
        return str(file_path)

    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_path: Path to file to delete

        Returns:
            True if deleted, False if file not found
        """
        path = Path(file_path)

        if not path.exists():
            logger.warning(f"File not found for deletion: {file_path}")
            return False

        try:
            path.unlink()
            logger.info(f"File deleted: {file_path}")
            return True
        except PermissionError as e:
            logger.error(f"Permission error deleting file {file_path}: {e}")
            return False

    def list_old_files(self, hours: int = 24) -> List[str]:
        """
        List files older than specified hours.

        Args:
            hours: Age threshold in hours

        Returns:
            List of file paths older than threshold
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        old_files = []

        for file_path in self.upload_dir.iterdir():
            if file_path.is_file() and file_path.name != '.gitkeep':
                # Get file modification time
                mtime = datetime.utcfromtimestamp(file_path.stat().st_mtime)

                if mtime < cutoff_time:
                    old_files.append(str(file_path))

        logger.info(f"Found {len(old_files)} files older than {hours} hours")
        return old_files

    def cleanup_old_files(self, hours: int = 24) -> int:
        """
        Delete files older than specified hours.

        Args:
            hours: Age threshold in hours

        Returns:
            Number of files deleted
        """
        old_files = self.list_old_files(hours)
        deleted_count = 0

        for file_path in old_files:
            if self.delete_file(file_path):
                deleted_count += 1

        logger.info(f"Cleanup completed: {deleted_count} files deleted")
        return deleted_count
