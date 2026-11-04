# Quy Trình Thử Trang Phục Ảo & Video KOC Thời Trang (VTON Flux-CatVTON Pipeline)

- **Slug:** `vton-flux-catvton`
- **Trạng thái tái tạo trong Studio:** `đã thử tái tạo` (qua ComfyUI node + Kling 1.5 + HyperFrames template)
- **Tần suất xuất hiện:** Xuất hiện ở 3 kênh độc lập (@ddoquynhtram.magentx, @magentx.ai, @70.ai.studio)
- **Độ tin cậy:** Cao (Có bằng chứng video thực tế đạt 99.1K views và 22.5K views)

---

## 1. Đầu vào (Inputs)
1. **Ảnh trang phục gốc (Garment Asset):**
   - Định dạng: PNG/JPG 2K (tối thiểu 1024x1536).
   - Nền: Trải phẳng trên nền trắng/trung tính hoặc mannequin không đầu.
   - Yêu cầu: Đầy đủ chi tiết cúc áo, cổ áo, đường may, hoa văn sắc nét.
2. **Master DNA Người Mẫu KOC (Character Canvas):**
   - Mẫu nữ Gobi / Sóc Nhỏ (Bi) trong tư thế chuẩn (A-pose hoặc relaxed standing pose).
   - Bối cảnh: Studio tối giản hoặc bối cảnh đời thực (indoor living room / boutique).
3. **Audio Voiceover & BGM:**
   - File âm thanh giọng đọc tiếng Việt OmniVoice SOTA (`soc-nho`).
   - Nhạc nền thời trang lofi hoặc upbeat nhẹ (-14 LUFS, ducking tự động).

---

## 2. Công cụ & Kiến trúc (Tools & Architecture)
- **Cloth Segmentation:** SAM (Segment Anything Model) / GroundingDINO.
- **Warping & Texture Fit:** ComfyUI CatVTON (hoặc IDM-VTON) checkpoint `vit-h` + `denoise 0.70-0.80`.
- **Inpainting & Face Preservation:** Flux.1 Kontext Inpaint / SDXL ControlNet OpenPose.
- **Motion Synthesis:** Kling AI 1.5 (Image-to-Video, Camera Dynamic Pan, Motion: 4).
- **Final Assembly:** HeyGen HyperFrames (Composition 9:16 1080x1920, kinetic captions, Morphicons, safe zone layout).

---

## 3. Các bước thực hiện & Thông số kỹ thuật (Step-by-Step & Parameters)

### Bước 1: Tiền xử lý & Tách lớp trang phục (Segmentation)
- Nạp ảnh quần áo vào node `ComfyUI SAM`. Prompt: `clothing, dress, shirt, pants`.
- Xuất mask nhị phân (Binary Mask) vùng trang phục, giãn biên (dilate) 4px để tránh viền đen.

### Bước 2: Ghép trang phục lên KOC (VTON Diffusion Transfer)
- Node: `Load CatVTON Pipeline`.
- Model: `catvton-flux` / `catvton-sdxl`.
- Cấu hình thông số:
  - `Steps`: 30
  - `CFG Scale`: 5.0
  - `Denoise`: 0.75
  - `Sampler`: Euler Ancestral (`euler_a`)
- Output: 1 ảnh KOC mặc hoàn chỉnh trang phục mới với tỷ lệ cơ thể chuẩn.

### Bước 3: Sinh chuyển động video người mẫu (Image-to-Video Motion)
- Nạp ảnh từ Bước 2 vào **Kling AI 1.5** (hoặc Runway Gen-3 Alpha).
- Mode: `Professional Mode`, thời lượng: 5 giây hoặc 10 giây.
- Prompt điều khiển:
  ```
  A fashionable model doing a gentle 45-degree body turn, smiling softly, natural fabric drape physics, realistic soft studio shadows, cinematic lighting, 4k ultra realistic, shot on 35mm lens --motion 4
  ```
- Camera Movement: `Horizontal Pan Left 1.5, Zoom In 1.2`.

### Bước 4: Lắp ráp & Hoàn thiện trên HeyGen HyperFrames
- Tự động tạo composition qua HyperFrames CLI:
  `python -m socnhotv --project soc-nho-tv video render --template vton-koc`
- Cấu trúc layout:
  - Nền video KOC xoay dáng: `fit: cover`.
  - Vùng an toàn TikTok (Safe Zone): Padding top 180px (tránh icon tìm kiếm), padding bottom 320px (tránh giỏ hàng và thanh mô tả).
  - Kinetic Subtitle: Cỡ chữ 48px, font Inter ExtraBold, highlight màu vàng hổ phách `#F59E0B`.

---

## 4. Đầu ra (Deliverables)
- Video MP4 9:16 (1080x1920, 30fps CFR, H.264/AAC).
- Chuẩn âm lượng: -14.0 LUFS tích hợp.
- Thời lượng: 15–30 giây (gồm 3 góc quay trang phục: toàn cảnh, cận cảnh chất vải, xoay nghiêng).

---

## 5. Lỗi thường gặp & Cách khắc phục (Troubleshooting)
1. **Lỗi logo hoặc chữ trên áo bị méo mó, biến thành ký tự vô nghĩa:**
   - *Nguyên nhân:* Mô hình diffusion tự do inpaint lại vùng chữ.
   - *Khắc phục:* Dùng node `Mask Composite` để đè lại chính xác 100% vector logo gốc lên ngực áo ở bước hậu kỳ.
2. **Lỗi cổ áo hoặc tay áo bị dính liền vào da người mẫu:**
   - *Khắc phục:* Giảm `Denoise` từ 0.75 xuống 0.65 và tăng độ phân giải mask lên 2048px.
3. **Lỗi chuyển động camera bị giật cục hoặc cơ thể biến dạng khi xoay:**
   - *Khắc phục:* Giảm chỉ số `--motion` từ 6 xuống 3-4 trong Kling 1.5. Luôn dùng chế độ `End Frame` nếu muốn video lặp vô tận (Looping Video).
