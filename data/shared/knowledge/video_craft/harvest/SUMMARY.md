# Báo Cáo Tổng Hợp Nghiên Cứu Video Craft (Batch 1: Seq 001 - 010)

- **Thời gian thực hiện**: 04/11/2026
- **Phạm vi**: 10 mục đầu tiên từ tin nhắn Messenger "Stored" (mới nhất → cũ hơn).
- **Trạng thái thực thi**: 100% hoàn tất Batch 1.

---

## 1. Thống Kê Tổng Quan Đợt 1 (10 Mục)

| Trạng thái | Số lượng | Tỷ lệ | Diễn giải |
|---|---|---|---|
| **Học chuyên sâu (LEARN / LEARN-PARTIAL)** | **7** | 70% | Seq 001, 002, 003, 005, 006, 007, 008, 009 (Phân tích đầy đủ G1→G6, bóc tách kỹ thuật & phễu) |
| **Ghi nhận Sản phẩm / Thị trường (NOTE-PRODUCT)** | **1** | 10% | Seq 004 (Đầm hoa nhí NEAU NuNu Dress trên TikTok Shop) |
| **Bỏ qua không phù hợp (SKIP-irrelevant)** | **1** | 10% | Seq 010 (Video tiếng Ả Rập về xe đạp thể thao / cycling) |
| **Tổng cộng đã duyệt** | **10** | 100% | Đã ghi nhận đầy đủ vào `triage.csv`, `accepted.md`, `skipped.md`, `notes.md` |

---

## 2. Top 5 Bài Học Áp Dụng Ngay Cho Hệ Thống Sóc Nhỏ TV / HyperFrames

### 1. Template Chia Đôi Màn Hình (Split-Canvas Lookbook Layout - Seq 005)
- **Tỷ lệ vàng 45:55**: Cột trái (45%) chạy video người mẫu tạo dáng bước đi liên tục; Cột phải (55%) hiển thị thẻ sticker cắt dán (sticker cutout) kèm nét vẽ phác thảo (Doodle SVG) và thông tin outfit.
- **Tính năng HyperFrames**: Đã đề xuất tạo template `lookbook-split-canvas-v1.html` trong `requests_for_A.md`.

### 2. Chuỗi Cắt Cảnh Dồn Dập Tạo Niềm Tin (Rapid Montage Proof - Seq 002)
- Cắt dồn dập 8-10 bối cảnh khác nhau của cùng 1 nhân vật KOC AI với nhịp cắt siêu tốc **0.8 giây/shot** trong 5 giây đầu.
- Giúp đập tan nghi ngờ của người xem về sự nhất quán của nhân vật (Character Consistency).

### 3. Ghép Nối 2 Phân Đoạn Video AI Mượt Mà (Dual-Node Video Stitching - Seq 007)
- Khắc phục giới hạn 5s-10s của các mô hình video AI (Kling 1.5, Minimax, Runway Gen-3): Tạo 2 clip liên tiếp, lấy **Last Frame của Clip 1 làm First Frame của Clip 2**.
- Tự động hóa qua script ghép nối FFmpeg mượt mà không bị giật khung hình.

### 4. Thay Thế Toàn Diện 4 Lớp Trong Video (Video-to-Video Replacement - Seq 008)
- Thay vì dựng lại video từ đầu, lấy 1 video TikTok gốc hoạt động hiệu quả và thay thế cùng lúc 4 lớp: Sản phẩm (VTON), Bối cảnh (Background), Diễn viên (Face/Body Swap), và Ngôn ngữ/Khẩu hình môi (Lip-Sync Translation).
- Tích hợp chuẩn hoá vào workflow `motion-mimic` của dự án.

### 5. Đóng Gói Preset Camera Motion Ảo (Virtual Camera Choreography - Seq 006)
- Không dùng prompt mô tả chuyển động bằng chữ mơ hồ, chuẩn hóa thành 5 chuyển động camera có tọa độ rõ ràng: Pan (Quét ngang), Push-in (Tiến sát), Orbit (Xoay quanh), Pedestal (Nâng góc), Tracking (Bám đuổi).

---

## 3. Các Mô Hình Phễu "Lùa Gà" Thường Gặp Cần Cảnh Giác

1. **Phễu "Khóa học 899k / Agent 1 câu lệnh" (Seq 001)**: Thực chất là dùng giao diện web Flow cơ bản của Google/Higgsfield để ghép ảnh KOC vào phòng nội thất, không có "Agent tự động bán hàng" nào thực sự.
2. **Phễu "Zoom miễn phí buổi tối" (Seq 002)**: Lấy cớ chia sẻ kỹ thuật nhân vật nhất quán để bán gói hội viên coaching chục triệu đồng.
3. **Phễu "50k/tháng có KOC vô tận" (Seq 003)**: Thực chất chỉ là website bọc ngoài các mã nguồn mở IDM-VTON / OOTDiffusion, thu phí theo lượt render.
4. **Phễu "Comment 333 nhận phần mềm AI vô tận miễn phí" (Seq 009)**: Lấy bản ComfyUI Desktop portable mã nguồn mở từ cộng đồng Trung Quốc, thêm tiếng Việt cơ bản rồi kêu gọi comment để kéo tương tác và leads vào nhóm Zalo kín.

---

## 4. Tài Liệu Kỹ Thuật Đã Tạo (Techniques Library)
1. `techniques/confession-hook.md`
2. `techniques/in-situ-koc-placement.md`
3. `techniques/rapid-montage-proof.md`
4. `techniques/frictionless-remix-workflow.md`
5. `techniques/split-canvas-lookbook.md`
6. `techniques/sticker-cutout-doodle.md`
7. `techniques/camera-motion-choreography.md`
8. `techniques/dual-node-video-stitching.md`
9. `techniques/video-element-replacement.md`
10. `techniques/local-comfyui-pipeline.md`
