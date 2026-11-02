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

    def handle_popup(popup):
        print(f"[POPUP] Popup opened: {popup.url}")
        try:
            popup.wait_for_load_state("domcontentloaded", timeout=20000)
            time.sleep(3)
            popup.screenshot(path="shots/everai_oauth_popup_1.png")
            # Click account email
            acc = popup.locator("text=dinhthienthoai@gmail.com, [data-identifier*='gmail.com'], div[data-email], div[role='link']").first
            if acc.count() > 0:
                print("[POPUP] Clicking Google account...")
                acc.click()
                time.sleep(3)
                popup.screenshot(path="shots/everai_oauth_popup_clicked.png")
            
            # If prompt to continue
            cont = popup.locator("button:has-text('Continue'), button:has-text('Tiếp tục'), button:has-text('Allow'), button:has-text('Cho phép'), #submit_approve_access").first
            if cont.count() > 0 and cont.is_visible():
                print("[POPUP] Clicking Continue/Tiếp tục...")
                cont.click()
                time.sleep(3)
        except Exception as e:
            print(f"[POPUP] Error/Info: {e}")

    ctx.on("page", handle_popup)

    print("[1] Navigating to https://everai.vn/login?next=/ ...")
    page.goto("https://everai.vn/login?next=/", wait_until="domcontentloaded", timeout=45000)
    time.sleep(3)
    page.screenshot(path="shots/everai_login_screen.png")

    # Click 'Đăng nhập với Google'
    google_btn = page.locator("button:has-text('Đăng nhập với Google'), a:has-text('Đăng nhập với Google')").first
    if google_btn.is_visible():
        print("[2] Clicking 'Đăng nhập với Google'...")
        google_btn.click()
        time.sleep(6)

    # In case redirect happened in same tab
    print("Checking current page URL:", page.url)
    if "accounts.google.com" in page.url:
        print("[REDIRECT] On Google login in main tab...")
        page.screenshot(path="shots/everai_google_redirect.png")
        acc = page.locator("text=dinhthienthoai@gmail.com, [data-identifier*='gmail.com'], div[data-email]").first
        if acc.count() > 0:
            print("Clicking Google account on main page...")
            acc.click()
            time.sleep(4)
        cont = page.locator("button:has-text('Continue'), button:has-text('Tiếp tục')").first
        if cont.count() > 0 and cont.is_visible():
            cont.click()
            time.sleep(4)

    # Wait for return to everai
    time.sleep(5)
    page.screenshot(path="shots/everai_after_login.png")
    print("Post-login URL:", page.url)

    # Print navigation links/buttons on page
    links = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a, button, [role="button"]')).map(el => ({
            tag: el.tagName,
            text: (el.innerText || '').trim().replace(/\\s+/g, ' '),
            href: el.href || ''
        })).filter(x => x.text || x.href);
    }""")
    print("\nAvailable links after login:")
    for l in links:
        if any(kw in l['text'].lower() or kw in l['href'].lower() for kw in ['giọng', 'voice', 'nhân bản', 'chuyển văn bản', 'clone', 'tts', 'menu']):
            print(" ->", l)

    ctx.close()
