# Session A — Video & Templates

**Trạng thái:** Đang tiến hành (A1 Hoàn tất -> Chuyển sang A2)

## Tiến độ chi tiết

### A1 — Video Engine HyperFrames + Preset đa nền tảng + Hàng đợi render
- **Hoàn thành:** 2026-11-04
- **Các thành phần đã triển khai:**
  1. `tool/src/socnhotv/video/platforms.py`: 6 PlatformPresets (tiktok, douyin, reels, shorts, youtube, facebook), safe zones, loudness -14 LUFS, hàm `get_platform()`, `list_platforms()`, `fit_strategy()`.
  2. `tool/src/socnhotv/video/fallback_ffmpeg.py`: Fallback ffmpeg compositor với cảnh báo `FALLBACK_USED`, xử lý ghép scenes, voiceover, bgm theo tỷ lệ preset.
  3. `tool/src/socnhotv/video/hyperframes_engine.py`: `HyperFramesEngine` quản lý build bundle deterministic, `check()`, `render()` qua CLI/fallback, audio mastering -14 LUFS qua `AudioMastering`, trích xuất thumbnail JPEG 1.0s.
  4. `tool/src/socnhotv/core/adapters/hyperframes_adapter.py`: Refactor thành lớp bọc mỏng gọi `HyperFramesEngine`, bảo đảm 100% backward compatibility cho `graph_runner`.
  5. `tool/src/socnhotv/video/queue.py`: Hàng đợi `RenderQueue` đa tiến trình (asyncio, `MAX_PARALLEL=2`), render đa nền tảng, ghi nhật ký sự kiện `runs/events/render.jsonl`, tích hợp contract `create_draft_post` khi có `auto_draft`.
  6. `tool/src/socnhotv/core/api/routes/video.py`: Các API endpoint `GET /video/platforms`, `POST /projects/{pid}/video/render`, `GET /projects/{pid}/video/render/{job_id}`, `GET /projects/{pid}/video/renders`, cancel và SSE events stream.
  7. `tool/src/socnhotv/video/cli.py`: CLI độc lập `python -m socnhotv.video.cli` hỗ trợ `platforms` và `render`.
- **Kiểm thử:**
  - `tests/test_video_platforms.py`: 5/5 passed
  - `tests/test_video_engine.py`: 4/4 passed
  - `tests/test_video_queue.py`: 3/3 passed
  - `tests/test_core_step4_hyperframes.py`: 5/5 passed (DAG & Artifacts render)
  - Render thực tế 5s cho TikTok (1080x1920) và YouTube (1920x1080), ffprobe và loudnorm chuẩn xác.
