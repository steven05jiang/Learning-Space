"""
Integration tests for OAuth login flow to verify local user and account creation.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.account import Account
from models.database import get_db
from models.user import User
from services.auth import auth_service


@pytest.mark.integration
class TestOAuthIntegration:
    """Integration tests for OAuth authentication flow."""

    @pytest.fixture
    async def db_session(self) -> AsyncSession:
        """Get a real database session for testing."""
        async for session in get_db():
            yield session
            break

    async def test_oauth_authenticate_creates_user_and_account(
        self, db_session: AsyncSession
    ):
        """Test that OAuth authentication creates both user and account records."""
        # Test data from a hypothetical Google OAuth response
        provider = "google"
        provider_account_id = "google_user_123"
        access_token = "test_access_token"
        user_info = {
            "id": provider_account_id,
            "email": "testuser@example.com",
            "display_name": "Test User",
            "avatar_url": "https://example.com/avatar.jpg",
        }

        # Verify no user exists initially
        initial_user_query = select(User).where(User.email == user_info["email"])
        initial_result = await db_session.execute(initial_user_query)
        initial_user = initial_result.scalar_one_or_none()
        assert initial_user is None, "User should not exist before OAuth login"

        # Authenticate through OAuth service
        user, jwt_token = await auth_service.authenticate_oauth_user(
            db=db_session,
            provider=provider,
            provider_account_id=provider_account_id,
            access_token=access_token,
            user_info=user_info,
        )

        # Verify user was created
        assert user is not None
        assert user.email == user_info["email"]
        assert user.display_name == user_info["display_name"]
        assert user.avatar_url == user_info["avatar_url"]
        assert isinstance(user.id, int)

        # Verify JWT token is tied to local user ID
        assert jwt_token is not None
        from core.jwt import verify_token

        payload = verify_token(jwt_token)
        assert payload is not None
        assert payload["sub"] == str(user.id)
        assert payload["email"] == user.email

        # Verify account was created and linked
        account_query = (
            select(Account)
            .where(Account.provider == provider)
            .where(Account.provider_account_id == provider_account_id)
        )
        account_result = await db_session.execute(account_query)
        account = account_result.scalar_one_or_none()

        assert account is not None, "OAuth account should be created"
        assert account.user_id == user.id
        assert account.provider == provider
        assert account.provider_account_id == provider_account_id
        assert account.access_token == access_token

        # Verify user record exists in database
        user_query = (
            select(User).where(User.id == user.id).options(selectinload(User.accounts))
        )
        db_user_result = await db_session.execute(user_query)
        db_user = db_user_result.scalar_one_or_none()

        assert db_user is not None, "User should exist in database"
        assert len(db_user.accounts) == 1
        assert db_user.accounts[0].provider == provider

    async def test_oauth_subsequent_login_finds_existing_user(
        self, db_session: AsyncSession
    ):
        """Test subsequent OAuth login finds existing user (no duplicate)."""
        # Test data
        provider = "google"
        provider_account_id = "google_user_456"
        access_token = "first_access_token"
        user_info = {
            "id": provider_account_id,
            "email": "returning@example.com",
            "display_name": "Returning User",
            "avatar_url": "https://example.com/avatar2.jpg",
        }

        # First login - creates user
        first_user, first_token = await auth_service.authenticate_oauth_user(
            db=db_session,
            provider=provider,
            provider_account_id=provider_account_id,
            access_token=access_token,
            user_info=user_info,
        )

        # Second login - should find existing user
        new_access_token = "second_access_token"
        second_user, second_token = await auth_service.authenticate_oauth_user(
            db=db_session,
            provider=provider,
            provider_account_id=provider_account_id,
            access_token=new_access_token,
            user_info=user_info,
        )

        # Verify same user returned
        assert second_user.id == first_user.id
        assert second_user.email == first_user.email

        # Verify no duplicate users created
        user_count_query = select(User).where(User.email == user_info["email"])
        users_result = await db_session.execute(user_count_query)
        users = users_result.scalars().all()
        assert len(users) == 1, "Should not create duplicate users"

        # Verify account tokens were updated
        account_query = (
            select(Account)
            .where(Account.provider == provider)
            .where(Account.provider_account_id == provider_account_id)
        )
        account_result = await db_session.execute(account_query)
        account = account_result.scalar_one_or_none()
        assert account.access_token == new_access_token

    async def test_oauth_creates_linkable_foundation(self, db_session: AsyncSession):
        """Test OAuth login creates proper foundation for multi-provider linking."""
        # First provider login
        google_user, google_token = await auth_service.authenticate_oauth_user(
            db=db_session,
            provider="google",
            provider_account_id="google_789",
            access_token="google_token",
            user_info={
                "id": "google_789",
                "email": "multilink@example.com",
                "display_name": "Multi Link User",
            },
        )

        # Simulate linking a second provider to the same user
        await auth_service.link_oauth_account(
            db=db_session,
            current_user=google_user,
            provider="github",
            provider_account_id="github_789",
            access_token="github_token",
            user_info={
                "id": "github_789",
                "email": "multilink@github.com",
                "display_name": "Multi Link User",
            },
        )

        # Verify user now has both accounts
        user_query = (
            select(User)
            .where(User.id == google_user.id)
            .options(selectinload(User.accounts))
        )
        result = await db_session.execute(user_query)
        user = result.scalar_one_or_none()

        assert len(user.accounts) == 2
        providers = {account.provider for account in user.accounts}
        assert providers == {"google", "github"}

        # Verify both accounts point to the same user
        for account in user.accounts:
            assert account.user_id == google_user.id

    async def test_oauth_with_existing_email_links_account(
        self, db_session: AsyncSession
    ):
        """Test OAuth login when user exists with same email but different provider."""
        # Create a user with GitHub first
        github_user, github_token = await auth_service.authenticate_oauth_user(
            db=db_session,
            provider="github",
            provider_account_id="github_999",
            access_token="github_token",
            user_info={
                "id": "github_999",
                "email": "same@example.com",
                "display_name": "Same Email User",
            },
        )

        # Now login with Google using the same email
        google_user, google_token = await auth_service.authenticate_oauth_user(
            db=db_session,
            provider="google",
            provider_account_id="google_999",
            access_token="google_token",
            user_info={
                "id": "google_999",
                "email": "same@example.com",  # Same email
                "display_name": "Same Email User",
            },
        )

        # Should link to the same user, not create a duplicate
        assert google_user.id == github_user.id
        assert google_user.email == github_user.email

        # User should now have both accounts
        user_query = (
            select(User)
            .where(User.id == github_user.id)
            .options(selectinload(User.accounts))
        )
        result = await db_session.execute(user_query)
        user = result.scalar_one_or_none()

        assert len(user.accounts) == 2
        providers = {account.provider for account in user.accounts}
        assert providers == {"github", "google"}

        # Verify no duplicate users with same email
        email_query = select(User).where(User.email == "same@example.com")
        email_result = await db_session.execute(email_query)
        users_with_email = email_result.scalars().all()
        assert len(users_with_email) == 1
