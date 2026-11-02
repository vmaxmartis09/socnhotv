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

        # Listen for any video blobs or downloaded files
        page.on("response", lambda r: print(f"[MEDIA] {r.status} {r.url[:120]}") if any(k in r.url for k in ["video", "mp4", "blob:", "googlevideo", "video-generation"]) else None)

        print("[*] Reconnecting to active Flow Project...")
        await page.goto(PROJECT_URL, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3000)

        # Loop and check for completion every 10s up to 180s
        for sec in range(10, 190, 10):
            await page.wait_for_timeout(10000)
            print(f"[*] Waiting for Veo AI generation... {sec}s")
            await page.screenshot(path="shots/flow_render_progress.png")

            # Check if stop button has reverted to arrow_forward (finished)
            stop_btn = page.locator("button.generate-icon-button:has(.mat-icon:has-text('stop')), button:has-text('Dừng')")
            if await stop_btn.count() == 0:
                print(f"[🎉] RENDER COMPLETE AT {sec}s!")
                break

        await page.screenshot(path="shots/flow_render_complete.png")

        # Extract all generated video elements and links
        videos = await page.evaluate("""() => {
            const list = [];
            document.querySelectorAll('video').forEach(v => {
                if (v.src) list.push(v.src);
                v.querySelectorAll('source').forEach(s => { if (s.src) list.push(s.src); });
            });
            return list;
        }""")
        print("Generated Videos found:", videos)

        # Look for download buttons or action menus on generated cards
        cards = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('.media-card, [class*=\"card\"], [class*=\"asset\"], [class*=\"output\"]')).map(c => ({
                text: c.innerText ? c.innerText.trim().slice(0, 60) : '',
                html: c.innerHTML.slice(0, 200)
            }));
        }""")
        print("Generated Cards count:", len(cards))

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
