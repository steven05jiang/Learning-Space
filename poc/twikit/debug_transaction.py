"""Debug script to see what Twitter's homepage actually returns for ondemand.s"""
import asyncio
import re
import httpx
import bs4

async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }
    async with httpx.AsyncClient() as session:
        resp = await session.get("https://x.com", headers=headers, follow_redirects=True)
        text = resp.text

        # Try the existing regex
        existing = re.compile(r"""['|\"]{1}ondemand\.s['|\"]{1}:\s*['|\"]{1}([\w]*)['|\"]{1}""")
        m = existing.search(text)
        print(f"Existing regex match: {m}")

        # Find all occurrences of 'ondemand' in the page
        for match in re.finditer(r'.{0,60}ondemand.{0,60}', text):
            print(f"Context: {match.group()!r}")
            print()

asyncio.run(main())
