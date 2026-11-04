# Session C — Social & Publishing

**Trạng thái:** Đang thực hiện (C1, C2 & C3 xong, sang C4)

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
- **Nghiệm thu kiểm thử C1:** 16/16 test social passed.

---

## C2 — UI Social Manager (HOÀN THÀNH)
- **Kiến trúc màn hình `/social` (`app/[locale]/social/page.tsx`):**
  - Navigation tab đầy đủ: Lịch xuất bản (`calendar`), Hàng chờ duyệt (`approvals`), Tất cả bài viết (`posts`), Tài khoản & Kênh (`accounts`), Phân tích (`analytics`).
  - Badge đếm số lượng bài chờ duyệt tự động đồng bộ.
  - Tích hợp chuẩn Morphicons `@/components/ui/icons` và theme dark/light.
- **Thành phần giao diện (`components/social/**`):**
  - `PostChip.tsx`: Phân màu theo nền tảng, chấm trạng thái động, hỗ trợ kéo thả `@dnd-kit/core`.
  - `CalendarView.tsx`: Chế độ Tháng (lưới 7 ngày, hiển thị ghi chú chiến dịch, kéo thả đổi ngày), Tuần (trục 24h, hiển thị khung giờ vàng trống `isGolden`, bấm để tạo bài), Danh sách (Agenda). Hỗ trợ nút Hoàn tác (Undo) và múi giờ `Asia/Ho_Chi_Minh`.
  - `ApprovalsTab.tsx`: Hàng chờ duyệt thẻ lớn, player xem trước video, tab caption từng nền tảng, checklist kiểm tra tự động 5 tiêu chí. Hỗ trợ duyệt nhanh, duyệt hàng loạt, từ chối kèm lý do và chỉnh sửa trực tiếp.
  - `PostsTab.tsx`: Bảng quản lý tập trung toàn bộ bài viết, bộ lọc trạng thái và nền tảng, tìm kiếm từ khóa, thao tác chọn nhiều.
  - `AccountsTab.tsx`: Lưới AccountCard, thẻ "Thêm tài khoản mới" nét đứt chuẩn design manifesto, modal chỉnh sửa khung giờ 7 ngày.
  - `PostComposer.tsx`: Drawer trượt phải dùng chung, quản lý media, chọn đa tài khoản, TargetEditor, sinh caption AI, gợi ý giờ vàng, mô phỏng hiển thị trên điện thoại.
  - `AgendaList.tsx`: Hiển thị danh sách nhóm theo ngày, dùng chung cho cả Calendar và PublishTab.
- **Gộp khu lịch cũ & điều hướng:**
  - `PublishTab.tsx`: Thay thế toàn bộ code cũ gọi endpoint 404 bằng bản rút gọn dùng chung `useSocialStore`, `AgendaList`, `PostChip`, nút "+ Lên lịch" mở trực tiếp PostComposer.
  - `publish/page.tsx`: Redirect tự động sang `/social`.
  - `lib/api/social.ts` & `store/modules/social.ts`: Client API & Zustand store độc lập của Session C.
- **Nghiệm thu C2:**
  - TypeScript `npx tsc --noEmit | grep -E "social|PublishTab|publish/page"`: 0 lỗi.
  - 4 ảnh chụp màn hình trong `data/projects/soc-nho-tv/shots/`: `C2_month.png`, `C2_week.png`, `C2_approvals.png`, `C2_composer.png`.

---

## C3 — Publish Adapters, Manual Packages & Scheduler Worker (HOÀN THÀNH)
- **Kiến trúc Adapter (`social/adapters/`):**
  - `base.py`: Interface `PublishAdapter`, `Capabilities`, `Issue`, `PublishResult`.
  - `youtube.py`: YouTube Data API v3 Resumable upload 2-phase protocol, set thumbnail, native `publishAt` (private), categoryId 22, shorts auto-detection. Quota awareness chặn sớm khi vượt giới hạn 10.000 units/ngày (video.insert = 1.600 units).
  - `tiktok.py`: Content Posting API: query creator info, FILE_UPLOAD chunked, Direct Post (`video.publish`) hoặc Upload to inbox (`video.upload`).
  - `meta.py`: Facebook Page Video (resumable) và Instagram Reels (Container -> Status poll -> Media publish).
  - `manual.py`: Xuất gói xuất bản thủ công (`publishing/packages/<post_id>/<platform>/`) gồm `video.mp4`, `cover.jpg`, `caption.txt`, `hashtags.txt`, `checklist.md`, `meta.json`. Hỗ trợ đóng gói `.zip` tải về trực tiếp.
  - `browser_assisted.py`: Tích hợp Ego Lite mở sẵn trang upload và điền sẵn caption, dừng chờ người dùng kiểm tra và tự bấm nút Publish.
- **Scheduler Worker (`social/scheduler.py`):**
  - APScheduler / AsyncIO loop chu kỳ 30 giây.
  - Cơ chế khoá mục tiêu (`publishing`), đảm bảo tính bất biến idempotent (không đăng trùng nếu crash giữa chừng).
  - Cổng bảo vệ phê duyệt: Không bao giờ đăng bài khi `approval.required` mà chưa có trạng thái `approved`.
  - Cơ chế retry lũy tiến thông minh: lỗi tạm thời lùi lịch 2, 10, 30 phút; lỗi vĩnh viễn (quota, auth 401/403) đánh dấu `failed` và chuyển trạng thái account sang `expired`.
  - Ghi heartbeat định kỳ vào `publishing/scheduler.heartbeat`.
- **API Mở rộng (`core/api/routes/social.py`):**
  - `GET /accounts/{id}/connect`, `GET /social/oauth/callback/{platform}`, `POST /accounts/{id}/refresh`
  - `POST /posts/{id}/targets/{tid}/validate`, `POST /posts/{id}/publish-now`, `POST …/mark-published`
  - `GET /scheduler/status`, `GET /packages/{post}/{platform}.zip`
- **UI bổ sung:**
  - `AccountCard`: Nút kết nối OAuth mở cửa sổ xác thực và làm mới token.
  - `PostsTab`: Widget giám sát Scheduler Heartbeat thời gian thực, nút tải gói đăng tay `.zip`, nút "Tôi đã đăng" nhập URL và nút "Xuất bản ngay" cho bài đã duyệt.
- **Nghiệm thu kiểm thử C3:**
  - `test_social_adapters.py` (4 passed: mock HTTP YouTube resumable, quota 403, TikTok direct post, Meta Reels container)
  - `test_social_scheduler.py` (1 passed: đúng giờ mới đăng, chưa duyệt không đăng, idempotency, heartbeat)
  - `test_social_manual.py` (1 passed: tạo gói thủ công đầy đủ 6 tệp, nén file `.zip` hợp lệ)
  - Đã xuất thử gói đăng tay thật cho bài `post_ep1_tt` của project `soc-nho-tv`.
  - Tổng số test social passed: 22/22.
