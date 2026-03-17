from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app
from models.account import Account
from models.user import User
from services.auth import auth_service

client = TestClient(app)


@pytest.mark.asyncio
class TestAccountUnlinking:
    """Test OAuth account unlinking functionality."""

    async def test_unlink_oauth_account_success(self):
        """Test successful account unlinking when user has multiple accounts."""
        from sqlalchemy.ext.asyncio import AsyncSession

        # Create mock database session
        db = Mock(spec=AsyncSession)
        db.delete = AsyncMock()
        db.commit = AsyncMock()

        # Create test user with multiple accounts
        account1 = Account(
            id=1,
            user_id=123,
            provider="github",
            provider_account_id="github123",
            access_token="token1",
        )
        account2 = Account(
            id=2,
            user_id=123,
            provider="google",
            provider_account_id="google456",
            access_token="token2",
        )
        current_user = User(
            id=123,
            email="user@example.com",
            display_name="Test User",
            accounts=[account1, account2],
        )

        # Call unlink_oauth_account (should succeed since user has 2 accounts)
        await auth_service.unlink_oauth_account(
            db=db,
            current_user=current_user,
            account_id=1,
        )

        # Assertions
        db.delete.assert_called_once_with(account1)
        db.commit.assert_called_once()

    async def test_unlink_oauth_account_last_account_blocked(self):
        """Test unlinking fails when trying to unlink the last account."""
        from sqlalchemy.ext.asyncio import AsyncSession

        from core.errors import ErrorCode, ValidationError

        # Create mock database session
        db = Mock(spec=AsyncSession)

        # Create test user with only one account
        account1 = Account(
            id=1,
            user_id=123,
            provider="github",
            provider_account_id="github123",
            access_token="token1",
        )
        current_user = User(
            id=123,
            email="user@example.com",
            display_name="Test User",
            accounts=[account1],
        )

        # Should raise ValidationError with CANNOT_UNLINK_LAST_ACCOUNT code
        with pytest.raises(ValidationError) as exc_info:
            await auth_service.unlink_oauth_account(
                db=db,
                current_user=current_user,
                account_id=1,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.code == ErrorCode.CANNOT_UNLINK_LAST_ACCOUNT
        assert "Cannot unlink the last account" in str(exc_info.value.detail)

        # Database should not be modified
        db.delete.assert_not_called()
        db.commit.assert_not_called()

    async def test_unlink_oauth_account_not_found(self):
        """Test unlinking fails when account doesn't exist or doesn't belong to user."""
        from sqlalchemy.ext.asyncio import AsyncSession

        # Create mock database session
        db = Mock(spec=AsyncSession)

        # Create test user with accounts, but not the one we're trying to unlink
        account1 = Account(
            id=1,
            user_id=123,
            provider="github",
            provider_account_id="github123",
            access_token="token1",
        )
        account2 = Account(
            id=2,
            user_id=123,
            provider="google",
            provider_account_id="google456",
            access_token="token2",
        )
        current_user = User(
            id=123,
            email="user@example.com",
            display_name="Test User",
            accounts=[account1, account2],
        )

        # Try to unlink account ID 999 which doesn't exist
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.unlink_oauth_account(
                db=db,
                current_user=current_user,
                account_id=999,
            )

        assert exc_info.value.status_code == 404
        assert "Account not found or does not belong to current user" in str(
            exc_info.value.detail
        )

        # Database should not be modified
        db.delete.assert_not_called()
        db.commit.assert_not_called()

    async def test_unlink_oauth_account_empty_accounts(self):
        """Test unlinking fails when user has no accounts (edge case)."""
        from sqlalchemy.ext.asyncio import AsyncSession

        # Create mock database session
        db = Mock(spec=AsyncSession)

        # Create test user with no accounts
        current_user = User(
            id=123,
            email="user@example.com",
            display_name="Test User",
            accounts=[],
        )

        # Should raise HTTPException with 404 since account doesn't exist
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.unlink_oauth_account(
                db=db,
                current_user=current_user,
                account_id=1,
            )

        assert exc_info.value.status_code == 404
        assert "Account not found or does not belong to current user" in str(
            exc_info.value.detail
        )

        # Database should not be modified
        db.delete.assert_not_called()
        db.commit.assert_not_called()


class TestUnlinkAccountEndpoint:
    """Test the DELETE /auth/accounts/{account_id} endpoint."""

    def test_unlink_account_success(self):
        """Test successful account unlinking via endpoint."""
        from core.deps import get_current_user
        from models.database import get_db

        # Create test user with multiple accounts
        account1 = Account(
            id=1,
            user_id=123,
            provider="github",
            provider_account_id="github123",
            access_token="token1",
        )
        account2 = Account(
            id=2,
            user_id=123,
            provider="google",
            provider_account_id="google456",
            access_token="token2",
        )
        test_user = User(
            id=123,
            email="test@example.com",
            display_name="Test User",
            accounts=[account1, account2],
        )

        # Mock database session
        async def mock_get_db():
            mock_db = Mock()
            mock_db.delete = AsyncMock()
            mock_db.commit = AsyncMock()
            return mock_db

        # Override authentication dependency
        def get_test_user():
            return test_user

        app.dependency_overrides[get_current_user] = get_test_user
        app.dependency_overrides[get_db] = mock_get_db

        try:
            response = client.delete("/auth/accounts/1")
            assert response.status_code == 204

        finally:
            app.dependency_overrides.clear()

    def test_unlink_account_last_account(self):
        """Test unlinking last account returns 400."""
        from core.deps import get_current_user
        from models.database import get_db

        # Create test user with only one account
        account1 = Account(
            id=1,
            user_id=123,
            provider="github",
            provider_account_id="github123",
            access_token="token1",
        )
        test_user = User(
            id=123,
            email="test@example.com",
            display_name="Test User",
            accounts=[account1],
        )

        # Mock database session (shouldn't be used)
        async def mock_get_db():
            mock_db = Mock()
            return mock_db

        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_db] = mock_get_db

        try:
            response = client.delete("/auth/accounts/1")
            assert response.status_code == 400

            data = response.json()
            assert data["code"] == "CANNOT_UNLINK_LAST_ACCOUNT"
            assert "Cannot unlink the last account" in data["detail"]

        finally:
            app.dependency_overrides.clear()

    def test_unlink_account_not_found(self):
        """Test unlinking non-existent account returns 404."""
        from core.deps import get_current_user
        from models.database import get_db

        # Create test user with accounts, but not the one we're trying to unlink
        account1 = Account(
            id=1,
            user_id=123,
            provider="github",
            provider_account_id="github123",
            access_token="token1",
        )
        account2 = Account(
            id=2,
            user_id=123,
            provider="google",
            provider_account_id="google456",
            access_token="token2",
        )
        test_user = User(
            id=123,
            email="test@example.com",
            display_name="Test User",
            accounts=[account1, account2],
        )

        # Mock database session (shouldn't be used)
        async def mock_get_db():
            mock_db = Mock()
            return mock_db

        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_db] = mock_get_db

        try:
            # Try to unlink account ID 999 which doesn't exist
            response = client.delete("/auth/accounts/999")
            assert response.status_code == 404

            data = response.json()
            assert "Account not found or does not belong to current user" in data["detail"]

        finally:
            app.dependency_overrides.clear()

    def test_unlink_account_unauthenticated(self):
        """Test unlinking account without authentication returns 401."""
        response = client.delete("/auth/accounts/1")
        assert response.status_code == 401

    def test_unlink_account_invalid_account_id(self):
        """Test unlinking with invalid account ID format returns 422."""
        from core.deps import get_current_user

        # Create test user
        test_user = User(
            id=123,
            email="test@example.com",
            display_name="Test User",
        )

        app.dependency_overrides[get_current_user] = lambda: test_user

        try:
            # Try with non-integer account ID
            response = client.delete("/auth/accounts/invalid")
            assert response.status_code == 422

        finally:
            app.dependency_overrides.clear()