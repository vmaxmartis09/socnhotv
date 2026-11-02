import os
import sys
import asyncio
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")
PROFILE_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\AI_Agent_Profile")
PROJECT_URL = "https://flow.google.com/project/905a28b7-ceb4-4cf9-b92d-443050bd2d43"

PROMPT = (
    "A smooth cinematic photorealistic video of a beautiful young Vietnamese woman "
    "wearing an elegant cream cardigan, standing in a cozy cafe, smiling warmly, "
    "gently turning her head, blinking naturally, and moving her hands gracefully. "
    "Continuous fluid realistic motion, 4k ultra realistic, highly detailed face."
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
        await page.goto(PROJECT_URL, wait_until="networkidle", timeout=60000)

        # Type prompt into ProseMirror textbox
        print("[*] Typing video prompt into textbox...")
        textbox = page.locator(".ProseMirror, [contenteditable='true']").first
        await textbox.click()
        await textbox.fill(PROMPT)
        await page.wait_for_timeout(2000)

        # Check generate button status
        gen_btn = page.locator("button[aria-label='Bắt đầu tạo'], button.generate-icon-button").first
        is_disabled = await gen_btn.is_disabled()
        print(f"[*] Generate button disabled status: {is_disabled}")

        await page.screenshot(path="shots/flow_prompt_typed.png")

        # Click generate
        print("[+] Triggering generation...")
        await gen_btn.click(force=True)
        await page.wait_for_timeout(5000)

        await page.screenshot(path="shots/flow_generation_dispatched.png")
        print("[+] Dispatched successfully!")

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
