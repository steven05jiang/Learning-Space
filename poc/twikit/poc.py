"""
Twikit POC — fetch bookmarks and a specific tweet.

Usage:
  # Fetch bookmarks (default 5):
  uv run poc.py bookmarks

  # Fetch a specific tweet by ID:
  uv run poc.py tweet 1234567890

  # Fetch bookmarks with custom count:
  uv run poc.py bookmarks --count 10

  # Set auth cookies manually (first time):
  uv run poc.py set-cookies --auth-token <auth_token> --ct0 <ct0>

  # Show how to get cookies from browser:
  uv run poc.py get-cookies-help

Authentication (priority order):
  1. cookies.json  — saved session (auto-created after first login)
  2. --auth-token / --ct0 flags with `set-cookies`
  3. X_USERNAME + X_PASSWORD env vars (blocked by Cloudflare on most IPs)

Getting cookies from browser (recommended):
  1. Open x.com and log in
  2. Open DevTools → Application → Cookies → https://x.com
  3. Copy values of `auth_token` and `ct0`
  4. Run: uv run poc.py set-cookies --auth-token <value> --ct0 <value>
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from twikit import Client

COOKIES_FILE = Path(__file__).parent / "cookies.json"


def build_cookies_json(auth_token: str, ct0: str) -> dict:
    """Minimal cookies dict that twikit needs."""
    return {
        "auth_token": auth_token,
        "ct0": ct0,
    }


async def get_client() -> Client:
    client = Client(language="en-US")

    if COOKIES_FILE.exists():
        print(f"[auth] Loading session from {COOKIES_FILE}")
        client.load_cookies(str(COOKIES_FILE))
    else:
        username = os.environ.get("X_USERNAME")
        password = os.environ.get("X_PASSWORD")
        if not username or not password:
            print("ERROR: No cookies.json found and X_USERNAME/X_PASSWORD not set.")
            print("Run:  uv run poc.py get-cookies-help")
            sys.exit(1)

        print(f"[auth] Logging in as {username} ...")
        await client.login(
            auth_info_1=username,
            password=password,
        )
        client.save_cookies(str(COOKIES_FILE))
        print(f"[auth] Session saved to {COOKIES_FILE}")

    return client


async def fetch_bookmarks(count: int = 5) -> None:
    client = await get_client()
    print(f"\n[bookmarks] Fetching up to {count} bookmarks ...\n")

    bookmarks = await client.get_bookmarks(count=count)

    if not bookmarks:
        print("No bookmarks found.")
        return

    for i, tweet in enumerate(bookmarks, 1):
        print(f"--- Bookmark {i} ---")
        print(f"  ID      : {tweet.id}")
        print(f"  Author  : @{tweet.user.screen_name} ({tweet.user.name})")
        print(f"  Created : {tweet.created_at}")
        print(f"  Text    : {tweet.text[:120]}{'...' if len(tweet.text) > 120 else ''}")
        print(f"  Likes   : {tweet.favorite_count}  Retweets: {tweet.retweet_count}  Views: {tweet.view_count}")
        print()


async def fetch_tweet(tweet_id: str) -> None:
    client = await get_client()
    print(f"\n[tweet] Fetching tweet {tweet_id} ...\n")

    tweet = await client.get_tweet_by_id(tweet_id)

    print(f"ID      : {tweet.id}")
    print(f"Author  : @{tweet.user.screen_name} ({tweet.user.name})")
    print(f"Created : {tweet.created_at}")
    print(f"Text    :\n{tweet.text}")
    print(f"\nLikes   : {tweet.favorite_count}")
    print(f"Retweets: {tweet.retweet_count}")
    print(f"Replies : {tweet.reply_count}")
    print(f"Views   : {tweet.view_count}")

    if tweet.media:
        print(f"\nMedia ({len(tweet.media)} item(s)):")
        for m in tweet.media:
            print(f"  - type={m.get('type')}  url={m.get('media_url_https', m.get('url', 'n/a'))}")

    if tweet.urls:
        print(f"\nURLs:")
        for u in tweet.urls:
            print(f"  - {u.get('expanded_url', u.get('url'))}")


def cmd_set_cookies(args: list) -> None:
    if "--auth-token" not in args or "--ct0" not in args:
        print("Usage: uv run poc.py set-cookies --auth-token <value> --ct0 <value>")
        sys.exit(1)

    auth_token = args[args.index("--auth-token") + 1]
    ct0 = args[args.index("--ct0") + 1]

    cookies = build_cookies_json(auth_token, ct0)
    COOKIES_FILE.write_text(json.dumps(cookies, indent=2))
    print(f"Saved cookies to {COOKIES_FILE}")


def cmd_get_cookies_help() -> None:
    print("""
How to get X.com cookies from your browser
==========================================

Option A — Chrome / Edge DevTools:
  1. Go to https://x.com and make sure you're logged in
  2. Press F12 → Application tab → Cookies → https://x.com
  3. Find `auth_token` and copy its value
  4. Find `ct0` and copy its value
  5. Run:
       uv run poc.py set-cookies --auth-token <auth_token_value> --ct0 <ct0_value>

Option B — "Cookie-Editor" browser extension:
  1. Install: https://cookie-editor.com
  2. Go to https://x.com
  3. Click the extension → Export (JSON)
  4. Rename the file to cookies.json in this directory
  5. The POC will load it automatically
""")


def usage() -> None:
    print(__doc__)
    sys.exit(1)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        usage()

    cmd = args[0]
    if cmd == "bookmarks":
        count = 5
        if "--count" in args:
            idx = args.index("--count")
            count = int(args[idx + 1])
        asyncio.run(fetch_bookmarks(count=count))
    elif cmd == "tweet":
        if len(args) < 2:
            print("ERROR: provide a tweet ID, e.g.  uv run poc.py tweet 1234567890")
            sys.exit(1)
        asyncio.run(fetch_tweet(args[1]))
    elif cmd == "set-cookies":
        cmd_set_cookies(args[1:])
    elif cmd == "get-cookies-help":
        cmd_get_cookies_help()
    else:
        usage()
