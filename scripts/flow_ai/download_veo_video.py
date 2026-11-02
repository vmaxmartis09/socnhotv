import os
import sys
import time
import asyncio
import urllib.request
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")
PROFILE_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\AI_Agent_Profile")
PROJECT_URL = "https://flow.google.com/project/905a28b7-ceb4-4cf9-b92d-443050bd2d43"
OUTPUT_DIR = os.path.abspath(r"assets/samples/sample_video/output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
        await page.goto(PROJECT_URL, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3000)

        # Click the video card on the left canvas to open video viewer
        # In screenshot, the big video card is at x: ~325, y: ~225
        print("[*] Clicking the generated video card on canvas...")
        await page.mouse.click(325, 225)
        await page.wait_for_timeout(3000)

        await page.screenshot(path="shots/flow_video_viewer.png")

        # Now search for video element or download button
        v_info = await page.evaluate("""() => {
            const v = document.querySelector('video');
            const btns = Array.from(document.querySelectorAll('button, a')).map(b => ({
                text: b.innerText.trim(),
                aria: b.getAttribute('aria-label'),
                href: b.getAttribute('href')
            })).filter(b => b.text || b.aria || b.href);
            return {
                videoSrc: v ? (v.src || v.currentSrc) : null,
                buttons: btns
            };
        }""")
        print("Video info in viewer:", v_info)

        # If download button exists, click it
        download_btn = page.locator("button[aria-label*='Tải'], button[aria-label*='Download'], button:has-text('Tải xuống'), a[download]").first
        if await download_btn.count() > 0:
            print("[+] Found download button! Triggering download...")
            async with page.expect_download() as dl_info:
                await download_btn.click()
            download = await dl_info.value
            target_path = os.path.join(OUTPUT_DIR, "google_veo_generated_video.mp4")
            await download.save_as(target_path)
            print(f"[🎉🎉🎉] DOWNLOADED VEO VIDEO SUCCESSFULLY TO: {target_path} (Size: {os.path.getsize(target_path)} bytes)")

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
