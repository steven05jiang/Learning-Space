from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from core.deps import get_current_user
from core.jwt import create_access_token
from main import app
from models.user import User

client = TestClient(app)


class TestAuthLogoutEndpoint:
    """Test the POST /auth/logout endpoint."""

    def test_logout_requires_authentication(self):
        """Test that /auth/logout requires authentication."""
        response = client.post("/auth/logout")
        assert response.status_code == 401

    def test_logout_invalid_token(self):
        """Test /auth/logout with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/auth/logout", headers=headers)
        assert response.status_code == 401

    def test_logout_success(self):
        """Test successful logout."""
        # Create test user
        test_user = User(
            id=123,
            email="test@example.com",
            display_name="Test User",
            created_at=datetime(2023, 1, 1, tzinfo=timezone.utc)
        )
        test_user.accounts = []

        # Override the get_current_user dependency
        def get_test_user():
            return test_user

        app.dependency_overrides[get_current_user] = get_test_user

        try:
            # Create valid JWT token
            token_data = {
                "sub": str(test_user.id),
                "email": test_user.email,
                "display_name": test_user.display_name
            }
            token = create_access_token(token_data)

            # Make logout request
            headers = {"Authorization": f"Bearer {token}"}
            response = client.post("/auth/logout", headers=headers)

            # Verify response
            assert response.status_code == 204
            assert response.content == b""  # No content for 204

        finally:
            app.dependency_overrides.clear()

    def test_logout_different_users(self):
        """Test logout works for different users."""
        # Test user 1
        user1 = User(
            id=456,
            email="user1@example.com",
            display_name="User One",
            created_at=datetime(2023, 1, 1, tzinfo=timezone.utc)
        )
        user1.accounts = []

        # Test user 2
        user2 = User(
            id=789,
            email="user2@example.com",
            display_name="User Two",
            created_at=datetime(2023, 1, 1, tzinfo=timezone.utc)
        )
        user2.accounts = []

        # Test logout for user 1
        def get_user1():
            return user1

        app.dependency_overrides[get_current_user] = get_user1

        try:
            token1_data = {"sub": "456", "email": "user1@example.com"}
            token1 = create_access_token(token1_data)

            headers1 = {"Authorization": f"Bearer {token1}"}
            response1 = client.post("/auth/logout", headers=headers1)
            assert response1.status_code == 204

        finally:
            app.dependency_overrides.clear()

        # Test logout for user 2
        def get_user2():
            return user2

        app.dependency_overrides[get_current_user] = get_user2

        try:
            token2_data = {"sub": "789", "email": "user2@example.com"}
            token2 = create_access_token(token2_data)

            headers2 = {"Authorization": f"Bearer {token2}"}
            response2 = client.post("/auth/logout", headers=headers2)
            assert response2.status_code == 204

        finally:
            app.dependency_overrides.clear()

    def test_logout_with_missing_auth_header(self):
        """Test logout without Authorization header."""
        response = client.post("/auth/logout")
        assert response.status_code == 401

    def test_logout_with_malformed_auth_header(self):
        """Test logout with malformed Authorization header."""
        # Test without Bearer prefix
        headers = {"Authorization": "token123"}
        response = client.post("/auth/logout", headers=headers)
        assert response.status_code == 401

        # Test with empty Bearer
        headers = {"Authorization": "Bearer "}
        response = client.post("/auth/logout", headers=headers)
        assert response.status_code == 401

        # Test with wrong scheme
        headers = {"Authorization": "Basic dGVzdDp0ZXN0"}
        response = client.post("/auth/logout", headers=headers)
        assert response.status_code == 401