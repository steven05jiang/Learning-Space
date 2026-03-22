"""Playwright-based URL content fetcher — renders JavaScript and bypasses bot blocks."""

import logging

from playwright.async_api import async_playwright

from services.url_fetcher import FetchResult

logger = logging.getLogger(__name__)


class PlaywrightFetcherService:
    """Fetches URL content using a headless Chromium browser via Playwright.

    Use this instead of URLFetcherService when sites return 403/blocked responses
    to plain HTTP requests (e.g. openai.com, twitter.com, linkedin.com).
    """

    def __init__(self, timeout: float = 30.0):
        self.timeout = int(timeout * 1000)  # Playwright uses milliseconds

    async def fetch_url_content(self, url: str) -> FetchResult:
        if not url or not url.strip():
            return FetchResult(
                success=False,
                error_type="validation_error",
                error_message="URL cannot be empty",
            )

        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            return FetchResult(
                success=False,
                error_type="validation_error",
                error_message="URL must start with http:// or https://",
            )

        logger.info(f"Fetching content via Playwright: {url}")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                try:
                    context = await browser.new_context(
                        user_agent=(
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"
                        ),
                        locale="en-US",
                        viewport={"width": 1280, "height": 800},
                    )
                    page = await context.new_page()

                    response = await page.goto(
                        url,
                        timeout=self.timeout,
                        wait_until="domcontentloaded",
                    )

                    if response is None:
                        return FetchResult(
                            success=False,
                            error_type="network_error",
                            error_message="No response received",
                        )

                    status = response.status
                    content_type = (
                        response.headers.get("content-type", "").split(";")[0].lower()
                    )
                    final_url = page.url

                    if status >= 400:
                        error_type = self._classify_http_error(status)
                        error_message = f"HTTP {status}"
                        logger.warning(f"HTTP error fetching {url}: {error_message}")
                        return FetchResult(
                            success=False,
                            status_code=status,
                            error_type=error_type,
                            error_message=error_message,
                            final_url=final_url,
                            content_type=content_type,
                        )

                    content = await page.content()

                    logger.info(
                        f"Playwright fetched {len(content)} chars from {url} "
                        f"(status: {status}, type: {content_type})"
                    )

                    return FetchResult(
                        success=True,
                        content=content,
                        content_type=content_type or "text/html",
                        status_code=status,
                        final_url=final_url,
                    )
                finally:
                    await browser.close()

        except Exception as e:
            error_message = f"Playwright error: {str(e)}"
            logger.error(
                f"Playwright fetch failed for {url}: {error_message}", exc_info=True
            )
            return FetchResult(
                success=False,
                error_type="unknown_error",
                error_message=error_message,
            )

    def _classify_http_error(self, status_code: int) -> str:
        if status_code == 404:
            return "not_found"
        elif status_code == 403:
            return "forbidden"
        elif status_code == 401:
            return "unauthorized"
        elif status_code == 429:
            return "rate_limited"
        elif 400 <= status_code < 500:
            return "client_error"
        elif 500 <= status_code < 600:
            return "server_error"
        return "http_error"


playwright_fetcher_service = PlaywrightFetcherService()
