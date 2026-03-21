"""
Mock OAuth provider responses for integration testing.

Provides realistic OAuth flow mocking for Twitter and GitHub without external API calls.
"""

from typing import Dict, Optional

import httpx
import respx


def setup_twitter_oauth_mock(
    mock_user_data: Optional[Dict] = None,
    access_token: str = "mock_access_token_123",
    provider_user_id: str = "1234567890",
) -> Dict:
    """
    Set up Twitter OAuth API mocks using respx.

    Returns the mock user data that will be returned by the mocked API calls.
    """
    if mock_user_data is None:
        mock_user_data = {
            "id": provider_user_id,
            "username": "testuser",
            "name": "Test User",
            "profile_image_url": "https://pbs.twimg.com/profile_images/test.jpg",
        }

    # Mock token exchange endpoint
    respx.post("https://api.twitter.com/2/oauth2/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": access_token,
                "token_type": "bearer",
                "scope": "tweet.read users.read",
                "expires_in": 7200,
            },
        )
    )

    # Mock user info endpoint
    respx.get("https://api.twitter.com/2/users/me").mock(
        return_value=httpx.Response(200, json={"data": mock_user_data})
    )

    return mock_user_data


def setup_github_oauth_mock(
    mock_user_data: Optional[Dict] = None,
    access_token: str = "mock_access_token_456",
    provider_user_id: str = "9876543",
) -> Dict:
    """
    Set up GitHub OAuth API mocks using respx.

    Returns the mock user data that will be returned by the mocked API calls.
    """
    if mock_user_data is None:
        mock_user_data = {
            "id": int(provider_user_id),
            "login": "testuser",
            "name": "Test User",
            "email": "testuser@example.com",
            "avatar_url": "https://avatars.githubusercontent.com/u/test?v=4",
        }

    # Mock token exchange endpoint
    respx.post("https://github.com/login/oauth/access_token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": access_token,
                "token_type": "bearer",
                "scope": "user:email",
            },
        )
    )

    # Mock user info endpoint
    respx.get("https://api.github.com/user").mock(
        return_value=httpx.Response(200, json=mock_user_data)
    )

    # Mock user emails endpoint (GitHub specific)
    respx.get("https://api.github.com/user/emails").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "email": mock_user_data.get("email", "testuser@example.com"),
                    "primary": True,
                    "verified": True,
                    "visibility": "private",
                }
            ],
        )
    )

    return mock_user_data


def setup_oauth_error_mock(
    provider: str = "twitter", error_type: str = "invalid_grant", status_code: int = 400
) -> None:
    """
    Set up OAuth error responses for testing error scenarios.

    Args:
        provider: "twitter" or "github"
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
    elif provider == "github":
        respx.post("https://github.com/login/oauth/access_token").mock(
            return_value=httpx.Response(status_code, json=error_response)
        )
        respx.get("https://api.github.com/user").mock(
            return_value=httpx.Response(401, json={"message": "Bad credentials"})
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
