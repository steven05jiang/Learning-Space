"""
Mock HTTP responses for provider content fetching in integration tests.

Provides realistic content responses for various URLs without external HTTP calls.
"""

from typing import Dict, List
from urllib.parse import urlparse

import httpx
import respx

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


def setup_fetch_success(
    respx_mock,
    url: str,
    content: str = None,
    content_type: str = "text/html",
    status_code: int = 200,
    final_url: str = None,
) -> Dict:
    """
    Mock successful HTTP fetch response for a specific URL.

    Args:
        url: The URL to mock
        content: Response content (auto-generated if None)
        content_type: MIME type of the response
        status_code: HTTP status code
        final_url: Final URL after redirects (defaults to original URL)

    Returns:
        Dict containing the mock response data for verification
    """
    if content is None:
        content = _generate_default_content(url, content_type)

    if final_url is None:
        final_url = url

    headers = {
        "content-type": f"{content_type}; charset=utf-8",
        "content-length": str(len(content)),
    }

    respx_mock.get(url).mock(
        return_value=httpx.Response(
            status_code,
            content=content,
            headers=headers,
            request=httpx.Request("GET", final_url),
        )
    )

    return {
        "url": url,
        "final_url": final_url,
        "content": content,
        "content_type": content_type.split(";")[0],  # Remove charset
        "status_code": status_code,
        "headers": headers,
    }


def setup_fetch_redirect(
    original_url: str,
    final_url: str,
    content: str = None,
    redirect_chain: List[str] = None,
) -> Dict:
    """
    Mock HTTP fetch with redirects.

    Args:
        original_url: Initial URL that redirects
        final_url: Final URL after all redirects
        content: Content of the final response
        redirect_chain: List of intermediate URLs (optional)

    Returns:
        Dict containing the mock response data
    """
    if content is None:
        content = _generate_default_content(final_url)

    # Mock the original URL with a redirect
    respx.get(original_url).mock(
        return_value=httpx.Response(302, headers={"location": final_url})
    )

    # Mock any intermediate redirects
    if redirect_chain:
        for i, redirect_url in enumerate(redirect_chain):
            next_url = (
                redirect_chain[i + 1] if i + 1 < len(redirect_chain) else final_url
            )
            respx.get(redirect_url).mock(
                return_value=httpx.Response(302, headers={"location": next_url})
            )

    # Mock the final URL
    setup_fetch_success(final_url, content)

    return {
        "original_url": original_url,
        "final_url": final_url,
        "content": content,
        "redirect_chain": redirect_chain or [],
    }


def setup_fetch_error(
    url: str, status_code: int = 404, error_content: str = None
) -> Dict:
    """
    Mock HTTP fetch error response.

    Args:
        url: The URL to mock
        status_code: HTTP error status code
        error_content: Error response content

    Returns:
        Dict containing the mock error response data
    """
    if error_content is None:
        error_content = _generate_error_content(status_code)

    respx.get(url).mock(
        return_value=httpx.Response(
            status_code, content=error_content, headers={"content-type": "text/html"}
        )
    )

    return {"url": url, "status_code": status_code, "error_content": error_content}


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


def setup_twitter_content_mock(tweet_id: str = "1234567890") -> Dict:
    """
    Mock Twitter content fetching for authenticated provider access.

    Args:
        tweet_id: Twitter tweet ID to mock

    Returns:
        Dict containing mock Twitter API response data
    """
    tweet_data = {
        "id": tweet_id,
        "text": "This is a mock tweet for testing purposes. #testing #mock",
        "author_id": "9876543210",
        "created_at": "2026-03-20T12:00:00.000Z",
        "public_metrics": {"retweet_count": 5, "like_count": 25, "reply_count": 3},
    }

    user_data = {
        "id": "9876543210",
        "username": "testuser",
        "name": "Test User",
        "verified": False,
    }

    # Mock Twitter API v2 endpoints
    respx.get(f"https://api.twitter.com/2/tweets/{tweet_id}").mock(
        return_value=httpx.Response(
            200, json={"data": tweet_data, "includes": {"users": [user_data]}}
        )
    )

    return {"tweet": tweet_data, "user": user_data, "tweet_id": tweet_id}


def setup_github_content_mock(owner: str = "testuser", repo: str = "test-repo") -> Dict:
    """
    Mock GitHub content fetching for authenticated provider access.

    Args:
        owner: GitHub repository owner
        repo: GitHub repository name

    Returns:
        Dict containing mock GitHub API response data
    """
    repo_data = {
        "id": 123456789,
        "name": repo,
        "full_name": f"{owner}/{repo}",
        "description": "A test repository for mocking purposes",
        "html_url": f"https://github.com/{owner}/{repo}",
        "language": "Python",
        "stargazers_count": 42,
        "forks_count": 7,
        "topics": ["testing", "mock", "python"],
    }

    # Mock GitHub API endpoints
    respx.get(f"https://api.github.com/repos/{owner}/{repo}").mock(
        return_value=httpx.Response(200, json=repo_data)
    )

    return {"repo": repo_data, "owner": owner, "repo_name": repo}


def setup_json_api_mock(url: str, json_data: Dict, status_code: int = 200) -> Dict:
    """
    Mock JSON API response.

    Args:
        url: API endpoint URL
        json_data: JSON response data
        status_code: HTTP status code

    Returns:
        Dict containing the mock response info
    """
    respx.get(url).mock(
        return_value=httpx.Response(
            status_code, json=json_data, headers={"content-type": "application/json"}
        )
    )

    return {"url": url, "json_data": json_data, "status_code": status_code}


def _generate_default_content(url: str, content_type: str = "text/html") -> str:
    """Generate realistic default content based on URL and content type."""
    domain = urlparse(url).netloc.lower()

    if content_type.startswith("text/html"):
        if "github.com" in domain:
            return """
<!DOCTYPE html>
<html>
<head>
    <title>GitHub Repository</title>
    <meta name="description" content="A sample GitHub repository for testing">
</head>
<body>
    <h1>Test Repository</h1>
    <p>This is a mock GitHub repository page for integration testing.</p>
    <div class="repository-content">
        <h2>About</h2>
        <p>Mock repository content with realistic HTML structure.</p>
    </div>
</body>
</html>
            """.strip()

        elif "twitter.com" in domain:
            return """
<!DOCTYPE html>
<html>
<head>
    <title>Twitter</title>
    <meta name="description" content="A sample tweet for testing">
</head>
<body>
    <div class="tweet">
        <p>This is a mock tweet for testing purposes. #testing</p>
        <div class="tweet-stats">25 likes, 5 retweets</div>
    </div>
</body>
</html>
            """.strip()

        else:
            return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Article - {domain}</title>
    <meta name="description" content="A sample article for testing content fetching">
</head>
<body>
    <h1>Sample Article</h1>
    <p>This is mock content for URL: {url}</p>
    <p>Generated for integration testing purposes.</p>
</body>
</html>
            """.strip()

    elif content_type.startswith("application/json"):
        return (
            '{"title": "Mock JSON Content", "url": "'
            + url
            + '", "type": "test_content"}'
        )

    else:
        return f"Mock content for {url} - Content-Type: {content_type}"


def _generate_error_content(status_code: int) -> str:
    """Generate realistic error content based on status code."""
    error_messages = {
        404: "Not Found",
        403: "Forbidden",
        401: "Unauthorized",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }

    message = error_messages.get(status_code, f"HTTP Error {status_code}")

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{status_code} {message}</title>
</head>
<body>
    <h1>{status_code} {message}</h1>
    <p>This is a mock error response for testing purposes.</p>
</body>
</html>
    """.strip()
