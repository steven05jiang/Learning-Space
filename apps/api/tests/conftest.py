import asyncio
from typing import AsyncGenerator, Generator

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.jwt import create_access_token
from main import app
from models.database import Base, get_db
from models.user import User
from models.category import Category

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Seed system categories
        system_categories = [
            "Technology",
            "Science",
            "Business",
            "Arts",
            "Health",
            "Education",
            "Politics",
            "Entertainment",
            "Sports",
            "Philosophy",
        ]

        for category_name in system_categories:
            category = Category(name=category_name, is_system=True, owner_id=None)
            session.add(category)

        await session.commit()
        yield session

    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database override."""

    def get_test_db():
        return db_session

    app.dependency_overrides[get_db] = get_test_db

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        email="test@example.com",
        display_name="Test User",
        avatar_url="https://example.com/avatar.jpg",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(test_user: User) -> dict:
    """Create authentication headers with a valid JWT token."""
    token_data = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "display_name": test_user.display_name,
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}
