import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

def check_cdp_available():
    try:
        r = requests.get("http://localhost:9222/json/version", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

def main():
    print("="*70)
    print("👀 AGENT ĐANG CHỜ CỔNG CHROME 9222 TỪ BẠN...")
    print("="*70)
    print("[*] Hãy nhấp đúp vào file 'scripts/legacy_windows/mo_google_flow.bat' trong thư mục vmax.")
    
    # Chờ tối đa 5 phút
    start_time = time.time()
    connected = False
    while time.time() - start_time < 300:
        if check_cdp_available():
            connected = True
            print("\n[+] ĐÃ PHÁT HIỆN CHROME CDP 9222 KẾT NỐI THÀNH CÔNG!")
            break
        time.sleep(2)
        print(".", end="", flush=True)

    if not connected:
        print("\n[!] Hết thời gian chờ kết nối cổng 9222.")
        return

    # Kết nối Playwright tới Chrome 9222
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        print("[+] Agent đã liên kết thành công với Chrome trên màn hình của bạn!")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        
        print(f"[*] Trang hiện tại: {page.url}")
        page.screenshot(path="shots/cdp_connected_state.png")

        # Chờ đăng nhập Google Flow
        print("[*] Đang kiểm tra trạng thái Google Flow...")
        if "flow.google.com" not in page.url:
            page.goto("https://flow.google.com", timeout=45000)

        # Chờ người dùng đăng nhập xong
        while "flow.google.com" in page.url and "accounts.google.com" in page.url:
            print("[*] Đang chờ bạn đăng nhập hoàn tất trên màn hình...", flush=True)
            time.sleep(3)

        print("[🎉] ĐÃ TRUY CẬP VÀO STUDIO GOOGLE FLOW!")
        page.screenshot(path="shots/flow_studio_ready.png")

if __name__ == "__main__":
    main()
