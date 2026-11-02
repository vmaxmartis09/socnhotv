import os
import sys
import time
import asyncio
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")
PROFILE_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\AI_Agent_Profile")
PROJECT_URL = "https://flow.google.com/project/905a28b7-ceb4-4cf9-b92d-443050bd2d43"
OUTPUT_DIR = os.path.abspath(r"assets/samples/sample_video/output")
TARGET_FILE = os.path.join(OUTPUT_DIR, "veo_real_ai_motion.mp4")

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

        stream_url = None
        stream_headers = {}

        def on_req(req):
            nonlocal stream_url, stream_headers
            if "videoplayback" in req.url:
                stream_url = req.url
                stream_headers = req.headers

        page.on("request", on_req)

        await page.goto(PROJECT_URL, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3000)

        # Open video card
        await page.mouse.click(325, 225)
        await page.wait_for_timeout(3000)

        # Click play to trigger request
        play_btn = page.locator("button:has(.mat-icon:has-text('play_arrow')), button[aria-label='Phát']").first
        if await play_btn.is_visible():
            await play_btn.click()
            await page.wait_for_timeout(3000)

        if stream_url:
            print("[+] Captured stream URL with auth tokens!")
            # Use page.request.get to download with identical browser session/cookies/auth!
            print("[*] Fetching video via Playwright APIRequestContext...")
            resp = await page.request.get(stream_url, headers=stream_headers)
            print(f"[*] Response status: {resp.status}")
            if resp.status in [200, 206]:
                body = await resp.body()
                with open(TARGET_FILE, "wb") as f:
                    f.write(body)
                print(f"[🎉🎉🎉] ĐÃ LƯU VIDEO GOOGLE VEO 3.1 CHUYỂN ĐỘNG THỰC TẾ: {TARGET_FILE} ({os.path.getsize(TARGET_FILE)} bytes)")
            else:
                print("Failed status:", resp.status)

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
