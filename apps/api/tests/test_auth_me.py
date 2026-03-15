from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from core.deps import get_current_user
from core.jwt import create_access_token
from main import app
from models.account import Account
from models.user import User

client = TestClient(app)


class TestAuthMeEndpoint:
    """Test the GET /auth/me endpoint."""

    def test_me_endpoint_requires_authentication(self):
        """Test that /auth/me requires authentication."""
        response = client.get("/auth/me")
        assert response.status_code == 401  # Our custom HTTPBearer returns 401 when no auth header

    def test_me_endpoint_invalid_token(self):
        """Test /auth/me with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401

    def test_me_endpoint_success(self):
        """Test successful /auth/me request."""
        # Create test user and account
        test_user = User(
            id=123,
            email="test@example.com",
            display_name="Test User",
            avatar_url="https://example.com/avatar.jpg",
            created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        )

        test_account = Account(
            id=1,
            user_id=123,
            provider="github",
            provider_account_id="github123",
            last_login_at=datetime(2023, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        )

        # Set up relationship
        test_user.accounts = [test_account]
        test_account.user = test_user

        # Override the get_current_user dependency
        def get_test_user():
            return test_user

        app.dependency_overrides[get_current_user] = get_test_user

        try:
            # Create valid JWT token (not actually used due to override, but needed for auth header)
            token_data = {
                "sub": str(test_user.id),
                "email": test_user.email,
                "display_name": test_user.display_name
            }
            token = create_access_token(token_data)

            # Make authenticated request
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/auth/me", headers=headers)

            # Verify response
            assert response.status_code == 200
            data = response.json()

            assert data["id"] == 123
            assert data["email"] == "test@example.com"
            assert data["display_name"] == "Test User"
            assert data["avatar_url"] == "https://example.com/avatar.jpg"
            assert data["created_at"] == "2023-01-01T12:00:00+00:00"

            assert len(data["providers"]) == 1
            provider = data["providers"][0]
            assert provider["provider"] == "github"
            assert provider["last_login_at"] == "2023-06-01T12:00:00+00:00"

        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    def test_me_endpoint_multiple_providers(self):
        """Test /auth/me with multiple linked providers."""
        # Create test user with multiple accounts
        test_user = User(
            id=456,
            email="multi@example.com",
            display_name="Multi User",
            created_at=datetime(2023, 1, 1, tzinfo=timezone.utc)
        )

        github_account = Account(
            id=1,
            user_id=456,
            provider="github",
            provider_account_id="github456",
            last_login_at=datetime(2023, 6, 1, tzinfo=timezone.utc)
        )

        google_account = Account(
            id=2,
            user_id=456,
            provider="google",
            provider_account_id="google456",
            last_login_at=datetime(2023, 7, 1, tzinfo=timezone.utc)
        )

        test_user.accounts = [github_account, google_account]

        # Override the get_current_user dependency
        def get_test_user():
            return test_user

        app.dependency_overrides[get_current_user] = get_test_user

        try:
            # Create valid JWT token
            token_data = {"sub": "456", "email": "multi@example.com"}
            token = create_access_token(token_data)

            # Make authenticated request
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/auth/me", headers=headers)

            # Verify response
            assert response.status_code == 200
            data = response.json()

            assert data["id"] == 456
            assert len(data["providers"]) == 2

            # Check both providers are included
            provider_names = [p["provider"] for p in data["providers"]]
            assert "github" in provider_names
            assert "google" in provider_names

        finally:
            app.dependency_overrides.clear()

    def test_me_endpoint_no_providers(self):
        """Test /auth/me with user having no linked providers."""
        # Create test user with no accounts
        test_user = User(
            id=789,
            email="noprov@example.com",
            display_name="No Provider User",
            created_at=datetime(2023, 1, 1, tzinfo=timezone.utc)
        )
        test_user.accounts = []

        # Override the get_current_user dependency
        def get_test_user():
            return test_user

        app.dependency_overrides[get_current_user] = get_test_user

        try:
            # Create valid JWT token
            token_data = {"sub": "789", "email": "noprov@example.com"}
            token = create_access_token(token_data)

            # Make authenticated request
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/auth/me", headers=headers)

            # Verify response
            assert response.status_code == 200
            data = response.json()

            assert data["id"] == 789
            assert data["providers"] == []

        finally:
            app.dependency_overrides.clear()

    def test_me_endpoint_null_last_login(self):
        """Test /auth/me with provider having null last_login_at."""
        # Create test user and account with null last_login_at
        test_user = User(
            id=999,
            email="nulllogin@example.com",
            display_name="Null Login User",
            created_at=datetime(2023, 1, 1, tzinfo=timezone.utc)
        )

        test_account = Account(
            id=1,
            user_id=999,
            provider="github",
            provider_account_id="github999",
            last_login_at=None  # Null last login
        )

        test_user.accounts = [test_account]

        # Override the get_current_user dependency
        def get_test_user():
            return test_user

        app.dependency_overrides[get_current_user] = get_test_user

        try:
            # Create valid JWT token
            token_data = {"sub": "999", "email": "nulllogin@example.com"}
            token = create_access_token(token_data)

            # Make authenticated request
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/auth/me", headers=headers)

            # Verify response
            assert response.status_code == 200
            data = response.json()

            assert len(data["providers"]) == 1
            provider = data["providers"][0]
            assert provider["provider"] == "github"
            assert provider["last_login_at"] is None

        finally:
            app.dependency_overrides.clear()