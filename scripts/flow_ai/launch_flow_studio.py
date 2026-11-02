import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

PROFILE_DIR = os.environ.get("BROWSER_PROFILE_DIR", os.path.join(os.path.expanduser("~"), ".agent-browser", "profiles", r"ai_profile"))
TARGET_URL = "https://accounts.google.com/v3/signin/challenge/pwd?continue=https%3A%2F%2Fflow.google.com%2F&flowEntry=ServiceLogin&flowName=GlifWebSignIn"

def run():
    print("="*75)
    print("🌐 ĐANG MỞ GOOGLE FLOW TRÊN MÀN HÌNH ĐỂ KẾT NỐI VEO 3.1...")
    print("="*75, flush=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                "--start-maximized"
            ],
            no_viewport=True
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(TARGET_URL, timeout=45000)
        print("[+] Đã mở cửa sổ đăng nhập Google Flow trên màn hình của bạn!", flush=True)
        print("[*] Hãy nhập mật khẩu cho tài khoản dinhthienthoai@gmail.com để vào Studio Google Flow.", flush=True)

        # Lắng nghe cho đến khi URL chuyển sang flow.google.com (đăng nhập thành công)
        while len(context.pages) > 0:
            current_url = page.url
            if "flow.google.com" in current_url and "accounts.google.com" not in current_url:
                print(f"🎉 ĐĂNG NHẬP THÀNH CÔNG VÀO GOOGLE FLOW: {current_url}", flush=True)
                page.screenshot(path="shots/flow_logged_in.png")
                # Giữ thêm để agent tiếp quản
                time.sleep(10)
                break
            time.sleep(2)

if __name__ == "__main__":
    run()
