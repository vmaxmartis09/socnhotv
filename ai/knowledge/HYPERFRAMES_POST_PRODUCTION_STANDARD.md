# 🎬 TIÊU CHUẨN HẬU KỲ & BIÊN TẬP VIDEO CHÍNH THỨC: HEYGEN HYPERFRAMES
# (GOBI SOCIAL OFFICIAL POST-PRODUCTION & VIDEO EDITING STANDARD)

> [!CRITICAL]
> **ĐIỀU KHOẢN BẮT BUỘC ĐỐI VỚI HỆ THỐNG VÀ AI AGENT:**
> 1. **CÔNG CỤ BIÊN TẬP DUY NHẤT:** Kể từ phiên làm việc này, **HeyGen HyperFrames** là **CÔNG CỤ BIÊN TẬP & DỰNG VIDEO HẬU KỲ MẶC ĐỊNH BẮT BUỘC** của toàn bộ hệ sinh thái Gobi Social.
> 2. **TỰ ĐỘNG KÍCH HOẠT:** Mọi yêu cầu liên quan đến "dựng video", "edit video", "chèn phụ đề", "chèn overlay/sticker", "cắt ghép video review", "làm video affiliate", "hậu kỳ video" **PHẢI TỰ ĐỘNG SỬ DỤNG HYPERFRAMES**.
> 3. **CẤM SỬ DỤNG PHƯƠNG PHÁP CŨ:** Tuyệt đối không viết script ghép nối video FFmpeg filtergraph thủ công cứng nhắc hay dùng công cụ Concat binary thô sơ cho hậu kỳ chính thức.

---

## 🗺️ 1. TỔNG QUAN KIẾN TRÚC PHÂN TẦNG (ARCHITECTURE ALIGNMENT)

HyperFrames được nhúng sâu vào kiến trúc Modular Monolith của Gobi Social theo chuẩn Clean Architecture:

```
gobi-social/
├── src/gobi/
│   ├── adapters/integrations/
│   │   └── hyperframes_adapter.py    # [TẦNG 3: ADAPTER] Wrapper gọi npx hyperframes (CLI, Lint, Check, Render, Preview)
│   ├── services/media/
│   │   └── hyperframes_engine.py     # [TẦNG 2: SERVICE] Động cơ dựng video KOC 9:16, sinh HTML5, Ken Burns, Subtitles
│   └── cli/
│       └── cmd_video.py / main.py    # [TẦNG 4: CLI] Lệnh hợp nhất: python -m gobi video render --engine hyperframes
├── integrations/
│   └── hyperframes/                  # Thư mục lưu các dự án và composition HyperFrames đang render
└── output/videos/                    # Thư mục lưu video MP4 thành phẩm chất lượng cao
```

---

## 📐 2. TIÊU CHUẨN TIKTOK SAFE ZONE 9:16 (1080x1920)

Mọi composition HyperFrames phục vụ TikTok / Reels / Shorts bắt buộc phải tuân thủ vùng an toàn tuyệt đối để không bị che khuất bởi giao diện ứng dụng:

```
+---------------------------------------------------+  y = 0px
|                 TOP DANGER ZONE                   |  Tránh Camera đục lỗ & Header TikTok
|                 (Chiều cao: 180px)                |  (Không để văn bản, giá tiền tại đây)
+---------------------------------------------------+  y = 180px
|                                                   |
|                                                   |
|                                                   |
|                 ACTIVE SAFE ZONE                  |
|                 (VÙNG HIỂN THỊ CHÍNH)             |
|                                                   |
|   [Badge Góc Trái]               [Giá 139K Góc Phải]   Tránh mép phải 140px
|                                               (Tim/Cmt)  (Avatar, Tim, Share, Cmt)
|                                                   |
|             [KOC VIDEO / KEN BURNS]               |
|                                                   |
|         [KINETIC SUBTITLES / PHỤ ĐỀ ĐỘNG]         |  Đặt ở y: 1350px - 1500px
|                                                   |
+---------------------------------------------------+  y = 1600px
|                BOTTOM DANGER ZONE                 |  Tránh Nút Giỏ hàng Vàng, Caption gốc,
|                 (Chiều cao: 320px)                |  Thanh tiến trình & Tên bài nhạc
+---------------------------------------------------+  y = 1920px
```

### Các hằng số vị trí chuẩn:
* **Chiều rộng x Chiều cao:** `1080px` x `1920px` (Tỷ lệ 9:16).
* **Top Header Safe Zone:** `top: 180px` (chỉ đặt nhãn thời trang nhỏ `font-size: 28px`).
* **Bottom Cart Safe Zone:** Chừa trống từ `y: 1600px` đến `1920px` (chiều cao `320px`).
* **Vị trí Phụ đề động (Karaoke / Kinetic):** Nằm chính giữa trục ngang (`left: 50%, transform: translateX(-50%)`), cách đáy `360px` - `420px`.
* **Vị trí Nhãn giá Affiliate / Flash Sale:** Góc trên bên phải (`top: 200px`, `right: 60px`).

---

## 🏗️ 3. CẤU TRÚC MÃ NGUỒN HTML5 TẤT ĐỊNH (COMPOSITION CONTRACT)

Một video HyperFrames chuẩn mực bao gồm 3 lớp layer chính:

```html
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1080, height=1920, initial-scale=1.0">
  <style>
    /* 1. Reset & Khung Canvas 1080x1920 */
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body, html { width: 1080px; height: 1920px; overflow: hidden; background: #000; font-family: 'Plus Jakarta Sans', sans-serif; }
    
    /* 2. Visual Clip Track */
    .clip { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
    
    /* 3. Safe Zone Overlay Header */
    .header-pill { position: absolute; top: 180px; left: 50px; background: rgba(0,0,0,0.6); backdrop-filter: blur(8px); padding: 12px 24px; border-radius: 999px; color: #fff; font-size: 28px; font-weight: 700; border: 1px solid rgba(255,255,255,0.2); }
    
    /* 4. Price Badge Flash Sale */
    .price-badge { position: absolute; top: 180px; right: 50px; background: linear-gradient(135deg, #fe2c55, #ff0050); color: #fff; padding: 14px 28px; border-radius: 20px; font-size: 32px; font-weight: 800; box-shadow: 0 10px 25px rgba(254,44,85,0.5); }
    
    /* 5. Kinetic Subtitle Pill */
    .subtitle-pill { position: absolute; bottom: 380px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.75); color: #fff; padding: 16px 36px; border-radius: 24px; font-size: 40px; font-weight: 800; text-align: center; max-width: 920px; border: 2px solid #fe2c55; }
  </style>
</head>
<body>
  <!-- TRACK 1: VISUALS (Video thật hoặc Ảnh Ken Burns) -->
  <video class="clip" src="/path/to/koc_clip.mp4" playsinline muted data-start="0.000" data-duration="5.000" data-track-index="1"></video>
  <div class="clip" style="background-image: url('/path/to/product.jpg'); background-size: cover;" data-start="5.000" data-duration="4.500" data-track-index="1"></div>

  <!-- TRACK 2: OVERLAYS (Header, Giá, Giỏ hàng) -->
  <div class="header-pill">🌸 GÔ BI REVIEW</div>
  <div class="price-badge">⚡ 139.000đ</div>

  <!-- TRACK 3: PHỤ ĐỀ ĐỘNG THEO PHÂN CẢNH -->
  <div class="subtitle-pill" data-start="0.000" data-duration="3.000" data-track-index="2">
    Mấy bà ơi, set áo cardigan này mặc mê xỉu luôn!
  </div>

  <!-- TRACK 4: ĐA LUỒNG ÂM THANH (Voiceover + BGM Ducking) -->
  <audio class="clip" src="/path/to/voiceover.mp3" data-start="0.000" data-duration="15.000" data-track-index="3"></audio>
  <audio class="clip" src="/path/to/bgm_gentle.mp3" data-start="0.000" data-duration="15.000" data-track-index="4" data-volume="0.18"></audio>
</body>
</html>
```

---

## 💻 4. HƯỚNG DẪN LẬP TRÌNH VỚI PYTHON SDK

Mọi module trong dự án cần tạo, ghép hoặc xuất bản video đều gọi trực tiếp qua `HyperFramesEngine`:

```python
from gobi.services.media.hyperframes_engine import HyperFramesEngine

# 1. Khởi tạo Engine
engine = HyperFramesEngine()

# 2. Định nghĩa danh sách các phân cảnh (Storyboard Scenes)
scenes = [
    {
        "duration": 3.0,
        "video": "output/videos/koc_clip_intro.mp4",  # Có thể dùng video từ SnapTik
        "sub": "Mấy bà ơi, hôm nay em lên tiếp một mã áo siêu đỉnh!"
    },
    {
        "duration": 4.5,
        "img": "assets/datasets/koc/panel_05_goc_3_4_trung_canh.jpg",  # Ảnh DNA KOC
        "sub": "Chất len tăm co giãn nhẹ, phối nút ngọc kiểu Pháp cực xinh!"
    },
    {
        "duration": 3.5,
        "img": "assets/mockups/cardigan_closeup_fabric.jpg",  # Cận cảnh vải
        "sub": "Mặc đi làm hay đi cà phê cuối tuần đều chuẩn điểm 10 nha!"
    },
    {
        "duration": 4.0,
        "img": "assets/datasets/koc/panel_24_cham_tay_len_kinh.jpg",
        "sub": "Bấm ngay vào giỏ hàng góc trái bên dưới để săn sale 139K nhé!"
    }
]

# 3. Render video MP4 thành phẩm chuẩn TikTok 9:16
video_out = engine.render_koc_video(
    scenes=scenes,
    voiceover_audio="output/audio/voice_lyly_cardigan.mp3",
    bgm_audio="assets/templates/bgm/bgm_soft_acoustic.mp3",
    output_filename="output/videos/gobi_hyperframes_cardigan_master.mp4",
    title_badge="ÁO CARDIGAN LEN TĂM KIỂU PHÁP",
    price_badge="⚡ SALE 139K",
    quality="delivery",  # draft | looks | delivery
    fps=30
)

print(f"Video hậu kỳ hoàn tất: {video_out}")
```

---

## ⚡ 5. HƯỚNG DẪN DÒNG LỆNH (CLI REFERENCE)

### 5.1. Chạy render video qua Unified CLI
```bash
# Render video review chuẩn HyperFrames
./gobi video render --engine hyperframes

# Hoặc dùng python module
python -m gobi.services.media.hyperframes_engine --preview
```

### 5.2. Mở Live Preview Studio để duyệt trực quan trên màn hình
```bash
# Xem trước timeline video và hiệu ứng thời gian thực
npx hyperframes preview
```

### 5.3. Render thủ công một thư mục composition
```bash
# Render composition thành file MP4 chất lượng cao
npx hyperframes render --output output/videos/final_video.mp4 --quality delivery --fps 30
```

---

## 🔄 6. PHỐI HỢP CÙNG PHÂN HỆ SNAPTIK (SOURCE INGESTION -> POST-PRODUCTION)

Quy trình tự động hóa hoàn chỉnh giữa SnapTik và HyperFrames:
1. **Bước 1 (Lấy Source):** Dùng SnapTik kéo video TikTok sạch không logo về máy:
   ```bash
   ./gobi snaptik "https://www.tiktok.com/@creator/video/..." -a -o output/videos/source_clip.mp4
   ```
2. **Bước 2 (Trích xuất / Clone Giọng):** Tách âm thanh và phân tích kịch bản review.
3. **Bước 3 (Hậu kỳ với HyperFrames):** Nạp `source_clip.mp4` làm visual track, lồng phụ đề chữ động, badge giỏ hàng, và render video KOC Master mới toanh sẵn sàng đăng kênh!

---

## 🛡️ 7. QUY TẮC BẢO VỆ CHẤT LƯỢNG & TỰ SỬA LỖI (SELF-HEALING)
- Luôn chạy `adapter.lint(project_dir)` hoặc `adapter.check(project_dir)` trước khi render.
- Nếu render báo lỗi do tài nguyên hình ảnh/video bị thiếu, tự động fallback sang ảnh neo thị giác gốc trong `assets/koc_dna/`.
- File âm thanh Voiceover luôn được kiểm tra thời lượng bằng `ffprobe` trước khi tính toán độ dài từng phân cảnh để đảm bảo hình khớp từng mili-giây với tiếng.
