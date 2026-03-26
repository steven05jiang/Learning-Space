"""Tests for tiered URL fetcher service."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services.tiered_url_fetcher import TieredURLFetcherService
from services.url_fetcher import FetchResult


@pytest.fixture
def fetcher():
    """Create a TieredURLFetcherService instance for testing."""
    with patch("services.tiered_url_fetcher.settings") as mock_settings:
        mock_settings.api_required_domains = "twitter.com:twitter,x.com:twitter"
        return TieredURLFetcherService()


@pytest.mark.asyncio
async def test_empty_url_validation(fetcher):
    """Test that empty URLs are rejected."""
    result = await fetcher.fetch_url_content("", 1)
    assert not result.success
    assert result.error_type == "validation_error"
    assert "cannot be empty" in result.error_message


@pytest.mark.asyncio
async def test_invalid_url_validation(fetcher):
    """Test that invalid URLs are rejected."""
    result = await fetcher.fetch_url_content("not-a-url", 1)
    assert not result.success
    assert result.error_type == "validation_error"
    assert "must start with http" in result.error_message


@pytest.mark.asyncio
async def test_api_blocklist_hit_not_supported(fetcher):
    """Test domain blocklist hit with no integration."""
    result = await fetcher.fetch_url_content("https://twitter.com/example", 1)
    assert not result.success
    assert result.error_type == "NOT_SUPPORTED"
    assert "not yet supported" in result.error_message


@pytest.mark.asyncio
async def test_http_success_tier2a(fetcher):
    """Test successful HTTP fetch (Tier 2a)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html"}
    mock_response.text = "A" * 500  # Long enough content
    mock_response.url = "https://example.com"
    mock_response.reason_phrase = "OK"

    with patch("httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_context
        mock_context.get.return_value = mock_response

        result = await fetcher.fetch_url_content("https://example.com", 1)

        assert result.success
        assert result.fetch_tier == "http"
        assert result.content == "A" * 500
        assert result.content_type == "text/html"
        assert result.status_code == 200


@pytest.mark.asyncio
async def test_http_403_fallback_to_playwright(fetcher):
    """Test HTTP 403 falling back to Playwright (Tier 2b)."""
    # Mock HTTP response with 403
    mock_http_response = MagicMock()
    mock_http_response.status_code = 403
    mock_http_response.headers = {"content-type": "text/html"}
    mock_http_response.text = "Forbidden"
    mock_http_response.url = "https://example.com"
    mock_http_response.reason_phrase = "Forbidden"

    # Mock successful Playwright response
    mock_playwright_result = FetchResult(
        success=True,
        content="Playwright content",
        content_type="text/html",
        status_code=200,
        final_url="https://example.com",
    )

    with patch("httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_context
        mock_context.get.return_value = mock_http_response

        with patch(
            "services.tiered_url_fetcher.playwright_fetcher_service"
        ) as mock_playwright:
            mock_playwright.fetch_url_content = AsyncMock(
                return_value=mock_playwright_result
            )

            result = await fetcher.fetch_url_content("https://example.com", 1)

            assert result.success
            assert result.fetch_tier == "playwright"
            assert result.content == "Playwright content"
            mock_playwright.fetch_url_content.assert_called_once_with(
                "https://example.com"
            )


@pytest.mark.asyncio
async def test_http_timeout(fetcher):
    """Test HTTP timeout."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_context
        mock_context.get.side_effect = httpx.TimeoutException("Request timed out")

        # Mock Playwright service to prevent it from being called
        with patch(
            "services.tiered_url_fetcher.playwright_fetcher_service"
        ) as mock_playwright:
            mock_playwright_result = FetchResult(
                success=False,
                error_type="timeout",
                error_message="Playwright timed out",
            )
            mock_playwright.fetch_url_content = AsyncMock(
                return_value=mock_playwright_result
            )

            result = await fetcher.fetch_url_content("https://example.com", 1)

            assert not result.success
            assert result.error_type == "FETCH_ERROR"  # Mapped from playwright timeout
            assert "Playwright timed out" in result.error_message


@pytest.mark.asyncio
async def test_content_too_short_bot_blocked(fetcher):
    """Test content too short is treated as bot blocked."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html"}
    mock_response.text = "Short"  # Only 5 chars, below threshold
    mock_response.url = "https://example.com"

    with patch("httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_context
        mock_context.get.return_value = mock_response

        # Mock Playwright failure as well
        mock_playwright_result = FetchResult(
            success=False,
            error_type="navigation_error",
            error_message="Still blocked",
        )

        with patch(
            "services.tiered_url_fetcher.playwright_fetcher_service"
        ) as mock_playwright:
            mock_playwright.fetch_url_content = AsyncMock(
                return_value=mock_playwright_result
            )

            result = await fetcher.fetch_url_content("https://example.com", 1)

            assert not result.success
            assert result.error_type == "BOT_BLOCKED"


@pytest.mark.asyncio
async def test_bot_blocking_detection_cloudflare(fetcher):
    """Test bot blocking detection via content analysis."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html"}
    mock_response.text = (
        "Please wait while we check if you're human. Cloudflare security check."
    )
    mock_response.url = "https://example.com"

    with patch("httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_context
        mock_context.get.return_value = mock_response

        # Mock Playwright fallback
        mock_playwright_result = FetchResult(
            success=True,
            content="Real content",
            content_type="text/html",
            status_code=200,
        )

        with patch(
            "services.tiered_url_fetcher.playwright_fetcher_service"
        ) as mock_playwright:
            mock_playwright.fetch_url_content = AsyncMock(
                return_value=mock_playwright_result
            )

            result = await fetcher.fetch_url_content("https://example.com", 1)

            # Should fall through to Playwright and succeed
            assert result.success
            assert result.fetch_tier == "playwright"


@pytest.mark.asyncio
async def test_all_tiers_fail(fetcher):
    """Test when all tiers fail."""
    # Mock HTTP failure
    with patch("httpx.AsyncClient") as mock_client:
        mock_context = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_context
        mock_context.get.side_effect = httpx.NetworkError("Network failed")

        # Mock Playwright failure
        mock_playwright_result = FetchResult(
            success=False,
            error_type="timeout",
            error_message="Playwright timed out",
        )

        with patch(
            "services.tiered_url_fetcher.playwright_fetcher_service"
        ) as mock_playwright:
            mock_playwright.fetch_url_content = AsyncMock(
                return_value=mock_playwright_result
            )

            result = await fetcher.fetch_url_content("https://example.com", 1)

            assert not result.success
            assert result.error_type == "FETCH_ERROR"  # Mapped from playwright timeout


def test_load_api_required_domains():
    """Test loading API-required domains from config."""
    with patch("services.tiered_url_fetcher.settings") as mock_settings:
        mock_settings.api_required_domains = (
            "twitter.com:twitter,x.com:twitter,youtube.com:youtube"
        )

        fetcher = TieredURLFetcherService()

        expected_domains = {
            "twitter.com": "twitter",
            "x.com": "twitter",
            "youtube.com": "youtube",
        }

        assert fetcher.api_required_domains == expected_domains


def test_bot_blocking_detection():
    """Test bot blocking detection logic."""
    fetcher = TieredURLFetcherService()

    # Test 403 status
    response_403 = MagicMock()
    response_403.status_code = 403
    response_403.text = "Access denied"
    assert fetcher._is_bot_blocked(response_403)

    # Test 429 status
    response_429 = MagicMock()
    response_429.status_code = 429
    response_429.text = "Rate limited"
    assert fetcher._is_bot_blocked(response_429)

    # Test Cloudflare content
    response_cf = MagicMock()
    response_cf.status_code = 200
    response_cf.text = "Checking if you are human. Cloudflare security."
    assert fetcher._is_bot_blocked(response_cf)

    # Test normal response
    response_ok = MagicMock()
    response_ok.status_code = 200
    response_ok.text = "Normal web page content here"
    assert not fetcher._is_bot_blocked(response_ok)


def test_error_classification():
    """Test error type classification."""
    fetcher = TieredURLFetcherService()

    # HTTP errors
    assert fetcher._classify_http_error(403) == "bot_blocked"
    assert fetcher._classify_http_error(429) == "bot_blocked"
    assert fetcher._classify_http_error(404) == "not_found"
    assert fetcher._classify_http_error(401) == "unauthorized"
    assert fetcher._classify_http_error(500) == "server_error"
    assert fetcher._classify_http_error(400) == "client_error"

    # Playwright error mapping
    assert fetcher._classify_playwright_error("timeout") == "FETCH_ERROR"
    assert fetcher._classify_playwright_error("network_error") == "FETCH_ERROR"
    assert fetcher._classify_playwright_error("navigation_error") == "BOT_BLOCKED"
    assert fetcher._classify_playwright_error("content_error") == "BOT_BLOCKED"
    assert fetcher._classify_playwright_error("unknown_error") == "FETCH_ERROR"
    assert fetcher._classify_playwright_error("some_other_error") == "FETCH_ERROR"
    assert fetcher._classify_playwright_error(None) == "FETCH_ERROR"
