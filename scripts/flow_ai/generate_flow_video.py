import os
import sys
import asyncio
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")
PROFILE_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\AI_Agent_Profile")
PROJECT_URL = "https://flow.google.com/project/905a28b7-ceb4-4cf9-b92d-443050bd2d43"
IMG_PATH = os.path.abspath(r"assets/samples/sample_video/images\01_hook_model_cafe.jpg")

PROMPT = (
    "A photorealistic video of this beautiful Asian young woman smiling in the cafe, "
    "gently turning her head, softly breathing and blinking naturally, "
    "holding the cardigan with smooth continuous motion, high quality cinematic 4k"
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

        # 1. Upload sample image as first frame
        print(f"[*] Uploading reference image: {IMG_PATH}")
        add_btn = page.locator("button:has-text('add')").last
        async with page.expect_file_chooser() as fc_info:
            await add_btn.click()
        file_chooser = await fc_info.value
        await file_chooser.set_files(IMG_PATH)
        await page.wait_for_timeout(4000)
        print("[+] Image uploaded to prompt bar!")

        # 2. Enter prompt into ProseMirror / contenteditable
        print("[*] Entering motion prompt...")
        textbox = page.locator(".ProseMirror, [contenteditable='true']").last
        await textbox.click()
        await textbox.fill(PROMPT)
        await page.wait_for_timeout(1500)

        await page.screenshot(path="shots/flow_prompt_ready.png")

        # 3. Submit generation
        submit_btn = page.locator("button[type='submit'], button:has-text('arrow_forward')").last
        print("[+] Clicking Submit/Generate button...")
        await submit_btn.click()
        await page.wait_for_timeout(6000)

        await page.screenshot(path="shots/flow_generation_started.png")
        print("[*] Generation triggered! Status screenshot saved.")

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
