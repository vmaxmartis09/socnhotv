import os
import sys
import time
import asyncio
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")
PROFILE_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\AI_Agent_Profile")
PROJECT_URL = "https://flow.google.com/project/905a28b7-ceb4-4cf9-b92d-443050bd2d43"
OUTPUT_DIR = os.path.abspath(r"assets/samples/sample_video/output")

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

        # Capture direct media download requests
        media_urls = []
        page.on("response", lambda r: media_urls.append(r.url) if any(x in r.url for x in [".mp4", "googlevideo", "video-generation", "videoplayback", "blob:"]) else None)

        await page.goto(PROJECT_URL, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3000)

        # Click the video card
        await page.mouse.click(325, 225)
        await page.wait_for_timeout(3000)

        # Inspect video element directly
        video_src = await page.evaluate("""() => {
            const v = document.querySelector('video');
            return v ? (v.currentSrc || v.src) : null;
        }""")
        print("[*] video.src in DOM:", video_src)

        # Click play button to start playback and trigger video stream network request
        play_btn = page.locator("button:has(.mat-icon:has-text('play_arrow')), button[aria-label='Phát']").first
        if await play_btn.is_visible():
            print("[+] Clicking Play button...")
            await play_btn.click()
            await page.wait_for_timeout(4000)

        print("[*] Captured Media URLs during playback:", media_urls)

        # Click download button (top right header icon with download)
        dl_btn = page.locator("button[aria-label='Tải nội dung nghe nhìn xuống'], button:has-text('download')").first
        if await dl_btn.is_visible():
            print("[+] Clicking download icon button...")
            async with page.expect_download(timeout=15000) as dl_info:
                await dl_btn.click()
            dl = await dl_info.value
            target_path = os.path.join(OUTPUT_DIR, "flow_ai_video_motion.mp4")
            await dl.save_as(target_path)
            print(f"[🎉] SAVED MP4 TO: {target_path} (Size: {os.path.getsize(target_path)} bytes)")

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
