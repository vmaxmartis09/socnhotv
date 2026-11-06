# A1 — Video Engine HyperFrames + Preset đa nền tảng + Hàng đợi render

Bạn là Session A (Video). Đọc trước: `CLAUDE.md`, `ai/plans/2026-11-roadmap/CONTRACTS.md` (vùng sở hữu của A), `ai/skills/hyperframes/SKILL.md`, `ai/skills/hyperframes-core/SKILL.md`, `ai/skills/hyperframes-cli/SKILL.md`, file hiện có `tool/src/socnhotv/core/adapters/hyperframes_adapter.py` (649 dòng: `generate_html_composition`, `build_project_bundle`, `render_fallback_ffmpeg`, `render` gọi `npx hyperframes`, `render_from_artifacts`), `tool/src/socnhotv/video/contracts.py` (stub từ bootstrap).

Thực trạng: CLAUDE.md nói `tool/src/socnhotv/video/hyperframes_engine.py` là engine chuẩn nhưng file chưa tồn tại; toàn bộ logic đang nằm ở adapter, cứng 9:16, 1 kiểu HTML.

## Mục tiêu
Một engine render tất định, dùng được cho mọi template và mọi nền tảng, có hàng đợi job thật.

## Việc cần làm
1. **`video/platforms.py`** — bảng preset (pydantic):
   | id | kích thước | fps | max dài | safe zone (top/bottom/left/right px) | ghi chú |
   |---|---|---|---|---|---|
   | tiktok | 1080×1920 | 30 | 600s | 180/320/40/120 | cột nút phải |
   | douyin | 1080×1920 | 30 | 900s | 200/340/40/120 | |
   | reels | 1080×1920 | 30 | 180s | 220/380/40/100 | |
   | shorts | 1080×1920 | 30 | 180s | 160/300/40/110 | |
   | youtube | 1920×1080 | 30 | none | 60/90/60/60 | title-safe 90% |
   | facebook | 1080×1350 (4:5) | 30 | 240s | 80/160/40/40 | feed |
   Kèm `loudness_lufs` (-14 tất cả, youtube -14), `audio_bitrate`, `video_bitrate`, `codec`. Hàm `get_platform(id)`, `fit_strategy` (`cover`/`contain`/`blur-pad`) khi đổi tỉ lệ.
2. **`video/hyperframes_engine.py`** — class `HyperFramesEngine`:
   - `build(composition_html, assets, platform) -> bundle_dir` (thư mục project HyperFrames hợp lệ theo `hyperframes-core`: `index.html`, `data-*` timing, `class="clip"`, GSAP paused timeline, assets copy vào bundle).
   - `render(bundle_dir, out_path, platform) -> Path` gọi CLI HyperFrames (cách gọi đúng lấy từ `status/REQUESTS.md`/`hyperframes-cli`), timeout theo độ dài, log stdout ra `runs/render_queue/<job>.log`.
   - `check(bundle_dir)` chạy `hyperframes check` trước khi render; fail → trả lỗi rõ ràng.
   - Fallback FFmpeg chỉ khi CLI không có (giữ logic cũ, chuyển từ adapter sang `video/fallback_ffmpeg.py`), log cảnh báo `FALLBACK_USED`.
   - Post-process audio: gọi `core/adapters/audio_mastering.py` (đọc, không sửa) để đạt -14 LUFS.
   - Thumbnail: trích frame ở 1.0s → `<out>.jpg`.
3. **Refactor `core/adapters/hyperframes_adapter.py`** thành lớp mỏng gọi `HyperFramesEngine` (giữ nguyên API public để `graph_runner.py` và test `test_core_step4_hyperframes.py` vẫn pass). Không sửa `graph_runner.py`.
4. **Hàng đợi render `video/queue.py`**: thay stub `submit_render` bằng implement thật nhưng **giữ chữ ký** trong contracts.
   - Job lưu `runs/render_queue/<job_id>.json`; worker asyncio 1 tiến trình, đồng thời tối đa `MAX_PARALLEL=2` (đọc env `SOCNHOTV_RENDER_PARALLEL`).
   - 1 `RenderRequest` nhiều `platforms` → render tuần tự từng nền tảng, `outputs[platform]` = `output/<output_name>/<platform>.mp4`.
   - Trạng thái + tiến độ % (parse log) + huỷ job.
   - Khi job `done`: nếu `RenderRequest.data.get("auto_draft")` → gọi `socnhotv.social.contracts.create_draft_post(...)` (không import gì khác của C).
   - Ghi sự kiện `runs/events/render.jsonl`.
5. **API `core/api/routes/video.py`** (chỉ file này): `GET /video/platforms`, `POST /projects/{pid}/video/render` (body RenderRequest), `GET /projects/{pid}/video/render/{job_id}`, `GET /projects/{pid}/video/renders?status=`, `POST /projects/{pid}/video/render/{job_id}/cancel`, `GET /projects/{pid}/video/render/{job_id}/events` (SSE tiến độ, dùng `sse-starlette` đã có). Worker khởi động bằng `@router.on_event("startup")` hoặc lazy-start ở request đầu.
6. **CLI**: `tool/src/socnhotv/video/cli.py` — `python -m socnhotv.video.cli render --project <id> --template <tid> --platforms tiktok,youtube --data data.json`. (Không sửa `cli/__init__.py` chung; ghi vào REQUESTS nếu cần gắn vào `python -m socnhotv`.)

## Nghiệm thu
- `tool/tests/test_video_platforms.py`, `test_video_engine.py` (bundle hợp lệ, check gọi đúng, fallback khi thiếu CLI — mock subprocess), `test_video_queue.py` (1 request 3 nền tảng → 3 output, huỷ job, auto_draft gọi contract).
- Test cũ `test_core_step4_hyperframes.py` vẫn pass.
- Render thật 1 composition test 5s ra `tiktok` + `youtube`, kiểm `ffprobe` đúng kích thước, loudness ≈ -14 LUFS (`ffmpeg -af loudnorm=print_format=json`).
- Commit `feat(A1): HyperFramesEngine, platform presets, render queue`. Cập nhật `status/A.md`.
