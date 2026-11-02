import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

USER_PROFILE_DIR = os.environ.get("USER_PROFILE_DIR", os.path.join(os.path.expanduser("~"), ".agent-browser", "profiles", "ai_profile"))
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
os.makedirs("shots", exist_ok=True)

with sync_playwright() as p:
    args = [
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1280,900"
    ]
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=USER_PROFILE_DIR,
        executable_path=CHROME_EXE,
        headless=False,
        args=args,
        viewport=None
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    print("[1] Navigating to https://everai.vn/login?next=/ ...")
    page.goto("https://everai.vn/login?next=/", wait_until="domcontentloaded", timeout=45000)
    time.sleep(3)

    google_btn = page.locator("button:has-text('Đăng nhập với Google')").first
    if google_btn.is_visible():
        print("[2] Clicking Google login button...")
        google_btn.click()
        time.sleep(5)

    print("[3] Current URL:", page.url)

    # If on Google account chooser
    if "accounts.google.com" in page.url:
        print("[4] On Google Login page, finding account dinhthienthoai@gmail.com...")
        acc = page.locator("text=dinhthienthoai@gmail.com, [data-email*='dinhthienthoai'], div[data-identifier*='dinhthienthoai']").first
        if acc.count() > 0:
            print(" -> Found account! Clicking...")
            acc.click()
            time.sleep(5)
        else:
            print(" -> Account email not text matched, trying first role='link'...")
            first_acc = page.locator("li:has([data-email]), ul li div[role='link']").first
            if first_acc.count() > 0:
                first_acc.click()
                time.sleep(5)

        # If consent / continue prompt
        print("[5] Checking for consent / Continue button...")
        for _ in range(3):
            cont = page.locator("button:has-text('Continue'), button:has-text('Tiếp tục'), button:has-text('Allow'), button:has-text('Cho phép'), #submit_approve_access").first
            if cont.count() > 0 and cont.is_visible():
                print(" -> Clicking Continue button...")
                cont.click()
                time.sleep(4)

    # Wait for redirect back to everai.vn
    print("[6] Waiting for redirect to everai.vn...")
    for i in range(10):
        time.sleep(2)
        print(f" -> [{i+1}] Current URL: {page.url}")
        if "everai.vn" in page.url and "login" not in page.url:
            print("SUCCESSFULLY LOGGED IN!")
            break

    time.sleep(3)
    try:
        page.screenshot(path="shots/everai_dashboard_logged_in.png", timeout=5000)
    except Exception as e:
        print("Screenshot warning:", e)

    # Print current page title and interactive links
    print("\nPage title:", page.title())
    menu_items = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a, button, [role="button"]')).map(el => ({
            tag: el.tagName,
            text: (el.innerText || '').trim().replace(/\\s+/g, ' '),
            href: el.href || ''
        })).filter(x => x.text && x.text.length < 50);
    }""")
    print("Menu & actions on dashboard:")
    for m in menu_items[:30]:
        print(" *", m)

    ctx.close()
