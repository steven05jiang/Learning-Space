"""URL content fetcher service for retrieving web page content."""

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """Result of URL content fetching operation."""

    success: bool
    content: Optional[str] = None
    content_type: Optional[str] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    final_url: Optional[str] = None  # After redirects


class URLFetcherService:
    """Service for fetching content from URLs via HTTP GET requests."""

    def __init__(self, timeout: float = 30.0, max_redirects: int = 5):
        """Initialize the URL fetcher service.

        Args:
            timeout: Request timeout in seconds
            max_redirects: Maximum number of redirects to follow
        """
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.headers = {
            "User-Agent": "Learning-Space/1.0 (+https://learning-space.app)",
            "Accept": "text/html,application/xhtml+xml,text/plain,*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def fetch_url_content(self, url: str) -> FetchResult:
        """Fetch content from a URL using HTTP GET.

        Args:
            url: The URL to fetch content from

        Returns:
            FetchResult containing content or error information
        """
        if not url or not url.strip():
            return FetchResult(
                success=False,
                error_type="validation_error",
                error_message="URL cannot be empty",
            )

        # Basic URL validation
        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            return FetchResult(
                success=False,
                error_type="validation_error",
                error_message="URL must start with http:// or https://",
            )

        logger.info(f"Fetching content from URL: {url}")

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=self.headers,
                follow_redirects=True,
                max_redirects=self.max_redirects,
            ) as client:
                response = await client.get(url)

                # Extract content type
                content_type = (
                    response.headers.get("content-type", "").split(";")[0].lower()
                )

                # Check if response is successful
                if response.status_code >= 400:
                    error_type = self._classify_http_error(response.status_code)
                    error_message = (
                        f"HTTP {response.status_code}: {response.reason_phrase}"
                    )

                    logger.warning(f"HTTP error fetching {url}: {error_message}")

                    return FetchResult(
                        success=False,
                        status_code=response.status_code,
                        error_type=error_type,
                        error_message=error_message,
                        final_url=str(response.url),
                        content_type=content_type,
                    )

                # Get text content
                try:
                    content = response.text
                except UnicodeDecodeError as e:
                    logger.error(f"Unicode decode error for {url}: {e}")
                    return FetchResult(
                        success=False,
                        status_code=response.status_code,
                        error_type="decode_error",
                        error_message=f"Failed to decode response content: {str(e)}",
                        final_url=str(response.url),
                        content_type=content_type,
                    )

                logger.info(
                    f"Successfully fetched {len(content)} characters from {url} "
                    f"(status: {response.status_code}, type: {content_type})"
                )

                return FetchResult(
                    success=True,
                    content=content,
                    content_type=content_type,
                    status_code=response.status_code,
                    final_url=str(response.url),
                )

        except httpx.TimeoutException:
            error_message = f"Request timed out after {self.timeout} seconds"
            logger.warning(f"Timeout fetching {url}: {error_message}")
            return FetchResult(
                success=False,
                error_type="timeout",
                error_message=error_message,
            )

        except httpx.TooManyRedirects:
            error_message = f"Too many redirects (max: {self.max_redirects})"
            logger.warning(f"Too many redirects for {url}: {error_message}")
            return FetchResult(
                success=False,
                error_type="too_many_redirects",
                error_message=error_message,
            )

        except httpx.InvalidURL:
            error_message = "Invalid URL format"
            logger.warning(f"Invalid URL: {url}")
            return FetchResult(
                success=False,
                error_type="invalid_url",
                error_message=error_message,
            )

        except httpx.NetworkError as e:
            error_message = f"Network error: {str(e)}"
            logger.warning(f"Network error fetching {url}: {error_message}")
            return FetchResult(
                success=False,
                error_type="network_error",
                error_message=error_message,
            )

        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logger.error(
                f"Unexpected error fetching {url}: {error_message}", exc_info=True
            )
            return FetchResult(
                success=False,
                error_type="unknown_error",
                error_message=error_message,
            )

    def _classify_http_error(self, status_code: int) -> str:
        """Classify HTTP error status codes into error types.

        Args:
            status_code: HTTP status code

        Returns:
            Error type string
        """
        if 400 <= status_code < 500:
            if status_code == 404:
                return "not_found"
            elif status_code == 403:
                return "forbidden"
            elif status_code == 401:
                return "unauthorized"
            elif status_code == 429:
                return "rate_limited"
            else:
                return "client_error"
        elif 500 <= status_code < 600:
            return "server_error"
        else:
            return "http_error"


# Create singleton instance
url_fetcher_service = URLFetcherService()
