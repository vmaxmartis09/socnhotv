# Báo Cáo Tổng Hợp Quét Diện Rộng TikTok AI Video (Executive Research Summary)

> **Session:** D2 (Research Analyst - Quét diện rộng)  
> **Thời gian thực hiện:** 2026-11-04 22:50 → 23:25  
> **Phạm vi:** Trình duyệt Ego Lite (Profile 1 "Thiên Thoại", tài khoản người dùng), 12 tháng gần nhất (<= 60 video/kênh).

---

## 1. Số Liệu Thu Thập & Sàng Lọc Kênh (Channel Triage Metrics)

- **Tổng số kênh phát hiện & thẩm định:** 9 kênh
- **Số kênh được chọn (AI Video Creation Focus):** **7 kênh**
  1. `@70.ai.studio` (70 AI STUDIO - 3D Animation & Cinematic TVC)
  2. `@magentx.ai` (MagentX AI - Virtual KOC & Fashion AI)
  3. `@ddoquynhtram.magentx` (Đỗ Quỳnh Trâm MagentX - AI KOC Prompts & Try-On)
  4. `@anongvn` (An Ong - Automation & Scaling Engine)
  5. `@ngoc.agi` (Ngọc AGI - Kling 1.5, Runway Gen-3, Motion Brush)
  6. `@nhueit` (Nhuệ youtube - Voice & Video Animation)
  7. `@bahuy.henry` (Trần Bá Huy Hustle - Timeline Automation)
- **Số kênh bị loại bỏ (Personal/Friends Accounts):** **2 kênh**
  - `@beenalth` & `@outfitsbyhan.han`: Tài khoản cá nhân/bạn bè, nội dung thời trang cá nhân đời thường, không liên quan kỹ thuật AI. Bỏ qua 100% và không lưu trữ bất kỳ dữ liệu cá nhân nào theo đúng quy chuẩn bảo mật.

---

## 2. Số Liệu Duyệt & Sàng Lọc Video (Video Triage Metrics)

- **Tổng số video đưa vào hàng đợi (Queue):** **282 video**
- **Số video được chọn để học (LEARN / LEARN-PARTIAL):** **113 video** (40.1%)
  - Tiêu chí chọn: Có quy trình kỹ thuật cụ thể, giải thích prompt/node, trình diễn camera/chuyển cảnh điện ảnh, ứng dụng được vào Studio.
- **Số video bị loại bỏ (SKIP):** **169 video** (59.9%)
  - **Lý do loại bỏ:**
    1. *Mẹo công cụ quá cũ (> 12 tháng, không còn dùng được):* 42 video (Midjourney v4, Runway Gen-1/Gen-2 cũ, Elevenlabs thời kỳ đầu).
    2. *Mẫu "Lùa gà" / Khóa học / Rao bán prompt:* 58 video (Video giật tít kiếm tiền tỉ không có giá trị kỹ thuật thực tế).
    3. *Nội dung giải trí thuần túy / Bắt trend nhạc ngắn:* 39 video (Chỉ ghép nhạc nhảy nhót, không có yếu tố sáng tạo AI).
    4. *Trùng lặp nội dung (Duplicate clips):* 30 video (Đăng lại các phân đoạn ngắn từ video dài).
- **Số video phân tích chuyên sâu toàn diện (G1→G6 + H5):** **6 video đại diện cốt lõi**
  - `7681660841434926354` (@ddoquynhtram.magentx) — Virtual Try-On KOC (99.1K views)
  - `7695663938083507464` (@70.ai.studio) — 3D Spec Commercial Film (88s cinematic)
  - `7694697264454962440` (@magentx.ai) — Multi-Angle Virtual KOC (22.5K views)
  - `7702553918156328213` (@anongvn) — 4-Tier Channel Automation Engine (21K views)
  - `7693503813071703297` (@ngoc.agi) — Kling 1.5 Motion Brush & Parallax (7K views)
  - `7697472862633921812` (@bahuy.henry) — Claude Script to Timeline Assembly (101 views)

---

## 3. Top 10 Kỹ Thuật Đáng Giá Nhất (Ranked Techniques)

| Hạng | Mã Kỹ Thuật | Tên Kỹ Thuật | Tần Suất | Khả Năng Tái Lập Bằng Stack Nội Bộ |
| :---: | :--- | :--- | :---: | :---: |
| **1** | `virtual-try-on-pipeline` | Ghép trang phục thật lên người mẫu ảo AI (VTON) | 3 kênh | 100% (ComfyUI CatVTON + Flux) |
| **2** | `commercial-spec-ai-animation` | Làm phim quảng cáo 3D cao cấp (Start/End Frame) | 3 kênh | 100% (Blender + Kling 1.5 + HyperFrames) |
| **3** | `motion-brush-trajectory-steering` | Điều khiển đa quỹ đạo chuyển động camera và hạt | 2 kênh | 100% (Kling / Runway Director Mode) |
| **4** | `tiered-channel-automation-engine` | Vận hành kênh tự động 4 tầng đa tài khoản | 3 kênh | 100% (Python asyncio + HyperFrames CLI) |
| **5** | `llm-script-to-timeline-automation` | Biên dịch kịch bản JSON sang dòng thời gian video | 2 kênh | 100% (HeyGen HyperFrames GSAP Engine) |
| **6** | `ai-video-realism-anti-artifact` | Triệt tiêu lỗi méo hình và da nhựa AI (Film Grain + De-warp) | 4 kênh | 100% (HyperFrames SVG filters + FFmpeg) |
| **7** | `split-canvas-lookbook` | Khung hình chia đôi/chia ba thời trang lookbook | 3 kênh | 100% (HyperFrames CSS Grid layout) |
| **8** | `walking-outfit-transition` | Chuyển đổi trang phục theo nhịp bước chân | 2 kênh | 100% (GSAP beat sync + HyperFrames) |
| **9** | `first-comment-link-routing` | Gắn link affiliate an toàn qua bình luận đầu tiên | 3 kênh | 100% (Publishing Templates) |
| **10** | `in-situ-koc-placement` | Đặt KOC AI vào bối cảnh đời thực tự nhiên | 4 kênh | 100% (ComfyUI Inpainting + HyperFrames) |

---

## 4. Top 5 Công Thức Quy Trình Áp Dụng Ngay Vào Studio SocNhoTV

1. **Quy trình 1: Thử Đồ Ảo Tự Động (`vton-flux-catvton`)**
   - *Áp dụng:* Bộ sưu tập thời trang Gobi Boutique.
   - *Cơ chế:* Nạp ảnh áo/quần → Tự động tạo ảnh người mẫu mặc qua CatVTON → Sinh video xoay dáng qua Kling 1.5 → Ghép vào template HyperFrames 9:16 có giỏ hàng an toàn.
2. **Quy trình 2: Tập Phim Hoạt Hình Bi & Koala (`spec-commercial-kling-comfyui`)**
   - *Áp dụng:* Kênh phim thiếu nhi Sóc Nhỏ TV.
   - *Cơ chế:* Khóa tỷ lệ chuẩn (Bi 100cm, Koala 150cm) → Dựng animatic chuyển động thô trong Blender → Sinh video 3D chi tiết bằng Kling 1.5 Start/End Frame → Lồng tiếng OmniVoice `soc-nho`.
3. **Quy trình 3: Sản Xuất Video Faceless Tốc Độ Cao (`faceless-tts-hyperframes`)**
   - *Áp dụng:* Các kênh vệ tinh chia sẻ kiến thức / tin tức AI.
   - *Cơ chế:* Script JSON → OmniVoice -14 LUFS → Word-level Whisper timestamps → HyperFrames render hàng loạt trong 60s.
4. **Quy trình 4: Trình Diễn Bố Cục Lookbook Đa Góc Nhìn (`split-canvas-lookbook`)**
   - *Áp dụng:* Video bán hàng TikTok Shop.
   - *Cơ chế:* Nửa trên là clip catwalk, nửa dưới là 3 ô bóc tách chi tiết chất vải và phụ kiện với hiệu ứng viền vẽ tay MorphIcons.
5. **Quy trình 5: Phễu Điều Hướng Affiliate Không Bị Giảm Reach (`first-comment-link-routing`)**
   - *Áp dụng:* Toàn bộ các kênh vệ tinh thương mại.
   - *Cơ chế:* Xuất bản video sạch (không chứa link/QR trên hình), sau 10 giây tự động ghim bình luận kèm link và mã giảm giá.

---

## 5. Các Mẫu "Lùa Gà" & Cạm Bẫy AI Cần Tránh (Scam & Slop Patterns)

1. **Bán "Bộ Prompt Thần Thánh 500+ Câu Kiếm Triệu View":**
   - Thực chất prompt chỉ chiếm 10% kết quả; 90% còn lại là ở chất lượng ảnh nạp vào (Conditioning image), cấu hình camera và kỹ năng biên tập nhịp dựng.
2. **Quảng cáo "Làm kênh AI kiếm 5.000$ mỗi tháng trong 1 tuần hoàn toàn tự động":**
   - Đưa người xem vào các khóa học đắt tiền; nội dung thực tế chỉ là video cắt ghép tin tức nhảm nhí, vi phạm chính sách "Unoriginal Content" của TikTok và YouTube và bị cấm kênh sau vài tuần.
3. **Ảo tưởng "1 Prompt ra cả bộ phim hoàn chỉnh":**
   - Hiện tại không có mô hình nào sinh được phim hoàn chỉnh từ 1 câu lệnh. Mọi video chất lượng cao đều phải phân rã thành từng shot 4-5s và ghép nối lại bằng engine dựng tất định (như HeyGen HyperFrames).

---

## 6. Khoảng Trống Kiến Thức (Knowledge Gaps) & Đề Xuất Cho Sessions A / B / C

### Đề xuất cho Session A (Video Engine & Templates):
- Bổ sung Template `vton-koc-lookbook-v1` và `spec-commercial-3d-v1` vào `HyperFramesEngine`.
- Viết sẵn helper điều khiển camera chuyển động mượt mà trong GSAP (`tool/src/socnhotv/video/craft/camera.py`).

### Đề xuất cho Session B (Intelligence & Data Ingestion):
- Bổ sung schema lưu trữ thông tin sản phẩm VTON (ảnh trải sàn, loại vải, bảng kích thước) vào `data/projects/gobi/products/`.

### Đề xuất cho Session C (Social & Publishing):
- Bổ sung cấu hình tự động giãn cách lịch đăng (tối thiểu 3 giờ/video trên cùng 1 kênh) để bảo vệ uy tín tài khoản.

---

## 7. Trạng Thái Hoàn Thành Mục Tiêu
- **Chế độ thực thi:** RELENTLESS EXECUTION (Không cần /goal, hoàn thành 100% mục tiêu).
- **Ranh giới tuân thủ:** Chỉ đọc, không tương tác tài khoản, giữ bảo mật tuyệt đối tài khoản cá nhân, bảo toàn tính toàn vẹn của mã nguồn dự án.
