import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

USER_PROFILE_DIR = os.environ.get("USER_PROFILE_DIR", os.path.join(os.path.expanduser("~"), ".agent-browser", "profiles", "ai_profile"))
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
AUDIO_FILE = os.path.abspath(r"assets\cloned_voices\koc_neil_girl\mau_voice_45s_everai.mp3")
os.makedirs("shots", exist_ok=True)
os.makedirs("output", exist_ok=True)

SCRIPT_TEXT = (
    "Mấy bà ơi, hôm nay em lên tiếp một mã áo thun chống nắng siêu đỉnh cho mùa hè này luôn nha! "
    "Chất thì rất là co giãn đàn hồi, mặc thoải mái lắm luôn ý, mấy bà bấm ngay vào giỏ hàng góc trái kẻo hết size nhá!"
)

print("="*60)
print("🚀 VMAX AUTO EVERAI VOICE CLONING (CHUẨN VIDEO @benaithucchien)")
print("="*60)

with sync_playwright() as p:
    args = [
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1280,920"
    ]
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=USER_PROFILE_DIR,
        executable_path=CHROME_EXE,
        headless=False,
        args=args,
        viewport=None
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    # Step 1: Đi tới everai.vn
    print("[1] Đang mở https://everai.vn/login?next=/ trên màn hình...")
    page.goto("https://everai.vn/login?next=/", wait_until="domcontentloaded", timeout=45000)
    time.sleep(3)

    # Click Đăng nhập với Google nếu chưa đăng nhập
    google_btn = page.locator("button:has-text('Đăng nhập với Google')").first
    if google_btn.is_visible():
        print("[2] Bấm nút 'Đăng nhập với Google'...")
        google_btn.click()
        time.sleep(4)

    # Chờ người dùng xác nhận Google (nếu Google hỏi mật khẩu/OTP) hoặc tự động chuyển tiếp
    print("[3] Đang theo dõi URL để tự động tiếp quản ngay khi đăng nhập xong...")
    logged_in = False
    for i in range(120): # Chờ tối đa 4 phút, kiểm tra mỗi 2 giây
        curr_url = page.url
        # Chỉ khi domain chính thức là everai.vn và không ở trang login
        if curr_url.startswith("https://everai.vn") and "/login" not in curr_url and "/sign-up" not in curr_url:
            print(f"[THÀNH CÔNG] Đã đăng nhập vào EverAI! URL: {curr_url}")
            logged_in = True
            break
        
        # Nếu đang ở trang chọn tài khoản Google thì tự động click tài khoản
        if "accounts.google.com" in curr_url:
            acc = page.locator("[data-email*='dinhthienthoai'], div[data-identifier*='dinhthienthoai']").first
            if acc.count() > 0 and acc.is_visible():
                print(" -> Tự động click tài khoản dinhthienthoai@gmail.com...")
                try:
                    acc.click()
                except Exception:
                    pass
            cont = page.locator("button:has-text('Continue'), button:has-text('Tiếp tục'), #submit_approve_access").first
            if cont.count() > 0 and cont.is_visible():
                try:
                    cont.click()
                except Exception:
                    pass

        time.sleep(2)

    if not logged_in:
        print("[TIMEOUT] Chưa đăng nhập xong.")
        ctx.close()
        sys.exit(1)

    time.sleep(4)
    page.screenshot(path="shots/everai_03_logged_in.png")

    # Step 2: Mở menu -> Nhân bản giọng nói
    print("[4] Đang chuyển đến tính năng 'Nhân bản giọng nói'...")
    menu_clone = page.get_by_text("Nhân bản giọng nói").first
    if menu_clone.count() > 0 and menu_clone.is_visible():
        menu_clone.click()
    else:
        # Thử mở thanh menu bên trái (3 gạch)
        nav_toggle = page.locator("button[aria-label*='menu'], .navbar-toggler, [class*='hamburger'], div:has(> svg)").first
        if nav_toggle.count() > 0:
            nav_toggle.click()
            time.sleep(1)
        menu_clone = page.get_by_text("Nhân bản giọng nói").first
        if menu_clone.count() > 0:
            menu_clone.click()
        else:
            page.goto("https://everai.vn/voice-cloning", wait_until="domcontentloaded")

    time.sleep(4)
    page.screenshot(path="shots/everai_04_clone_page.png")
    print("URL Nhân bản giọng nói:", page.url)

    # Step 3: Tải file audio mẫu lên (mau_voice_45s_everai.mp3)
    print(f"[5] Đang upload file audio mẫu: {AUDIO_FILE} ...")
    file_input = page.locator("input[type='file']").first
    if file_input.count() > 0:
        file_input.set_input_files(AUDIO_FILE)
    else:
        upload_area = page.locator(".dropzone, [class*='upload']").or_(page.get_by_text("Chọn hoặc kéo thả")).first
        with page.expect_file_chooser() as fc_info:
            upload_area.click()
        fc = fc_info.value
        fc.set_files(AUDIO_FILE)

    time.sleep(5)
    page.screenshot(path="shots/everai_05_audio_uploaded.png")

    # Step 4: Tích chọn 'Loại bỏ nhiễu nền khỏi âm thanh mẫu'
    noise_cb = page.locator("label:has-text('Loại bỏ nhiễu'), input[type='checkbox']").first
    if noise_cb.count() > 0:
        print("[6] Tích chọn lọc nhiễu nền...")
        try:
            if not noise_cb.is_checked():
                noise_cb.click()
        except Exception:
            pass

    # Step 5: Cấu hình: Ngôn ngữ Việt Nam, Use Case Vlog/Quảng cáo, Model Everai v1.6
    print("[7] Điền kịch bản nghe thử & chọn model...")
    # Điền kịch bản
    text_preview = page.locator("textarea, input[placeholder*='văn bản'], div[contenteditable='true']").first
    if text_preview.count() > 0:
        text_preview.fill(SCRIPT_TEXT)

    # Tích điều khoản cam kết bản quyền
    terms_cb = page.get_by_text("Tôi xác nhận rằng tôi có quyền").or_(page.locator("input[type='checkbox']")).last
    if terms_cb.count() > 0:
        try:
            terms_cb.click()
        except Exception:
            pass

    time.sleep(2)
    page.screenshot(path="shots/everai_06_form_filled.png")

    # Step 6: Bấm 'Tạo giọng'
    print("[8] Bấm nút 'Tạo giọng'...")
    gen_btn = page.locator("button:has-text('Tạo giọng')").first
    if gen_btn.is_visible():
        gen_btn.click()

    # Chờ sinh 3 bản nghe thử
    print("[9] Đang chờ EverAI sinh 3 bản nghe thử (khoảng 30-60 giây)...")
    page.get_by_text("Xác nhận").first.wait_for(timeout=90000)
    time.sleep(3)
    page.screenshot(path="shots/everai_07_previews_ready.png")

    # Chọn option 1 và bấm 'Xác nhận'
    print("[10] Chọn bản nghe thử tốt nhất và bấm 'Xác nhận'...")
    confirm_btn = page.locator("button:has-text('Xác nhận')").first
    confirm_btn.click()
    time.sleep(3)
    page.screenshot(path="shots/everai_08_modal_register.png")

    # Step 7: Điền thông tin đăng ký giọng: Tên, Giới tính Nữ, Tuổi Thanh niên
    print("[11] Điền thông tin giọng: 'KOC Neil Girl' - Nữ - Thanh niên...")
    name_input = page.locator("input[placeholder*='Tên Giọng'], input[name*='name']").first
    if name_input.count() > 0:
        name_input.fill("KOC Neil Girl")

    save_btn = page.locator("button:has-text('Lưu')").first
    if save_btn.is_visible():
        save_btn.click()
        time.sleep(5)
        page.screenshot(path="shots/everai_09_voice_saved.png")

    # Step 8: Đi tới 'Chuyển văn bản' để tạo audio hoàn chỉnh
    print("[12] Chuyển tới 'Chuyển văn bản'...")
    tts_menu = page.get_by_text("Chuyển văn bản").first
    if tts_menu.count() > 0:
        tts_menu.click()
    else:
        page.goto("https://everai.vn/text-to-speech", wait_until="domcontentloaded")

    time.sleep(4)
    page.screenshot(path="shots/everai_10_tts_page.png")

    # Nhập kịch bản vào ô chuyển văn bản
    tts_box = page.locator("textarea, div[contenteditable='true']").first
    tts_box.fill(SCRIPT_TEXT)
    time.sleep(2)

    # Bấm Tạo Audio và tải về
    print("[13] Bấm 'TẠO AUDIO'...")
    create_audio_btn = page.locator("button:has-text('TẠO AUDIO'), button:has-text('Tạo audio')").first
    create_audio_btn.click()

    # Chờ nút Tải xuống
    print("[14] Đang chờ sinh file MP3...")
    time.sleep(15)
    page.screenshot(path="shots/everai_11_audio_ready.png")

    # Bắt sự kiện tải file
    download_btn = page.locator("button:has-text('Tải xuống'), a[download], [aria-label*='download'], button:has([class*='download'])").first
    if download_btn.count() > 0:
        with page.expect_download() as dl_info:
            download_btn.click()
        dl = dl_info.value
        out_mp3 = os.path.abspath("output/everai_koc_cloned_voice.mp3")
        dl.save_as(out_mp3)
        print(f" -> [THÀNH CÔNG RỰC RỠ] Đã tải về file: {out_mp3} ({os.path.getsize(out_mp3):,} bytes)")

    ctx.close()
