import respx
from httpx import Response

MOCK_PAGE_HTML = "<html><head><title>Test Page</title></head><body>Content here.</body></html>"
MOCK_TWEET_JSON = {"data": {"text": "Mock tweet content for testing."}}


def setup_fetch_success(respx_mock, url: str):
    respx_mock.get(url).mock(return_value=Response(200, text=MOCK_PAGE_HTML))


def setup_fetch_requires_auth(respx_mock, url: str):
    """Simulates a site that returns 401 on unauthenticated access."""
    respx_mock.get(url).mock(return_value=Response(401))


def setup_twitter_api_fetch(respx_mock, tweet_api_url: str):
    """Simulates a successful authenticated fetch via Twitter API."""
    respx_mock.get(tweet_api_url).mock(return_value=Response(200, json=MOCK_TWEET_JSON))