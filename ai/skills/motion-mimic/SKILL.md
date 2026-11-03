---
name: motion-mimic
description: Quy trình độc lập cho phép AI KOC Gobi (LyLy, Neau) bắt chước 100% chuyển động, nhép môi, cử chỉ từ một video bất kỳ (TikTok/Reels/Video nạp vào) và dựng xuất bản video 9:16 qua HeyGen HyperFrames.
metadata:
  version: "1.0.0"
  date: "2026-10-20"
  author: "Gobi Social Architecture"
---

# 🎭 Gobi Video Motion Mimic Workflow (Quy Trình AI KOC Bắt Chước Video Nạp Vào)

## 1. Giới thiệu tổng quan
Quy trình **Motion Mimic** là một pipeline độc lập hoàn toàn với luồng e-commerce/affiliate thông thường. Nó cho phép người dùng nạp vào bất kỳ một video nào (video TikTok viral, clip hát cover, clip nhảy, hoặc video người thật ngồi nói), hệ thống sẽ:
1. **Trích xuất chuyển động & khẩu hình** từ video mẫu.
2. **Ép chuyển động đó lên nhân vật AI KOC** (Gobi LyLy, Neau hoặc avatar do bạn chọn).
3. **Dựng và đóng gói video chuẩn TikTok 9:16** bằng HeyGen HyperFrames với các bố cục: Solo toàn màn hình, Split 3 tầng (Meta What's up AI), hoặc Side-by-side (Duet).

---

## 2. Kiến trúc 5 bước thực thi

```
+-------------------------------------------------------------+
| 1. Ingestion: Reference Video (Link TikTok / File MP4)     |
+-------------------------------------------------------------+
                             |
                             v
+-------------------------------------------------------------+
| 2. Character DNA: Avatar KOC (Gobi LyLy / Neau / Custom)    |
+-------------------------------------------------------------+
                             |
                             v
+-------------------------------------------------------------+
| 3. Motion Transfer: Local LivePortrait / Kling Motion Control|
+-------------------------------------------------------------+
                             |
                             v
+-------------------------------------------------------------+
| 4. Audio Processing: Giữ âm thanh gốc / OmniVoice Clone     |
+-------------------------------------------------------------+
                             |
                             v
+-------------------------------------------------------------+
| 5. HeyGen HyperFrames Engine: Render MP4 9:16 Deterministic |
|    (Bố cục: Solo | Split 3 Tầng | Side-by-Side Duet)        |
+-------------------------------------------------------------+
```

---

## 3. Các bố cục hiển thị (HyperFrames Layouts)

1. **`solo` (Mặc định):**
   * Nhân vật AI KOC phủ 100% khung hình dọc 9:16 (1080x1920).
   * Thay thế hoàn toàn người mẫu gốc trong video ban đầu.
   * Thích hợp: Clip nhảy viral, clip hát cover, clip diễn xuất ngắn.

2. **`split_3_tier` (Chuẩn What's up AI):**
   * Chia 3 tầng màn hình đều nhau:
     * **Tầng 1 (Trên cùng):** Slide tiêu đề, bằng chứng số liệu, logo công cụ.
     * **Tầng 2 (Ở giữa):** Nhân vật AI KOC thực hiện động tác/khẩu hình.
     * **Tầng 3 (Dưới cùng):** Video người thật đang điều khiển/nói chuyện.
   * Thích hợp: Video tutorial dạy AI, video so sánh công nghệ, video meta-showcase.

3. **`side_by_side` (Duet / So sánh):**
   * Chia đôi màn hình theo chiều dọc (Trái: Video mẫu gốc | Phải: Nhân vật AI bắt chước).
   * Thích hợp: Video kiểm chứng độ khớp (Proof-of-mimic), video bắt trend duet.

---

## 4. Hướng dẫn sử dụng CLI

### 4.1. Lệnh cơ bản nạp video cho Gobi bắt chước:
```bash
# Nạp 1 video bất kỳ (file nội bộ hoặc link TikTok) để LyLy bắt chước toàn màn hình
python -m gobi mimic --ref "scratch/whatsup_video.mp4" --character gobi_lyly --layout solo
```

### 4.2. Dựng video 3 tầng chuẩn What's up AI:
```bash
python -m gobi mimic \
  --ref "scratch/whatsup_video.mp4" \
  --character gobi_lyly \
  --layout split_3_tier \
  --title "BÍ QUYẾT XÂY KÊNH BẰNG A.I" \
  --out "gobi_tutorial_3tiers.mp4"
```

### 4.3. Dựng video so sánh Song Song (Duet Side-by-Side):
```bash
python -m gobi mimic \
  --ref "scratch/whatsup_video.mp4" \
  --character gobi_neau \
  --layout side_by_side \
  --title "SO SÁNH NGƯỜI THẬT & AI KOC"
```

---

## 5. Sử dụng qua Python API

```python
from gobi.domain.motion_mimic_models import MotionMimicInput, MimicLayoutMode, MotionEngineType, AudioStrategy
from gobi.services.workflows.motion_mimic_workflow import MotionMimicWorkflow

# Khởi tạo input
task = MotionMimicInput(
    reference_video_path_or_url="scratch/whatsup_video.mp4",
    character_avatar_path="gobi_lyly",
    layout_mode=MimicLayoutMode.SPLIT_3_TIER,
    engine_type=MotionEngineType.LOCAL_LIVEPORTRAIT,
    audio_strategy=AudioStrategy.KEEP_ORIGINAL,
    title_badge="GOBI AI MIMIC",
    subtitles_text="KOC AI bắt chước chuyển động 100% tự nhiên!"
)

# Chạy workflow độc lập
workflow = MotionMimicWorkflow()
result = workflow.execute(task)

if result.is_success:
    print(f"Video hoàn tất tại: {result.output_video_path}")
```

---

## 6. Cấu hình & Tùy biến Engine
Toàn bộ thông số lưu tập trung tại:
`configs/workflows/motion_mimic_config.json`
* Có thể thay đổi cổng LivePortrait local, API key Kling AI, đường dẫn avatar nhân vật mà không chạm vào mã nguồn chính.
