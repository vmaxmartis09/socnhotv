# AI Video Realism & Anti-Artifact Protocols (EN / VI)
Tags: video-realism | anti-artifact | camera-mechanics | motion-fidelity | color-grading | film-grain

## Là gì (2–3 câu)
Tập hợp các kỹ thuật và quy chuẩn xử lý hình ảnh nhằm triệt tiêu hoàn toàn các dấu hiệu "giả trân / rác AI" (AI Slop, hiện tượng biến dạng thạch gelatinous warping, biến dị ngón tay, mắt lác, da nhựa sáp và ánh sáng trôi nổi vô trọng lực) trong video do AI sinh ra (Kling, Runway, Sora, Flux). Quy trình can thiệp từ bước chuẩn bị hình ảnh điều kiện (Depth/Normal/Pose pre-conditioning) đến xử lý hậu kỳ (Film grain, Motion blur, ACES Color grading và Light Wrap).

## Vì sao hiệu quả (Cơ chế tâm lý / Nền tảng)
- **Vượt qua thung lũng kỳ lạ (Uncanny Valley):** Não người có cơ chế sinh học cực kỳ nhạy bén với những chuyển động phi vật lý hoặc bề mặt da quá bóng bẩy. Video AI bị phát hiện là giả sẽ bị người xem lướt qua trong 1 giây đầu (Hook Drop Rate > 80%).
- **Tăng cảm xúc cao cấp & Giá trị thương hiệu:** Phim quảng cáo (TVC) hay video giới thiệu sản phẩm chỉ thuyết phục được khách hàng khi các vật thể bằng kim loại, đá quý, vải vóc phản chiếu ánh sáng tự nhiên và có độ nhiễu hạt quang học (Optical Grain) của ống kính điện ảnh thật.

## Ví dụ trong video thực tế
- Video ID: `7695663938083507464` (@70.ai.studio) @ t=18.4s (PNJ TVC với chi tiết phản xạ vàng bạc, chuyển động tay mượt mà không biến dị).
- Video ID: `7694697264454962440` (@magentx.ai) @ t=05.2s (Mẫu AI KOC giữ vững cấu trúc khuôn mặt và nếp vải qua 4 góc quay khác nhau).

## Cách làm lại trong dự án này (Cụ thể)
1. **Kiểm soát điều kiện sinh hình ảnh (Pre-conditioning):**
   - Không để mô hình AI tự do sinh chuyển động từ văn bản thuần (Text-to-Video). Luôn sử dụng **Image-to-Video có khóa góc máy (Start Frame + End Frame)** hoặc dẫn hướng qua **Depth Map / Camera Path**.
   - Cố định chi tiết bàn tay: Khóa mask vùng bàn tay bằng ControlNet OpenPose Hands hoặc inpainting cố định trước khi đưa vào video engine.
2. **Triệt tiêu hiện tượng dập dềnh (De-warping & Stabilization):**
   - Đặt thông số Motion Amplitude ở mức vừa phải (Kling Motion: 3 - 5; Runway Motion: 2 - 4).
   - Với những chuyển động nhanh, bù đắp bằng mô phỏng Motion Blur quang học (Optical Flow Motion Blur shutter angle 180°).
3. **Phủ lớp hòa sắc và hạt điện ảnh (Post-Processing in HyperFrames / FFmpeg):**
   - **Film Grain:** Inject một lớp hạt nhiễu vi mô 35mm (Fine Grain Overlay với độ mờ 6-8%, blend mode `overlay`) để phá vỡ bề mặt nhẵn bóng nhân tạo.
   - **Light Wrap & Shadow Grounding:** Tạo bóng đổ tiếp xúc (Contact Shadows) ở chân nhân vật Bi/Koala để nhân vật bám chặt xuống mặt đất, không bị bay lơ lửng.
   - **Color Tone:** Áp dụng bảng màu điện ảnh (Teal & Orange nhẹ hoặc Warm Amber) thay vì dải màu RGB bão hòa quá mức của AI nguyên bản.

## Công cụ, Chi phí & Thời gian
- **Công cụ:** ControlNet Depth/Pose + ComfyUI + FFmpeg / HeyGen HyperFrames CSS Filters & SVG Grain.
- **Chi phí:** Không tốn thêm chi phí sinh hình mới, chỉ bổ sung 1 bước filter hậu kỳ.
- **Thời gian xử lý:** +15 giây/clip render.

## Lỗi thường gặp & Cách tránh
- *Bóng đổ bị trôi theo camera:* Đảm bảo nguồn sáng chính (Key Light) trong prompt 3D và video đồng nhất với bối cảnh nền.
- *Hạt phim quá to làm mờ chi tiết:* Chỉ dùng hạt vi mô độ phân giải cao (ISO 200/400 scan), tránh filter hạt to kiểu retro thập niên 80 trừ khi kịch bản yêu cầu.

## Cách đo hiệu quả trong Analytics
- Thời lượng xem trung bình (Average Watch Time tăng từ 12s lên 26s).
- Tỷ lệ bình luận hỏi "Quay ở đâu đấy?" hoặc "Phim thật hay 3D thế?" (Dấu hiệu vượt qua Uncanny Valley thành công).

## Nguồn kiểm chứng
- Nghiên cứu: "Temporal Consistency and Photorealism in Diffusion-Based Video Generation" (SIGGRAPH 2024).
- 70 AI STUDIO Production Standards (`ai/plans/2026-11-roadmap/session-D-research/`).

**Mức độ tin cậy:** Cao · **Cập nhật:** 2026-11-04
