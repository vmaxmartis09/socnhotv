import sys
import asyncio
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

profile = os.path.join(os.path.expanduser("~"), ".agent-browser", r"profiles\ai_profile")

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check"
            ]
        )
        page = await browser.new_page()
        try:
            await page.goto("https://accounts.google.com/v3/signin/confirmidentifier?continue=https://flow.google.com/&flowName=GlifWebSignIn&flowEntry=ServiceLogin", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
            btn = page.locator("button:has-text('Tiếp theo'), button:has-text('Next')").first
            if await btn.is_visible():
                print("Clicking Tiếp theo...")
                await btn.click()
                await page.wait_for_timeout(4000)
            print("Current URL:", page.url)
            await page.screenshot(path="shots/google_verify_screen.png")
            
            # Check what inputs are on screen
            password_input = page.locator("input[type='password']")
            if await password_input.count() > 0:
                print("Password input detected!")
            else:
                print("No password input.")
        except Exception as e:
            print("Error:", e)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
