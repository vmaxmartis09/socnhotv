# Session B — Sources & Intelligence

**Trạng thái:** Đang tiến hành (B1 & B2 HOÀN TẤT, chuẩn bị sang B3)

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
  - `test_sources_api.py`: 3/3 test pass.
  - Chụp ảnh màn hình lưu tại `data/projects/soc-nho-tv/shots/B1_sources_ui.png`.

## B2 — Bản địa hoá video Douyin/TikTok -> Việt (Đã hoàn thành)
- **Tập tin đã tạo/sửa:**
  - `tool/src/socnhotv/sources/asr.py`: Trích xuất lời thoại tiếng Trung bằng `faster-whisper` (word timestamps, CPU int8) kết hợp ưu tiên bóc tách từ file VTT gốc.
  - `tool/src/socnhotv/sources/translate.py`: Dịch từng câu ZH -> VI kèm nạp bảng thuật ngữ/thương hiệu `knowledge/glossary.json`. Kiểm soát tốc độ đọc 15 ký tự/s (ngưỡng trần 1.25x), tự động rút gọn câu khi vượt thời lượng.
  - `tool/src/socnhotv/sources/rewrite.py`: Viết lại kịch bản theo 3 phong cách (`faithful`: sát ý, `hook_boost`: hook 3s giữ chân + CTA mạnh, `character`: phong cách Sóc Nhỏ Bi / KOC).
  - `tool/src/socnhotv/sources/revoice.py`: Tổng hợp giọng đọc TTS (Edge-TTS / OmniVoice), canh khớp thời lượng và đi qua bộ `AudioMastering` chuẩn -14 LUFS (EBU R128).
  - `tool/src/socnhotv/sources/localize_pipeline.py`: Pipeline liên hoàn khép kín ASR -> Dịch -> Viết lại -> Revoice -> gửi `RenderRequest` qua hợp đồng `socnhotv.video.contracts.submit_render`.
  - Khóa bản quyền nghiêm ngặt: Mode L (giữ video gốc) lập tức từ chối HTTP 400 nếu nguồn là `reference_only`. Mode R (dựng lại bằng media riêng) được phép chạy với `source_ref`.
  - API `routes/sources.py`: Đã bổ sung `/localize`, `/transcript`, `/script` (GET/PUT).
  - Node plugin: Đăng ký node `localize` (Input: video, audio; Output: script, audio, captions).
  - Frontend `LocalizeStudio.tsx`: Giao diện 3 cột xem video gốc, bảng câu dịch/kịch bản tương tác inline, bộ điều khiển Mode R/L, giọng đọc `VoiceSelectorWithClone`, style và nút bấm Bản địa hoá.
- **Kiểm thử nghiệm thu:**
  - `test_sources_localize.py`: 6/6 test pass.
  - Kiểm thử thực tế: Đoạn thoại mẫu dịch sang tiếng Việt, viết lại theo phong cách Sóc Nhỏ và xuất ra `voice.vi.mp3` đạt chuẩn âm thanh TikTok Mastering (-14 LUFS).
