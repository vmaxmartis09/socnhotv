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
        await page.goto(PROJECT_URL, wait_until="networkidle", timeout=60000)

        # 1. Click "Luôn phê duyệt" (Always Approve) to permanently auto-approve all generations
        approve_btn = page.locator("button:has-text('Luôn phê duyệt'), div:has-text('Luôn phê duyệt')").first
        if await approve_btn.count() == 0:
            approve_btn = page.locator("button:has-text('Phê duyệt'), div:has-text('Phê duyệt')").first

        if await approve_btn.is_visible():
            print("[+] Clicking 'Luôn phê duyệt' (Always Approve)...")
            await approve_btn.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path="shots/flow_approved_state.png")

        # 2. Wait for Veo generation to finish (renders in background)
        print("[*] Veo 3.1 generation is now actively rendering in Flow Studio!")
        for step in range(1, 25):
            await page.wait_for_timeout(10000)
            print(f"[*] Render progress: {step*10}s elapsed...")
            await page.screenshot(path="shots/flow_rendering_active.png")

            # Check if video tag appeared or card is rendered
            video_el = page.locator("video")
            if await video_el.count() > 0:
                print(f"[🎉] FOUND {await video_el.count()} RENDERED VIDEOS!")
                # Get src
                src = await video_el.first.get_attribute("src")
                print("Video src:", src)
                break

        await page.screenshot(path="shots/flow_render_final_check.png")
        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
