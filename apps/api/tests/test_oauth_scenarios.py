"""
Tests for OAuth authentication scenarios including email collision handling.
"""

from unittest.mock import AsyncMock

import pytest

from models.account import Account
from models.user import User
from services.auth import auth_service


class TestOAuthScenarios:
    """Test OAuth authentication edge cases."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_oauth_with_existing_email_links_account(self, mock_db):
        """Test OAuth login when user exists with same email but no provider account."""
        # Existing user with email but no Google account
        existing_user = User(
            id=1,
            email="user@example.com",
            display_name="Existing User",
            accounts=[],  # No accounts linked yet
        )

        # Mock database queries
        auth_service.find_user_by_provider_account = AsyncMock(return_value=None)
        auth_service.find_user_by_email = AsyncMock(return_value=existing_user)

        # OAuth user info
        provider = "google"
        provider_account_id = "google_123"
        access_token = "test_token"
        user_info = {
            "id": provider_account_id,
            "email": "user@example.com",  # Same email as existing user
            "display_name": "User Name",
        }

        # Test OAuth authentication
        user, jwt_token = await auth_service.authenticate_oauth_user(
            db=mock_db,
            provider=provider,
            provider_account_id=provider_account_id,
            access_token=access_token,
            user_info=user_info,
        )

        # Verify the existing user is returned (not a new user created)
        assert user.id == existing_user.id
        assert user.email == existing_user.email

        # Verify account was added to database
        mock_db.add.assert_called_once()
        added_account = mock_db.add.call_args[0][0]
        assert isinstance(added_account, Account)
        assert added_account.user_id == existing_user.id
        assert added_account.provider == provider
        assert added_account.provider_account_id == provider_account_id

        # Verify database operations
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(existing_user, ["accounts"])

        # Verify JWT token generated
        assert jwt_token is not None

    @pytest.mark.asyncio
    async def test_oauth_returning_user_updates_tokens(self, mock_db):
        """Test OAuth login for returning user (provider account already linked)."""
        # Existing user with Google account already linked
        existing_account = Account(
            id=1,
            user_id=1,
            provider="google",
            provider_account_id="google_123",
            access_token="old_token",
        )

        existing_user = User(
            id=1,
            email="user@example.com",
            display_name="Returning User",
            accounts=[existing_account],
        )

        # Mock finding existing user by provider account
        auth_service.find_user_by_provider_account = AsyncMock(
            return_value=existing_user
        )
        auth_service.update_account_tokens = AsyncMock()

        # OAuth login data
        provider = "google"
        provider_account_id = "google_123"
        new_access_token = "new_token"
        user_info = {
            "id": provider_account_id,
            "email": "user@example.com",
            "display_name": "Returning User",
        }

        # Test OAuth authentication
        user, jwt_token = await auth_service.authenticate_oauth_user(
            db=mock_db,
            provider=provider,
            provider_account_id=provider_account_id,
            access_token=new_access_token,
            user_info=user_info,
        )

        # Verify same user returned
        assert user.id == existing_user.id

        # Verify tokens were updated
        auth_service.update_account_tokens.assert_called_once_with(
            mock_db,
            existing_user,
            provider,
            new_access_token,
            None,
            username=None,
        )

        # Verify JWT token generated
        assert jwt_token is not None

    @pytest.mark.asyncio
    async def test_oauth_new_user_creates_both_records(self, mock_db):
        """Test OAuth login for completely new user (no existing email)."""
        # No existing user found by provider account or email
        auth_service.find_user_by_provider_account = AsyncMock(return_value=None)
        auth_service.find_user_by_email = AsyncMock(return_value=None)

        # Mock user creation
        new_user = User(
            id=2,
            email="newuser@example.com",
            display_name="New User",
        )
        auth_service.create_user_with_account = AsyncMock(return_value=new_user)

        # OAuth login data
        provider = "google"
        provider_account_id = "google_456"
        access_token = "new_user_token"
        user_info = {
            "id": provider_account_id,
            "email": "newuser@example.com",
            "display_name": "New User",
        }

        # Test OAuth authentication
        user, jwt_token = await auth_service.authenticate_oauth_user(
            db=mock_db,
            provider=provider,
            provider_account_id=provider_account_id,
            access_token=access_token,
            user_info=user_info,
        )

        # Verify new user created
        auth_service.create_user_with_account.assert_called_once_with(
            mock_db,
            provider,
            provider_account_id,
            access_token,
            user_info,
            None,
        )

        # Verify user and token returned
        assert user == new_user
        assert jwt_token is not None
