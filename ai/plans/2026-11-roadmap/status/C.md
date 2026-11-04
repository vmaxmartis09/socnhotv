# Session C — Social & Publishing

**Trạng thái:** Đang thực hiện (C1 xong, sang C2)

## C1 — Social Domain, Storage, API & Legacy Migration (HOÀN THÀNH)
- **Mô hình (`social/models.py`):**
  - Đầy đủ pydantic v2: `SocialAccount`, `Post`, `PostTarget`, `PostMedia`, `PostApproval`, `PostingWindow`, `RecurringSlot`, `CampaignTag`, `CalendarNote`.
  - Múi giờ ISO-8601 mặc định `Asia/Ho_Chi_Minh` (`DEFAULT_TZ = ZoneInfo("Asia/Ho_Chi_Minh")`).
- **Lưu trữ (`social/store.py`):**
  - Ghi nguyên tử (`.tmp` + `os.replace` + `fsync`) kết hợp `fcntl.flock` file locking.
  - Phân vùng theo project: `publishing/accounts.json`, `publishing/posts/<post_id>.json`, `publishing/slots.json`, `publishing/notes.json`, `publishing/audit.jsonl`.
  - Hỗ trợ đầy đủ CRUD, truy vấn filter (status, platform, account, from, to, q), phân tích log audit.
- **Di trú (`social/migrate.py`):**
  - Đọc `schedule.json` và `channels.json` cũ → tự động chuyển đổi thành SocialAccount + RecurringSlot + Post/PostTarget.
  - Idempotent: ghi nhận qua `.migrated_v1`, chạy nhiều lần không nhân đôi dữ liệu.
  - Đã di trú thành công dữ liệu thật của project `soc-nho-tv`.
- **Hợp đồng liên session (`social/contracts.py`):**
  - Cập nhật `create_draft_post` giữ nguyên chữ ký, kết nối trực tiếp `SocialStore` và tự tạo `PostTarget` theo tài khoản mặc định.
  - Bổ sung `ingest_inbox(project_id)` chuyển đổi các file nháp từ inbox sang Post chính thức và dọn vào `_done/`.
- **Nghiệp vụ (`social/service.py`):**
  - Máy trạng thái nghiêm ngặt (`InvalidStateTransitionError` → HTTP 409).
  - Luồng: draft → submit_for_approval → approve → schedule.
  - `suggest_time`: tìm slot vàng gần nhất, kiểm tra tránh xung đột lịch (≥ 2 giờ giữa các bài cùng account), tôn trọng `daily_limit`.
  - `caption_variants`: tự động sinh caption phù hợp giới hạn từng nền tảng (TikTok 2200, YouTube 100/5000, Instagram 2200, Facebook), tự gắn hashtags, footer và disclosure affiliate.
- **API (`core/api/routes/social.py`):**
  - Tích hợp 20+ endpoint: CRUD accounts, posts, submit, approve, reject, schedule, cancel, duplicate, kéo-thả đổi giờ `PUT /targets/{tid}/time`, `GET /calendar`, slots, notes, suggest-time, caption-variants, migrate, audit.
- **Nghiệm thu kiểm thử:**
  - `test_social_models.py` (3 passed)
  - `test_social_store.py` (3 passed, bao gồm 24 concurrent threads ghi đồng thời)
  - `test_social_migrate.py` (1 passed, kiểm tra di trú và tính bất biến idempotent)
  - `test_social_service.py` (5 passed, lifecycle, rejection, schedule published rejection, conflict avoidance, variants)
  - `test_social_api.py` (4 passed, TestClient gọi toàn bộ workflow API)
  - Tổng cộng 16/16 test social passed.
