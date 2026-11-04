# Session B — Sources & Intelligence

**Trạng thái:** Đang tiến hành (B1 HOÀN TẤT, chuẩn bị sang B2)

## B1 — Nạp nguồn nội dung (Đã hoàn thành)
- **Tập tin đã tạo/sửa:**
  - `tool/src/socnhotv/sources/models.py`: SourceItem, IngestRequest, UpdateRightsRequest, SourceStats, SceneCut. Quyền mặc định `reference_only`.
  - `tool/src/socnhotv/sources/downloader.py`: yt-dlp Python API, ưu tiên MP4 <=1080p, trích xuất audio WAV 16kHz mono (ffmpeg), phụ đề VTT, rate-limit 2s/platform + backoff retry 3 lần, phát hiện Douyin/TikTok yêu cầu cookie rõ ràng, không hack captcha.
  - `tool/src/socnhotv/sources/local.py`: Nhập tập tin video local mp4/mov (quyền mặc định `owned`), ffprobe duration, sinh thumbnail + audio wav.
  - `tool/src/socnhotv/sources/scenes.py`: Tách cảnh tự động với `scenedetect` (ContentDetector 27.0) và fallback ffmpeg; sinh thumbnail cảnh và ghi `scenes.json`.
  - `tool/src/socnhotv/sources/jobs.py`: Hàng đợi asyncio tải đa luồng (tối đa 3 song song), tracking tiến trình, ghi sự kiện `runs/events/sources.jsonl`.
  - `tool/src/socnhotv/sources/service.py`: CRUD nguồn, danh sách lọc/tìm kiếm, xoá vào `raw/_trash/`, khóa nghiêm ngặt quyền `confirm_rights`.
  - `tool/src/socnhotv/core/api/routes/sources.py`: REST API `/projects/{pid}/sources` (ingest urls/file, list, get, patch rights, delete trash, stream file, trigger scenes).
  - `tool/src/socnhotv/core/nodes/plugins/sources.py`: Đăng ký node `source_video` vào NodeRegistry.
  - Frontend: `lib/api/sources.ts`, `store/modules/sources.ts`, `messages/modules/sources.{vi,en}.json`, `components/sources/{SourceCard,SourceDetailModal,AddSourcesModal,SourcesList}.tsx`, `app/[locale]/sources/page.tsx`.
- **Kiểm thử nghiệm thu:**
  - `test_sources_downloader.py`: 4/4 test pass.
  - `test_sources_api.py`: 3/3 test pass (ping, upload, filter, trash, rights guard).
  - Test tải thật: YouTube clip (`https://www.youtube.com/watch?v=jNQXAC9IVRw`) tải thành công, tạo MP4 + WAV 16k + thumb.jpg + scenes.json.
  - Test nạp local: `/tmp/real_test_source.mp4` -> ready, scenes.json sinh đúng 1 cảnh với thumbnail `scene_001.jpg`.
  - Test Douyin: Thử link `https://v.douyin.com/iREq9Gq/` -> Douyin trả về lỗi `Fresh cookies are needed`. Hệ thống bắt đúng lỗi và thông báo người dùng cung cấp cookiefile, tuân thủ đúng nguyên tắc không cố vượt captcha.
  - Giao diện UI: Chụp ảnh màn hình lưu tại `data/projects/soc-nho-tv/shots/B1_sources_ui.png`.
