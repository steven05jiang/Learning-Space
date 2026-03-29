import os
from typing import AsyncGenerator
from unittest.mock import patch

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.jwt import create_access_token
from main import app
from models.account import Account
from models.database import get_db
from models.user import User

# Tables to truncate between tests (dependency order: children first)
_TRUNCATE_TABLES = "accounts, messages, conversations, resources, users"


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Per-test database session using real PostgreSQL.

    Creates a fresh engine and session per test. After each test all rows
    are deleted so the next test starts with a clean slate. Schema is
    assumed to exist (created by `alembic upgrade head` in CI / make infra-up
    locally before running integration tests).
    """
    engine = create_async_engine(os.environ["TEST_DATABASE_URL"])
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        yield session

    # Delete all rows after each test (CASCADE handles FK order)
    async with engine.begin() as conn:
        await conn.execute(
            text(f"TRUNCATE {_TRUNCATE_TABLES} RESTART IDENTITY CASCADE")
        )

    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client that shares the test database session."""

    async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = get_test_db

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def mock_oauth(respx_mock):
    """Activates all OAuth provider mocks for the duration of a test."""
    from tests.mocks.oauth_mock import setup_google_oauth_mock, setup_twitter_oauth_mock

    setup_twitter_oauth_mock(respx_mock)
    setup_google_oauth_mock(respx_mock)
    return respx_mock


@pytest.fixture
def mock_llm():
    """Replaces the LLM client with MockLLMClient."""
    from tests.mocks.llm_mock import MockLLMClient

    with patch("services.llm_processor.Anthropic", return_value=MockLLMClient()):
        yield


@pytest.fixture
def mock_fetch(respx_mock):
    """Default: all external URL fetches return a mock HTML page."""
    from tests.mocks.provider_fetch_mock import setup_fetch_success

    setup_fetch_success(respx_mock, url="https://example.com/article")
    return respx_mock


@pytest.fixture
async def test_user(db_session):
    user = User(display_name="Test User", email="test@example.com")
    db_session.add(user)
    await db_session.flush()
    account = Account(
        user_id=user.id,
        provider="twitter",
        provider_account_id="twitter-123",
        access_token="mock-token",
    )
    db_session.add(account)
    await db_session.flush()
    return user


@pytest.fixture
async def auth_headers(test_user) -> dict:
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}
