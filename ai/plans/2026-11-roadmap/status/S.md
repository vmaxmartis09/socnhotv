# Báo Cáo Tiến Độ Session S — Social Manager

**Trạng thái:** HOÀN THÀNH 100% (S1_social_manager)  
**Ngày thực hiện:** 2026-11-04  
**Phạm vi sở hữu:** `socnhotv/social/**`, `core/api/routes/social.py`, `components/social/**`, `components/studio/tabs/PublishTab.tsx`, `lib/api/social.ts`, `store/modules/social.ts`, `messages/modules/social.*`, `tool/tests/test_social_*.py`.

---

## 1. ĐÃ LÀM GÌ

### 1.1. Dọn Dẹp Dữ Liệu Giả (Zero Root Pollution)
- Đã di chuyển toàn bộ 26 tệp bài viết giả/seed test (`post_*.json`) từ `data/projects/soc-nho-tv/publishing/posts/` sang `data/projects/soc-nho-tv/publishing/_demo/posts/`.
- Di chuyển `schedule.json` cũ sang `data/projects/soc-nho-tv/publishing/_demo/schedule.json`.
- Di chuyển các file inbox test sang `_demo/inbox/`.
- Dữ liệu rác đã được làm sạch hoàn toàn; khi không có bài đăng mới, giao diện tab Lịch đăng hiển thị Empty State chuẩn với nút gợi ý hành động.

### 1.2. Giới Hạn & Quản Lý Tối Đa 10 Tài Khoản Đa Nền Tảng
- Khai báo hằng số `MAX_ACCOUNTS = 10` trong `socnhotv.social.models` và xử lý ngoại lệ `AccountLimitExceededError`.
- Endpoint `POST /projects/{pid}/social/accounts` kiểm tra và trả về mã lỗi **HTTP 409 Conflict** khi cố gắng tạo tài khoản thứ 11.
- Khởi tạo đầy đủ 10 tài khoản mẫu chuẩn cho dự án `soc-nho-tv`:
  1. `chan_yt_1`: YouTube - Sóc Nhỏ TV Official (Kênh chính)
  2. `chan_yt_2`: YouTube - Sóc Nhỏ Shorts (Kênh phụ / Shorts)
  3. `chan_yt_3`: YouTube - Sóc Nhỏ Review KOC (Bán hàng)
  4. `chan_tt_1`: TikTok - Sóc Nhỏ TV TikTok (Kênh chính)
  5. `chan_tt_2`: TikTok - Bi & Bạn Koala Hài Hước (Giải trí)
  6. `chan_tt_3`: TikTok - Sóc Nhỏ Shop KOC (Bán hàng)
  7. `chan_fb_1`: Facebook - Sóc Nhỏ TV Fanpage (Kênh chính)
  8. `chan_fb_2`: Facebook - Hội Phụ Huynh Nuôi Con (Cộng đồng)
  9. `chan_ig_1`: Instagram - Sóc Nhỏ TV Instagram (Kênh chính)
  10. `chan_th_1`: Threads - Sóc Nhỏ TV Threads (Kênh chính)
- Tài khoản thứ 11 bị chặn cả ở tầng Store lẫn tầng API (409). Trên giao diện, thẻ nét đứt "+ Thêm" tự động ẩn khi đủ 10 tài khoản và hiển thị huy hiệu "Đã đủ 10".

### 1.3. Bảng Quy Tắc Nền Tảng & Kiểm Tra Tương Thích (`platform_rules.py`)
- Định nghĩa thông số kỹ thuật chuẩn cho 6 nền tảng: YouTube, TikTok, Facebook, Instagram, Threads, X:
  - Giới hạn thời lượng, dung lượng MB, độ dài tiêu đề, độ dài caption, số lượng hashtag tối đa.
  - Hạn ngạch API đăng tải mỗi ngày (ví dụ: YouTube tối đa 6 video/ngày).
- Hàm `validate(video, target, account) -> list[Issue]`:
  - Bắt lỗi vượt thời lượng (`duration_exceeded`), dung lượng quá lớn (`size_exceeded`).
  - Cảnh báo lệch tỉ lệ khung hình (`ratio_mismatch`), ví dụ video ngang 16:9 đăng lên TikTok sẽ cảnh báo nếu không có biến thể 9:16 dọc.
  - Bắt lỗi caption quá dài, quá nhiều hashtag, tài khoản hết hạn xác thực OAuth (`account_expired`).
- Hàm `pick_best_variant`: Tự động tìm đường dẫn biến thể tối ưu nhất từ render job theo từng nền tảng.

### 1.4. Kho Video Đăng Được (`video_library.py`)
- Endpoint `GET /projects/{pid}/social/videos`:
  - Quét toàn bộ render jobs đã hoàn thành (`status == "done"`) trong `runs/render_queue/`.
  - Quét các video hoàn chỉnh trong `content/episodes/` và `library/`.
  - Đọc metadata bằng `ffprobe` (thời lượng, kích thước width/height, tỉ lệ, dung lượng MB) có cache vào `.video_cache.json`.
  - Liên kết với lịch sử bài viết để thống kê `posted_count` (số lần đã đăng) và `last_posted_at`.

### 1.5. Lập Kế Hoạch Hàng Loạt & Tự Xếp Lịch Chuẩn (`planner.py`)
- Endpoint `POST /projects/{pid}/social/plans/preview`:
  - Hỗ trợ 3 chiến lược: `auto` (Tự động thông minh), `now` (Đăng ngay), `fixed` (Giờ cố định).
  - Thuật toán `auto`:
    - Duyệt từ `max(now, start_at)`, tuyệt đối không đặt vào quá khứ.
    - Múi giờ chuẩn hóa: `Asia/Ho_Chi_Minh` (+07:00).
    - Khung giờ vàng: Tự động xếp vào `posting_windows` của từng tài khoản.
    - Giới hạn khoảng cách: Đảm bảo tối thiểu `min_gap_minutes` (mặc định 120 phút) giữa 2 bài của cùng 1 kênh.
    - Quota Planner: Tự động phát hiện khi vượt hạn ngạch API trong ngày (YouTube tối đa 6 video/ngày) và tự động đẩy bài sang ngày tiếp theo kèm cảnh báo `quota_pushed`.
    - So le thông minh: Giãn cách 15-30 phút giữa các tài khoản cùng nền tảng, không đăng cùng 1 phút.
- Endpoint `POST /projects/{pid}/social/plans/commit`:
  - Nhận danh sách mục tiêu đã duyệt và lưu nguyên tử thành các `Post` và `PostTarget` trong hệ thống.

### 1.6. Sinh Caption Tự Động Đa Nền Tảng (`captions.py`)
- Endpoint `POST /projects/{pid}/social/captions/generate`:
  - Sử dụng trích đoạn kịch bản / transcript của video.
  - Sinh hook 1 dòng hấp dẫn theo 3 mục tiêu (`story`, `education`, `sales`).
  - Cắt gọt caption đúng giới hạn ký tự từng nền tảng (Threads 500, X 280, TikTok/IG 2200, FB/YouTube 5000).
  - Hashtags: Lựa chọn đúng số lượng và chủ đề phù hợp từng mạng xã hội.
  - Chế độ `vary_per_account=true`: Khi đăng lên nhiều tài khoản cùng nền tảng, mỗi tài khoản nhận được biến thể hook và câu chữ khác nhau để chống spam trùng lặp nội dung.
  - Tự động chèn liên kết affiliate và thông báo tài trợ (#quangcao) theo đúng quy định.

### 1.7. Hàng Đợi Chuẩn Xác & Dải Trạng Thái Đầu Tab (`queue.py`)
- Endpoint `GET /projects/{pid}/social/queue?bucket=upcoming|overdue|published|failed`:
  - Sửa dứt điểm lỗi hiển thị ngày cũ là sắp tới: Bucket `upcoming` **chỉ gồm bài có `scheduled_at >= now`**.
  - Bucket `overdue` gom các bài chưa đăng nhưng đã quá giờ.
  - Trả về dải chỉ số tóm tắt: `{accounts}/10 tài khoản · {pending} chờ duyệt · {overdue} quá hạn · bài kế tiếp {time}`.

### 1.8. Giao Diện Người Dùng (UI/UX Theo Chuẩn Manifesto)
- **Tab Lịch đăng (`PublishTab.tsx`)**:
  - Dải trạng thái đầu tab: Bấm vào từng mục để lọc hàng đợi tương ứng.
  - Nút chính nổi bật: `+ Lên kế hoạch đăng` mở Trung tâm đăng.
  - Hàng tài khoản cuộn ngang: Hiển thị avatar, biểu tượng nền tảng, chấm màu trạng thái không đè tên. Thẻ nét đứt `+ Thêm` tự động ẩn khi đủ 10 tài khoản.
  - 4 sub-tab hàng đợi (`Sắp tới`, `Quá hạn`, `Đã đăng`, `Lỗi`), gom nhóm theo ngày (`Hôm nay`, `Ngày mai`, thứ trong tuần).
  - Thành phần dòng bài viết dùng chung `PostRow.tsx`: Thumbnail, tiêu đề xuống dòng 2 dòng có tooltip đầy đủ, badge nền tảng đủ chữ, tên kênh, giờ đăng, trạng thái, menu `…` đầy đủ thao tác (Sửa, Đổi giờ, Nhân bản, Đăng ngay, Tôi đã đăng, Tải gói ZIP, Hủy).
- **Trung tâm đăng ("PublishCenterModal.tsx")**:
  - Panel nổi lớn mở từ tab Lịch đăng và từ nút "Xem Lịch".
  - Chuyển đổi 2 tab cấp cao: `Kế hoạch đăng (5 bước)` và `Xem Lịch Đăng` (tích hợp `CalendarView` tháng/tuần).
  - Wizard 5 bước:
    - Bước 1: Chọn video (lưới thumbnail, thời lượng, tỉ lệ, dung lượng, chip biến thể, đã đăng n lần, tìm kiếm, lọc chưa đăng).
    - Bước 2: Chọn tài khoản + Ma trận tương thích Video × Kênh hiển thị ✓/⚠/✕ trực quan kèm lý do.
    - Bước 3: Soạn nội dung đa kênh + Nút "Viết caption tự động" + Khung mô phỏng điện thoại (`PhonePreview.tsx`) cắt "...xem thêm" chuẩn từng nền tảng.
    - Bước 4: Lập lịch tự động (Tự xếp lịch chuẩn, Đăng ngay, Giờ cố định) + Lưới xem trước ngày × tài khoản, điều chỉnh giờ trực tiếp.
    - Bước 5: Tóm tắt kế hoạch + Công tắc khóa an toàn "Duyệt trước khi đăng" + Nút xác nhận lưu lịch.
- **Sheet Cấu hình Tài khoản (`AccountDetailSheet.tsx`)**:
  - Quản lý tên kênh, handle, nhóm phân loại, 7 ngày khung giờ vàng, giới hạn bài/ngày, khoảng cách tối thiểu, hashtags mặc định, chữ ký chân bài.

### 1.9. Kiểm Thử Tự Động & Nghiệm Thu
- Chạy toàn bộ test suite social: **47/47 tests passed (100%)**:
  - `test_social_limits.py`: Kiểm tra giới hạn 10 tài khoản, chặn 409 khi tạo tài khoản thứ 11.
  - `test_social_rules.py`: Kiểm tra thông số nền tảng, validate thời lượng, dung lượng, tỉ lệ 16:9/9:16, độ dài text, hashtags, trạng thái tài khoản.
  - `test_social_plan.py`: Kiểm tra auto-schedule không đặt vào quá khứ, múi giờ +07:00, min_gap 120 phút, đẩy hạn ngạch quota YouTube sang ngày hôm sau, commit plan.
  - `test_social_queue.py`: Kiểm tra bucket upcoming loại bỏ ngày quá khứ, overdue gom bài trễ hạn, chỉ số summary.
  - `test_social_captions.py`: Kiểm tra giới hạn ký tự theo nền tảng, chèn disclosure affiliate, sinh biến thể khác nhau cho từng tài khoản (`vary_per_account`).
  - Cùng 42 bài test kế thừa từ C1-C4.
- TypeScript compilation: `cd tool/dashboard && npx tsc --noEmit 2>&1 | grep -E "social|PublishTab"`: **0 lỗi**.
- Đã ghi yêu cầu đổi nhãn tab tiếng Anh sang tiếng Việt cho Session E2 vào `ai/plans/2026-11-roadmap/status/REQUESTS.md`.

---

## 2. CHƯA LÀM GÌ (Phạm Vi Cố Tình Loại Trừ)
- Giữ nguyên triết lý Zero Clutter: Không nhồi nhét Analytics, Automation Rules, hay Notifications vào tab Lịch đăng (panel ~400px) để đảm bảo giao diện tập trung 100% vào nghiệp vụ quản lý xuất bản và lên kế hoạch.
- Không tự ý đăng bài thật lên tài khoản mạng xã hội của người dùng khi chưa có hành động bấm xác nhận trực tiếp trong UI (bảo vệ an toàn tài khoản).
- Không tự ý can thiệp vào các component thuộc quyền sở hữu của Session E2/E3 (`components/canvas/**`, `NodeTab.tsx`, `canvasSlice.ts`, `i18n/request.ts`, `RightPanel.tsx`, `PageBar.tsx`).

---

## 3. CHƯA KIỂM CHỨNG GÌ (Pending Live Verification)
- Chưa kiểm chứng xuất bản thật với API production của Google Cloud / TikTok Developer / Meta Developer đối với các tài khoản người dùng thực tế đang hoạt động (hiện sử dụng mock adapters và manual package generator `.zip` để bảo đảm an toàn dữ liệu và hạn ngạch của người dùng).
- Khi người dùng cấu hình client_id / secret thật vào KeyVault, luồng OAuth và Resumable Upload sẵn sàng hoạt động ngay mà không cần thay đổi kiến trúc.

---

## 4. DANH SÁCH ẢNH CHỤP NGHIỆM THU (Tại `data/projects/soc-nho-tv/shots/`)
1. `S_publish_tab.png`: Giao diện tab Lịch đăng gọn gàng trong panel ~400px với 10 tài khoản, dải trạng thái đầu tab và hàng đợi.
2. `S_mobile_375px.png`: Giao diện hiển thị chuẩn responsive trên màn hình di động 375px.
3. `S_wizard_step1.png`: Trung tâm đăng - Bước 1: Chọn video trong kho hoàn tất kèm thông số.
4. `S_wizard_matrix.png`: Trung tâm đăng - Bước 2: Chọn tài khoản và Ma trận tương thích Video × Kênh.
5. `S_wizard_content_phone.png`: Trung tâm đăng - Bước 3: Soạn caption AI và Khung mô phỏng điện thoại.
6. `S_wizard_schedule.png`: Trung tâm đăng - Bước 4: Tự xếp lịch chuẩn đa kênh, quota-aware.
7. `S_wizard_confirm.png`: Trung tâm đăng - Bước 5: Bảng tóm tắt và công tắc khóa an toàn duyệt bài.
8. `S_calendar_view.png`: Giao diện Lịch xuất bản tháng/tuần trực quan tích hợp bên trong Trung tâm đăng.
