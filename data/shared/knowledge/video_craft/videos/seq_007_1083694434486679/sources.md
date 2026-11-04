# Tài liệu & Nguồn truy vết (Sources & Verification) — Seq 007

Video ID: `1083694434486679` | Tiêu đề: "Làm video AI bán quần áo hàng loạt với Infinite Canvas" | Giảng viên: Thân Ca

## Chuỗi truy vết 3 tầng (3-Tier Investigation)

### Tầng 1: Dấu vết từ Video
1. **Nền tảng Infinite Canvas & Giảng viên Thân Ca**:
   - Kênh đăng lại: Jolie Mê Xem Phim.
   - Giảng viên chính: Thân Ca (chuyên gia đào tạo sản xuất video AI thương mại điện tử).
   - Nội dung video: Hướng dẫn chi tiết từng click chuột trên giao diện Canvas node-graph.
   - Mô hình AI sử dụng: **Kling 1.5** (chọn độ phân giải 2K, tỷ lệ 9:16 dọc, thời lượng 15s mỗi node).
   - Độ tin cậy: Tuyệt đối (Quy trình thao tác trực tiếp trên màn hình).

### Tầng 2: Công nghệ Dual-Node Stitching (Nối 2 clip AI thành video dài)
2. **Kỹ thuật Last-Frame to First-Frame Continuity**:
   - Vấn đề: Các model Video AI (Kling, Runway, Wan, Hailuo) thường giới hạn thời lượng 5s–10s, nếu sinh 30s một lúc sẽ bị biến dạng (morphing drift).
   - Giải pháp công nghiệp:
     - Node 1: Sinh 15s với prompt dạo phố.
     - Trích xuất frame cuối cùng (t=14.9s) của Node 1.
     - Node 2: Dùng frame vừa trích xuất làm ảnh khởi đầu (Start Frame) cho Node 2 -> sinh tiếp 15s xoay người cận cảnh.
     - Kết quả: Nhân vật, trang phục và ánh sáng liên tục 100% không bị nhảy giật.
   - Độ tin cậy: Rất cao.

### Tầng 3: Tích hợp vào HyperFrames Engine của SocNhoTV
3. **HyperFrames Clip Stitching Pipeline**:
   - HyperFrames giải quyết trọn vẹn bước 6 của video này:
     ```html
     <!-- Clip 1: Catwalk dạo phố -->
     <video class="clip" data-start="0" data-duration="15" src="kling_part1.mp4"></video>
     <!-- Clip 2: Cận cảnh xoay người -->
     <video class="clip" data-start="15" data-duration="15" src="kling_part2.mp4"></video>
     ```
   - HyperFrames tự động bổ sung subtitle karaoke, nhạc nền ducking và lớp đồ họa bán hàng trên cùng mà không cần mở phần mềm ngoài.

## Bảng tổng hợp nguồn

| URL / Định danh | Loại | Điều học được | Độ tin cậy |
|---|---|---|---|
| `https://www.facebook.com/share/v/1HDkUceE27/` | Video tutorial gốc | Quy trình 6 bước trên Infinite Canvas, cách thiết lập Kling 1.5 | Tuyệt đối |
| `https://klingai.com/` | Nền tảng Video AI | Tài liệu API Kling 1.5: Hỗ trợ video 15s, start-frame conditioning | Rất cao |
| `socnhotv.video.hyperframes_engine` | Core engine dự án | Cấu trúc ghép clip đa track tất định bằng HTML5/GSAP | Tuyệt đối |
