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

# KOC Model prompt in Flow
KOC_PROMPT = (
    "A photorealistic video of a beautiful young Vietnamese female fashion model "
    "wearing a chic white dress, smiling warmly at the camera, gently turning and posing, "
    "blinking naturally, smooth continuous motion, 4k ultra realistic, cinematic lighting"
)

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

        print("[*] Accessing Flow Studio for KOC Model generation...")
        await page.goto(PROJECT_URL, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3000)

        # Type prompt
        textbox = page.locator(".ProseMirror, [contenteditable='true']").first
        await textbox.click()
        await textbox.fill(KOC_PROMPT)
        await page.wait_for_timeout(1000)

        # Click send
        gen_btn = page.locator("button[aria-label='Bắt đầu tạo'], button.generate-icon-button").first
        await gen_btn.click()
        await page.wait_for_timeout(4000)

        # Check for approval button
        approve_span = page.locator("span:has-text('Phê duyệt')").first
        if await approve_span.is_visible():
            print("[+] Clicking Phê duyệt for KOC model...")
            box = await approve_span.bounding_box()
            if box:
                await page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
            await page.wait_for_timeout(4000)

        # Wait for video generation to complete
        print("[*] Rendering KOC Fashion Model with Veo 3.1...")
        for t in range(1, 19):
            await page.wait_for_timeout(10000)
            print(f"[*] Elapsed {t*10}s...")
            stop_btn = page.locator("button.generate-icon-button:has(.mat-icon:has-text('stop')), button:has-text('Dừng')")
            if await stop_btn.count() == 0 and t >= 3:
                print(f"[+] KOC Render complete at {t*10}s!")
                break

        await page.screenshot(path="shots/koc_flow_complete.png")

        # Open the latest video card on canvas (top left or first card)
        print("[*] Opening KOC video card...")
        # Get position of newest media card
        await page.mouse.click(325, 225)
        await page.wait_for_timeout(3000)

        # Click play to trigger videoplayback request
        play_btn = page.locator("button:has(.mat-icon:has-text('play_arrow')), button[aria-label='Phát']").first
        if await play_btn.is_visible():
            await play_btn.click()
            await page.wait_for_timeout(3000)

        if stream_url:
            print("[*] Fetching KOC Video MP4...")
            resp = await page.request.get(stream_url, headers=stream_headers)
            if resp.status in [200, 206]:
                body = await resp.body()
                with open(FINAL_KOC_VIDEO, "wb") as f:
                    f.write(body)
                print(f"[🎉] XUẤT VIDEO NGƯỜI MẪU AI KOC CHUYỂN ĐỘNG THẬT THÀNH CÔNG: {FINAL_KOC_VIDEO} ({os.path.getsize(FINAL_KOC_VIDEO)} bytes)")

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
