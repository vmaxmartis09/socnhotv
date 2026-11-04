# Tài liệu & Nguồn truy vết (Sources & Verification) — Seq 003

Video ID: `2272929803457749` | Tiêu đề: "50K/tháng tạo KOC ảo review thời trang cực dễ" | Kênh: AI Thực Chiến

## Chuỗi truy vết 3 tầng (3-Tier Investigation)

### Tầng 1: Dấu vết từ Video & Kênh
1. **Công cụ được chỉ đích danh: Co-Maker**:
   - Tên nền tảng: Co-Maker (nền tảng tạo video AI KOC thời trang dạng SaaS).
   - Mô hình hoạt động: Cung cấp kho Template video có sẵn (các chuyển động mẫu hot trend TikTok). Người dùng bấm "Remix" -> tải ảnh trang phục lên -> hệ thống tự xử lý virtual try-on và render video 15 phút.
   - Quảng cáo 50k/tháng: Thực chất là gói dùng thử cơ bản hoặc chi phí credit token ban đầu, sau đó người dùng vẫn phải trả thêm token để render nhiều.
   - Độ tin cậy: Cao (Giao diện web Co-Maker được quay trực tiếp trong video).

### Tầng 2: Công nghệ cốt lõi đằng sau Co-Maker (Virtual Try-on & Video Remix)
2. **Virtual Try-On Diffusion Models (OOTDiffusion & IDM-VTON)**:
   - Cơ chế: Mô hình nhận 2 đầu vào: (1) Ảnh người mẫu KOC và (2) Ảnh sản phẩm quần áo phẳng (flat-lay).
   - Mô hình tách vùng quần áo cũ bằng Mask Segmentation, tiêm đặc trưng vải (texture, nếp gấp, logo) của trang phục mới vào cơ thể người mẫu mà không làm thay đổi dáng đứng hay khuôn mặt.
   - Bằng chứng tài liệu:
     - Paper: *IDM-VTON: Improving Diffusion Models for Authentic Virtual Try-on in the Wild* (2024).
     - Repo: `https://github.com/yisol/IDM-VTON`
   - Độ tin cậy: Rất cao.

3. **Template-Driven Video Generation (Cơ chế Remix)**:
   - Thay vì tạo video ngẫu nhiên, hệ thống khoá sẵn:
     - Nhịp camera (Camera track / Motion vector)
     - Nhịp nhạc (BGM)
     - Khung chữ phụ đề (Subtitle positioning)
   - Người dùng chỉ thay thế **Asset Slot** (Ảnh quần áo, Tên sản phẩm, Giá bán).
   - Đây là mô hình tương đồng 100% với kiến trúc `RenderRequest` của Session A trong dự án SocNhoTV.

### Tầng 3: Đối chiếu với Hệ sinh thái Gobi / SocNhoTV
4. **Tự chủ công nghệ không phụ thuộc SaaS bên thứ 3**:
   - Co-Maker thu phí người dùng và phụ thuộc máy chủ đóng.
   - SocNhoTV có thể tái lập toàn bộ quy trình "Remix 3 bước" này ngay trong Web Dashboard bằng:
     1. Template HTML5 HyperFrames (cố định layout an toàn 9:16).
     2. Slot sản phẩm từ kho `products/` (Session B).
     3. Render engine cục bộ hoặc CloudRun không giới hạn.

## Bảng tổng hợp nguồn

| URL / Định danh | Ngày truy cập | Loại nguồn | Điều học được | Độ tin cậy | Chứng minh điều gì |
|---|---|---|---|---|---|
| `https://www.facebook.com/share/v/1Vm4Ei6GFF/` | 2026-11-04 | Video gốc | Quy trình Remix 3 bước (Mẫu -> Upload đồ -> Xuất video 15p) | Rất cao | Khảo sát trải nghiệm người dùng thực tế |
| `https://github.com/yisol/IDM-VTON` | 2026-11-04 | Open-source SOTA | Cơ chế thử đồ ảo Virtual Try-on giữ nguyên phom dáng | Rất cao | Công nghệ cốt lõi tạo mẫu KOC thời trang |
| `https://github.com/levihsu/OOTDiffusion` | 2026-11-04 | Open-source SOTA | Thử đồ ảo cho cả nửa thân trên (half-body) và toàn thân (full-body) | Rất cao | Giải pháp mã nguồn mở tự host |
| `socnhotv.video.contracts` | 2026-11-04 | Nội bộ dự án | Thiết kế `RenderRequest(template_id, data)` chuẩn hoá | Tuyệt đối | Kiến trúc hệ thống tương đồng để triển khai |
