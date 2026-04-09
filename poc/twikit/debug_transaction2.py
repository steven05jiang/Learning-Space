"""Debug what chunk ID 20113 (ondemand.s) maps to and how to get its hash"""
import asyncio
import re
import httpx

async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }
    async with httpx.AsyncClient() as session:
        resp = await session.get("https://x.com", headers=headers, follow_redirects=True)
        text = resp.text

        # The new format seems to be: 20113:"ondemand.s"
        # Find the chunk ID for ondemand.s
        m = re.search(r'(\d+):"ondemand\.s"', text)
        if m:
            chunk_id = m.group(1)
            print(f"Chunk ID for ondemand.s: {chunk_id}")

            # Now look for the hash mapping: e[chunk_id]="hash" or p[chunk_id]="hash"
            # Common webpack pattern: e[20113]="abcdef"
            patterns = [
                rf'\b{chunk_id}\b[^"]*"([a-f0-9]{{8,}})"',  # number followed by hash
                rf'"([a-f0-9]{{8,}})"\s*:\s*\[?{chunk_id}',  # hash before number
                rf'\[{chunk_id}\]\s*=\s*"([a-f0-9]{{8,}})"',  # array assignment
                rf',{chunk_id}:"([a-f0-9]{{8,}})"',  # comma-separated
                rf'{chunk_id}:"([^"]+)"',  # direct mapping
            ]
            for pat in patterns:
                matches = re.findall(pat, text)
                if matches:
                    print(f"Pattern {pat!r} found: {matches[:3]}")

            # Look for p={...} or e={...} hash maps near the chunk ID
            # Find 300 chars around the chunk_id reference
            idx = text.find(f'{chunk_id}:"ondemand.s"')
            if idx >= 0:
                context = text[max(0, idx-500):idx+200]
                print(f"\nContext around chunk_id:")
                print(context)

        # Also check the main.js or other entry scripts
        # Find script tags
        script_srcs = re.findall(r'src="(https://abs\.twimg\.com/[^"]+\.js)"', text)
        print(f"\nScript sources ({len(script_srcs)} found):")
        for s in script_srcs[:5]:
            print(f"  {s}")

asyncio.run(main())
