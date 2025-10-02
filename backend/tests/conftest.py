"""
Pytest fixtures shared across all test modules.
"""
import pytest
from httpx import AsyncClient
from typing import AsyncGenerator
from frontend.src.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing API endpoints.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
