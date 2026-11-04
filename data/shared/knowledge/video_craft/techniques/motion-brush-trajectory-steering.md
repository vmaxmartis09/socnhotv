# Motion Brush & Multi-Layer Trajectory Steering (EN / VI)
Tags: generative-video | motion-brush | camera-physics | kling-ai | runway-gen3 | continuity

## Là gì (2–3 câu)
Kỹ thuật chỉ định vùng chuyển động độc lập (Region-based Motion Vector) và quỹ đạo camera (Pan / Tilt / Zoom / Roll) trên ảnh tĩnh trước khi tạo video AI. Cho phép tách biệt chuyển động của nhân vật, chuyển động của nền (background parallax) và chuyển động của camera, ngăn ngừa hiện tượng "tan chảy" (melting artifact) hoặc biến dạng hình thể khi nhân vật di chuyển.

## Vì sao hiệu quả (Cơ chế tâm lý / Nền tảng)
- **Tạo cảm giác chân thực không gian (Spatial Depth):** Mắt người phân biệt cảnh quay chuyên nghiệp với video AI nghiệp dư qua hiệu ứng thị sai (parallax effect): vật ở gần di chuyển nhanh hơn vật ở xa.
- **Tránh hiện tượng "nhân vật đơ, cảnh trôi":** Khi chỉ dùng text prompt, AI thường di chuyển cả khung hình một cách thụ động. Motion brush buộc AI chỉ tác động lực vật lý vào đúng vùng mong muốn (ví dụ: chỉ tóc và tà áo bay, còn khuôn mặt giữ nguyên cấu trúc).

## Ví dụ trong video thực tế
- Video ID: `7693503813071703297` (@ngoc.agi) @ t=18.5s (Kling AI 1.5 vs Runway Gen-3 Alpha: Hướng dẫn chi tiết tạo chuyển động mượt không biến dạng - 7074 views).
- Video ID: `7704184521054375186` (@magentx.ai) @ t=09.2s.

## Cách làm lại trong dự án này (Cụ thể)
1. **Thiết lập Brush phân lớp:**
   - *Brush 1 (Nhân vật / Chủ thể):* Tọa độ chuyển động X=0, Y=-0.5, Z=+1.2 (nhân vật bước về phía trước camera).
   - *Brush 2 (Trang phục / Tóc):* Chế độ Dynamic Flow, hướng gió từ trái sang phải, cường độ 3/10.
   - *Brush 3 (Hậu cảnh):* Giữ nguyên (Static) hoặc Parallax ngược chiều camera pan nhẹ để tạo chiều sâu.
2. **Cấu hình Camera Điều khiển:**
   - Horizontal: +1.5 (Pan sang phải nhẹ nhàng).
   - Zoom: +0.8 (Dolly in từ từ tạo cảm giác tập trung vào sản phẩm).
   - Roll: 0 (Khóa trục nghiêng để giữ đường chân trời thẳng).
3. **Tích hợp với HeyGen HyperFrames:**
   - Đưa đoạn video đã render vào HyperFrames timeline. Sử dụng GSAP timeline để match chuyển động camera: khi video AI kết thúc cú pan sang phải, transition trong HyperFrames tiếp tục trượt sang phải (Match Cut Continuity), tạo cảm giác một cú máy liền mạch không ngắt quãng.

## Công cụ, Chi phí & Thời gian
- **Công cụ:** Kling AI 1.5 (Motion Brush v2) / Runway Gen-3 Alpha (Motion Brush + Camera Control).
- **Chi phí:** 10 - 20 credits/lần generate (~\$0.10 - \$0.20).
- **Thời gian xử lý:** 60 - 90 giây/clip 5 giây.

## Lỗi thường gặp & Cách tránh
- *Lỗi biên vùng brush bị rách (Edge tearing):* Luôn dùng cọ mềm (soft feathered edge) khi quét brush, chừa lại khoảng đệm 5-10px quanh đường biên chủ thể.
- *Lỗi camera di chuyển quá nhanh gây chóng mặt:* Đặt thông số camera chuyển động dưới mức 3.0/10; ưu tiên chuyển động chậm rãi, mượt mà.

## Cách đo hiệu quả trong Analytics
- Average watch time (Thời gian xem trung bình tăng >= 20%).
- Tỷ lệ xem lại (Loop rate >= 15%).

## Nguồn kiểm chứng
- Kling AI Official Documentation: "Mastering Motion Brush 2.0" (2026).
- Runway Research: "Controllable Video Generation via Dense Trajectory Priors".
- Bài phân tích chuyên sâu của Ngọc AGI trên TikTok/YouTube.

**Mức độ tin cậy:** Cao · **Cập nhật:** 2026-11-04
