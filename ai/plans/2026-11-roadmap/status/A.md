# Session A — Video & Templates

**Trạng thái:** Đang tiến hành (A3 Hoàn tất -> Chuyển sang A4)

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

---

### A2 — Hệ thống Template video + 8 template khởi đầu
- **Hoàn thành:** 2026-11-04
- **Các thành phần đã triển khai:**
  1. `tool/src/socnhotv/video/templates/schema.py`: Pydantic `TemplateMeta`, `Slot`, `DurationConfig`, `validate_template_data()` với thông báo lỗi tiếng Việt chuẩn xác.
  2. `tool/src/socnhotv/video/templates/loader.py`: `list_templates()`, `get_template()`, `get_template_dir()`, `reload_templates()` kết nối đồng bộ vào contract stub `video/contracts.py`.
  3. `tool/src/socnhotv/video/templates/compose.py`: `compose_template()` nạp Jinja2 `composition.html.j2` + `styles.css`, căn chỉnh Safe Zone tự co theo preset nền tảng, phân bổ timing scenes theo audio thoại.
  4. `tool/src/socnhotv/video/templates/preview.py`: `generate_template_preview()` render nhanh 540p từ `sample.data.json` ra `preview.mp4` + `preview.jpg`.
  5. `tool/src/socnhotv/core/nodes/plugins/video.py`: Đăng ký Node `template_render` (Category Composition) và `platform_export` (Category Output) vào `NodeRegistry`.
  6. `tool/src/socnhotv/core/api/routes/video.py`: Thêm API templates: `GET /video/templates`, `GET /video/templates/{tid}`, `POST /video/templates/{tid}/validate`, `POST /video/templates/{tid}/preview`, `GET /video/templates/{tid}/preview.mp4`, `GET /video/templates/{tid}/preview.jpg`.
  7. Nối template compose vào `RenderQueue` tự động build bundle theo Jinja2 composition khi có `req.template_id`.

- **Danh mục 8 template khởi đầu:**

| ID | Tên | Phân loại | Nền tảng hỗ trợ | Trạng thái Preview |
|---|---|---|---|---|
| `tiktok-sales-v1` | Bán hàng TikTok – Hook 3s | sales | tiktok, reels, shorts, douyin, facebook | Đã sinh `preview.jpg` + `preview.mp4` |
| `koc-review-v1` | KOC Review Sản Phẩm – 5 Sao | review | tiktok, reels, shorts, facebook | Đã sinh `preview.jpg` + `preview.mp4` |
| `affiliate-compare-v1` | So Sánh Sản Phẩm Affiliate – Kèo Cân Não | affiliate | tiktok, reels, shorts, youtube | Đã sinh `preview.jpg` + `preview.mp4` |
| `unboxing-v1` | Mở Hộp Đập Hộp – Punch-in Chi Tiết | review | tiktok, reels, shorts, youtube | Đã sinh `preview.jpg` + `preview.mp4` |
| `localized-reup-v1` | Bản Địa Hoá Video – Lồng Tiếng & Vietsub | reup | tiktok, reels, shorts, facebook | Đã sinh `preview.jpg` + `preview.mp4` |
| `yt-animation-episode-v1` | Hoạt Hình Dài Tập YouTube 16:9 – Sóc Nhỏ & Koala | animation | youtube, facebook, tiktok | Đã sinh `preview.jpg` + `preview.mp4` |
| `shorts-fact-v1` | Kiến Thức Thú Vị – Kinetic Typography & Count-up | education | shorts, tiktok, reels | Đã sinh `preview.jpg` + `preview.mp4` |
| `story-cartoon-v1` | Truyện Kể Thiếu Nhi Dọc – Trang Sách Lật & Karaoke Sub | story | tiktok, reels, shorts, youtube | Đã sinh `preview.jpg` + `preview.mp4` |

- **Kiểm thử:**
  - `tests/test_video_templates.py`: 4/4 passed
  - Toàn bộ 16 tests `tests/test_video_*.py` passed 100%.

---

### A3 — UI: Thư viện Template + Trình đổ dữ liệu + Hàng đợi Render
- **Hoàn thành:** 2026-11-04
- **Các thành phần đã triển khai:**
  1. `tool/dashboard/lib/api/video.ts`: Typed API client cho toàn bộ endpoint platforms, templates, renders, validate, preview, cancel, sse.
  2. `tool/dashboard/store/modules/video.ts`: Zustand store quản lý templates, activeTemplate, platforms, renderJobs, filters và trạng thái realtime.
  3. `tool/dashboard/components/navigation/nav-modules/video.ts`: 2 mục menu điều hướng Thư viện Mẫu (`/templates`) và Hàng đợi Render (`/renders`) với icons Morphicons.
  4. `tool/dashboard/messages/modules/video.{vi,en}.json`: Bộ nhãn i18n đầy đủ cho module Video & Templates.
  5. `tool/dashboard/components/templates/TemplateCard.tsx`: Thẻ mẫu hiển thị preview ảnh, hover phát preview.mp4 muted, badge thể loại, thời lượng và nền tảng.
  6. `tool/dashboard/components/templates/SlotField.tsx`: Bộ điều khiển tự động theo kiểu dữ liệu slot (text đếm ký tự, product, media[], number).
  7. `tool/dashboard/components/renders/RenderJobCard.tsx`: Thẻ job thống nhất hiển thị trạng thái, tabs video player đa nền tảng, tải mp4, huỷ job và gửi sang lịch đăng.
  8. `tool/dashboard/app/[locale]/templates/page.tsx`: Thư viện templates với bộ lọc Category chip, nền tảng, tìm kiếm, lưới thẻ kèm nút tạo mới nét đứt.
  9. `tool/dashboard/app/[locale]/templates/[id]/page.tsx`: Trình đổ dữ liệu slot, chọn giọng OmniVoice `VoiceSelectorWithClone`, kịch bản, xem trước với lớp overlay Safe Zone động theo từng nền tảng, nút xem nhanh 540p, chọn nhiều nền tảng và kích hoạt render.
  10. `tool/dashboard/app/[locale]/renders/page.tsx`: Hàng đợi quản lý tiến trình render trực quan theo thời gian thực.
- **Kiểm thử:**
  - `npx tsc --noEmit | grep -E "templates|renders|lib/api/video|store/modules/video"`: 0 lỗi.
  - Render thật `tiktok-sales-v1` đa nền tảng (TikTok + YouTube) thành công qua hàng đợi.
  - Chụp ảnh màn hình lưu trữ:
    - `data/projects/soc-nho-tv/shots/A3_templates_gallery.png`
    - `data/projects/soc-nho-tv/shots/A3_template_detail.png`
    - `data/projects/soc-nho-tv/shots/A3_renders_queue.png`
    - `data/projects/soc-nho-tv/shots/A3_mobile_375px.png` (scrollWidth = 375px, không tràn ngang).
