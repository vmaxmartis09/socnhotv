# Session B — Sources & Intelligence

**Trạng thái:** HOÀN THÀNH 100% TOÀN BỘ CÁC BƯỚC B1 → B4

| Hạng mục | Trạng thái | Độ hoàn thiện | Test Case | Ghi chú |
|---|---|:---:|:---:|---|
| **B1 — Nạp nguồn nội dung** | Hoàn thành | 100% | 7/7 passed | yt-dlp, local upload, scenedetect, rights guard |
| **B2 — Bản địa hoá Douyin/TikTok** | Hoàn thành | 100% | 6/6 passed | ASR, translate, rewrite, revoice -14 LUFS, Mode R/L |
| **B3 — Blueprint, Sản phẩm & KOC** | Hoàn thành | 100% | 6/6 passed | Blueprint beats, compliance filter, 3 script generators |
| **B4 — Học kênh đối thủ & Ý tưởng** | Hoàn thành | 100% | 4/4 passed | Channel scraper, strategy, rapidfuzz < 70, 30 ideas Kanban |
| **Tích hợp E2E Pipeline** | Hoàn thành | 100% | 1/1 passed | Link -> Source -> Blueprint -> KOC Script -> RenderRequest -> Idea scripted |
| **Tổng cộng Session B** | **HOÀN TẤT** | **100%** | **24/24 passed** | Sẵn sàng bàn giao cho Session C & Final Integration |

---

## Chi tiết các giai đoạn thực hiện

### B1 — Nạp nguồn nội dung
- **Tập tin đã tạo:**
  - `tool/src/socnhotv/sources/models.py`: Model `SourceItem`, `IngestRequest`, `UpdateRightsRequest`, `SceneCut`, `SourceStats`. Quyền mặc định `reference_only`.
  - `tool/src/socnhotv/sources/downloader.py`: `yt-dlp` API, MP4 <=1080p, tách WAV 16kHz mono, VTT subtitles, rate limit 2s/platform, backoff retry.
  - `tool/src/socnhotv/sources/local.py`: Nhập video local mp4/mov (mặc định `owned`), ffprobe duration, sinh thumbnail + audio wav.
  - `tool/src/socnhotv/sources/scenes.py`: Tách cảnh với `scenedetect` ContentDetector (27.0) và ffmpeg fallback, sinh thumbnail từng cảnh và `scenes.json`.
  - `tool/src/socnhotv/sources/jobs.py`: Asyncio queue tải tối đa 3 tiến trình song song, tracking tiến trình, ghi sự kiện `runs/events/sources.jsonl`.
  - `tool/src/socnhotv/sources/service.py`: CRUD nguồn, chuyển rác `raw/_trash/`, khóa `confirm_rights`.
  - `tool/src/socnhotv/core/api/routes/sources.py`: REST API `/projects/{pid}/sources`.
  - `tool/src/socnhotv/core/nodes/plugins/sources.py`: Đăng ký node `source_video`.
  - Frontend: `lib/api/sources.ts`, `components/sources/{SourceCard,SourceDetailModal,AddSourcesModal,SourcesList}.tsx`, `app/[locale]/sources/page.tsx`.

### B2 — Bản địa hoá video Douyin/TikTok -> Việt
- **Tập tin đã tạo:**
  - `tool/src/socnhotv/sources/asr.py`: Bóc tách thoại bằng `faster-whisper` (word timestamps, CPU int8) kết hợp ưu tiên VTT gốc.
  - `tool/src/socnhotv/sources/translate.py`: Dịch câu ZH -> VI kèm nạp bảng thuật ngữ `knowledge/glossary.json`, giới hạn 15 ký tự/giây (ngưỡng trần 1.25x), tự rút gọn câu khi quá dài.
  - `tool/src/socnhotv/sources/rewrite.py`: Viết lại kịch bản theo 3 phong cách (`faithful`, `hook_boost`, `character` Sóc Nhỏ Bi / KOC).
  - `tool/src/socnhotv/sources/revoice.py`: Tổng hợp giọng đọc TTS (Edge-TTS / OmniVoice), canh khớp thời lượng và đi qua chuỗi TikTok Mastering chuẩn -14 LUFS (EBU R128).
  - `tool/src/socnhotv/sources/localize_pipeline.py`: Pipeline liên hoàn ASR -> Dịch -> Viết lại -> Revoice -> gửi `RenderRequest` qua hợp đồng `submit_render`.
  - Khóa bản quyền: Mode L (giữ video gốc) chặn HTTP 400 nếu nguồn là `reference_only`. Mode R (dựng lại bằng media riêng) được phép chạy với `source_ref`.
  - Frontend: `LocalizeStudio.tsx` (giao diện 3 cột xem video, kịch bản inline, bộ điều khiển Mode R/L, giọng đọc).

### B3 — Phân tích video mẫu → Blueprint · Sản phẩm · Kịch bản KOC review & Affiliate
- **Tập tin đã tạo:**
  - `tool/src/socnhotv/intelligence/products.py`: Mô hình `Product`, CRUD lưu `products/<id>/product.json`, parser OpenGraph import nhanh metadata từ URL không cần login.
  - `tool/src/socnhotv/intelligence/compliance.py`: Bộ lọc tuân thủ chính sách quảng cáo. Chặn cam kết chữa bệnh, cam kết 100%, tự chèn nhãn tiếp thị `#affiliate #quangcao`.
  - `tool/src/socnhotv/intelligence/analyzer.py`: Phân tích video thành `VideoBlueprint` chuẩn (role: `hook, problem, agitate, reveal, demo, proof, compare, offer, urgency, cta`), tính nhịp pacing (cuts/10s), so khớp template bằng rapidfuzz.
  - `tool/src/socnhotv/intelligence/patterns.py`: Tổng hợp công thức viral (thời lượng hook trung vị, chuỗi role phổ biến, mẫu hook/CTA).
  - `tool/src/socnhotv/intelligence/script_gen.py`: 3 generator (`koc_review`, `tiktok_sales`, `affiliate_compare`), lưu `content/scripts/`, tạo `ContentIdea` (status `scripted`), và đóng gói `RenderRequest`.
  - `tool/src/socnhotv/core/api/routes/intel.py`: Cụm REST API products, blueprint, patterns, generate-script.
  - `tool/src/socnhotv/core/nodes/plugins/sources.py`: Đăng ký node `blueprint_analyze` và `script_from_blueprint`.
  - Frontend: `lib/api/intel.ts`, `components/products/*`, `app/[locale]/products/page.tsx` (lưới sản phẩm, thẻ nét đứt thêm mới), `components/intel/{BlueprintView,ScriptWizardModal}.tsx`, nút "Phân tích cấu trúc" trong `SourceDetailModal.tsx`.

### B4 — Học kênh đối thủ → Channel Blueprint → Chiến lược & Bảng ý tưởng
- **Tập tin đã tạo:**
  - `tool/src/socnhotv/intelligence/channel_ingest.py`: `yt_dlp` `extract_flat` bóc tách metadata N video kênh (mặc định 50, tối đa 200), tính `views_per_day`, tải đầy đủ top 5 outlier vào B1 `reference_only`, lưu `knowledge/channels/<id>/{channel.json, videos.jsonl}`.
  - `tool/src/socnhotv/intelligence/channel_analyze.py`: Thống kê median views, phân phối shorts/longs, heatmap lịch đăng (7 ngày x 24 giờ), tính outlier score = views / median, gom nhóm 3-7 content pillars, trừu tượng hoá mẫu tiêu đề.
  - `tool/src/socnhotv/intelligence/strategy.py`: Chiến lược độc quyền cho dự án, xác lập định vị, 4 pillars (`pillar_animation_life`, `pillar_science_fun`, `pillar_koc_review`, `pillar_affiliate_hacks`), quy tắc tiêu đề, thumbnail, lịch đăng đề xuất, format mix (20% Long 3D, 40% Shorts, 40% KOC Sales), KPIs 30 ngày. Hàng rào bản quyền: kiểm tra rapidfuzz ratio < 70% so với mọi tiêu đề nguồn.
  - `tool/src/socnhotv/intelligence/ideas.py`: Sinh 30 `ContentIdea` tự động vượt qua guardrail < 70%, ánh xạ template phù hợp, hỗ trợ `promote_idea` (sinh script + render request) và `schedule_idea_to_social` (nối Session C).
  - `tool/src/socnhotv/core/nodes/plugins/sources.py`: Đăng ký node `channel_insight`.
  - Frontend:
    - `components/intel/ChannelDetailView.tsx`: Biểu đồ SVG lượt xem top outliers, heatmap lịch đăng, thanh tỉ trọng pillars, bảng top outliers.
    - `components/intel/StrategyView.tsx`: Định vị độc quyền, 4 pillars, quy tắc tiêu đề/thumbnail, format mix, 30-day KPIs.
    - `components/intel/IdeaBoard.tsx`: Bảng Kanban kéo-thả `@dnd-kit` 4 cột (`new` -> `scripted` -> `rendered` -> `scheduled`), nút viết kịch bản và lên lịch đăng.
    - `components/intel/AddChannelModal.tsx`: Hộp thoại nạp link kênh đối thủ.
    - `app/[locale]/intel/page.tsx`: Điều hướng tab tích hợp 4 phân hệ (Blueprints, Channels, Strategy, Ideas).

---

## Lệnh mẫu vận hành (CLI & API)

```bash
# 1. Chạy toàn bộ 24 test case của Session B
cd tool && .venv/bin/python -m pytest tests/test_sources_*.py tests/test_intel_*.py -v

# 2. Nạp kênh đối thủ qua API
curl -X POST http://localhost:8000/projects/soc-nho-tv/intel/channels \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/@competitor", "max_videos": 50}'

# 3. Tạo chiến lược kênh
curl -X POST http://localhost:8000/projects/soc-nho-tv/intel/strategy \
  -H "Content-Type: application/json" \
  -d '{"channel_ids": ["ch_competitor"]}'

# 4. Sinh 30 ý tưởng nội dung kèm kiểm tra guardrail < 70%
curl -X POST "http://localhost:8000/projects/soc-nho-tv/intel/ideas/generate?count=30"

# 5. Phân tích video nguồn thành Blueprint
curl -X POST http://localhost:8000/projects/soc-nho-tv/intel/analyze/local_2cf1c9fea639

# 6. Sinh kịch bản KOC Review kèm kiểm duyệt quảng cáo
curl -X POST http://localhost:8000/projects/soc-nho-tv/intel/generate-script \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "soc_nho_sunshield",
    "generator_type": "koc_review",
    "character_name": "LyLy",
    "voice_id": "soc-nho",
    "platforms": ["tiktok", "shorts", "reels"]
  }'
```

---

## Giới hạn & Ước tính chi phí vận hành

1. **Cơ chế chống bot Douyin / TikTok:**
   - Khi Douyin yêu cầu xác thực captcha trượt hoặc cookie đăng nhập: Hệ thống thông báo rõ ràng cho người dùng, **tuyệt đối không can thiệp hack captcha trái phép** theo quy định tại `CONTRACTS.md`.
2. **Quy định Bản quyền & Rights Management:**
   - Mọi video nguồn từ web mặc định gán `rights = "reference_only"`.
   - Chế độ **Mode L** (tái sử dụng video gốc) bị khóa cứng (HTTP 400).
   - Chế độ **Mode R** (học khung cấu trúc, viết lại thoại, dựng bằng media nội bộ) được cấp phép đầy đủ kèm liên kết `source_ref`.
3. **Ước tính chi phí LLM / Vision:**
   - **Phân tích Blueprint video (lô <= 12 khung hình):** ~\$0.002 - \$0.005 / video.
   - **Phân tích Kênh đối thủ (extract_flat metadata 50 video + clustering):** ~\$0.001 / kênh.
   - **Sinh kịch bản & Bộ lọc tuân thủ chính sách:** ~\$0.001 / kịch bản.
   - Tổng chi phí trí tuệ nhân tạo ước tính cho 1 chiến dịch 30 video hoàn chỉnh: **dưới \$0.15 USD**.
