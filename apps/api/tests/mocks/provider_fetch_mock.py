"""
Mock HTTP responses for provider content fetching in integration tests.

Provides realistic content responses for various URLs without external HTTP calls.
"""

from typing import Dict

import httpx
import respx

# Mock HTML content
MOCK_PAGE_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Sample Article</title>
    <meta name="description" content="A sample article for testing content fetching">
</head>
<body>
    <h1>Sample Article</h1>
    <p>This is mock content for integration testing purposes.</p>
</body>
</html>"""

# Mock Twitter API response data
MOCK_TWEET_JSON = {
    "data": {
        "id": "1234567890",
        "text": "This is a mock tweet for testing purposes. #testing #mock",
        "author_id": "9876543210",
        "created_at": "2026-03-20T12:00:00.000Z",
        "public_metrics": {"retweet_count": 5, "like_count": 25, "reply_count": 3},
    },
    "includes": {
        "users": [
            {
                "id": "9876543210",
                "username": "testuser",
                "name": "Test User",
                "verified": False,
            }
        ]
    },
}


def setup_fetch_success(respx_mock, url: str) -> Dict:
    """
    Mock successful HTTP fetch response for a specific URL.

    Args:
        respx_mock: respx mock instance
        url: The URL to mock

    Returns:
        Dict containing the mock response data for verification
    """
    content = MOCK_PAGE_HTML
    content_type = "text/html"
    status_code = 200

    headers = {
        "content-type": f"{content_type}; charset=utf-8",
        "content-length": str(len(content)),
    }

    respx_mock.get(url).mock(
        return_value=httpx.Response(
            status_code,
            content=content,
            headers=headers,
            request=httpx.Request("GET", url),
        )
    )

    return {
        "url": url,
        "final_url": url,
        "content": content,
        "content_type": content_type,
        "status_code": status_code,
        "headers": headers,
    }



def setup_fetch_requires_auth(respx_mock, url: str) -> Dict:
    """
    Mock HTTP fetch that requires authentication (returns 401).

    Args:
        respx_mock: respx mock instance
        url: The URL to mock

    Returns:
        Dict containing the mock error response data
    """
    respx_mock.get(url).mock(
        return_value=httpx.Response(
            401, content="Unauthorized", headers={"content-type": "text/html"}
        )
    )

    return {"url": url, "status_code": 401, "error_content": "Unauthorized"}


def setup_twitter_api_fetch(respx_mock, tweet_api_url: str) -> Dict:
    """
    Mock Twitter API fetch response.

    Args:
        respx_mock: respx mock instance
        tweet_api_url: Twitter API endpoint URL

    Returns:
        Dict containing the mock Twitter API response data
    """
    respx_mock.get(tweet_api_url).mock(
        return_value=httpx.Response(200, json=MOCK_TWEET_JSON)
    )

    return {"url": tweet_api_url, "json_data": MOCK_TWEET_JSON, "status_code": 200}
