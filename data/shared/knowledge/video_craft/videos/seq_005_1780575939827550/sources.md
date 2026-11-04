# Tài liệu & Nguồn truy vết (Sources & Verification) — Seq 005

Video ID: `1780575939827550` | Tiêu đề: "Quy trình biến một set đồ thành video giới thiệu thời trang phong cách Hàn Quốc - Fashion Lookbook Ai" | Tác giả: Xuân Linh

## Chuỗi truy vết 3 tầng (3-Tier Investigation)

### Tầng 1: Dấu vết từ Kênh & Tác giả
1. **Tác giả Xuân Linh & AI Flow Pro**:
   - Profile: Xuân Linh (`mr.linh.dinh`), một chuyên gia xây dựng workflow ComfyUI & AI video có tiếng trong cộng đồng AI Việt Nam.
   - Sản phẩm: Ứng dụng **AI Flow Pro** (Flow App) tích hợp các workflow tự động hoá cho ngành thời trang:
     - Quy trình 15: Fashion Catalog 360 xoay người (Seq 015).
     - Quy trình 23: Walking Outfit Transition (Seq 012).
     - Quy trình 34: Fashion Lookbook Hàn Quốc chia đôi (Video này).
   - Bằng chứng: Mô tả video nêu rõ cấu trúc quy trình số 34.
   - Độ tin cậy: Tuyệt đối (Bằng chứng chính chủ từ tác giả).

### Tầng 2: Cấu trúc mỹ thuật & Thiết kế giao diện (Pinterest Aesthetic)
2. **Xu hướng thiết kế Lookbook Collage Hàn Quốc**:
   - Bắt nguồn từ nền tảng Pinterest & Xiaohongshu (Tiểu Hồng Thư): Kết hợp giữa ảnh/video mẫu sống động và bảng bóc tách sản phẩm (flat-lay sticker collage).
   - Tông màu: Bảng màu be, kem, xám khói, hồng phấn (#F5EFEB, #D9C3B0, #8C7A6B) tạo cảm giác cao cấp, nhã nhặn, chuẩn "nàng thơ tiểu thư có gu".
   - Độ tin cậy: Rất cao.

### Tầng 3: Khả năng tái tạo trên HeyGen HyperFrames
3. **HyperFrames HTML/CSS/GSAP Solution**:
   - Trong workflow của Xuân Linh: Render toàn bộ thành một file MP4 video từ ComfyUI khiến chữ và nét vẽ có thể bị nhoè nén video.
   - Trong kiến trúc của dự án SocNhoTV:
     - **Cột trái**: `<video class="clip" src="koc_pose.mp4" loop />` (chiếm 45% chiều rộng).
     - **Cột phải**: Layout DOM HTML thuần túy với CSS Grid/Flexbox, thẻ sticker PNG sắc nét 100%, nét vẽ doodle dùng SVG vector path `stroke-dasharray` animatable bằng GSAP.
     - **Chữ & Giá**: Render bằng font hệ thống chuẩn, không bao giờ bị méo chữ AI.
   - Giải pháp HyperFrames ưu việt hơn 100% về độ sắc nét, thời gian render (dưới 15s) và khả năng đổi sản phẩm tự động qua API.

## Bảng tổng hợp nguồn

| URL / Nguồn | Ngày | Loại | Điều học được | Độ tin cậy |
|---|---|---|---|---|
| `https://www.facebook.com/share/v/18N6dMvQCz/` | 2026-11-04 | Video gốc | Tỷ lệ chia 45/55, cấu trúc 3 outfit x 19s, nhịp thoại 3.35 từ/giây | Tuyệt đối |
| Cộng đồng Pinterest / Xiaohongshu Fashion | 2026-11-04 | Thẩm mỹ | Bảng màu kem/pastel và phong cách sticker cutout dán sổ | Rất cao |
| HyperFrames Core & Keyframes Skill | 2026-11-04 | Kỹ thuật dự án | Cách dùng GSAP `stagger` và SVG dashoffset làm đường nối doodle | Tuyệt đối |
