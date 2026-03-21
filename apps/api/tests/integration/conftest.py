"""Integration test fixtures for API testing."""

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from core.jwt import create_access_token
from main import app
from models.database import Base, get_db
from models.user import User
from services.llm_processor import LLMResult


# Integration test database URL (can be configured via environment)
INTEGRATION_DB_URL = getattr(settings, "integration_database_url", "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def pg_engine():
    """Create a PostgreSQL engine for integration tests."""
    engine = create_async_engine(
        INTEGRATION_DB_URL,
        pool_pre_ping=True,
        pool_recycle=300,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an integration test database session with real PostgreSQL."""
    async_session = sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_oauth():
    """Mock OAuth provider responses for integration tests."""
    oauth_responses = {
        "google": {
            "user_info": {
                "id": "google123",
                "email": "test@example.com",
                "name": "Test User",
                "picture": "https://example.com/avatar.jpg",
            },
            "token_info": {
                "access_token": "mock_google_token",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
        },
        "github": {
            "user_info": {
                "id": 12345,
                "login": "testuser",
                "email": "test@example.com",
                "name": "Test User",
                "avatar_url": "https://example.com/avatar.jpg",
            },
            "token_info": {
                "access_token": "mock_github_token",
                "token_type": "Bearer",
                "scope": "user:email",
            },
        },
        "twitter": {
            "user_info": {
                "id": "twitter123",
                "username": "testuser",
                "name": "Test User",
                "profile_image_url": "https://example.com/avatar.jpg",
            },
            "token_info": {
                "access_token": "mock_twitter_token",
                "token_type": "Bearer",
                "expires_in": 7200,
            },
        },
    }
    return oauth_responses


@pytest.fixture
def mock_llm():
    """Mock LLM service responses for integration tests."""

    def create_llm_result(
        title: str = "Test Article Title",
        summary: str = "This is a test summary of the article content.",
        tags: List[str] = None,
        success: bool = True,
        error_message: str = None,
        error_type: str = None,
    ) -> LLMResult:
        if tags is None:
            tags = ["test", "article", "technology"]

        return LLMResult(
            success=success,
            title=title if success else None,
            summary=summary if success else None,
            tags=tags if success else None,
            error_message=error_message,
            error_type=error_type,
        )

    mock_service = Mock()
    mock_service.process_content = AsyncMock(return_value=create_llm_result())

    # Add helper to create custom responses
    mock_service.create_result = create_llm_result

    with patch("services.llm_processor.LLMProcessorService", return_value=mock_service):
        yield mock_service


@pytest.fixture
def mock_fetch():
    """Mock HTTP fetch responses for integration tests."""

    mock_responses = {
        "https://example.com/article": {
            "status_code": 200,
            "headers": {"content-type": "text/html; charset=utf-8"},
            "content": """
            <html>
                <head><title>Test Article</title></head>
                <body>
                    <h1>Test Article</h1>
                    <p>This is a test article content for integration testing.</p>
                </body>
            </html>
            """,
        },
        "https://api.example.com/data": {
            "status_code": 200,
            "headers": {"content-type": "application/json"},
            "content": json.dumps({"data": "test", "status": "ok"}),
        },
        "https://example.com/error": {
            "status_code": 404,
            "headers": {"content-type": "text/plain"},
            "content": "Not found",
        },
    }

    async def mock_fetch_func(url: str, **kwargs) -> Dict[str, Any]:
        """Mock fetch function that returns predefined responses."""
        if url in mock_responses:
            response_data = mock_responses[url]
            return {
                "url": url,
                "status_code": response_data["status_code"],
                "headers": response_data["headers"],
                "content": response_data["content"],
                "success": response_data["status_code"] < 400,
            }
        else:
            return {
                "url": url,
                "status_code": 404,
                "headers": {"content-type": "text/plain"},
                "content": "URL not found in mock responses",
                "success": False,
            }

    # Mock both the URL fetcher service and any direct HTTP calls
    with patch("services.url_fetcher.URLFetcherService.fetch_url", side_effect=mock_fetch_func):
        with patch("httpx.AsyncClient.get") as mock_get:
            # Configure mock_get to return httpx.Response-like objects
            async def mock_httpx_get(url, **kwargs):
                response_data = mock_responses.get(url, mock_responses["https://example.com/error"])
                mock_response = Mock()
                mock_response.status_code = response_data["status_code"]
                mock_response.headers = response_data["headers"]
                mock_response.text = response_data["content"]
                mock_response.content = response_data["content"].encode() if isinstance(response_data["content"], str) else response_data["content"]
                return mock_response

            mock_get.side_effect = mock_httpx_get
            yield {
                "responses": mock_responses,
                "add_response": lambda url, **kwargs: mock_responses.update({url: kwargs}),
                "mock_fetch": mock_fetch_func,
            }


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for integration tests."""
    user = User(
        email="integrationtest@example.com",
        display_name="Integration Test User",
        avatar_url="https://example.com/integration-avatar.jpg",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(test_user: User) -> Dict[str, str]:
    """Create authentication headers for integration tests."""
    token_data = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "display_name": test_user.display_name,
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for integration tests with database override."""

    def get_test_db():
        return db_session

    app.dependency_overrides[get_db] = get_test_db

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client

    app.dependency_overrides.clear()