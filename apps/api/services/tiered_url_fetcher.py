"""Tiered URL content fetcher service with API, HTTP, and Playwright fallbacks."""

import logging
from dataclasses import dataclass
from typing import Dict, Optional
from urllib.parse import urlparse

import httpx

from core.config import settings
from services.playwright_fetcher import playwright_fetcher_service

logger = logging.getLogger(__name__)


@dataclass
class TieredFetchResult:
    """Extended result of tiered URL content fetching operation."""

    success: bool
    content: Optional[str] = None
    content_type: Optional[str] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    final_url: Optional[str] = None  # After redirects
    fetch_tier: Optional[str] = None  # 'api', 'http', 'playwright'


class TieredURLFetcherService:
    """Service for fetching content using a tiered strategy."""

    def __init__(self, timeout: float = 15.0, max_redirects: int = 5):
        """Initialize the tiered URL fetcher service.

        Args:
            timeout: Request timeout in seconds
            max_redirects: Maximum number of redirects to follow
        """
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        # Load domain blocklist from config
        self.api_required_domains = self._load_api_required_domains()

    def _load_api_required_domains(self) -> Dict[str, str]:
        """Load API-required domains from config settings.

        Returns:
            Dictionary mapping domain to provider name
        """
        domains_config = settings.api_required_domains or ""
        domain_map = {}

        if domains_config:
            try:
                for pair in domains_config.split(","):
                    pair = pair.strip()
                    if not pair:
                        continue

                    if ":" not in pair:
                        logger.warning(
                            f"Invalid API_REQUIRED_DOMAINS format: '{pair}' "
                            f"(expected 'domain:provider'). Skipping."
                        )
                        continue

                    parts = pair.split(":", 1)
                    domain = parts[0].strip()
                    provider = parts[1].strip()

                    if not domain or not provider:
                        logger.warning(
                            f"Invalid API_REQUIRED_DOMAINS entry: '{pair}' "
                            f"(domain and provider cannot be empty). Skipping."
                        )
                        continue

                    domain_map[domain] = provider

            except Exception as e:
                logger.error(
                    f"Failed to parse API_REQUIRED_DOMAINS config: {e}. "
                    f"Using empty domain map."
                )
                return {}

        logger.info(
            f"Loaded {len(domain_map)} API-required domains: {list(domain_map.keys())}"
        )
        return domain_map

    async def fetch_url_content(self, url: str, owner_id: int) -> TieredFetchResult:
        """Fetch content from a URL using the tiered strategy.

        Args:
            url: The URL to fetch content from
            owner_id: Owner ID for checking linked accounts

        Returns:
            TieredFetchResult containing content or error information
        """
        if not url or not url.strip():
            return TieredFetchResult(
                success=False,
                error_type="validation_error",
                error_message="URL cannot be empty",
            )

        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            return TieredFetchResult(
                success=False,
                error_type="validation_error",
                error_message="URL must start with http:// or https://",
            )

        logger.info(f"Starting tiered fetch for URL: {url}")

        # Parse domain
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
        except Exception as e:
            return TieredFetchResult(
                success=False,
                error_type="validation_error",
                error_message=f"Invalid URL format: {str(e)}",
            )

        # Check if domain is on API blocklist
        if domain in self.api_required_domains:
            return await self._tier1_api_fetch(url, domain, owner_id)
        else:
            # Try Tier 2a (HTTP) first
            tier2a_result = await self._tier2a_http_fetch(url)
            if tier2a_result.success:
                return tier2a_result

            # Fall back to Tier 2b (Playwright)
            return await self._tier2b_playwright_fetch(url)

    async def _tier1_api_fetch(
        self, url: str, domain: str, owner_id: int
    ) -> TieredFetchResult:
        """Tier 1: API-based fetch for blocklisted domains.

        Args:
            url: The URL to fetch
            domain: Domain name
            owner_id: Owner ID for account lookup

        Returns:
            TieredFetchResult with API fetch results
        """
        provider = self.api_required_domains[domain]
        logger.info(f"Domain {domain} requires API fetch via provider {provider}")

        # TODO: Implementation pending linked account lookup system
        # When account linking is implemented:
        # 1. Check if user has linked account for this provider (owner_id)
        # 2. If yes, use provider-specific API client to fetch content
        # 3. If no linked account, return AUTH_REQUIRED error
        # For now, we don't have any API integrations implemented

        return TieredFetchResult(
            success=False,
            error_type="NOT_SUPPORTED",
            error_message=f"Fetching content from {domain} is not yet supported.",
        )

    async def _tier2a_http_fetch(self, url: str) -> TieredFetchResult:
        """Tier 2a: Direct HTTP fetch.

        Args:
            url: The URL to fetch

        Returns:
            TieredFetchResult with HTTP fetch results
        """
        logger.info(f"Tier 2a: HTTP fetch for {url}")

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=self.headers,
                follow_redirects=True,
                max_redirects=self.max_redirects,
            ) as client:
                response = await client.get(url)

                content_type = (
                    response.headers.get("content-type", "").split(";")[0].lower()
                )

                # Check for bot-blocking signals
                if self._is_bot_blocked(response):
                    logger.info(
                        f"Bot blocking detected for {url}, "
                        f"status: {response.status_code}"
                    )
                    return TieredFetchResult(
                        success=False,
                        status_code=response.status_code,
                        error_type="bot_blocked",
                        error_message=f"Bot blocked (HTTP {response.status_code})",
                        final_url=str(response.url),
                        content_type=content_type,
                    )

                # Check for other HTTP errors
                if response.status_code >= 400:
                    error_type = self._classify_http_error(response.status_code)
                    error_message = (
                        f"HTTP {response.status_code}: {response.reason_phrase}"
                    )

                    logger.warning(f"HTTP error fetching {url}: {error_message}")

                    return TieredFetchResult(
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
                    return TieredFetchResult(
                        success=False,
                        status_code=response.status_code,
                        error_type="decode_error",
                        error_message=f"Failed to decode response content: {str(e)}",
                        final_url=str(response.url),
                        content_type=content_type,
                    )

                # Check for minimal content threshold
                if len(content.strip()) < 500:
                    logger.info(f"Content too short for {url}: {len(content)} chars")
                    return TieredFetchResult(
                        success=False,
                        status_code=response.status_code,
                        error_type="bot_blocked",
                        error_message="Content too short, likely blocked",
                        final_url=str(response.url),
                        content_type=content_type,
                    )

                logger.info(
                    f"HTTP fetch successful for {url}: {len(content)} chars, "
                    f"status: {response.status_code}, type: {content_type}"
                )

                return TieredFetchResult(
                    success=True,
                    content=content,
                    content_type=content_type,
                    status_code=response.status_code,
                    final_url=str(response.url),
                    fetch_tier="http",
                )

        except httpx.TimeoutException:
            error_message = f"Request timed out after {self.timeout} seconds"
            logger.warning(f"Timeout fetching {url}: {error_message}")
            return TieredFetchResult(
                success=False,
                error_type="timeout",
                error_message=error_message,
            )

        except httpx.TooManyRedirects:
            error_message = f"Too many redirects (max: {self.max_redirects})"
            logger.warning(f"Too many redirects for {url}: {error_message}")
            return TieredFetchResult(
                success=False,
                error_type="too_many_redirects",
                error_message=error_message,
            )

        except httpx.InvalidURL:
            error_message = "Invalid URL format"
            logger.warning(f"Invalid URL: {url}")
            return TieredFetchResult(
                success=False,
                error_type="invalid_url",
                error_message=error_message,
            )

        except httpx.NetworkError as e:
            error_message = f"Network error: {str(e)}"
            logger.warning(f"Network error fetching {url}: {error_message}")
            return TieredFetchResult(
                success=False,
                error_type="network_error",
                error_message=error_message,
            )

        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logger.error(
                f"Unexpected error fetching {url}: {error_message}", exc_info=True
            )
            return TieredFetchResult(
                success=False,
                error_type="unknown_error",
                error_message=error_message,
            )

    async def _tier2b_playwright_fetch(self, url: str) -> TieredFetchResult:
        """Tier 2b: Playwright headless browser fetch.

        Args:
            url: The URL to fetch

        Returns:
            TieredFetchResult with Playwright fetch results
        """
        logger.info(f"Tier 2b: Playwright fetch for {url}")

        try:
            # Use existing playwright_fetcher_service
            playwright_result = await playwright_fetcher_service.fetch_url_content(url)

            if playwright_result.success:
                return TieredFetchResult(
                    success=True,
                    content=playwright_result.content,
                    content_type=playwright_result.content_type,
                    status_code=playwright_result.status_code,
                    final_url=playwright_result.final_url,
                    fetch_tier="playwright",
                )
            else:
                # Classify the error type for failed Playwright fetch
                error_type = self._classify_playwright_error(
                    playwright_result.error_type
                )

                return TieredFetchResult(
                    success=False,
                    error_type=error_type,
                    error_message=playwright_result.error_message,
                    status_code=playwright_result.status_code,
                    final_url=playwright_result.final_url,
                    content_type=playwright_result.content_type,
                )

        except Exception as e:
            logger.error(f"Playwright fetch failed for {url}: {e}", exc_info=True)
            return TieredFetchResult(
                success=False,
                error_type="FETCH_ERROR",
                error_message=f"Playwright fetch failed: {str(e)}",
            )

    def _is_bot_blocked(self, response: httpx.Response) -> bool:
        """Check if response indicates bot blocking.

        Args:
            response: HTTP response object

        Returns:
            True if response indicates bot blocking
        """
        # Check status codes
        if response.status_code in [403, 429]:
            return True

        # Check response content for blocking indicators
        try:
            content = response.text.lower()
            bot_indicators = [
                "cloudflare",
                "access denied",
                "enable javascript",
                "recaptcha",
                "blocked",
                "bot detected",
                "automation",
            ]

            for indicator in bot_indicators:
                if indicator in content:
                    return True

        except Exception:  # nosec B110 — intentional: content read failure != bot blocked
            pass

        return False

    def _classify_http_error(self, status_code: int) -> str:
        """Classify HTTP error status codes.

        Args:
            status_code: HTTP status code

        Returns:
            Error type string
        """
        if status_code in [403, 429]:
            return "bot_blocked"
        elif status_code == 404:
            return "not_found"
        elif status_code == 401:
            return "unauthorized"
        elif 400 <= status_code < 500:
            return "client_error"
        elif 500 <= status_code < 600:
            return "server_error"
        else:
            return "http_error"

    def _classify_playwright_error(self, playwright_error_type: Optional[str]) -> str:
        """Classify Playwright error into standardized error types.

        Args:
            playwright_error_type: Error type from Playwright fetcher

        Returns:
            Standardized error type
        """
        if not playwright_error_type:
            return "FETCH_ERROR"

        # Map playwright error types to our standardized types
        error_mapping = {
            "timeout": "FETCH_ERROR",
            "network_error": "FETCH_ERROR",
            "navigation_error": "BOT_BLOCKED",
            "content_error": "BOT_BLOCKED",
            "unknown_error": "FETCH_ERROR",
        }

        return error_mapping.get(playwright_error_type, "FETCH_ERROR")


# Create singleton instance
tiered_url_fetcher_service = TieredURLFetcherService()
