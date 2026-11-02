import os
import sys
import asyncio
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")
PROFILE_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\AI_Agent_Profile")
PROJECT_URL = "https://flow.google.com/project/905a28b7-ceb4-4cf9-b92d-443050bd2d43"

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
        
        # In prompt bar bottom-right: button with tune icon (x: 943, y: 947 in full scale or x: ~1343)
        # Let's find all buttons in the bottom right prompt box
        print("[*] Finding buttons in prompt box...")
        prompt_box = page.locator(".ProseMirror, [role='textbox']").first
        print("[*] Prompt box found:", await prompt_box.count())

        # Click the tune settings button (it has text 'tune')
        tune_btn = page.locator("button:has-text('tune')").first
        if await tune_btn.count() > 0:
            print("[+] Found tune button! Clicking...")
            await tune_btn.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path="shots/flow_settings_panel.png")

        # Dump options in overlay container
        options = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('.cdk-overlay-container *')).map(el => {
                const text = el.innerText ? el.innerText.trim() : '';
                return text;
            }).filter(t => t.length > 0 && t.length < 50);
        }""")
        print("Settings options:", list(dict.fromkeys(options))[:40])

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
