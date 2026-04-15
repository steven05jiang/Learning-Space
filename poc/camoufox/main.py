"""
Dual-mode browser scraper POC — Playwright + Camoufox fallback.

Usage:
  uv run main.py                           # Auto-select browser
  uv run main.py --visible                 # Show browser window
  uv run main.py --browser playwright      # Force Playwright only
  uv run main.py --browser camoufox        # Force Camoufox only
  uv run main.py --tweet-id <id>           # Custom tweet ID
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

OUTPUT_FILE = Path(__file__).parent / "scraped_tweets.json"
DEFAULT_TWEET_ID = "2034627967926825175"


def _is_blocked(html: str) -> bool:
    """Detect if response is a Cloudflare/blocking page."""
    if not html:
        return True
    lower = html.lower()
    blockers = ["cloudflare", "checking your browser", "ray id",
               "access denied", "captcha", "ddos protection"]
    return any(b in lower for b in blockers)


def parse_tweet(page, url: str) -> dict | None:
    """Parse tweet data from loaded page."""
    try:
        # Wait for JS to render, then check for article
        page.wait_for_timeout(2000)
        if page.locator('article[data-testid="tweet"]').count() == 0:
            print("[!] No tweet article found on page")
            return None
    except Exception as e:
        print(f"[!] Error finding tweet: {e}")
        return None

    tweet_data = {
        "url": url,
        "scraped_at": datetime.now().isoformat(),
        "handle": None,
        "display_name": None,
        "author_raw": None,
        "content": None,
        "metrics": {},
        "media": [],
    }

    # Extract author info
    try:
        author_elem = page.locator('div[data-testid="User-Name"]').first
        author_text = author_elem.inner_text()
        tweet_data["author_raw"] = author_text
        for part in author_text.split("\n"):
            if part.startswith("@"):
                tweet_data["handle"] = part.replace("@", "")
            elif part and not part.startswith("·"):
                tweet_data["display_name"] = part
    except Exception as e:
        print(f"[!] Error extracting author: {e}")

    # Extract tweet content - longest div in article
    try:
        article = page.locator('article[data-testid="tweet"]').first
        divs = article.locator('div').all()
        longest_div, max_len = None, 0
        for div in divs:
            txt = div.inner_text()
            if len(txt) > max_len:
                max_len = len(txt)
                longest_div = txt
        if longest_div and max_len > 200:
            tweet_data["content"] = longest_div
    except Exception as e:
        print(f"[!] Error extracting content: {e}")

    # Extract metrics
    for metric_name, selector in [
        ("likes", 'button[data-testid="like"]'),
        ("retweets", 'button[data-testid="retweet"]'),
        ("replies", 'button[data-testid="reply"]'),
    ]:
        try:
            btn = page.locator(selector).first
            tweet_data["metrics"][metric_name] = btn.locator("span").last.inner_text()
        except Exception:
            tweet_data["metrics"][metric_name] = None

    try:
        view_elem = page.locator('span:has-text("Views")').first
        tweet_data["metrics"]["views"] = view_elem.locator("..").inner_text()
    except Exception:
        tweet_data["metrics"]["views"] = None

    # Extract media
    try:
        for i, img in enumerate(page.locator('div[data-testid="tweetPhoto"]').all()):
            try:
                src = img.locator("img").get_attribute("src")
                tweet_data["media"].append({"type": "image", "index": i, "src": src})
            except Exception:
                pass
    except Exception:
        pass

    return tweet_data


def main():
    parser = argparse.ArgumentParser(description="Dual-mode X.com Scraper")
    parser.add_argument("--visible", action="store_true", help="Show browser window")
    parser.add_argument("--browser", default="auto",
                        choices=["auto", "playwright", "camoufox"],
                        help="Browser selection (default: auto)")
    parser.add_argument("--tweet-id", type=str, default=DEFAULT_TWEET_ID, help="Tweet ID")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file")
    args = parser.parse_args()

    tweet_url = f"https://x.com/HiTw93/status/{args.tweet_id}"
    output_file = Path(args.output) if args.output else OUTPUT_FILE

    print("=" * 60)
    print("Dual-mode X.com Scraper POC")
    print("=" * 60)
    print(f"URL: {tweet_url}")
    print(f"Browser: {args.browser}")
    print(f"Headless: {not args.visible}")
    print("=" * 60)

    tweet = None
    browser_used = "unknown"

    if args.browser in ["auto", "playwright"]:
        print("[*] Trying Playwright (Chromium)...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=not args.visible)
                page = browser.new_page()
                page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
                page.goto(tweet_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)
                
                html = page.content()
                if not _is_blocked(html):
                    browser_used = "playwright"
                    tweet = parse_tweet(page, tweet_url)
                    browser.close()
                else:
                    browser.close()
                    raise Exception("Blocked by Cloudflare")
        except Exception as e:
            print(f"[!] Playwright failed: {e}")
            browser_used = None

    if tweet is None and args.browser in ["auto", "camoufox"]:
        print("[*] Trying Camoufox (Firefox)...")
        try:
            from camoufox import Camoufox
            with Camoufox(headless=not args.visible) as browser:
                page = browser.new_page()
                page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
                page.goto(tweet_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)
                browser_used = "camoufox"
                tweet = parse_tweet(page, tweet_url)
        except Exception as e:
            print(f"[!] Camoufox failed: {e}")
            browser_used = None

    if tweet is None:
        print("\n[!] Failed to scrape - all browsers blocked")
        sys.exit(1)

    print(f"\n[+] Successfully scraped with {browser_used}")

    if tweet:
        tweet["browser_used"] = browser_used
        print("\n" + "=" * 60)
        print("SCRAPED TWEET DATA")
        print("=" * 60)
        print(f"Browser: {browser_used}")
        print(f"Handle: @{tweet.get('handle', 'N/A')}")
        print(f"Display Name: {tweet.get('display_name', 'N/A')}")
        print(f"\nContent (first 200 chars):\n{tweet.get('content', 'N/A')[:200]}...")
        print(f"\nMetrics: {tweet.get('metrics', {})}")
        print(f"Media: {len(tweet.get('media', []))} items")

        existing = []
        if output_file.exists():
            try:
                existing = json.loads(output_file.read_text())
            except Exception:
                existing = []
        existing.append(tweet)
        output_file.write_text(json.dumps(existing, indent=2, default=str))
        print(f"\n[+] Saved to {output_file}")
    else:
        print("\n[!] Failed to parse tweet")
        sys.exit(1)


if __name__ == "__main__":
    main()
