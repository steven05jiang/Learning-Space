"""
Mock OAuth provider responses for integration testing.

Provides realistic OAuth flow mocking for Twitter and GitHub without external API calls.
"""

from typing import Dict

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
        return_value=httpx.Response(200, json=MOCK_GOOGLE_USER)
    )

    return MOCK_GOOGLE_USER
