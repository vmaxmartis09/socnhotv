# Tài liệu & Nguồn truy vết (Sources & Verification) — Seq 001

Video ID: `1342818958924942` | Tiêu đề: "Làm video bán hàng Nội Thất chỉ bằng 1 câu lệnh cho Agent"

## Chuỗi truy vết 3 tầng (3-Tier Investigation)

### Tầng 1: Dấu vết từ Video & Kênh
1. **Trang đích Landing Page**:
   - URL: `https://videoagentcis.netlify.app/`
   - Tiêu đề: "Khóa học làm video bằng Agent: một câu lệnh ra video | 899.000đ"
   - Tiết lộ công nghệ cốt lõi: *"Agent tự viết kịch bản, vào Flow làm clip, tải về và dựng thành video hoàn chỉnh. Tặng bộ skill Autovideo..."*
   - Phát hiện: Công cụ video generator thực tế đằng sau là **Flow App / Google Flow** (cùng nền tảng với các video của kênh Xuân Linh, Toby). Không phải "1 câu lệnh thần thánh" mà là browser automation / skill điều khiển Web App tạo video.
   - Độ tin cậy: Cao (Bằng chứng trực tiếp từ Landing Page của chính tác giả).

2. **Kênh phát hành**:
   - Tác giả: Hương Muốn Nghỉ Hưu (Facebook ID: 100070056146166).
   - Nội dung kênh: Chuỗi video bán khoá học ứng dụng AI làm video cho các ngành hàng: Bất động sản, nội thất, xe máy, mỹ phẩm, thời trang.

### Tầng 2: Công nghệ thực tế (AI Flow & Virtual KOC)
3. **Google Flow / AI Flow Pro (Omni Flash Engine)**:
   - Bản chất: Nền tảng điều khiển chuyển động hình ảnh và ghép nhân vật vào bối cảnh dựa trên mô hình sinh video (Image-to-Video) và Motion Control.
   - Nhận dạng: Các chuyển động của mẫu trong video (ngồi sofa, ấn tay vào đệm) là kết quả của tính năng Motion Brush / Inpainting / Image-to-Video trên Flow App, sau đó ghép giọng đọc qua mô hình Lip-sync (như LivePortrait / Hedra).
   - Độ tin cậy: Cao.

4. **Kỹ thuật Virtual KOC bán hàng nội thất (In-situ Product Placement)**:
   - Bài toán kỹ thuật: Lấy 1 ảnh sản phẩm thật (ghế sofa, bàn ăn) -> Inpaint hoặc đặt nhân vật 3D/AI vào cùng không gian -> Giữ nguyên kết cấu sản phẩm thật (không làm biến dạng vân gỗ, đệm sofa) trong khi nhân vật cử động tương tác.
   - Độ tin cậy: Cao (Kiểm chứng qua các bài nghiên cứu về Virtual Try-on & In-situ KOC Placement).

### Tầng 3: Bằng chứng độc lập & Đối chiếu
5. **ComfyUI Inpainting + LivePortrait vs SaaS Flow**:
   - Bằng chứng đối chiếu: Các cộng đồng ComfyUI VN & quốc tế đều sử dụng pipeline: FLUX Inpainting (đặt nhân vật vào ảnh nội thất) -> LivePortrait hoặc Kling v1.5 Image-to-Video để nhân vật tương tác -> ElevenLabs / Edge-TTS lồng tiếng.
   - So với khoá học 899.000đ: Bản chất khoá học chỉ hướng dẫn dùng giao diện web Flow App thương mại có phí, che giấu sự phụ thuộc vào token và giới hạn của Flow App.
   - Độ tin cậy: Rất cao.

## Bảng tổng hợp nguồn

| URL | Ngày truy cập | Loại nguồn | Điều học được | Độ tin cậy | Chứng minh điều gì |
|---|---|---|---|---|---|
| `https://videoagentcis.netlify.app/` | 2026-11-04 | Trang chính thức tác giả | Giá khoá học 899k, lộ diện công cụ là "Flow", tặng kèm skill script | Rất cao | Bản chất là phễu bán khoá học dùng Flow App |
| `https://www.facebook.com/share/v/1M9eBwkWdL/` | 2026-11-04 | Video gốc | Nhịp cắt 1.96 cut/10s, âm lượng chuẩn -14 LUFS, khung hình 16:9 ngang | Rất cao | Đo lường metrics thực tế của video |
| `https://github.com/KwaiVGI/LivePortrait` | 2026-11-04 | Open-source Repo | Cơ chế điều khiển cử động môi và đầu của nhân vật ảo qua driving video | Rất cao | Kỹ thuật lip-sync mẫu ảo tương tác |
| `https://huggingface.co/black-forest-labs/FLUX.1-Fill-dev` | 2026-11-04 | Open-source Model | Khả năng inpaint nhân vật vào ảnh nội thất có sẵn mà giữ nguyên chi tiết sofa | Rất cao | Cơ chế tạo ảnh gốc ghép người vào sofa |
