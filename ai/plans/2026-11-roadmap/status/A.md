# Session A — Video & Templates

**Trạng thái:** HOÀN TẤT 100% (A1, A2, A3, A4 ĐÃ ĐẠT TOÀN DIỆN MỤC TIÊU ROADMAP)

## Tổng kết tiến độ các phần

| Hạng mục | Trạng thái | Unit / Integration Tests | Ghi chú |
|---|---|---|---|
| **A1 — Video Engine HyperFrames & Render Queue** | 100% | 12/12 passed | 6 Presets, Fallback FFmpeg, -14 LUFS, Background Worker |
| **A2 — Hệ thống 8 Starter Templates** | 100% | 4/4 passed | 8 Templates đầy đủ Jinja2 + CSS + Preview MP4/JPG, Node plugins |
| **A3 — UI Thư viện Mẫu, Trình đổ dữ liệu, Hàng đợi** | 100% | TypeScript 0 lỗi | Gallery, SlotField, Realtime SSE Queue, Safe-zone overlays |
| **A4 — Pipeline Hoạt Hình YouTube & Auto Shorts** | 100% | 5/5 passed | Scale Lock Bi 100cm / Koala 150cm, 3 Shorts tự trích xuất, E2E Draft |

---

## Chi tiết các thành phần đã hoàn thành

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
- **Kiểm thử & Bằng chứng UI:**
  - `npx tsc --noEmit`: 0 lỗi.
  - Chụp ảnh màn hình lưu trữ trong `data/projects/soc-nho-tv/shots/`:
    - `A3_templates_gallery.png`
    - `A3_template_detail.png`
    - `A3_renders_queue.png`
    - `A3_mobile_375px.png` (scrollWidth = 375px, không tràn ngang).

---

### A4 — Pipeline Hoạt hình YouTube Dài Tập + Tự Cắt Shorts + Nghiệm thu E2E
- **Hoàn thành:** 2026-11-04
- **Các thành phần đã triển khai:**
  1. `tool/src/socnhotv/video/episode/planner.py`: Chuyển đổi kịch bản thô thành danh sách phân cảnh `ScenePlan[]`, khóa cứng tỉ lệ nhân vật theo `SCALE_LOCK.md`: **Sóc Nhỏ (Bi) 100cm, Bác sĩ Koala 150cm** (`"Bi the squirrel is two-thirds the height of the koala doctor (100cm vs 150cm), Bi's head reaches the doctor's chest"`), ước tính chi phí và thời lượng.
  2. `tool/src/socnhotv/video/episode/assets.py`: Sinh ảnh keyframe tỉ lệ 16:9 cho từng phân cảnh, lưu cache theo hash prompt/scale lock trong `output/<ep>/scenes/`, hàm `estimate_episode_cost()`.
  3. `tool/src/socnhotv/video/episode/voice.py`: `synthesize_episode_voice()` tổng hợp giọng đọc đa nhân vật (Bi = `soc-nho`, Koala), ghép nối dòng thời gian âm thanh và áp dụng chuỗi TikTok Audio Mastering (-14 LUFS, 192kbps MP3).
  4. `tool/src/socnhotv/video/episode/assemble.py`: `assemble_episode()` đóng gói RenderRequest template `yt-animation-episode-v1` (16:9), tự động sinh mục lục YouTube `chapters.txt` và metadata gợi ý SEO `youtube_meta.json`.
  5. `tool/src/socnhotv/video/episode/shorts.py`: `extract_and_assemble_shorts()` tự động phân tích và trích xuất 3 video Shorts 9:16 (Story clip, Fact/Education, Highlight) đa nền tảng (`shorts`, `tiktok`, `reels`) với cờ `auto_draft: True`.
  6. `tool/src/socnhotv/core/api/routes/video.py`: Bổ sung 3 API endpoints quản lý tập phim:
     - `POST /projects/{pid}/video/episodes/{eid}/plan`: Phân tích kịch bản và ước tính chi phí.
     - `POST /projects/{pid}/video/episodes/{eid}/build`: Thực thi pipeline tạo 1 video YouTube 16:9 + 3 video Shorts 9:16 đưa vào RenderQueue.
     - `GET /projects/{pid}/video/episodes/{eid}/status`: Tra cứu tiến trình và các video thành phẩm.
  7. UI Dashboard:
     - `tool/dashboard/components/renders/EpisodeBuildPanel.tsx`: Giao diện sản xuất tập phim trực quan với bộ soạn thảo kịch bản, bảng phân cảnh sửa được action, duyệt ảnh keyframe, ước tính chi phí, chuyển chế độ mock, và hiển thị kết quả chapters, metadata, các video shorts đã sinh.
     - `tool/dashboard/app/[locale]/renders/episode/[eid]/page.tsx`: Route trang sản xuất tập phim.
     - `tool/dashboard/lib/api/video.ts`: Bổ sung các kiểu dữ liệu và client methods cho episode pipeline.
  8. **Nghiệm thu E2E Session A (`tool/tests/test_video_e2e.py`):**
     - `test_plan_episode_scale_lock`: Passed
     - `test_assets_and_voice_pipeline`: Passed
     - `test_e2e_queue_and_auto_draft`: Passed (Khẳng định 1 video chính + 3 video shorts render hoàn tất và gọi contract `create_draft_post` đúng 4 lần)
     - `test_assemble_and_shorts_generation`: Passed
     - `test_api_video_episodes`: Passed
     - Toàn bộ 21/21 tests trong `tests/test_video_*.py` passed 100%.

---

## Chỉ số Render thực tế & Benchmark

Đã đo đạc và lưu trữ trong file `data/projects/soc-nho-tv/output/_metrics/render_metrics.json`:
- **Tốc độ Render:** 39.25 giây render / 1 phút video thành phẩm (đạt tỷ lệ 1.53x real-time trên phần cứng cục bộ).
- **Chi phí sản xuất ước tính:** ~$0.075 USD / tập phim hoạt hình 5 phân cảnh (ảnh keyframe qua SOTA API, voiceover OmniVoice cục bộ $0, render HyperFrames cục bộ $0).
- **Chuẩn âm thanh TikTok:** Toàn bộ audio thoại đều qua bộ lọc chuẩn -14 LUFS, EQ presence +3.5dB @3.2kHz, compressor 4:1.
- **Vùng an toàn Safe Zone:** 100% tuân thủ kích thước an toàn cho TikTok, Reels, Shorts và YouTube.

---

## Lệnh Chạy Mẫu

1. **Chạy toàn bộ 21 video tests:**
   ```bash
   cd tool && uv run pytest tests/test_video_*.py -v
   ```

2. **Chạy render test CLI độc lập:**
   ```bash
   python -m socnhotv.video.cli render --template tiktok-sales-v1 --data '{"product_name": "Bình Nước Bi", "price_original": "150.000đ", "price_sale": "99.000đ"}' --platforms tiktok,youtube --output test_run
   ```

3. **Lập kế hoạch và sản xuất tập phim hoạt hình qua API:**
   ```bash
   curl -X POST http://localhost:8000/projects/soc-nho-tv/video/episodes/ep_01/plan \
     -H "Content-Type: application/json" \
     -d '{"script": "Cảnh 1: Rừng thông\nBi: Xin chào các bạn nhỏ!\nKoala: Hôm nay chúng mình cùng học bài học mới nhé!", "title": "Bài Học Đánh Răng"}'
   
   curl -X POST http://localhost:8000/projects/soc-nho-tv/video/episodes/ep_01/build \
     -H "Content-Type: application/json" \
     -d '{"use_mock": true}'
   ```

---

## Đề xuất cho 99_FINAL_INTEGRATION

1. **Nối nút "Sản Xuất Video" từ `EpisodeDetail.tsx` (trang quản lý tập phim):**
   Thêm nút hành động điều hướng từ trang chi tiết Episode sang `/renders/episode/[eid]` để người dùng bấm một click là sang ngay màn hình sản xuất video A4.
2. **Kích hoạt tự động lên lịch đăng từ Session C:**
   Khi 3 video Shorts được sinh ra và gọi `create_draft_post`, Session C (Publishing) có thể tự động gán vào các slot đăng bài tối ưu của kênh TikTok / Shorts theo chiến lược đăng tải.
