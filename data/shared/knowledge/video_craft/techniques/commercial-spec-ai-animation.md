# Commercial Spec AI Animation Pre-vis & Generation (EN / VI)
Tags: commercial-ads | 3d-animation | tvc-spec | ai-filmmaking | hyperframes | motion-design

## Là gì (2–3 câu)
Phương pháp sản xuất clip quảng cáo thương mại cao cấp (Spec Commercial / TVC quảng cáo thương hiệu) bằng cách kết hợp khung xương đồ hoạ 3D (Blender / Maya animatic pre-vis) làm điều kiện dẫn hướng (ControlNet Openpose/Depth/Normal) cho mô hình sinh video AI (Kling 1.5, Runway Gen-3 Alpha, Veo). Cho phép đạo diễn kiểm soát 100% quỹ đạo camera, bố cục ánh sáng và tương tác vật thể mà không bị ngẫu nhiên (hallucination).

## Vì sao hiệu quả (Cơ chế tâm lý / Nền tảng)
- **Chuẩn điện ảnh (Cinematic Trust):** Người xem nhận diện được giá trị thương hiệu cao cấp qua chất lượng đổ bóng ray-tracing, phản chiếu kim loại, chuyển động camera phức tạp (dolly zoom, 360 orbit) - điều mà video AI thuần văn bản prompt không thể làm được.
- **Tỷ lệ chia sẻ (Viral Advocacy):** Clip spec commercial chất lượng cao kích thích người xem chia sẻ vì tính mãn nhãn thị giác và bất ngờ trước năng lực của AI.

## Ví dụ trong video thực tế
- Video ID: `7695663938083507464` (@70.ai.studio) @ t=22.4s ("Nếu tụi mình làm AI viral clip cho @PNJ OFFICIAL" - 88s, TVC spec vàng bạc đá quý PNJ).
- Video ID: `7694645250429734152` (@70.ai.studio) @ t=05.1s (21.8K views, dự án thương mại khách hàng Hàn Quốc).

## Cách làm lại trong dự án này (Cụ thể)
1. **Tiền kỳ 3D Pre-vis:**
   - Dựng mô hình 3D thô (low-poly proxy) trong Blender hoặc nạp mô hình nhân vật Sóc Nhỏ (Bi 100cm / Koala 150cm).
   - Thiết lập chuyển động camera (Keyframe 3D camera move: orbital pan quanh sản phẩm).
   - Render ra chuỗi pass: Depth pass + Lineart/Canny pass + Normal map pass.
2. **Khuếch tán AI (Diffusion Video Conditioning):**
   - Đưa depth pass vào ComfyUI với node ControlNet Advanced / Animatediff hoặc Kling AI Image-to-Video với Start Frame & End Frame khóa cứng.
   - Prompt ánh sáng thương mại: `Cinematic macro commercial shot, luxury studio rim lighting, 8k raytracing, hyper-realistic jewelry reflection, shot on Arri Alexa LF 35mm`.
3. **Hậu kỳ tất định với HeyGen HyperFrames:**
   - Dựng chuỗi render vào `<hf-video-track>`, đồng bộ âm thanh sound design (SFX tiếng lách cách kim loại, swoosh không gian).
   - Thêm animated logo reveal bằng SVG morphing thông qua component MorphIcon.

## Công cụ, Chi phí & Thời gian
- **Công cụ:** Blender 3D (proxy animation) + ComfyUI / Kling AI 1.5 / Runway Gen-3 + HeyGen HyperFrames.
- **Chi phí GPU:** ~\$0.20 - \$0.40 cho 1 cảnh 5 giây tiêu chuẩn 1080p.
- **Thời gian sản xuất:** 2 - 4 giờ cho 1 TVC ngắn 30s hoàn chỉnh.

## Lỗi thường gặp & Cách tránh
- *Lỗi biến dạng hình khối sản phẩm (Shape morphing):* Với sản phẩm có logo hoặc hình dạng đặc thù (nhẫn, chai lọ, hộp sản phẩm), luôn dùng LoRA huấn luyện riêng cho sản phẩm đó hoặc giữ nguyên mô hình 3D thật ở foreground rồi chỉ dùng AI cho background.
- *Lỗi ánh sáng nhảy giật giữa các frame (Flicker):* Áp dụng deflicker pass trong FFmpeg (`-vf deflicker`) hoặc bật Frame Interpolation RIFE.

## Cách đo hiệu quả trong Analytics
- Retention rate ở 50% thời lượng video (giữ chân > 45%).
- Tỷ lệ lưu video (Save rate >= 3%).

## Nguồn kiểm chứng
- Studio 70 AI: Quy trình sản xuất TVC AI thương mại (2026).
- RunwayML: Gen-3 Alpha Camera Control & Director Mode Documentation.
- Kling AI: Advanced Motion Brush & 3D Vector Guidelines.

**Mức độ tin cậy:** Rất cao · **Cập nhật:** 2026-11-04
