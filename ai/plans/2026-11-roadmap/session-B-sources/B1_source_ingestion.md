# B1 — Nạp nguồn nội dung: Douyin / TikTok / YouTube / file local

Bạn là Session B (Sources & Intelligence). Đọc: `CLAUDE.md`, `ai/plans/2026-11-roadmap/CONTRACTS.md` (vùng của B + mục 3 Bản quyền), `ai/skills/agent-reach/` nếu có, `core/storage/project_store.py`, `socnhotv/workspace/paths.py`, `core/api/data_routes.py` (chỉ đọc — xem cách upload library).

Thực trạng: `yt-dlp` chưa cài trước bootstrap (kiểm `status/REQUESTS.md`), không có module nguồn nào.

## Mục tiêu
Dán 1 link (hoặc nhiều link / 1 playlist / 1 file) → hệ thống tải về, chuẩn hoá, trích metadata, lưu kèm thông tin bản quyền, sẵn sàng cho B2–B4.

## Việc cần làm
1. **`sources/models.py`**: `SourceItem {id, project_id, platform: douyin|tiktok|youtube|bilibili|facebook|instagram|local, url, author, author_url, title, description, duration_s, published_at, stats{views,likes,comments,shares}, hashtags[], music, rights: owned|licensed|permission|reference_only (mặc định reference_only), rights_note, files{video, audio, thumb, subtitle_orig}, status: queued|downloading|ready|failed, created_at}`.
2. **`sources/downloader.py`**: dùng `yt_dlp` Python API (không subprocess nếu được):
   - Định dạng ưu tiên mp4 ≤1080p, tách thêm audio wav 16k mono (`ffmpeg`) cho ASR.
   - Lấy phụ đề gốc nếu có (`writesubtitles`, `writeautomaticsub`, langs `zh-Hans,zh,vi,en`).
   - Cookie: hỗ trợ `cookiefile` do người dùng tự xuất (đường dẫn trong settings), **không** tự đăng nhập, không lưu mật khẩu. Nếu Douyin chặn → trả lỗi rõ "cần cookie" + hướng dẫn, không thử vượt captcha.
   - Rate-limit nhẹ (1 tải/2s/platform), retry 3 lần backoff.
   - Lưu: `raw/<source_id>/{video.mp4,audio.wav,thumb.jpg,meta.json,subs.*.vtt}`; `meta.json` = SourceItem.
3. **`sources/local.py`**: nhập file mp4/mov có sẵn (rights mặc định `owned`).
4. **`sources/jobs.py`**: hàng đợi tải asyncio (tối đa 3 song song), trạng thái + %; sự kiện `runs/events/sources.jsonl`.
5. **`sources/scenes.py`**: tách cảnh bằng `scenedetect` (ContentDetector) → `raw/<id>/scenes.json` [{start,end,thumb}]; keyframe mỗi cảnh. Fallback ffmpeg `select='gt(scene,0.3)'` nếu thiếu opencv.
6. **API `core/api/routes/sources.py`**: `POST /projects/{pid}/sources` (body `{urls: [], rights?, note?}` hoặc multipart file) → job ids; `GET /projects/{pid}/sources?platform=&rights=&q=`; `GET /projects/{pid}/sources/{sid}`; `PATCH …/{sid}` (đổi rights/note — bắt buộc gửi `confirm_rights: true` khi đổi khỏi `reference_only`); `DELETE …/{sid}` (xoá vào `raw/_trash/`, không xoá vĩnh viễn); `GET …/{sid}/file/{name}` (stream); `POST …/{sid}/scenes`.
7. **Node plugin `core/nodes/plugins/sources.py`**: node `source_video` (input: url text; output: video, audio, text metadata) — category "Input".
8. **UI tối thiểu** `app/[locale]/sources/page.tsx` + `components/sources/*`: ô dán nhiều link, lưới `SourceCard` (thumb, nền tảng, tác giả, thời lượng, view, badge rights màu: xám reference_only / xanh owned / vàng licensed/permission), trạng thái tải realtime, chi tiết nguồn (player, metadata, cảnh, đổi rights có hộp xác nhận dùng `lib/confirm.ts`). `lib/api/sources.ts`, `store/modules/sources.ts`, i18n `messages/modules/sources.*.json`.

## Nghiệm thu
- `tool/tests/test_sources_downloader.py` (mock yt_dlp: map metadata đúng, retry, lỗi cookie rõ ràng), `test_sources_api.py` (TestClient: tạo, list, đổi rights cần confirm, xoá vào trash).
- Chạy thật: 1 link YouTube Shorts công khai + 1 file local → `ready`, có scenes.json. Douyin: thử 1 link; nếu cần cookie, ghi rõ kết quả vào `status/B.md`.
- UI `/sources` hoạt động trên 3000; chụp `shots/B1_*.png`.
- Commit `feat(B1): source ingestion (yt-dlp, local, scenes) + sources UI`. Cập nhật `status/B.md`.
