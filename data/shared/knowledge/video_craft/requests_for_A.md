# Đề xuất cho Session A (Video & Templates) từ Session D

Dưới đây là các đề xuất template, hiệu ứng, và cải tiến dựng video rút ra từ các video nghiên cứu thực tế.

| Ngày | Nguồn (Video ID) | Đề xuất Template / Node | Mô tả cấu trúc Beat / Visual | Độ ưu tiên |
|---|---|---|---|---|
| 2026-11-04 | Seq 001 (`1342818958924942`) | `product-avatar-insitu-v1` | Template dọc 9:16: Slot 1 ảnh background sản phẩm tĩnh (sofa, bàn, góc nhà), Slot 2 clip alpha nhân vật KOC (hoặc Bi 100cm), Beat 1 Hook thú nhận, Beat 2 Phóng to chi tiết đệm/sản phẩm (Punch-in 1.25x), Beat 3 Thẻ thông số nổi, Beat 4 CTA bán hàng. | Cao |
| 2026-11-04 | Seq 003 (`2272929803457749`) | Cơ chế "1-Click Remix" trên UI Dashboard | Nút bấm "Remix" trên từng card Template: Chọn ảnh sản phẩm từ `products/` -> Tự điền slot -> Submit `RenderRequest` mà không bắt người dùng phải cấu hình timeline thủ công. | Rất cao |
| 2026-11-04 | Seq 005 (`1780575939827550`) | `lookbook-split-canvas-v1` | Template thời trang 9:16 chia đôi (45% Video Model tạo dáng : 55% Bảng Sticker Cutout bóc tách từng món). Hỗ trợ 3 Set trang phục (mỗi set 19s). Tự động vẽ đường nối doodle SVG đồng bộ với giọng đọc giới thiệu món đồ. | Cực cao (Mẫu vàng) |
| 2026-11-04 | Seq 006 (`3061194297574911`) | Bộ Preset 5 Cú máy Camera ảo GSAP | Thêm các hàm helper vào `HyperFramesEngine`: `pan()`, `pushIn()`, `orbit()`, `pedestalUp()` để các template video có thể gọi trực tiếp thay vì tự viết CSS keyframes thủ công. | Cao |
| 2026-11-04 | Seq 007 (`1083694434486679`) | `dual-clip-stitcher` Module trong Engine | Hỗ trợ template nhận 2 video đầu vào (Part 1 Catwalk 15s + Part 2 Close-up Turn 15s) và tự động nối mượt với flash cut 0.15s, lồng voiceover và auto-ducking BGM, xuất ra video 30s liền mạch. | Rất cao |
| 2026-11-04 | Seq 008 (`1403971144535658`) | Adapter tích hợp `motion-mimic` vào Render Pipeline | Cho phép `RenderRequest` nhận thêm tham số `source_video_ref`, tự động gọi pipeline Motion Mimic để tráo mặt KOC Neau/LyLy vào cử chỉ video gốc rồi đóng gói qua HyperFrames. | Cao |
