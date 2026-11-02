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

        await page.goto(PROJECT_URL, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3000)

        # Click the lower "Phê duyệt" button
        spans = await page.locator("span:has-text('Phê duyệt')").all()
        print(f"[*] Found {len(spans)} Phê duyệt spans...")
        if spans:
            target_span = spans[-1]
            box = await target_span.bounding_box()
            if box:
                print(f"[+] Clicking Phê duyệt at ({box['x']}, {box['y']})...")
                await page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                await page.wait_for_timeout(3000)

        # Monitor until the second video card appears in the chat session
        print("[*] Waiting for Veo 3.1 KOC video to render...")
        for t in range(1, 20):
            await page.wait_for_timeout(8000)
            print(f"[*] Elapsed {t*8}s...")
            # Check cards in chat panel
            done = await page.evaluate("""() => {
                const msgs = document.querySelectorAll('.chat-message, [class*=\"bubble\"], [class*=\"output\"]');
                return Array.from(msgs).some(m => m.innerText.includes('A photorealistic video of a beautiful young Vietnamese') && m.querySelector('img, video, [class*=\"thumbnail\"]'));
            }""")
            if done:
                print(f"[🎉] KOC Video rendered at {t*8}s!")
                break

        await page.screenshot(path="shots/koc_rendered_in_chat.png")

        # Click the newly rendered video card in chat
        koc_thumb = page.locator(".chat-panel img, .chat-message img, [class*='thumbnail']").last
        if await koc_thumb.count() > 0:
            print("[+] Clicking KOC video thumbnail...")
            await koc_thumb.click()
            await page.wait_for_timeout(3000)

            # Click Play
            play_btn = page.locator("button:has(.mat-icon:has-text('play_arrow')), button[aria-label='Phát']").first
            if await play_btn.is_visible():
                await play_btn.click()
                await page.wait_for_timeout(3000)

        await page.screenshot(path="shots/koc_timeline.png")

        if stream_url:
            print("[*] Fetching video buffer...")
            resp = await page.request.get(stream_url, headers=stream_headers, timeout=60000)
            if resp.status in [200, 206]:
                body = await resp.body()
                with open(FINAL_KOC_VIDEO, "wb") as f:
                    f.write(body)
                print(f"[🎉🎉🎉] HOÀN TẤT! ĐÃ LƯU KOC VIDEO MP4: {FINAL_KOC_VIDEO} ({os.path.getsize(FINAL_KOC_VIDEO)} bytes)")

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
