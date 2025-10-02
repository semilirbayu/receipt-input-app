"""
Cleanup service for scheduled deletion of old receipt files.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.src.storage.temp_storage import TempStorageService
import logging

logger = logging.getLogger(__name__)


class CleanupService:
    """Service for scheduling and executing file cleanup tasks."""

    def __init__(self, storage_service: TempStorageService):
        """
        Initialize cleanup service.

        Args:
            storage_service: TempStorageService instance
        """
        self.storage_service = storage_service
        self.scheduler = AsyncIOScheduler()

    def cleanup_task(self) -> None:
        """Execute cleanup task - delete files older than 24 hours."""
        try:
            deleted_count = self.storage_service.cleanup_old_files(hours=24)
            logger.info(f"Cleanup: Deleted {deleted_count} receipt file(s) older than 24 hours")
        except Exception as e:
            logger.error(f"Cleanup task failed: {e}")

    def schedule_cleanup(self) -> None:
        """Schedule cleanup to run daily at 2 AM."""
        # Configure CronTrigger for daily execution at 2 AM
        trigger = CronTrigger(hour=2, minute=0)

        # Add job to scheduler
        self.scheduler.add_job(
            self.cleanup_task,
            trigger=trigger,
            id='cleanup_old_receipts',
            name='Delete receipts older than 24 hours',
            replace_existing=True
        )

        logger.info("Cleanup scheduler configured: daily at 2 AM")

    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Cleanup scheduler started")

    def stop(self) -> None:
        """Stop the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Cleanup scheduler stopped")
