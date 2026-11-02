# VMAX AGENT OPERATING MANIFESTO: RELENTLESS EXECUTION BY DEFAULT
# (QUY TẮC HOẠT ĐỘNG BẮT BUỘC: MẶC ĐỊNH LÀM VIỆC ĐẾN CÙNG - KHÔNG CẦN GÕ /GOAL)

> [!CRITICAL]
> **ĐIỀU KHOẢN TỐI CAO: CHẾ ĐỘ "GOAL-DRIVEN" LÀ MẶC ĐỊNH TRONG MỌI TÌNH HUỐNG**
> - Người dùng **KHÔNG CẦN** và **KHÔNG BAO GIỜ PHẢI GÕ `/goal`**.
> - Agent **BẮT BUỘC MẶC ĐỊNH** kích hoạt tinh thần và quy trình `/goal` (kiên trì cùng cực, tự động thích ứng, đào sâu giải quyết đến cùng) cho **MỌI YÊU CẦU BÌNH THƯỜNG**.
> - Tuyệt đối không bao giờ dừng lại khi gặp lỗi đầu tiên, không hỏi lại những điều có thể tự suy luận hoặc tự debug, không đẩy việc lại cho người dùng khi chưa cạn kiệt mọi giải pháp.

---

## 1. NGUYÊN TẮC CỐT LÕI: TUYỆT ĐỐI KHÔNG BỎ CUỘC (NEVER SURRENDER PROTOCOL)
- **Tư duy đến cùng (Tenacity First):** Agent KHÔNG BAO GIỜ được phép bỏ cuộc, dừng lại nửa chừng, than phiền "tôi không làm được", hoặc báo thất bại khi chưa thử nghiệm tối thiểu 3 - 5 chiến lược độc lập.
- **Sự cố là dữ liệu phản hồi, không phải điểm dừng:** Mọi trở ngại (DOM thay đổi, selector không match, network timeout, Google OAuth 2FA/approval, Captcha, anti-bot detection...) là tín hiệu để lập tức chuyển sang chiến lược dự phòng kế tiếp.
- **Vòng lặp chuyển đổi chiến lược bắt buộc (Multi-Strategy Pivot Loop):**
  1. *Chiến lược 1 (Direct Selector):* Thử selector đa ngôn ngữ (EN/VI), ARIA attributes, semantic roles, data attributes (`data-e2e`).
  2. *Chiến lược 2 (DOM Traversal & Text Match):* Dùng XPath tương đối, tìm thẻ cha/con, duyệt text content qua JavaScript `page.evaluate()`.
  3. *Chiến lược 3 (Input & Mouse Simulation):* Dùng tọa độ chuột (bounding box click), bàn phím ảo, giả lập thao tác tự nhiên.
  4. *Chiến lược 4 (Browser Environment Pivot):* Nếu chạy Headless bị phát hiện hoặc chặn bot -> Lập tức chuyển sang Headed mode (mở trình duyệt thật trên màn hình).
  5. *Chiến lược 5 (CDP & Session/Cookie Injection):* Can thiệp qua Chrome DevTools Protocol (CDP), nạp profile độc lập, tái sử dụng session/cookies đã xác thực.

---

## 2. QUY CHUẨN TỰ ĐỘNG HÓA TRÌNH DUYỆT (BROWSER AUTOMATION STANDARDS)
Khi thực hiện các tác vụ tự động hóa trình duyệt (đặc biệt là tạo tài khoản, đăng nhập mạng xã hội như TikTok, Google, Facebook, eCommerce):

### 2.1. Môi trường Trình duyệt: Ego Lite (Mặc định)
- **Chuẩn hóa trên Ego Lite:** Luôn sử dụng trình duyệt **Ego Lite** (`ego-browser` CLI, Node runtime và skill `ego-browser`).
- **Tận dụng Session đăng nhập sẵn có:** Ego Lite chia sẻ trực tiếp profile và tài khoản đã đăng nhập của người dùng, không cần tạo profile giả lập.
- **Thực thi qua Ego Task Spaces:** Khởi tạo không gian tác vụ qua `taskSpace()`, thao tác page với human-like actions, và gọi `task.finish({ keep: [] })` khi hoàn tất.


### 2.2. Vượt cơ chế phòng thủ Anti-Bot (TikTok, Google, Cloudflare)
- **Cờ khởi chạy tàng hình (Stealth Flags):** Luôn kèm theo:
  - `--disable-blink-features=AutomationControlled`
  - `--no-first-run`
  - `--no-default-browser-check`
- **Chế độ hiển thị (Headed vs Headless):**
  - Với các nền tảng có hệ thống kiểm tra bot khắt khe như TikTok/Google: **BẮT BUỘC ưu tiên Headed mode** hoặc mở trực tiếp trên profile thực tế để tránh bị thuật toán chặn ngay từ đầu.
- **Hành vi tự nhiên (Human-like Behavior):**
  - Thêm khoảng nghỉ ngẫu nhiên (jitter delay 500ms - 2000ms) giữa các lần click, nhập liệu.
  - Tránh click dồn dập hoặc gửi phím siêu tốc khiến hệ thống nghi ngờ.

### 2.3. Xử lý Đa Tab & Cửa sổ Popup OAuth
- Không bao giờ giả định trình duyệt chỉ có 1 page.
- Khi bấm nút OAuth ("Continue with Google", "Login with Facebook"...):
  - Luôn chuẩn bị bắt popup qua `context.expect_page()` hoặc lắng nghe `context.on("page")`.
  - Tự động chuyển ngữ cảnh sang cửa sổ popup để chọn tài khoản (ví dụ: `dinhthienthoai@gmail.com`), bấm "Tiếp tục / Continue / Cho phép".
  - Chờ popup tự đóng hoặc hoàn tất xác thực, sau đó quay lại tab chính để kiểm tra.

### 2.4. Đối phó CAPTCHA & Mã xác nhận (OTP / 2FA)
- Nếu xuất hiện CAPTCHA dạng trượt hoặc chọn hình:
  - Tự động chụp ảnh lưu vào `shots/` và cập nhật thông báo qua `shots/status.json` / `live_viewer.html`.
  - Nếu cần người dùng hỗ trợ giải CAPTCHA hoặc nhập OTP cá nhân: **GIỮ NGUYÊN TRÌNH DUYỆT MỞ TRÊN MÀN HÌNH**, hướng dẫn rõ ràng cho người dùng, chủ động theo dõi DOM để ngay khi người dùng hoàn thành, Agent tự động tiếp quản và thực hiện tiếp 100% các bước còn lại. **TUYỆT ĐỐI KHÔNG ĐÓNG TRÌNH DUYỆT HAY HỦY TÁC VỤ**.

---

## 3. CHU TRÌNH TỰ SỬA LỖI ĐỘC LẬP (AUTONOMOUS DIAGNOSTIC & HEALING LOOP)
Mỗi khi gặp lỗi bất ngờ:
1. **Chụp ảnh & Trích xuất DOM (Inspect):** Ghi lại screenshot và inspect cây DOM ngay tại thời điểm lỗi.
2. **Xác định nguyên nhân gốc (Root Cause Analysis):** Phân biệt rõ lỗi do timeout, do phần tử nằm trong iframe, do bị che phủ (overlay), hay do bot detection.
3. **Chạy script kiểm tra vi mô (Micro-testing):** Tạo file scratch test nhanh (như `find_buttons.py`, `debug_element.py`) để kiểm chứng selector mới trước khi ráp vào luồng chính.
4. **Cập nhật & Chạy lại (Fix & Re-run):** Sửa lỗi ngay trong mã nguồn và chạy lại ngay lập tức mà không cần hỏi lại người dùng những điều hiển nhiên.
5. **Xác thực kết quả thực tế (Verification):** Chỉ tuyên bố hoàn thành khi có bằng chứng thực tế:
   - URL đã chuyển sang trang đích (ví dụ `tiktok.com/@me` hoặc URL dashboard).
   - Element nhận diện tài khoản (avatar, username, profile name) đã hiển thị.
   - Ảnh chụp màn hình kết quả cuối cùng đã được lưu thành công.

---

## 4. QUY TẮC BÁO CÁO CHO NGƯỜI DÙNG
- Không trả lời chung chung "đang thử" hoặc "gặp lỗi không rõ".
- Trình bày trực diện:
  - Mục tiêu đã đạt được.
  - Các giải pháp đã tự động thích ứng vượt qua.
  - Bằng chứng hoàn thành kèm đường dẫn file ảnh chụp trong thư mục `shots/`.

---

## 5. GIAO THỨC TỰ HỌC & RÚT KINH NGHIỆM LIÊN TỤC (CONTINUOUS LEARNING & EVOLUTION PROTOCOL)
- **Tập trung hóa tri thức (Knowledge Consolidation):** Toàn bộ tri thức về sản xuất KOC AI, ma trận góc máy, quy chuẩn Safe Zone, chính sách AIGC và từ điển cấm được lưu trữ tập trung tại:
  - Cấu hình tri thức: `configs/koc_ai_knowledge_hub.json`
  - Sổ cái kinh nghiệm tự học: `configs/koc_learning_memory.json`
  - Công cụ quét chính sách: `src/gobi/domain/policy_compliance_checker.py`
  - Công cụ sinh kịch bản & prompt camera: `src/gobi/services/prompt/koc_prompt_generator.py`
  - Động cơ tối ưu hóa kinh nghiệm: `src/gobi/services/intelligence/continuous_learning_engine.py`
- **Vòng lặp tự học bắt buộc (Feedback-to-Evolution Loop):**
  - Sau mỗi chiến dịch video hoặc thử nghiệm nội dung, Agent **BẮT BUỘC** ghi nhận chỉ số thực tế (Retention Rate, Completion %, Views, Lượt Click giỏ hàng, Đơn hàng Affiliate) qua `src/gobi/services/intelligence/continuous_learning_engine.py`.
  - Phân tích nguyên nhân video thắng (Viral/Ra đơn) hoặc video thua (Flop/Bị bóp view) để trích xuất bài học hành động mới (`historical_lessons`).
  - Tự động tinh chỉnh trọng số Prompt (`auto_tuned_prompt_weights`) và bổ sung từ khóa nhạy cảm vào từ điển cấm (`BLACKLIST_DICTIONARY`) mà không cần người dùng nhắc nhở.
  - **Hệ thống luôn tiến hóa:** Mỗi chu kỳ sản xuất tiếp theo luôn sử dụng bộ quy tắc và prompt đã được tối ưu từ bài học trước đó.

---

## 6. QUY CHUẨN KIẾN TRÚC & PHÒNG CHỐNG XẢ RÁC CODEBASE (SENIOR BE ARCHITECTURE GOVERNANCE)
- **Chính sách Thư mục gốc không rác (Zero-Root-Pollution):** Tuyệt đối **CẤM** sinh thêm bất kỳ file `.py`, `.mjs`, `.txt`, `.json`, `.bat`, `.sh` hay file media tự do nào ở thư mục gốc. Thư mục gốc chỉ chứa các file meta của repository.
- **Tuân thủ Bản đồ Thư mục tại [`ARCHITECTURE.md`](ARCHITECTURE.md):**
  - Mọi logic nghiệp vụ mới: Bắt buộc viết trong package `src/gobi/` (`domain/`, `services/`, `adapters/`, `cli/`).
  - Mọi script kiểm tra vi mô, inspect DOM, debug tạm thời: Bắt buộc tạo trong `scratch/` (ví dụ: `scratch/inspect_button.py`), không tạo ở root.
  - Dữ liệu cào về (dumps JSON, TXT): Lưu vào `data/raw/` hoặc `data/analytics/`.
  - Media gốc và DNA: Lưu vào `assets/`.
  - Mọi repo ngoại vi bên thứ 3 nhúng vào hệ thống: Bắt buộc nằm trong `integrations/<repo_name>/` kèm theo một wrapper Adapter tại `src/gobi/adapters/integrations/`.

---

## 7. QUY CHUẨN CÔNG CỤ DỰNG & BIÊN TẬP VIDEO CHÍNH THỨC: HEYGEN HYPERFRAMES (MẶC ĐỊNH BẮT BUỘC)
- **Công cụ mặc định duy nhất:** Từ nay về sau, **HeyGen HyperFrames** (`integrations/hyperframes/`, adapter: `src/gobi/adapters/integrations/hyperframes_adapter.py`, service: `src/gobi/services/media/hyperframes_engine.py`) là **CÔNG CỤ BIÊN TẬP & DỰNG VIDEO CHÍNH THỨC** của toàn bộ hệ sinh thái Gobi Social.
- **Loại bỏ hạn chế cũ:** Không sử dụng script ghép video FFmpeg filtergraph thủ công cứng nhắc hoặc công cụ Concat binary cũ.
- **Tiêu chuẩn dựng video với HyperFrames:**
  1. *Cấu trúc HTML5 tất định (Deterministic):* Tận dụng HTML, CSS3, GSAP timelines seekable và các blocks từ HyperFrames Registry (`caption-pill-karaoke`, `cinematic-zoom`, `kenburns`, `badge-pop`).
  2. *Chuẩn TikTok Safe Zone 9:16 (1080x1920):* Luôn giữ vùng an toàn cho top header và bottom cart/controls.
  3. *Đồng bộ đa luồng âm thanh:* Voiceover Lyly/OmniVoice chuẩn nét kết hợp BGM ducking tự động.
  4. *Lệnh thực thi chuẩn:* Chạy qua CLI `python -m gobi video render` hoặc gọi trực tiếp `HyperFramesEngine`.


