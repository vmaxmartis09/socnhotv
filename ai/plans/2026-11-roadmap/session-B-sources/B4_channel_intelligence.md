# B4 — Học kênh YouTube/TikTok đối thủ → Channel Blueprint → Kế hoạch nội dung

Bạn là Session B. Đọc: `CONTRACTS.md`, `status/B.md`, `intelligence/contracts.py` (`ChannelBlueprint`, `ContentIdea`), `intelligence/analyzer.py` + `patterns.py` (B3), skill `research`.

## Mục tiêu
Dán link 1 kênh (YouTube/TikTok/Douyin) → hệ thống hiểu kênh đó thắng nhờ đâu (chủ đề, tiêu đề, thumbnail, độ dài, nhịp đăng, hook) → sinh **blueprint kênh của mình** (khác biệt hoá, không nhái nhận diện) + 30 ý tưởng có thứ tự ưu tiên → đẩy sang lịch đăng (C) qua `ContentIdea`.

## Việc cần làm
1. **`intelligence/channel_ingest.py`**: `yt_dlp` `extract_flat` lấy danh sách video kênh (tối đa N=200 mới nhất, cấu hình), metadata: title, duration, upload_date, view/like/comment, thumbnail url. Không tải video hàng loạt; chỉ tải đầy đủ (qua B1) top 5 theo `views/ngày tuổi`. Lưu `knowledge/channels/<channel_id>/{channel.json, videos.jsonl, thumbs/}`. Chạy lại = cập nhật delta.
2. **`intelligence/channel_analyze.py`**:
   - Thống kê: view trung vị, phân phối độ dài (shorts vs long), lịch đăng (thứ/giờ, tần suất), tốc độ tăng.
   - "Outlier score" = views / median của kênh → top outlier.
   - Cụm chủ đề (pillars): embedding tiêu đề (provider có embedding; không có thì TF-IDF + KMeans của numpy/sklearn nếu có, hoặc LLM gom nhóm) → 3–7 pillars kèm % video và % view.
   - Mẫu tiêu đề: LLM trừu tượng hoá top 30 tiêu đề thành khuôn (`"Tôi đã thử X trong 30 ngày"` → `"Tôi đã thử [hành động] trong [thời gian]"`), độ dài tiêu đề, emoji/số.
   - Thumbnail: vision LLM trên top 20 thumb → yếu tố chung (mặt người/nhân vật, chữ ≤4 từ, màu chủ đạo, biểu cảm).
   - Hook: phân tích blueprint (B3) của top 5 video đã tải đầy đủ.
   - Output `ChannelBlueprint` lưu `content/blueprints/channel_<id>.json`.
3. **`intelligence/strategy.py`** — "Kênh của mình": input = 1..3 ChannelBlueprint đối thủ + project hiện tại (nhân vật, brand kit, niche) → `content/strategy.json`: định vị khác biệt, 3–5 pillars của mình, quy tắc tiêu đề/thumbnail riêng, lịch đăng đề xuất theo nền tảng, mix format (long YT hoạt hình / Shorts / TikTok bán hàng), KPI 30 ngày. Kèm **guardrails**: không dùng tên/logo/nhân vật/giọng của kênh nguồn; không copy tiêu đề nguyên văn (kiểm bằng rapidfuzz ratio < 70 so với mọi tiêu đề nguồn).
4. **`intelligence/ideas.py`**: sinh 30 `ContentIdea` (title, hook, pillar, platform_targets, `template_id` gợi ý từ danh sách template A, `priority` 1–5 theo outlier pattern + độ khớp với nhân vật) → lưu qua contract, status `new`. Hàm `promote_idea(idea_id) -> script` gọi `script_gen` (B3) hoặc pipeline episode của A (chỉ gửi yêu cầu qua API A `POST /projects/{pid}/video/episodes/...` nếu tồn tại; không import nội bộ A).
5. **API** (`routes/intel.py`): `POST /projects/{pid}/intel/channels` (url) → job; `GET …/channels`, `GET …/channels/{cid}` (blueprint + thống kê cho biểu đồ); `POST …/strategy` (body: channel_ids); `GET …/strategy`; `POST …/ideas/generate`; `GET/PATCH …/ideas`; `POST …/ideas/{iid}/promote`.
6. **UI** `app/[locale]/intel/channels/**`, `components/intel/*`:
   - Danh sách kênh đã học (avatar, niche, số video, outlier top).
   - Chi tiết kênh: biểu đồ view theo thời gian (đọc skill `dataviz` trước khi vẽ; không thêm thư viện chart mới nếu chưa có trong package.json — dùng SVG thuần), heatmap lịch đăng, pillars dạng thanh %, bảng top outlier (bấm → mở nguồn trong `/sources/[id]`), mẫu tiêu đề, yếu tố thumbnail.
   - Trang Chiến lược: định vị, pillars, lịch đề xuất, KPI.
   - Bảng ý tưởng (kanban new → scripted → rendered → scheduled): kéo-thả bằng `@dnd-kit`; nút "Lên lịch" chuyển idea sang C (C đọc `content/ideas/`; nếu API C `POST /projects/{pid}/social/ideas/{iid}/schedule` tồn tại thì gọi).
7. **Node plugin**: `channel_insight` (url → blueprint text) để dùng trong canvas.

## Nghiệm thu Session B
- `test_intel_channel.py` (fixture videos.jsonl giả 50 video: median, outlier, lịch đăng, guardrail tiêu đề < 70).
- Chạy thật với 1 kênh YouTube hoạt hình thiếu nhi công khai → blueprint + strategy + 30 ideas hiển thị UI.
- E2E B (`test_sources_e2e.py`, mock): link → source → blueprint → script KOC → `submit_render` được gọi → ContentIdea `scripted`.
- `status/B.md`: % từng mảng, lệnh mẫu, giới hạn (Douyin cookie, chi phí vision/LLM ước tính mỗi video/kênh).
- Commit `feat(B4): channel intelligence, strategy, idea board`.
