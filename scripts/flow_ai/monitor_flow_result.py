import os
import sys
import time
import asyncio
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
        await page.goto(PROJECT_URL, wait_until="domcontentloaded", timeout=60000)

        print("[*] Monitoring Google Flow generation progress...")
        
        # Poll for completion (up to 3 minutes)
        for i in range(18):
            await page.wait_for_timeout(10000)
            print(f"[*] Checking status at {(i+1)*10}s...")
            await page.screenshot(path=f"shots/flow_poll_status.png")

            # Check if video elements or download buttons appeared
            video_tags = await page.locator("video, [data-media-type='video'], .media-card").count()
            print(f"[*] Detected video elements/cards: {video_tags}")

            # Check if stop button turned back into arrow_forward (done generating)
            stop_btn = page.locator("button:has-text('Dừng'), button:has(.mat-icon:has-text('stop'))")
            if await stop_btn.count() == 0:
                print("[+] Generation completed! Stop button is gone.")
                break

        await page.screenshot(path="shots/flow_generation_finished.png")

        # Find any video source URLs
        video_srcs = await page.evaluate("""() => {
            const list = [];
            document.querySelectorAll('video').forEach(v => {
                if (v.src) list.push(v.src);
                v.querySelectorAll('source').forEach(s => { if (s.src) list.push(s.src); });
            });
            return list;
        }""")
        print("Found video source URLs:", video_srcs)

        # Look for download buttons or action buttons
        actions = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('button, a')).map(el => ({
                text: el.innerText.trim(),
                aria: el.getAttribute('aria-label'),
                href: el.getAttribute('href')
            })).filter(a => a.text || a.aria || a.href);
        }""")
        with open("shots/flow_actions.txt", "w", encoding="utf-8") as f:
            for a in actions:
                f.write(str(a) + "\n")

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
