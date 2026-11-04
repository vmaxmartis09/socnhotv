# Session C — Social & Publishing

**Trạng thái:** HOÀN TẤT 100% (C1, C2, C3, C4 Hoàn thành toàn diện)

## Bảng Tiến Độ Tổng Thể Session C

| Phân hệ / Hạng mục | Tiến độ | Trạng thái | Ghi chú kỹ thuật |
|---|---|---|---|
| **C1: Data Models, Storage & Migration** | 100% | Hoàn thành | Pydantic v2, file lock fcntl, atomic write, di trú legacy idempotent |
| **C2: Social Manager UI** | 100% | Hoàn thành | Calendar (Month/Week/Agenda), Approvals, Posts, Accounts, Composer |
| **C3: Publish Adapters & Scheduler** | 100% | Hoàn thành | YouTube Resumable, TikTok Content Posting, Meta Graph, Manual Packages, Ego Lite |
| **C4: Analytics & Insights Engine** | 100% | Hoàn thành | KPI aggregations, ER %, Outliers, Join Template & Blueprints |
| **C4: Heatmap Giờ Vàng** | 100% | Hoàn thành | 7x24 grid median views, áp dụng posting_windows tự động |
| **C4: Automation Rules Engine** | 100% | Hoàn thành | render_done -> draft, idea_scripted, schedule_gap, auto-approve safety lock |
| **C4: Continuous Learning Loop** | 100% | Hoàn thành | learnings.md, recommendations.json cho Session A & B, REQUESTS.md |
| **C4: UI Phân Tích & Notifications** | 100% | Hoàn thành | Stat tiles, SVG pure chart, 7x24 heatmap, notification drawer, manual & CSV import |

---

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

---

## C4 — Analytics, Giờ Vàng, Vòng Tự Học & Automation Rules (HOÀN THÀNH)

### 1. Thu Thập Số Liệu Đa Nền Tảng (`social/analytics/collectors/`):
- `youtube.py`: Thu thập views, likes, comments qua YouTube Data API v3 (`videos.list(part="statistics")`) và watch time, avg retention, subscribers gained qua YouTube Analytics API.
- `tiktok.py`: Kết nối Content Posting API v2 query creator video stats.
- `meta.py`: Bóc tách insights video Facebook Page và Instagram Reels (`plays`, `reach`, `saved`, `shares`).
- `manual.py`: Bộ phân tích CSV đa năng, hỗ trợ xuất khẩu trực tiếp từ YouTube Studio và TikTok Studio, tự động ánh xạ cột và liên kết bài viết theo tiêu đề.
- Cơ chế lưu trữ: Ghi nhận snapshots theo mốc thời gian (1h, 6h, 24h, 72h, 7d, 28d) vào `data/projects/<id>/analytics/metrics/<target_id>.jsonl`.

### 2. Động Cơ Phân Tích & Giờ Vàng (`social/analytics/insights.py`):
- **Chỉ số KPI:** Tổng lượt xem, thời lượng xem, tỷ lệ giữ chân trung bình, tỷ lệ tương tác `ER = (likes + comments + shares + saves) / views * 100%`, người theo dõi mới, CTR sản phẩm, doanh thu affiliate.
- **Bản đồ nhiệt Giờ Vàng (7×24 Heatmap):** Tính toán median views 24h cho từng ô (thứ trong tuần × giờ đăng). Tự động sinh danh sách slot tối ưu và nút "Áp dụng khung giờ vàng" trực tiếp vào cấu hình tài khoản.
- **Join hiệu quả liên phân hệ:**
  - Session A: Khớp `Post.render_job_id` với `runs/render_queue/*.req.json` để xếp hạng hiệu quả theo mẫu template (`remake-v1`, `tiktok-sales-v1`, `koc-review-v1`).
  - Session B: Khớp `Post.idea_id` với `content/ideas/*.json` và `content/blueprints/` để đánh giá chủ đề và nhịp kịch bản.
- **Phát hiện bài đột phá & kém:** Phân loại bài bùng nổ (views ≥ 2.0x median) và bài kém (views ≤ 0.5x median) kèm giả thuyết tự động về hook, thumbnail, khung giờ.

### 3. Động Cơ Quy Tắc Tự Động Hoá (`social/automation.py`):
- Hỗ trợ các trigger: `render_done` (video render xong), `idea_scripted` (kịch bản hoàn tất), `schedule_gap` (lịch tuần tới bị trống).
- Khóa an toàn nghiêm ngặt: Mọi bài viết tự động dừng ở trạng thái `pending_approval`, chỉ tự động duyệt khi người dùng chủ động cấu hình `auto_approve: true` kèm cảnh báo rõ ràng.
- Trung tâm thông báo `SocialNotification` cập nhật thời gian thực vào thanh điều hướng.

### 4. Vòng Tự Học (Continuous Learning Loop):
- Tự động xuất `analytics/learnings.md` và `analytics/recommendations.json`.
- Ghi nhận khuyến nghị định hướng sản xuất cho Session A (templates ưu tiên) và Session B (chủ đề kịch bản ưu tiên) vào `status/REQUESTS.md` để `99_FINAL` tổng hợp.

### 5. Giao Diện Người Dùng (`/social/analytics`):
- Thẻ thống kê KPI với biểu tượng Morphicons.
- Biểu đồ đường xu hướng lượt xem 14 ngày (SVG thuần theo quy chuẩn `dataviz`, tương thích giao diện Sáng/Tối).
- Ma trận bản đồ nhiệt 7 ngày × 24 giờ với dải màu ngọc lục bảo (emerald) và tooltip động khi rê chuột.
- Bảng xếp hạng Top Outliers và Mẫu Video dẫn đầu.
- Khung xem trước báo cáo tự học Markdown.
- Modal nhập số liệu thủ công và import CSV Studio.
- Drawer Trung tâm thông báo và Modal quản lý Quy tắc tự động hoá.
- Mini views badge trên `PostChip` tại tab Lịch đối với các bài đã xuất bản.

---

## Hướng Dẫn Thiết Lập OAuth App Đa Nền Tảng (Official Guides)

### 1. YouTube Data API v3 & YouTube Analytics API
- **Cổng đăng ký:** [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- **Các bước thực hiện:**
  1. Tạo Project mới: ví dụ `socnhotv-publishing`.
  2. Vào **APIs & Services > Library**, tìm và kích hoạt:
     - `YouTube Data API v3`
     - `YouTube Analytics API`
  3. Cấu hình **OAuth Consent Screen**:
     - User Type: `External` (hoặc `Internal` nếu dùng Google Workspace).
     - Điền App name, User support email, Developer contact info.
     - Scopes bắt buộc:
       - `https://www.googleapis.com/auth/youtube.upload` (đăng video và shorts)
       - `https://www.googleapis.com/auth/youtube.readonly` (đọc trạng thái video)
       - `https://www.googleapis.com/auth/yt-analytics.readonly` (thu thập số liệu analytics)
  4. Tạo **Credentials > OAuth client ID**:
     - Application type: `Web application`.
     - Name: `SocNhoTV Dashboard`.
     - Authorized redirect URIs: `http://localhost:3000/api/auth/callback` (hoặc domain production).
  5. Lưu `Client ID` và `Client Secret` an toàn vào KeyVault:
     - Khóa: `oauth_youtube_client_id`, `oauth_youtube_client_secret`.
- **Hạn ngạch & Giới hạn (Quota & Limits):**
  - Mặc định: **10.000 units/ngày** (miễn phí).
  - Tác vụ `videos.insert` (tải video lên): tiêu tốn **1.600 units/lần**.
  - Tối đa khoảng 6 video tải lên mỗi ngày trên quota miễn phí.
  - Khi cần nâng hạn ngạch: Nộp biểu mẫu "YouTube API Quota Extension Request" trên Google Cloud Console (miễn phí, duyệt trong 2-3 ngày làm việc).

### 2. TikTok Content Posting API
- **Cổng đăng ký:** [TikTok for Developers](https://developers.tiktok.com/)
- **Các bước thực hiện:**
  1. Đăng ký tài khoản Developer và tạo App mới: chọn danh mục `Content Posting API`.
  2. Khai báo Scopes yêu cầu:
     - `video.publish`: Đăng video trực tiếp lên trang cá nhân/kênh TikTok của creator.
     - `video.upload`: Tải video lên hộp thư nháp (Inbox) của creator để creator kiểm tra trước khi công khai.
     - `user.info.basic`: Đọc thông tin cơ bản tài khoản (handle, avatar, display name).
  3. Cấu hình Redirect URI: `http://localhost:3000/api/auth/callback`.
  4. Nộp video demo quy trình: TikTok yêu cầu quay màn hình luồng người dùng bấm xác thực và đăng video trên giao diện để xét duyệt App Review.
  5. Lưu `Client Key` và `Client Secret` vào KeyVault:
     - Khóa: `oauth_tiktok_client_key`, `oauth_tiktok_client_secret`.
- **Hạn ngạch & Giới hạn:**
  - Sandbox: Tối đa 5 tài khoản test được cấp quyền.
  - Production: Giới hạn theo từng creator (thường không quá 10 video/ngày/creator để chống spam).

### 3. Meta Graph API (Facebook Page & Instagram Reels)
- **Cổng đăng ký:** [Meta for Developers](https://developers.facebook.com/)
- **Các bước thực hiện:**
  1. Tạo App với loại ứng dụng: `Business`.
  2. Thêm sản phẩm: **Facebook Login for Business** và **Instagram Graph API**.
  3. Yêu cầu Quyền hạn (Permissions):
     - `pages_show_list`: Liệt kê các Trang Facebook người dùng quản trị.
     - `pages_read_engagement`: Đọc thông tin tương tác của Trang.
     - `pages_manage_posts`: Đăng tải bài viết và video lên Trang Facebook.
     - `instagram_basic`: Đọc thông tin tài khoản Instagram Business/Creator.
     - `instagram_content_publish`: Xuất bản video trực tiếp lên Instagram Reels.
  4. Cấu hình Valid OAuth Redirect URIs: `http://localhost:3000/api/auth/callback`.
  5. Đảm bảo tài khoản Instagram đã được chuyển đổi sang `Professional Account` (Business hoặc Creator) và liên kết với Facebook Page.
  6. Lưu `App ID` và `App Secret` vào KeyVault:
     - Khóa: `oauth_meta_app_id`, `oauth_meta_app_secret`.
- **Hạn ngạch & Giới hạn:**
  - Instagram Reels API cho phép xuất bản tối đa **50 video Reels trong vòng 24 giờ** cho mỗi tài khoản Instagram.

---

## Nghiệm Thu Kiểm Thử Tổng Thể Session C

```bash
cd tool && .venv/bin/pytest tests/test_social_*.py
============================== 32 passed in 0.67s ==============================
```

- `test_social_models.py`: 3 passed (Models validation, timezone Asia/Ho_Chi_Minh)
- `test_social_store.py`: 3 passed (Atomic writes, fcntl flock, query filtering)
- `test_social_migrate.py`: 1 passed (Legacy schedule/channels migration, idempotency)
- `test_social_service.py`: 5 passed (State machine transitions, suggest time, caption generator)
- `test_social_api.py`: 4 passed (REST endpoints validation)
- `test_social_adapters.py`: 4 passed (YouTube resumable, TikTok chunked, Meta container, quota detection)
- `test_social_scheduler.py`: 1 passed (30s tick cycle, approval gate, exponential backoff)
- `test_social_manual.py`: 1 passed (Manual bundle generation, ZIP packaging)
- `test_social_analytics.py`: 6 passed (KPI aggregation, ER %, Heatmap matrix, Outliers detection, CSV parser, Learnings)
- `test_social_automation.py`: 3 passed (render_done event processing, safety auto-approve checks, schedule gap alert)
- `test_social_e2e.py`: 1 passed (Full End-to-End: Ingest -> Draft -> Approve -> Schedule -> Publish -> Metric Collect -> Insights)

**Tổng cộng:** 32/32 tests passed 100%. TypeScript compilation: 0 lỗi.

---

## Ảnh Chụp Màn Hình Nghiệm Thu (Lưu trữ tại `data/projects/soc-nho-tv/shots/`)

1. `C2_month.png`: Giao diện Lịch xuất bản chế độ Tháng (Month View).
2. `C2_week.png`: Giao diện Lịch xuất bản chế độ Tuần với khung giờ vàng (Week View).
3. `C2_approvals.png`: Hàng chờ duyệt bài viết với video player và checklist tự động.
4. `C2_composer.png`: Ngăn kéo soạn thảo bài viết đa nền tảng (Post Composer).
5. `C4_analytics_overview.png`: Tab Phân tích với thẻ KPI, biểu đồ lượt xem SVG thuần, bản đồ nhiệt giờ vàng 7×24, bảng bài bùng nổ và khung tự học.
6. `C4_automation_rules.png`: Modal quản lý Quy tắc tự động hoá và khoá an toàn duyệt bài.
7. `C4_notifications.png`: Ngăn kéo Trung tâm thông báo xuất bản và nhắc nhở lịch.
8. `C4_manual_metrics.png`: Hộp thoại cập nhật số liệu bài viết thủ công và Import CSV Studio.

