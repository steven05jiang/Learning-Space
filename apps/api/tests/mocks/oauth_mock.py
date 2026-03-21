"""
Mock OAuth provider responses for integration testing.

Provides realistic OAuth flow mocking for Twitter and GitHub without external API calls.
"""

from typing import Dict, Optional

import httpx
import respx

# Mock user data constants
MOCK_TWITTER_USER = {
    "id": "1234567890",
    "username": "testuser",
    "name": "Test User",
    "email": "test@example.com",
    "profile_image_url": "https://pbs.twimg.com/profile_images/test.jpg",
}

MOCK_GOOGLE_USER = {
    "sub": "google-user-456",
    "name": "Test User",
    "email": "test@example.com",
}


def setup_twitter_oauth_mock(respx_mock) -> Dict:
    """
    Set up Twitter OAuth API mocks using respx.

    Returns the mock user data that will be returned by the mocked API calls.
    """
    mock_user_data = MOCK_TWITTER_USER.copy()

    # Mock token exchange endpoint
    respx_mock.post("https://api.twitter.com/2/oauth2/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "mock-twitter-token",
                "token_type": "bearer",
                "scope": "tweet.read users.read",
                "expires_in": 7200,
            },
        )
    )

    # Mock user info endpoint
    respx_mock.get("https://api.twitter.com/2/users/me").mock(
        return_value=httpx.Response(200, json={"data": mock_user_data})
    )

    return mock_user_data


def setup_google_oauth_mock(respx_mock) -> Dict:
    """
    Set up Google OAuth API mocks using respx.

    Returns the mock user data that will be returned by the mocked API calls.
    """
    # Mock token exchange endpoint
    respx_mock.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "mock-google-token",
                "token_type": "bearer",
            },
        )
    )

    # Mock user info endpoint
    respx_mock.get("https://www.googleapis.com/oauth2/v3/userinfo").mock(
        return_value=httpx.Response(
            200,
            json=MOCK_GOOGLE_USER
        )
    )

    return MOCK_GOOGLE_USER


def setup_oauth_error_mock(
    provider: str = "twitter", error_type: str = "invalid_grant", status_code: int = 400
) -> None:
    """
    Set up OAuth error responses for testing error scenarios.

    Args:
        provider: "twitter" or "google"
        error_type: OAuth error type (invalid_grant, invalid_client, etc.)
        status_code: HTTP status code to return
    """
    error_response = {
        "error": error_type,
        "error_description": f"Mock {error_type} error for testing",
    }

    if provider == "twitter":
        respx.post("https://api.twitter.com/2/oauth2/token").mock(
            return_value=httpx.Response(status_code, json=error_response)
        )
        respx.get("https://api.twitter.com/2/users/me").mock(
            return_value=httpx.Response(
                401, json={"errors": [{"message": "Unauthorized"}]}
            )
        )
    elif provider == "google":
        respx.post("https://oauth2.googleapis.com/token").mock(
            return_value=httpx.Response(status_code, json=error_response)
        )
        respx.get("https://www.googleapis.com/oauth2/v3/userinfo").mock(
            return_value=httpx.Response(401, json={"error": "unauthorized"})
        )


class MockOAuthProvider:
    """
    Mock OAuth provider for unit testing without external HTTP calls.

    Can be used as a drop-in replacement for real OAuth providers in tests.
    """

    def __init__(self, provider_name: str = "twitter", client_id: str = "test_client"):
        self.provider_name = provider_name
        self.client_id = client_id
        self.client_secret = "test_secret"
        self._mock_access_token = f"mock_token_{provider_name}"
        self._mock_user_data = {
            "id": "1234567890",
            "username": "testuser",
            "name": "Test User",
            "email": "testuser@example.com",
        }

    async def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Return a mock authorization URL."""
        return f"https://{self.provider_name}.com/oauth/authorize?client_id={self.client_id}&redirect_uri={redirect_uri}&state={state}"

    async def exchange_code(
        self, code: str, redirect_uri: str, state: str = None
    ) -> str | None:
        """Return mock access token for any valid-looking code."""
        if code and code.startswith("valid_"):
            return self._mock_access_token
        return None

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Return mock user info for valid access token."""
        if access_token == self._mock_access_token:
            return self._mock_user_data.copy()
        return None

    def set_mock_user_data(self, user_data: Dict) -> None:
        """Update the mock user data returned by get_user_info."""
        self._mock_user_data.update(user_data)

    def set_mock_access_token(self, token: str) -> None:
        """Update the mock access token."""
        self._mock_access_token = token
