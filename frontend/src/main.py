"""
FastAPI main application entry point.
"""
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import API routers
from backend.src.api.v1 import upload, save, auth
from backend.src.api.middleware.file_validation import FileValidationMiddleware
from backend.src.services.cleanup_service import CleanupService
from backend.src.storage.temp_storage import TempStorageService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize cleanup service
storage_service = TempStorageService()
cleanup_service = CleanupService(storage_service)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown."""
    # Startup
    logger.info("Application startup: initializing cleanup scheduler")
    cleanup_service.schedule_cleanup()
    cleanup_service.start()

    yield

    # Shutdown
    logger.info("Application shutdown: stopping cleanup scheduler")
    cleanup_service.stop()


# Initialize FastAPI app
app = FastAPI(
    title="Receipt Processing Web App",
    description="Upload receipt images, extract data via OCR, and save to Google Sheets",
    version="0.1.0",
    lifespan=lifespan
)

# Add session middleware (for OAuth2 token storage)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development-only")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add file validation middleware
app.add_middleware(FileValidationMiddleware)

# Configure templates
templates = Jinja2Templates(directory="frontend/src/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/src/static"), name="static")

# Include API routers
app.include_router(upload.router, tags=["Receipt Processing"])
app.include_router(save.router, tags=["Receipt Processing"])
app.include_router(auth.router, tags=["Authentication"])


@app.get("/")
async def root(request: Request):
    """Render upload page (homepage)."""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/setup")
async def setup_page(request: Request):
    """Render Google Sheets setup page."""
    return templates.TemplateResponse("setup.html", {"request": request})


@app.get("/review/{receipt_id}")
async def review_page(request: Request, receipt_id: str):
    """
    Render review page with extracted data.

    Args:
        request: FastAPI request object
        receipt_id: Receipt UUID

    Returns:
        Rendered review template
    """
    # TODO: Load extracted data from session or storage
    # For now, pass receipt_id to template
    return templates.TemplateResponse(
        "review.html",
        {
            "request": request,
            "receipt_id": receipt_id
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "frontend.src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
