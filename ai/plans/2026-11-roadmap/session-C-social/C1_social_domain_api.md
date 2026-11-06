# C1 — Social Manager: Mô hình dữ liệu · Lưu trữ · API · Di trú lịch đăng cũ

Bạn là Session C (Social). Đọc: `CLAUDE.md`, `ai/plans/2026-11-roadmap/CONTRACTS.md` (vùng của C, mục 2.3, mục 3), `status/C.md` (nợ đầu vào), `socnhotv/social/contracts.py` (stub), và **chỉ đọc**: `core/api/app.py` dòng ~679–760 (`GET/POST /projects/{pid}/publishing`), `core/api/data_routes.py` dòng ~694–705 (`/channels`), `tool/dashboard/components/studio/tabs/PublishTab.tsx`, `tool/dashboard/lib/repositories/types.ts` (`ScheduledPost`, Channel), `data/projects/soc-nho-tv/publishing/schedule.json`, `core/providers/key_vault.py`.

## Thực trạng (lỗi cần biết)
- `PublishTab` gọi `POST /projects/{pid}/publishing/schedule` → **404**, dữ liệu chỉ nằm trong Zustand, reload là mất.
- `scheduledAt` là chuỗi tự do (`"Hàng ngày · 19:00"`), không parse được, không có timezone, không có lặp lịch thật.
- Chỉ 2 nền tảng youtube/tiktok, không có tài khoản thật, không trạng thái đăng thật.
- Endpoint cũ `/publishing` và `/channels` nằm ở file vùng khác → **giữ nguyên, không sửa**; C xây API mới dưới `/projects/{pid}/social/*` và đọc dữ liệu cũ để di trú.

## Mô hình (`social/models.py`, pydantic v2, thời gian ISO-8601 có timezone, mặc định `Asia/Ho_Chi_Minh`)
- `SocialAccount {id, platform: youtube|tiktok|facebook|instagram|douyin|threads|x, handle, display_name, avatar, channel_url, auth: {mode: oauth|manual|browser_assisted, token_ref (key_vault id, không lưu token thô), scopes[], expires_at}, status: connected|expired|manual|disabled, default_hashtags[], default_caption_footer, posting_windows[{weekday, start, end}], daily_limit, tags[]}`
- `Post {id, project_id, title, media[{path, platform_variant?, kind: video|image|carousel, duration_s, thumb}], source_ref, render_job_id, idea_id, status: draft|pending_approval|approved|scheduled|publishing|published|failed|cancelled, approval{required: true, by, at, note}, targets: [PostTarget]}`
- `PostTarget {id, account_id, platform, scheduled_at, caption, hashtags[], title (YT), description (YT), tags (YT), privacy: public|unlisted|private, made_for_kids, cover_time_s, first_comment, product_link (TikTok Shop/affiliate), disclosure_ad: bool, status, external_id, external_url, attempts, last_error, published_at}`
- `RecurringSlot {id, account_id, rrule (RFC5545, dùng python-dateutil), label, template_hint}` — khung giờ cố định ("T2/T4/T6 19:00").
- `CampaignTag`, `CalendarNote {date, text, color}` (ghi chú sự kiện: 11.11, Tết…).

## Lưu trữ `social/store.py`
- File JSON theo project: `publishing/accounts.json`, `publishing/posts/<post_id>.json`, `publishing/slots.json`, `publishing/notes.json`, `publishing/audit.jsonl` (mọi thay đổi trạng thái: ai, lúc nào, từ→tới).
- Ghi nguyên tử (`tmp` + `os.replace`) + file lock (`fcntl`) vì scheduler và API cùng ghi.
- **Di trú** `social/migrate.py`: đọc `publishing/schedule.json` + `publishing/channels.json` cũ → tạo Account (mode manual) + Post (status pending_approval, parse "Hàng ngày · HH:MM" thành RecurringSlot) — idempotent, giữ file cũ, ghi `publishing/.migrated_v1`.
- **Inbox**: hàm `ingest_inbox()` đọc `publishing/inbox/*.json` (từ stub contract cũ / A / B) → Post draft, chuyển file vào `inbox/_done/`.
- Thay stub `contracts.create_draft_post` bằng implement thật (giữ chữ ký), tự tạo 1 PostTarget cho mỗi platform với account mặc định của platform đó (nếu có).

## Logic `social/service.py`
- Chuyển trạng thái hợp lệ (máy trạng thái rõ ràng, sai → 409). `approved` bắt buộc khi `approval.required`.
- `suggest_time(account_id, after)` = slot trống gần nhất trong posting_windows/RecurringSlot, tránh trùng giờ (≥ 2h giữa 2 bài cùng account), tôn trọng `daily_limit`.
- `caption_variants(post, platforms)`: sinh caption từng nền tảng theo giới hạn (TikTok 2200, YT title 100 / desc 5000, IG 2200 + 30 hashtag, FB), tự gắn `default_caption_footer`, disclosure affiliate nếu post có `product_link`. Có thể gọi LLM qua `core/providers/router.py` (chỉ đọc/dùng), fallback rule-based.
- Đọc ideas từ `content/ideas/*.json` (contract B) → `schedule_idea(idea_id, account_id, at)` tạo Post draft gắn `idea_id`.

## API `core/api/routes/social.py` (prefix `/projects/{pid}/social`)
Accounts CRUD (`/accounts`), `/posts` (filter: status, platform, account, from, to, q), `POST /posts`, `PATCH /posts/{id}`, `POST /posts/{id}/submit` (→pending_approval), `/approve`, `/reject`, `/schedule` (body targets times), `/cancel`, `/duplicate`, `POST /posts/draft` (dùng bởi A/B UI), `GET /calendar?from&to&view=month|week` (trả target đã phẳng hoá + slot trống + notes), `PUT /posts/{id}/targets/{tid}/time` (kéo-thả), `GET/PUT /slots`, `GET/PUT /notes`, `POST /ideas/{iid}/schedule`, `POST /suggest-time`, `POST /caption-variants`, `POST /migrate`, `GET /audit?post_id=`.

## Nghiệm thu
- `tool/tests/test_social_models.py`, `test_social_store.py` (ghi đồng thời 2 thread không hỏng file), `test_social_migrate.py` (schedule.json thật hiện có → đúng số post + slot, chạy 2 lần không nhân đôi), `test_social_api.py` (luồng draft→submit→approve→schedule; reject; 409 khi sai trạng thái; kéo-thả đổi giờ; suggest_time tránh trùng).
- `create_draft_post` thật được A/B gọi thử trong test.
- Commit `feat(C1): social domain, storage, API, legacy schedule migration`. Cập nhật `status/C.md`.
