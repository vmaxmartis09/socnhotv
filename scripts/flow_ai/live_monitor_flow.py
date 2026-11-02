import os
import sys
import time
import asyncio
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")
PROFILE_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\AI_Agent_Profile")
PROJECT_URL = "https://flow.google.com/project/905a28b7-ceb4-4cf9-b92d-443050bd2d43"

async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=True,
            viewport={"width": 1440, "height": 900},
            args=["--disable-blink-features=AutomationControlled", "--no-first-run"]
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        page.on("response", lambda r: print(f"[NET] {r.status} {r.url[:110]}") if any(k in r.url for k in ["video", "image", "asset", "media", "batchexecute", "blob:"]) else None)

        print("[*] Opening Flow project to observe live generation...")
        await page.goto(PROJECT_URL, wait_until="networkidle", timeout=60000)

        # Wait while observing the canvas
        for t in range(1, 13):
            await page.wait_for_timeout(10000)
            print(f"[*] Elapsed: {t*10}s...")
            await page.screenshot(path=f"shots/flow_live_{t*10}s.png")

            # Check for media cards or newly spawned cards in the session chat / canvas
            cards = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('img, video, [class*=\"media\"], [class*=\"card\"], [class*=\"asset\"]')).map(el => ({
                    tag: el.tagName,
                    src: (el.src || el.getAttribute('data-src') || '').slice(0, 100),
                    className: el.className
                })).filter(c => c.src.startsWith('http') || c.src.startsWith('blob') || c.src.startsWith('data'));
            }""")
            if cards:
                print(f"[+] Found {len(cards)} generated media elements:", cards)

            # Check if chat response message arrived
            chat_msgs = await page.locator(".chat-message, [class*='message'], [class*='bubble']").all_inner_texts()
            if chat_msgs:
                print(f"[*] Chat messages: {chat_msgs[-2:]}")

        await page.screenshot(path="shots/flow_live_final.png")
        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
