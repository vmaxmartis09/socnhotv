import os
import sys
import asyncio
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")
PROFILE_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\AI_Agent_Profile")

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
        await page.goto("https://flow.google.com/?pli=1", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(4000)

        # Dismiss multi-step onboarding modals
        for step in range(6):
            backdrop = page.locator(".cdk-overlay-backdrop-showing")
            if await backdrop.count() == 0:
                print(f"[+] All modals cleared at step {step}!")
                break
            
            # Scroll any dialog container to bottom in case button is disabled until scrolled
            await page.evaluate("""() => {
                document.querySelectorAll('.cdk-overlay-container *').forEach(el => {
                    if (el.scrollHeight > el.clientHeight) {
                        el.scrollTop = el.scrollHeight;
                    }
                });
            }""")
            await page.wait_for_timeout(800)

            clicked = False
            for btn_text in ["Tiếp theo", "Tiếp tục", "Đồng ý", "Bắt đầu", " Chấp nhận", "Got it", "Continue", "Next", "I agree"]:
                btn = page.locator(f".cdk-overlay-container button:has-text('{btn_text}')").first
                if await btn.count() > 0 and await btn.is_visible():
                    print(f"[+] Step {step}: Clicking modal button '{btn_text}'")
                    await btn.click(force=True)
                    clicked = True
                    await page.wait_for_timeout(2000)
                    break
            if not clicked:
                print(f"[*] Step {step}: No matching text button found, dumping overlay buttons...")
                overlay_btns = await page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('.cdk-overlay-container button')).map(b => ({
                        text: b.innerText.trim(),
                        disabled: b.disabled
                    }));
                }""")
                print("Overlay buttons:", overlay_btns)
                break

        await page.screenshot(path="shots/flow_modals_cleared.png")

        # Click "+ Dự án mới"
        new_proj_btn = page.locator("button.new-project-button, button:has-text('Dự án mới')").first
        if await new_proj_btn.is_visible():
            print("[+] Clicking '+ Dự án mới'...")
            await new_proj_btn.click(force=True)
            await page.wait_for_timeout(8000)

        print("[*] Current Project URL:", page.url)
        await page.screenshot(path="shots/flow_project_studio.png")

        # Dump all buttons and inputs in the studio
        elements = await page.evaluate("""() => {
            const items = [];
            document.querySelectorAll('button, [role="button"], textarea, input, [contenteditable="true"]').forEach((el, idx) => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    items.push({
                        tag: el.tagName,
                        text: (el.innerText || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().slice(0, 80),
                        role: el.getAttribute('role'),
                        type: el.getAttribute('type'),
                        className: (el.className || '').toString().slice(0, 60),
                        x: Math.round(rect.x),
                        y: Math.round(rect.y)
                    });
                }
            });
            return items;
        }""")
        print("=== STUDIO INTERACTIVE ELEMENTS ===")
        for el in elements:
            print(el)

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
