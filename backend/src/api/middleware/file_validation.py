"""
File validation middleware for upload endpoint.
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class FileValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for validating file uploads before processing."""

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "multipart/form-data"}

    async def dispatch(self, request: Request, call_next):
        """
        Validate file upload requests.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response from next handler or error response
        """
        # Only validate upload endpoint
        if request.url.path == "/api/v1/upload" and request.method == "POST":
            # Check Content-Length header
            content_length = request.headers.get("content-length")

            if content_length:
                try:
                    size = int(content_length)
                    if size > self.MAX_FILE_SIZE:
                        logger.warning(f"File size {size} exceeds limit")
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "error_code": "FILE_TOO_LARGE",
                                "message": "File size exceeds 5MB limit"
                            }
                        )
                except ValueError:
                    pass

            # Check Content-Type header
            content_type = request.headers.get("content-type", "")

            # For multipart/form-data, content-type includes boundary
            if not any(allowed in content_type for allowed in ["multipart/form-data", "image/jpeg", "image/png"]):
                logger.warning(f"Invalid content type: {content_type}")
                # Note: This is a soft check - actual file type validation happens in endpoint

        # Continue to next handler
        response = await call_next(request)
        return response
