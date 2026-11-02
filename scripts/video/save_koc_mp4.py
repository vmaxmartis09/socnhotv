import os
import sys
import time
import asyncio
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")
PROFILE_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\AI_Agent_Profile")
PROJECT_URL = "https://flow.google.com/project/905a28b7-ceb4-4cf9-b92d-443050bd2d43"
OUTPUT_DIR = os.path.abspath(r"assets/samples/sample_video/output")
FINAL_KOC_VIDEO = os.path.join(OUTPUT_DIR, "koc_model_real_ai_motion.mp4")

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

        print("[*] Accessing Flow timeline...")
        await page.goto(PROJECT_URL, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3000)

        # Click the KOC card on the left (first card at x: 300, y: 200)
        await page.mouse.click(300, 200)
        await page.wait_for_timeout(3000)

        # Click Play button
        play_btn = page.locator("button:has(.mat-icon:has-text('play_arrow')), button[aria-label='Phát']").first
        if await play_btn.is_visible():
            print("[+] Clicking Play button...")
            await play_btn.click()
            await page.wait_for_timeout(4000)

        if stream_url:
            print("[*] Captured stream URL! Downloading chunks...")
            # Use python urllib or playwright request with range 0-3207829 or direct fetch
            resp = await page.request.get(stream_url, headers=stream_headers, timeout=120000)
            print(f"[*] Response status: {resp.status}")
            if resp.status in [200, 206]:
                body = await resp.body()
                with open(FINAL_KOC_VIDEO, "wb") as f:
                    f.write(body)
                print(f"[🎉🎉🎉] HOÀN TẤT TẢI VIDEO KOC AI: {FINAL_KOC_VIDEO} ({os.path.getsize(FINAL_KOC_VIDEO)} bytes)")

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
