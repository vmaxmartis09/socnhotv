import os
import sys
import asyncio
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")
profile = os.path.join(os.path.expanduser("~"), ".agent-browser", r"profiles\ai_profile")

async def run():
    print("Launching Chromium with ai_profile...")
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile,
            headless=False,  # Headed as mandated by rule 2.2 for Google/Anti-bot
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check"
            ]
        )
        page = await browser.new_page()
        try:
            print("Navigating to https://flow.google.com/about...")
            await page.goto("https://flow.google.com/about", wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(3000)
            
            # Click "Create with Google Flow"
            print("Looking for 'Create with Google Flow' button...")
            btn = page.locator("text='Create with Google Flow'").first
            if await btn.is_visible():
                print("Clicking 'Create with Google Flow'...")
                await btn.click()
                await page.wait_for_timeout(5000)
            
            print("Current URL after click:", page.url)
            await page.screenshot(path="shots/flow_after_click.png")
            
            # Check if there is Google sign-in
            if "accounts.google.com" in page.url:
                print("Google Sign-In detected!")
                # Check for dinhthienthoai@gmail.com
                acc = page.locator("text='dinhthienthoai@gmail.com'").first
                if await acc.is_visible():
                    print("Found saved account dinhthienthoai@gmail.com! Clicking...")
                    await acc.click()
                    await page.wait_for_timeout(5000)
                    await page.screenshot(path="shots/google_account_clicked.png")
            
            # Check if reached studio
            print("Final URL:", page.url)
            await page.screenshot(path="shots/flow_studio_state.png")
            
        except Exception as e:
            print("Error:", e)
            await page.screenshot(path="shots/flow_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
