from httpx import Response

MOCK_TWITTER_USER = {
    "id": "twitter-user-123",
    "name": "Test User",
    "email": "test@example.com",
}

MOCK_GOOGLE_USER = {
    "id": "google-user-456",
    "name": "Google Test User",
    "email": "google@example.com",
    "picture": "https://example.com/google-avatar.jpg",
}


def setup_twitter_oauth_mock(respx_mock):
    respx_mock.post("https://api.twitter.com/2/oauth2/token").mock(
        return_value=Response(
            200, json={"access_token": "mock-twitter-token", "token_type": "bearer"}
        )
    )
    respx_mock.get("https://api.twitter.com/2/users/me").mock(
        return_value=Response(200, json={"data": MOCK_TWITTER_USER})
    )


def setup_google_oauth_mock(respx_mock):
    respx_mock.post("https://oauth2.googleapis.com/token").mock(
        return_value=Response(
            200, json={"access_token": "mock-google-token", "token_type": "bearer"}
        )
    )
    respx_mock.get("https://www.googleapis.com/oauth2/v2/userinfo").mock(
        return_value=Response(200, json=MOCK_GOOGLE_USER)
    )
