from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from core.jwt import create_access_token
from models.user import User


class TestGetCurrentUser:
    """Test the get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self):
        """Test that a valid token returns the correct user."""
        # Create a test user
        test_user = User(
            id=123,
            email="test@example.com",
            display_name="Test User",
            avatar_url="https://example.com/avatar.jpg",
        )

        # Mock database session and query
        mock_db = AsyncMock(spec=AsyncSession)

        class MockResult:
            def scalar_one_or_none(self):
                return test_user

        mock_db.execute.return_value = MockResult()

        # Create a valid JWT token
        token_data = {
            "sub": str(test_user.id),
            "email": test_user.email,
            "display_name": test_user.display_name,
        }
        token = create_access_token(token_data)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Call the dependency
        user = await get_current_user(credentials, mock_db)

        # Verify the returned user
        assert user.id == test_user.id
        assert user.email == test_user.email
        assert user.display_name == test_user.display_name

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        """Test that an invalid token raises HTTPException with 401."""
        mock_db = AsyncMock(spec=AsyncSession)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid_token"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_db)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in str(exc_info.value.detail)
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    @pytest.mark.asyncio
    async def test_token_without_sub_raises_401(self):
        """Test that a token without 'sub' field raises HTTPException with 401."""
        mock_db = AsyncMock(spec=AsyncSession)

        token_data = {
            "email": "test@example.com",
            "display_name": "Test User",
            # Missing 'sub' field
        }
        token = create_access_token(token_data)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_db)

        assert exc_info.value.status_code == 401
        assert "Invalid token payload" in str(exc_info.value.detail)
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    @pytest.mark.asyncio
    async def test_nonexistent_user_raises_401(self):
        """Test that a token for a nonexistent user raises HTTPException with 401."""
        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock database query returning None (user not found)
        class MockResult:
            def scalar_one_or_none(self):
                return None

        mock_db.execute.return_value = MockResult()

        token_data = {
            "sub": "99999",  # Non-existent user ID
            "email": "nonexistent@example.com",
            "display_name": "Nonexistent User",
        }
        token = create_access_token(token_data)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_db)

        assert exc_info.value.status_code == 401
        assert "User not found" in str(exc_info.value.detail)
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    @pytest.mark.asyncio
    async def test_invalid_user_id_format_raises_401(self):
        """Test that a token with invalid user ID format raises HTTPException."""
        mock_db = AsyncMock(spec=AsyncSession)

        token_data = {
            "sub": "not_a_number",  # Invalid user ID format
            "email": "test@example.com",
            "display_name": "Test User",
        }
        token = create_access_token(token_data)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_db)

        assert exc_info.value.status_code == 401
        assert "Invalid user ID in token" in str(exc_info.value.detail)
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    @pytest.mark.asyncio
    async def test_database_error_raises_401(self):
        """Test that database errors raise HTTPException with 401."""
        # Mock database session that raises an exception
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.side_effect = Exception("Database error")

        token_data = {
            "sub": "123",
            "email": "test@example.com",
            "display_name": "Test User",
        }
        token = create_access_token(token_data)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_db)

        assert exc_info.value.status_code == 401
        assert "Authentication failed" in str(exc_info.value.detail)
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
