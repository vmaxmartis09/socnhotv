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

        video_bytes = None

        async def handle_response(response):
            nonlocal video_bytes
            if "videoplayback" in response.url:
                print(f"[+] Intercepting videoplayback stream ({response.status})...")
                try:
                    video_bytes = await response.body()
                    print(f"[+] Downloaded {len(video_bytes)} bytes from stream!")
                except Exception as e:
                    print("Stream capture error:", e)

        page.on("response", handle_response)

        await page.goto(PROJECT_URL, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3000)

        # Click video card on canvas
        print("[*] Opening video timeline player...")
        await page.mouse.click(325, 225)
        await page.wait_for_timeout(2500)

        # Click play button
        play_btn = page.locator("button:has(.mat-icon:has-text('play_arrow')), button[aria-label='Phát']").first
        if await play_btn.is_visible():
            print("[+] Clicking Play button...")
            await play_btn.click()
            await page.wait_for_timeout(6000)

        if video_bytes and len(video_bytes) > 50000:
            with open(TARGET_FILE, "wb") as f:
                f.write(video_bytes)
            print(f"[🎉🎉🎉] XUẤT VIDEO VEO CHUYỂN ĐỘNG THỰC TẾ THÀNH CÔNG: {TARGET_FILE} ({os.path.getsize(TARGET_FILE)} bytes)")
        else:
            print("[!] Chưa bắt được body stream, kiểm tra lại...")

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
