# Session B — Sources & Intelligence

**Trạng thái:** B1, B2, B3 HOÀN TẤT — Bắt đầu B4 (Channel Intelligence)

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

## B3 — Phân tích video mẫu → Blueprint · Sản phẩm · Kịch bản KOC review & Affiliate (Đã hoàn thành)
- **Tập tin đã tạo/sửa:**
  - `tool/src/socnhotv/intelligence/products.py`: Mô hình `Product`, CRUD lưu `products/<id>/product.json` + `products/_trash/`, parser OpenGraph import nhanh metadata từ URL không cần login.
  - `tool/src/socnhotv/intelligence/compliance.py`: Bộ lọc tuân thủ chính sách quảng cáo & TikTok Shop. Chặn tuyên bố y tế/chữa bệnh dứt điểm, cam kết 100%, tự động phát hiện và chèn nhãn tiếp thị `#affiliate #quangcao`.
  - `tool/src/socnhotv/intelligence/analyzer.py`: Phân tích video mẫu thành `VideoBlueprint` chuẩn (role gán tự động: `hook, problem, agitate, reveal, demo, proof, compare, offer, urgency, cta`), tính toán nhịp pacing (cuts/10s), so khớp template tương đồng nhất bằng rapidfuzz.
  - `tool/src/socnhotv/intelligence/patterns.py`: Tổng hợp công thức viral đa video cùng niche (tính thời lượng hook trung vị, chuỗi role phổ biến, mẫu hook/CTA).
  - `tool/src/socnhotv/intelligence/script_gen.py`: 3 bộ sinh kịch bản (`koc_review`, `tiktok_sales`, `affiliate_compare`), kiểm duyệt tuân thủ, lưu kịch bản vào `content/scripts/`, tự động tạo `ContentIdea` (status `scripted`) cho Session C, và đóng gói `RenderRequest` sẵn sàng render HyperFrames.
  - `tool/src/socnhotv/core/api/routes/intel.py`: Cụm REST API quản lý products (CRUD, import-url), phân tích video blueprint (`/intel/analyze/{source_id}`), tải blueprint, patterns và sinh kịch bản (`/intel/generate-script`).
  - `tool/src/socnhotv/core/nodes/plugins/sources.py`: Đăng ký 2 node mới `blueprint_analyze` và `script_from_blueprint`.
  - Frontend:
    - API client: `tool/dashboard/lib/api/intel.ts`.
    - Quản lý sản phẩm: `components/products/{ProductCard,ProductDetailModal,AddProductModal,ProductsList}.tsx`, `app/[locale]/products/page.tsx` (lưới sản phẩm, thẻ nét đứt thêm mới).
    - Phân tích Blueprint & Kịch bản: `components/intel/{BlueprintView,ScriptWizardModal}.tsx`, `app/[locale]/intel/page.tsx` (thanh timeline beat đa màu, số liệu nhịp, wizard 3 bước chọn sản phẩm -> nhân vật/giọng -> sinh kịch bản & gửi render).
    - Tích hợp chi tiết nguồn: Thêm nút "Phân tích cấu trúc" trong `SourceDetailModal.tsx`.
    - Điều hướng & Đa ngôn ngữ: `nav-modules/sources.ts` (thêm Sản phẩm, Blueprint & Trí tuệ), `messages/modules/sources.{vi,en}.json`.
- **Kiểm thử nghiệm thu:**
  - `test_intel_analyzer.py`: 2/2 test pass.
  - `test_intel_products_api.py`: 2/2 test pass.
  - `test_intel_script_gen.py`: 2/2 test pass.
  - Kiểm thử thực tế: Phân tích thành công video nguồn thành Blueprint, tạo sản phẩm mẫu "Kem Chống Nắng Sóc Nhỏ", sinh kịch bản KOC LyLy chuẩn tuân thủ kèm `ContentIdea` và `RenderRequest`.
