import os
import pytest
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from models.database import Base
from models.user import User
from models.account import Account
from core.jwt import create_access_token


@pytest.fixture(scope="session")
async def pg_engine():
    """Real PostgreSQL engine. Schema created once per session."""
    engine = create_async_engine(os.environ["TEST_DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(pg_engine):
    """Transactional session rolled back after each test — no cleanup needed."""
    async with pg_engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn)
        yield session
        await session.rollback()


@pytest.fixture
def mock_oauth(respx_mock):
    """Activates all OAuth provider mocks for the duration of a test."""
    from tests.mocks.oauth_mock import setup_twitter_oauth_mock, setup_google_oauth_mock
    setup_twitter_oauth_mock(respx_mock)
    setup_google_oauth_mock(respx_mock)
    return respx_mock


@pytest.fixture
def mock_llm():
    """Replaces the LLM client with MockLLMClient."""
    from tests.mocks.llm_mock import MockLLMClient
    with patch("services.llm_processor.get_llm_client", return_value=MockLLMClient()):
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
        user_id=user.id, provider="twitter",
        provider_account_id="twitter-123", access_token="mock-token"
    )
    db_session.add(account)
    await db_session.flush()
    return user


@pytest.fixture
async def auth_headers(test_user) -> dict:
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}