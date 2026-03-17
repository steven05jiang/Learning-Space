from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app
from models.user import User
from services.auth import auth_service
from services.oauth import oauth_service

client = TestClient(app)


@pytest.mark.asyncio
class TestAccountLinking:
    """Test OAuth account linking functionality."""

    async def test_link_oauth_account_success(self):
        """Test successful account linking."""
        from unittest.mock import Mock

        from sqlalchemy.ext.asyncio import AsyncSession

        # Create mock database session
        db = Mock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        # Create test user
        current_user = User(
            id=123,
            email="user@example.com",
            display_name="Test User",
            accounts=[],  # No existing accounts
        )

        # Mock find_user_by_provider_account to return None (account not linked)
        auth_service.find_user_by_provider_account = AsyncMock(return_value=None)

        user_info = {
            "id": "github123",
            "email": "user@github.com",
            "display_name": "GitHub User",
            "avatar_url": "https://github.com/avatar.jpg",
        }

        # Call link_oauth_account
        result = await auth_service.link_oauth_account(
            db=db,
            current_user=current_user,
            provider="github",
            provider_account_id="github123",
            access_token="test_token",
            user_info=user_info,
        )

        # Assertions
        assert result == current_user
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    async def test_link_oauth_account_already_linked_to_other_user(self):
        """Test linking account that belongs to another user returns 409."""
        from unittest.mock import Mock

        from sqlalchemy.ext.asyncio import AsyncSession

        # Create mock database session
        db = Mock(spec=AsyncSession)

        # Create test users
        current_user = User(id=123, email="user@example.com", display_name="Test User")
        other_user = User(id=456, email="other@example.com", display_name="Other User")

        # Mock find_user_by_provider_account to return other user
        auth_service.find_user_by_provider_account = AsyncMock(return_value=other_user)

        user_info = {
            "id": "github123",
            "email": "user@github.com",
            "display_name": "GitHub User",
        }

        # Should raise HTTPException with 409
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.link_oauth_account(
                db=db,
                current_user=current_user,
                provider="github",
                provider_account_id="github123",
                access_token="test_token",
                user_info=user_info,
            )

        assert exc_info.value.status_code == 409
        assert "already linked to another user" in str(exc_info.value.detail)

    async def test_link_oauth_account_already_linked_to_same_user(self):
        """Test linking account that already belongs to current user updates tokens."""
        from unittest.mock import Mock

        from sqlalchemy.ext.asyncio import AsyncSession

        # Create mock database session
        db = Mock(spec=AsyncSession)
        db.refresh = AsyncMock()

        # Create test user
        current_user = User(
            id=123,
            email="user@example.com",
            display_name="Test User",
            accounts=[],
        )

        # Mock find_user_by_provider_account to return current user
        auth_service.find_user_by_provider_account = AsyncMock(
            return_value=current_user
        )
        auth_service.update_account_tokens = AsyncMock()

        user_info = {
            "id": "github123",
            "email": "user@github.com",
            "display_name": "GitHub User",
        }

        # Call link_oauth_account
        result = await auth_service.link_oauth_account(
            db=db,
            current_user=current_user,
            provider="github",
            provider_account_id="github123",
            access_token="test_token",
            user_info=user_info,
        )

        # Should update tokens instead of creating new account
        auth_service.update_account_tokens.assert_called_once()
        assert result == current_user


class TestOAuthLinkEndpoint:
    """Test the OAuth link endpoint."""

    def test_oauth_link_github_authenticated(self):
        """Test initiating GitHub OAuth link with authentication."""
        from core.deps import get_current_user

        # Create test user
        test_user = User(
            id=123,
            email="test@example.com",
            display_name="Test User",
            avatar_url="https://example.com/avatar.jpg",
        )

        # Override authentication dependency
        def get_test_user():
            return test_user

        app.dependency_overrides[get_current_user] = get_test_user

        try:
            response = client.get("/auth/link/github")
            assert response.status_code == 200

            data = response.json()
            assert "authorization_url" in data
            assert "provider" in data
            assert "state" in data
            assert data["provider"] == "github"
            assert "github.com/login/oauth/authorize" in data["authorization_url"]
            assert "state=" in data["authorization_url"]

            # State should contain link prefix
            state = data["state"]
            assert state.startswith("link:123:")

        finally:
            app.dependency_overrides.clear()

    def test_oauth_link_unauthenticated(self):
        """Test OAuth link without authentication returns 401."""
        response = client.get("/auth/link/github")
        assert response.status_code == 401

    def test_oauth_link_invalid_provider(self):
        """Test OAuth link with invalid provider."""
        from core.deps import get_current_user

        # Create test user
        test_user = User(
            id=123,
            email="test@example.com",
            display_name="Test User",
        )

        app.dependency_overrides[get_current_user] = lambda: test_user

        try:
            response = client.get("/auth/link/invalid_provider")
            assert response.status_code == 400

            data = response.json()
            assert "detail" in data
            assert "Unsupported OAuth provider" in data["detail"]

        finally:
            app.dependency_overrides.clear()


class TestOAuthService:
    """Test OAuth service link state functionality."""

    def test_generate_link_state(self):
        """Test link state generation."""
        user_id = 123
        state = oauth_service.generate_link_state(user_id)

        # Should start with link prefix and contain user ID
        assert state.startswith("link:123:")
        assert len(state) > len("link:123:")

    def test_store_and_validate_link_state(self):
        """Test storing and validating link state."""
        user_id = 123
        provider = "github"
        state = oauth_service.generate_link_state(user_id)

        # Store the state
        oauth_service.store_link_state(state, provider, user_id)

        # Validate that it's a link state
        assert oauth_service.is_link_state(state)
        assert oauth_service.get_link_user_id(state) == user_id

        # Validate and consume state
        assert oauth_service.validate_and_consume_state(state, provider)

        # State should be consumed (one-time use)
        assert not oauth_service.is_link_state(state)
        assert oauth_service.get_link_user_id(state) is None

    def test_regular_state_not_link_state(self):
        """Test that regular states are not detected as link states."""
        provider = "github"
        state = oauth_service.generate_state()

        oauth_service.store_state(state, provider)

        # Should not be detected as link state
        assert not oauth_service.is_link_state(state)
        assert oauth_service.get_link_user_id(state) is None


@patch("services.auth.auth_service.link_oauth_account")
@patch("services.oauth.GitHubOAuthProvider.exchange_code")
@patch("services.oauth.GitHubOAuthProvider.get_user_info")
@pytest.mark.asyncio
async def test_oauth_callback_link_flow(
    mock_get_user_info: AsyncMock,
    mock_exchange_code: AsyncMock,
    mock_link_account: AsyncMock,
):
    """Test OAuth callback with link flow."""
    from unittest.mock import Mock

    from sqlalchemy.ext.asyncio import AsyncSession

    from core.deps import get_current_user_optional
    from models.database import get_db

    # Mock user for return value
    mock_user = User(
        id=123,
        email="testuser@example.com",
        display_name="Test User",
        avatar_url="https://example.com/avatar.jpg",
    )

    # Mock database session
    async def mock_get_db():
        mock_db = Mock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        return mock_db

    # Mock authenticated user for link flow
    async def mock_get_current_user_optional():
        return mock_user

    # Override dependencies
    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_current_user_optional] = mock_get_current_user_optional

    try:
        # Mock OAuth provider responses
        mock_exchange_code.return_value = "test_access_token"
        mock_get_user_info.return_value = {
            "id": "123456",
            "email": "testuser@github.com",
            "display_name": "Test User",
            "avatar_url": "https://example.com/avatar.jpg",
        }

        # Mock link account response
        mock_link_account.return_value = mock_user

        # Set up link state in OAuth service
        link_state = oauth_service.generate_link_state(123)
        oauth_service.store_link_state(link_state, "github", 123)

        # Test callback with link state
        response = client.get(
            f"/auth/callback/github?code=test_code&state={link_state}"
        )
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "linked successfully" in data["message"]
        assert "user" in data
        assert data["user"]["email"] == "testuser@example.com"

        # Should not contain access_token (unlike login flow)
        assert "access_token" not in data

    finally:
        app.dependency_overrides.clear()


@patch("services.oauth.GitHubOAuthProvider.exchange_code")
@patch("services.oauth.GitHubOAuthProvider.get_user_info")
@pytest.mark.asyncio
async def test_oauth_callback_link_flow_unauthenticated_blocked(
    mock_get_user_info: AsyncMock,
    mock_exchange_code: AsyncMock,
):
    """Test OAuth callback with link flow blocks unauthenticated requests."""
    from unittest.mock import Mock

    from sqlalchemy.ext.asyncio import AsyncSession

    from core.deps import get_current_user_optional
    from models.database import get_db

    # Mock user for return value
    mock_user = User(
        id=123,
        email="testuser@example.com",
        display_name="Test User",
        avatar_url="https://example.com/avatar.jpg",
    )

    # Mock database session
    async def mock_get_db():
        mock_db = Mock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        return mock_db

    # Mock unauthenticated user for link flow (should be blocked)
    async def mock_get_current_user_optional():
        return None  # No authentication

    # Override dependencies
    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_current_user_optional] = mock_get_current_user_optional

    try:
        # Mock OAuth provider responses
        mock_exchange_code.return_value = "test_access_token"
        mock_get_user_info.return_value = {
            "id": "123456",
            "email": "testuser@github.com",
            "display_name": "Test User",
            "avatar_url": "https://example.com/avatar.jpg",
        }

        # Set up link state in OAuth service
        link_state = oauth_service.generate_link_state(123)
        oauth_service.store_link_state(link_state, "github", 123)

        # Test callback with link state but no authentication - should be blocked
        response = client.get(
            f"/auth/callback/github?code=test_code&state={link_state}"
        )
        assert response.status_code == 401

        data = response.json()
        assert data["code"] == "AUTHENTICATION_REQUIRED"
        assert "Authentication required for account linking" in data["detail"]

    finally:
        app.dependency_overrides.clear()


@patch("services.oauth.GitHubOAuthProvider.exchange_code")
@patch("services.oauth.GitHubOAuthProvider.get_user_info")
@pytest.mark.asyncio
async def test_oauth_callback_link_flow_mismatched_user_blocked(
    mock_get_user_info: AsyncMock,
    mock_exchange_code: AsyncMock,
):
    """Test OAuth callback blocks when authenticated user doesn't match link state."""
    from unittest.mock import Mock

    from sqlalchemy.ext.asyncio import AsyncSession

    from core.deps import get_current_user_optional
    from models.database import get_db

    # Mock user for return value - different from the one in link state
    mock_user = User(
        id=456,  # Different ID from link state (123)
        email="different@example.com",
        display_name="Different User",
        avatar_url="https://example.com/avatar.jpg",
    )

    # Mock database session
    async def mock_get_db():
        mock_db = Mock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        return mock_db

    # Mock authenticated user (different from link state user)
    async def mock_get_current_user_optional():
        return mock_user

    # Override dependencies
    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_current_user_optional] = mock_get_current_user_optional

    try:
        # Mock OAuth provider responses
        mock_exchange_code.return_value = "test_access_token"
        mock_get_user_info.return_value = {
            "id": "123456",
            "email": "testuser@github.com",
            "display_name": "Test User",
            "avatar_url": "https://example.com/avatar.jpg",
        }

        # Set up link state for different user (123, not 456)
        link_state = oauth_service.generate_link_state(123)
        oauth_service.store_link_state(link_state, "github", 123)

        # Test callback with link state for user 123 but authenticated as user 456
        response = client.get(
            f"/auth/callback/github?code=test_code&state={link_state}"
        )
        assert response.status_code == 403

        data = response.json()
        assert data["code"] == "FORBIDDEN"
        assert "Link state does not match authenticated user" in data["detail"]

    finally:
        app.dependency_overrides.clear()


@patch("services.auth.auth_service.authenticate_oauth_user")
@patch("services.oauth.GitHubOAuthProvider.exchange_code")
@patch("services.oauth.GitHubOAuthProvider.get_user_info")
@pytest.mark.asyncio
async def test_oauth_callback_regular_login_flow(
    mock_get_user_info: AsyncMock,
    mock_exchange_code: AsyncMock,
    mock_authenticate: AsyncMock,
):
    """Test OAuth callback with regular login flow (not link)."""
    # Mock user for return value
    mock_user = User(
        id=123,
        email="testuser@example.com",
        display_name="Test User",
        avatar_url="https://example.com/avatar.jpg",
    )

    # Mock OAuth provider responses
    mock_exchange_code.return_value = "test_access_token"
    mock_get_user_info.return_value = {
        "id": "123456",
        "email": "testuser@github.com",
        "display_name": "Test User",
        "avatar_url": "https://example.com/avatar.jpg",
    }

    # Mock auth service response
    mock_authenticate.return_value = (mock_user, "mock_jwt_token")

    # Set up regular state (not link state)
    regular_state = oauth_service.generate_state()
    oauth_service.store_state(regular_state, "github")

    # Test callback with regular state
    response = client.get(f"/auth/callback/github?code=test_code&state={regular_state}")
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "testuser@example.com"

    # Should not contain link message
    assert "message" not in data
