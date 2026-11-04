# Tài liệu & Nguồn truy vết (Sources & Verification) — Seq 002

Video ID: `1805816287415896` | Tiêu đề: "THAM GIA LỚP ZOOM MIỄN PHÍ TẠI ĐÂY" | Kênh: AI Scale Up

## Chuỗi truy vết 3 tầng (3-Tier Investigation)

### Tầng 1: Dấu vết từ Kênh & Video
1. **Phễu chuyển đổi (Conversion Funnel)**:
   - Chiến lược: Sử dụng ManyChat trigger `"Comment AI"` -> Bot tự động gửi tin nhắn Messenger chứa link vào phòng Zoom / nhóm Zalo phễu.
   - Khóa học đề cập: *"AI Superpower"*, gắn mác "học phí hàng chục triệu ngoài thị trường, nay chia sẻ miễn phí" -> Mô hình Webinar Funnel chuẩn của các khóa học MMO/AI tại Việt Nam.
   - Độ tin cậy: Rất cao (Bằng chứng lời thoại và văn bản hiển thị từ chính video).

### Tầng 2: Công nghệ cốt lõi — Character Consistency (Nhất quán nhân vật)
2. **PuLID & InstantID cho FLUX / SDXL**:
   - Khái niệm: Các mô hình bảo tồn nhận diện khuôn mặt không cần huấn luyện lại (Tuning-free identity customization).
   - Cơ chế: Trích xuất embedding 512 chiều từ InsightFace của ảnh gốc, sau đó tiêm (inject) vào các lớp cross-attention của diffusion model (FLUX.1 hoặc SDXL).
   - Bằng chứng tài liệu:
     - Paper: *PuLID: Pure and Lightning ID Customization via Contrastive Alignment* (2024).
     - Repo: `https://github.com/ToTheBeginning/PuLID`
   - Độ tin cậy: Rất cao.

3. **Huấn luyện Custom LoRA (Flux LoRA)**:
   - Giải pháp công nghiệp: Khi cần nhân vật KOC AI hoạt động lâu dài (như Neau hay Bi của SocNhoTV), giải pháp tốt nhất là train LoRA (15–30 ảnh chân dung chất lượng cao) trên base model FLUX.1-dev. Độ nhận diện đạt >95% ở mọi góc xoay 360 độ và biểu cảm.
   - Độ tin cậy: Rất cao.

### Tầng 3: Khả năng thay thế & Dựng lại bằng Gobi Ecosystem
4. **Đối chiếu với Master DNA của dự án SocNhoTV**:
   - Dự án đã có quy chuẩn tại `characters/soc_nho/` (master DNA ảnh) và `characters/gobi_models/` (LyLy, Neau).
   - Thay vì phụ thuộc vào khóa học Zoom hoặc công cụ trả phí bên ngoài, toàn bộ quy trình này được giải quyết bằng local workflow hoặc API model với chi phí cực thấp (~0.01$/ảnh).

## Bảng tổng hợp nguồn

| URL / Định danh | Ngày truy cập | Loại nguồn | Điều học được | Độ tin cậy | Chứng minh điều gì |
|---|---|---|---|---|---|
| `https://www.facebook.com/share/r/1FHS4q8Kdq/` | 2026-11-04 | Video gốc | Nhịp cắt 3.85 cut/10s, montage dồn dập 0.8s/ảnh | Rất cao | Thước đo kỹ thuật dựng video giữ chân |
| `https://github.com/ToTheBeginning/PuLID` | 2026-11-04 | Open-source SOTA | Cơ chế giữ nguyên khuôn mặt qua zero-shot ID conditioning | Rất cao | Công nghệ thực tế tạo ảnh nhất quán |
| `https://github.com/InstantID/InstantID` | 2026-11-04 | Nghiên cứu AI | Kỹ thuật kết hợp ControlNet keypoints và identity embeddings | Rất cao | Độ ổn định khuôn mặt qua nhiều góc nghiêng |
| `https://manychat.com/` | 2026-11-04 | Tài liệu MarTech | Cơ chế bắt keyword "AI" trong comment để tự gửi kịch bản phễu | Rất cao | Bóc tách chiêu trò lùa gà phễu comment |
