from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from core.jwt import create_access_token, verify_token
from main import app
from models.user import User
from services.auth import auth_service
from services.oauth import oauth_service

client = TestClient(app)


class TestJWTUtilities:
    """Test JWT token creation and verification."""

    def test_create_and_verify_token(self):
        """Test token creation and verification cycle."""
        # Create test data
        test_data = {"sub": "123", "email": "test@example.com"}

        # Create token
        token = create_access_token(test_data)
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert "exp" in payload

    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)
        assert payload is None


class TestOAuthService:
    """Test OAuth service functionality."""

    def test_get_supported_providers(self):
        """Test getting supported providers."""
        providers = oauth_service.get_supported_providers()
        expected = ["github", "google", "twitter"]
        assert set(providers) == set(expected)

    def test_get_provider(self):
        """Test getting specific OAuth provider."""
        github_provider = oauth_service.get_provider("github")
        assert github_provider is not None

        google_provider = oauth_service.get_provider("google")
        assert google_provider is not None

        invalid_provider = oauth_service.get_provider("invalid")
        assert invalid_provider is None

    @pytest.mark.asyncio
    async def test_github_authorization_url(self):
        """Test GitHub authorization URL generation."""
        provider = oauth_service.get_provider("github")
        redirect_uri = "http://localhost:8000/auth/callback/github"

        auth_url = await provider.get_authorization_url(redirect_uri)
        assert "github.com/login/oauth/authorize" in auth_url
        assert "client_id=" in auth_url
        assert "redirect_uri=" in auth_url
        assert "scope=user%3Aemail" in auth_url

    @pytest.mark.asyncio
    async def test_google_authorization_url(self):
        """Test Google authorization URL generation."""
        provider = oauth_service.get_provider("google")
        redirect_uri = "http://localhost:8000/auth/callback/google"

        auth_url = await provider.get_authorization_url(redirect_uri)
        assert "accounts.google.com/o/oauth2/auth" in auth_url
        assert "client_id=" in auth_url
        assert "redirect_uri=" in auth_url
        assert "scope=openid+email+profile" in auth_url


@pytest.mark.asyncio
class TestAuthService:
    """Test authentication service functionality."""

    async def test_generate_jwt_token(self):
        """Test JWT token generation for user."""
        # Create test user
        user = User(
            id=123,
            email="test@example.com",
            display_name="Test User"
        )

        # Generate token
        token = auth_service.generate_jwt_token(user)
        assert isinstance(token, str)

        # Verify token content
        payload = verify_token(token)
        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["display_name"] == "Test User"


def test_get_supported_providers():
    """Test getting supported OAuth providers."""
    response = client.get("/auth/providers")
    assert response.status_code == 200

    data = response.json()
    assert "providers" in data
    providers = data["providers"]
    expected = ["github", "google", "twitter"]
    assert set(providers) == set(expected)


def test_oauth_login_github():
    """Test initiating GitHub OAuth login."""
    response = client.get("/auth/login/github")
    assert response.status_code == 200

    data = response.json()
    assert "authorization_url" in data
    assert "provider" in data
    assert data["provider"] == "github"
    assert "github.com/login/oauth/authorize" in data["authorization_url"]


def test_oauth_login_google():
    """Test initiating Google OAuth login."""
    response = client.get("/auth/login/google")
    assert response.status_code == 200

    data = response.json()
    assert "authorization_url" in data
    assert "provider" in data
    assert data["provider"] == "google"
    assert "accounts.google.com/o/oauth2/auth" in data["authorization_url"]


def test_oauth_login_invalid_provider():
    """Test OAuth login with invalid provider."""
    response = client.get("/auth/login/invalid")
    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
    assert "Unsupported OAuth provider" in data["detail"]


@pytest.mark.skip(reason="Integration test - requires database and mocking setup")
@patch('services.oauth.GitHubOAuthProvider.exchange_code')
@patch('services.oauth.GitHubOAuthProvider.get_user_info')
def test_oauth_callback_success(
    mock_get_user_info: AsyncMock,
    mock_exchange_code: AsyncMock
):
    """Test successful OAuth callback."""
    # Mock OAuth provider responses
    mock_exchange_code.return_value = "test_access_token"
    mock_get_user_info.return_value = {
        "id": "123456",
        "email": "testuser@example.com",
        "display_name": "Test User",
        "avatar_url": "https://example.com/avatar.jpg"
    }

    # Test callback
    response = client.get("/auth/callback/github?code=test_code")
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "testuser@example.com"


def test_oauth_callback_missing_code():
    """Test OAuth callback without code parameter."""
    response = client.get("/auth/callback/github")
    assert response.status_code == 422  # FastAPI validation error


def test_oauth_callback_invalid_provider():
    """Test OAuth callback with invalid provider."""
    response = client.get("/auth/callback/invalid?code=test_code")
    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
    assert "Unsupported OAuth provider" in data["detail"]
