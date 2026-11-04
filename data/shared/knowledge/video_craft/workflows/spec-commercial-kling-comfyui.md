# Quy Trình Sản Xuất Phim Quảng Cáo Thương Mại Cao Cấp (Spec Commercial 3D-to-Kling Pipeline)

- **Slug:** `spec-commercial-kling-comfyui`
- **Trạng thái tái tạo trong Studio:** `đã thử tái tạo` (qua Blender pre-vis + Kling 1.5 conditioning + HyperFrames post-processing)
- **Tần suất xuất hiện:** Xuất hiện ở 3 kênh độc lập (@70.ai.studio, @ngoc.agi, @magentx.ai)
- **Độ tin cậy:** Rất cao (Có bằng chứng TVC PNJ 88 giây tiêu chuẩn điện ảnh)

---

## 1. Đầu vào (Inputs)
1. **Moodboard & Kịch bản phân cảnh (Storyboard / Script):**
   - 5–8 phân cảnh chính (Shot list với mô tả góc máy: Close-up sản phẩm, Wide-shot bối cảnh, Macro phản xạ ánh sáng).
2. **Tài sản 3D / Keyframe tĩnh (3D Model / Keyframe Renders):**
   - 3D Model sản phẩm (trang sức, chai nước hoa, đồ công nghệ) hoặc mô hình nhân vật hoạt hình (Sóc Nhỏ 100cm, Koala 150cm).
3. **Soundtrack & Sound Design (SFX):**
   - Bản phối BGM dàn nhạc giao hưởng / cinematic riser.
   - Thư viện âm thanh tiếp xúc vật lý (Foley: tiếng kim loại chạm, tiếng gió rít, tiếng bước chân).

---

## 2. Công cụ & Kiến trúc (Tools & Architecture)
- **Pre-visualization & Camera Blocking:** Blender 4.x / Unreal Engine 5 (xuất Depth Map và Camera Path).
- **Style Conditioning:** Midjourney v6.1 / Flux.1 Dev (sinh Keyframe đầu và cuối có ánh sáng đồng nhất).
- **Video Generation Engine:** Kling AI 1.5 Professional Mode (hỗ trợ Start & End Frame) / Runway Gen-3 Alpha.
- **Micro-detail & Hand Refinement:** ComfyUI ControlNet Tile Upscaler (UltraSharp 4x).
- **Sound Design & Master Finishing:** HeyGen HyperFrames Audio Engine + FFmpeg Mastering (-14 LUFS, 35mm Film Grain Overlay).

---

## 3. Các bước thực hiện & Thông số kỹ thuật (Step-by-Step & Parameters)

### Bước 1: Dựng Camera Pre-vis & Khóa Chuyển Động (Blender / UE5)
- Tạo khối hộp đơn giản (Blockout) đại diện cho sản phẩm và nhân vật.
- Di chuyển camera theo đúng quỹ đạo mong muốn: Orbit quanh sản phẩm 90°, lướt nhanh từ tiền cảnh ra hậu cảnh.
- Render pass: `Depth Pass` (Z-depth) và `Normal Pass` ở 30fps.

### Bước 2: Sinh Keyframe Siêu Chi Tiết (Keyframe Generation)
- Dùng Flux.1 Dev với ControlNet Depth từ pass Blender ở Bước 1.
- Prompt điện ảnh chuẩn:
  ```
  Commercial cinematography of luxury jewelry, macro 100mm lens, softbox studio lighting, caustics reflection, shallow depth of field, anamorphic bokeh, photorealistic 8k, award-winning advertising photography --ar 16:9 --style raw
  ```
- Khóa cố định 2 khung hình: Khung đầu (Start Frame) và Khung kết thúc (End Frame).

### Bước 3: Nội suy Video bằng Kling AI 1.5 (Two-Frame Conditioning)
- Nạp đồng thời **Start Frame** và **End Frame** vào Kling 1.5.
- Cấu hình:
  - `Model`: Kling 1.5 Pro
  - `Duration`: 5 giây
  - `Motion Mode`: Smooth Cinematic
  - `Camera Movement`: Custom path tương ứng với Blender pre-vis
- AI sẽ tự động tính toán nội suy chuyển động giữa 2 mốc mà không bao giờ bị trôi hình hoặc biến dạng cấu trúc vật thể.

### Bước 4: Hậu kỳ Phim & Hòa sắc (Post-Processing & Sound Sync)
- Đưa các clips vào HeyGen HyperFrames:
  - Áp dụng lớp phủ hạt quang học `35mm Optical Grain` với CSS filter `mix-blend-mode: overlay`, `opacity: 0.07`.
  - Khớp các điểm chuyển cảnh (Cuts) chính xác với beat nhạc đập mạnh (Transient Beat Sync).
  - Thêm hiệu ứng âm thanh SFX whoosh và tiếng click sản phẩm tại mili-giây thứ 12 của mỗi cut.

---

## 4. Đầu ra (Deliverables)
- Video TVC chuẩn phát sóng: 1080x1920 (TikTok 9:16) hoặc 3840x2160 (4K 16:9).
- Định dạng ProRes 422HQ hoặc MP4 H.264 High-Profile 25Mbps.
- Âm lượng đạt chuẩn điện ảnh / social: -14.0 LUFS.

---

## 5. Lỗi thường gặp & Cách khắc phục (Troubleshooting)
1. **Lỗi vật thể kim loại/thủy tinh bị dập dềnh khi camera di chuyển:**
   - *Khắc phục:* Bắt buộc nạp cả Start Frame và End Frame; không để Kling tự suy đoán kết thúc.
2. **Lỗi màu sắc giữa các shot quay không đồng nhất (Color Inconsistency):**
   - *Khắc phục:* Áp dụng chung 1 bảng màu LUT (Cube 3D LUT) trong quá trình assemble video trên HyperFrames.
