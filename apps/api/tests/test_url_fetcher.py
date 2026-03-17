"""Tests for the URL fetcher service."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from services.url_fetcher import URLFetcherService


class TestURLFetcherService:
    """Test cases for URLFetcherService."""

    @pytest.fixture
    def fetcher(self):
        """Create a URLFetcherService instance for testing."""
        return URLFetcherService(timeout=5.0, max_redirects=3)

    async def test_successful_fetch(self, fetcher):
        """Test successful URL content fetching."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.url = "https://example.com/"

        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.get.return_value = mock_response

            result = await fetcher.fetch_url_content("https://example.com")

            assert result.success is True
            assert result.content == "<html><body>Test content</body></html>"
            assert result.content_type == "text/html"
            assert result.status_code == 200
            assert result.final_url == "https://example.com/"
            assert result.error_message is None

    async def test_empty_url(self, fetcher):
        """Test handling of empty URL."""
        result = await fetcher.fetch_url_content("")

        assert result.success is False
        assert result.error_type == "validation_error"
        assert result.error_message == "URL cannot be empty"

    async def test_whitespace_only_url(self, fetcher):
        """Test handling of whitespace-only URL."""
        result = await fetcher.fetch_url_content("   ")

        assert result.success is False
        assert result.error_type == "validation_error"
        assert result.error_message == "URL cannot be empty"

    async def test_invalid_url_scheme(self, fetcher):
        """Test handling of invalid URL scheme."""
        result = await fetcher.fetch_url_content("ftp://example.com")

        assert result.success is False
        assert result.error_type == "validation_error"
        assert result.error_message == "URL must start with http:// or https://"

    async def test_url_without_scheme(self, fetcher):
        """Test handling of URL without scheme."""
        result = await fetcher.fetch_url_content("example.com")

        assert result.success is False
        assert result.error_type == "validation_error"
        assert result.error_message == "URL must start with http:// or https://"

    async def test_404_not_found(self, fetcher):
        """Test handling of 404 Not Found error."""
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.reason_phrase = "Not Found"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.url = "https://example.com/notfound"

        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.get.return_value = mock_response

            result = await fetcher.fetch_url_content("https://example.com/notfound")

            assert result.success is False
            assert result.status_code == 404
            assert result.error_type == "not_found"
            assert "HTTP 404" in result.error_message
            assert result.final_url == "https://example.com/notfound"

    async def test_500_server_error(self, fetcher):
        """Test handling of 500 Server Error."""
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.reason_phrase = "Internal Server Error"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.url = "https://example.com/"

        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.get.return_value = mock_response

            result = await fetcher.fetch_url_content("https://example.com")

            assert result.success is False
            assert result.status_code == 500
            assert result.error_type == "server_error"
            assert "HTTP 500" in result.error_message

    async def test_403_forbidden(self, fetcher):
        """Test handling of 403 Forbidden error."""
        mock_response = AsyncMock()
        mock_response.status_code = 403
        mock_response.reason_phrase = "Forbidden"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.url = "https://example.com/"

        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.get.return_value = mock_response

            result = await fetcher.fetch_url_content("https://example.com")

            assert result.success is False
            assert result.status_code == 403
            assert result.error_type == "forbidden"
            assert "HTTP 403" in result.error_message

    async def test_timeout_error(self, fetcher):
        """Test handling of timeout error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.get.side_effect = httpx.TimeoutException("Request timed out")

            result = await fetcher.fetch_url_content("https://slow-example.com")

            assert result.success is False
            assert result.error_type == "timeout"
            assert "Request timed out after" in result.error_message

    async def test_too_many_redirects(self, fetcher):
        """Test handling of too many redirects error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.get.side_effect = httpx.TooManyRedirects("Too many redirects")

            result = await fetcher.fetch_url_content("https://redirect-loop.com")

            assert result.success is False
            assert result.error_type == "too_many_redirects"
            assert "Too many redirects" in result.error_message

    async def test_invalid_url_httpx_error(self, fetcher):
        """Test handling of invalid URL format detected by httpx."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.get.side_effect = httpx.InvalidURL("Invalid URL")

            result = await fetcher.fetch_url_content("https://[invalid-url")

            assert result.success is False
            assert result.error_type == "invalid_url"
            assert "Invalid URL format" in result.error_message

    async def test_network_error(self, fetcher):
        """Test handling of network error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.get.side_effect = httpx.NetworkError("Connection failed")

            result = await fetcher.fetch_url_content("https://unreachable.example.com")

            assert result.success is False
            assert result.error_type == "network_error"
            assert "Network error" in result.error_message

    async def test_unicode_decode_error(self, fetcher):
        """Test handling of Unicode decode error."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.url = "https://example.com/"

        # Mock text property to raise UnicodeDecodeError
        def raise_unicode_error():
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

        type(mock_response).text = property(lambda self: raise_unicode_error())

        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.get.return_value = mock_response

            result = await fetcher.fetch_url_content("https://example.com")

            assert result.success is False
            assert result.error_type == "decode_error"
            assert "Failed to decode response content" in result.error_message

    async def test_unexpected_error(self, fetcher):
        """Test handling of unexpected error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.get.side_effect = RuntimeError("Unexpected error")

            result = await fetcher.fetch_url_content("https://example.com")

            assert result.success is False
            assert result.error_type == "unknown_error"
            assert "Unexpected error" in result.error_message

    async def test_content_type_parsing(self, fetcher):
        """Test content type parsing with charset."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.text = "<html></html>"
        mock_response.url = "https://example.com/"

        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.get.return_value = mock_response

            result = await fetcher.fetch_url_content("https://example.com")

            assert result.success is True
            assert result.content_type == "text/html"

    async def test_missing_content_type(self, fetcher):
        """Test handling of missing content-type header."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.headers = {}  # No content-type header
        mock_response.text = "Plain text content"
        mock_response.url = "https://example.com/"

        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.get.return_value = mock_response

            result = await fetcher.fetch_url_content("https://example.com")

            assert result.success is True
            assert result.content_type == ""

    def test_classify_http_errors(self, fetcher):
        """Test HTTP error classification."""
        assert fetcher._classify_http_error(404) == "not_found"
        assert fetcher._classify_http_error(403) == "forbidden"
        assert fetcher._classify_http_error(401) == "unauthorized"
        assert fetcher._classify_http_error(429) == "rate_limited"
        assert fetcher._classify_http_error(400) == "client_error"
        assert fetcher._classify_http_error(422) == "client_error"
        assert fetcher._classify_http_error(500) == "server_error"
        assert fetcher._classify_http_error(502) == "server_error"
        assert fetcher._classify_http_error(503) == "server_error"

    def test_service_initialization(self):
        """Test service initialization with custom parameters."""
        fetcher = URLFetcherService(timeout=10.0, max_redirects=10)
        assert fetcher.timeout == 10.0
        assert fetcher.max_redirects == 10
        assert "Learning-Space" in fetcher.headers["User-Agent"]

    async def test_url_stripping(self, fetcher):
        """Test that URLs are properly stripped of whitespace."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.reason_phrase = "OK"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "Test content"
        mock_response.url = "https://example.com/"

        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.get.return_value = mock_response

            result = await fetcher.fetch_url_content("  https://example.com  ")

            assert result.success is True
            mock_context.get.assert_called_once_with("https://example.com")
