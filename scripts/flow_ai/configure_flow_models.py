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

        # Open tune settings
        tune_btn = page.locator("button:has-text('tune')").first
        await tune_btn.click()
        await page.wait_for_timeout(1000)

        # 1. Image settings: 9:16
        img_916 = page.locator("button:has-text('9:16')").first
        if await img_916.count() > 0:
            print("[+] Selecting Image aspect ratio 9:16...")
            await img_916.click()

        # 2. Video settings: 9:16
        vid_916 = page.locator("button:has-text('9:16')").last
        if await vid_916.count() > 0:
            print("[+] Selecting Video aspect ratio 9:16...")
            await vid_916.click()

        # 3. Video model dropdown: select Veo model
        vid_model_select = page.locator("mat-select, [role='combobox']").last
        if await vid_model_select.count() > 0:
            print("[+] Opening Video model dropdown...")
            await vid_model_select.click()
            await page.wait_for_timeout(1000)
            # Find Veo options
            veo_option = page.locator("mat-option:has-text('Veo'), [role='option']:has-text('Veo')").first
            if await veo_option.count() > 0:
                print("[+] Found Veo option:", await veo_option.inner_text())
                await veo_option.click()
            else:
                # print all options
                opts = await page.locator("mat-option, [role='option']").all_inner_texts()
                print("All video model options:", opts)

        # 4. Save settings
        save_btn = page.locator("button:has-text('Lưu')").first
        if await save_btn.count() > 0:
            print("[+] Clicking 'Lưu'...")
            await save_btn.click()
            await page.wait_for_timeout(1500)

        await page.screenshot(path="shots/flow_settings_saved.png")
        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
