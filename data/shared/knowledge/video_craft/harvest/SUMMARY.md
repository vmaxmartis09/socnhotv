# Báo Cáo Tổng Hợp Nghiên Cứu Video Craft (Lũy Kế Batch 1 & 2: Seq 001 - 020)

- **Thời gian thực hiện**: 04/11/2026
- **Phạm vi**: 20 mục đầu tiên từ tin nhắn Messenger "Stored" (mới nhất → cũ hơn).
- **Trạng thái thực thi**: 100% hoàn tất 20/234 mục.

---

## 1. Thống Kê Tổng Quan Lũy Kế (20 Mục)

| Trạng thái | Số lượng | Tỷ lệ | Danh sách mục |
|---|---|---|---|
| **Học chuyên sâu (LEARN)** | **9** | 45% | Seq 003, 005, 006, 007, 008, 011, 012, 014, 015, 020 |
| **Học một phần & bóc tách phễu (LEARN-PARTIAL)** | **5** | 25% | Seq 001, 002, 009, 013, 016 |
| **Ghi nhận Sản phẩm / Thị trường (NOTE-PRODUCT)** | **2** | 10% | Seq 004 (Đầm NuNu), Seq 019 (Khung tranh đèn LED Luviare) |
| **Bỏ qua không phù hợp (SKIP-irrelevant)** | **3** | 15% | Seq 010 (An ninh mạng), Seq 017 (Game dev 2D), Seq 018 (Game sprite) |
| **Chờ kiểm tra / Lỗi truy cập** | **0** | 0% | Tỷ lệ xử lý thành công 100% |
| **Tổng cộng đã duyệt** | **20** | 100% | Đã ghi nhận đầy đủ vào `triage.csv`, `accepted.md`, `skipped.md`, `notes.md` |

---

## 2. Top 5 Bài Học Đắt Giá Áp Dụng Ngay Cho Hệ Thống Sóc Nhỏ TV / HyperFrames

### 1. Công Thức Phối Màu Tương Phản Địa Vị Cao (High-Status Color Contrast - Seq 020)
- **Hiệu quả thực tế**: Đạt 4.5M views và 182K likes trên Reels.
- **Công thức ngôn từ & thị giác**: So sánh 5 nhịp cặp màu: `[Màu A] with [Màu B] looks [Bình thường], but [Màu A] with [Màu C] looks [Luxurious / Classy / Expensive / Chic / Elegant]!`.
- **Ứng dụng**: Template `fashion-color-contrast-v1.html` cho KOC Neau & LyLy.

### 2. Quy Trình Thời Trang Xoay Người 360° Khóa Cố Định Giao Diện (Seq 015 & Seq 012)
- **Xoay người 360 độ (Seq 015)**: Nhân vật xoay quanh trục studio, giấu biến đổi outfit khi xoay lưng về camera để triệt tiêu lỗi glitch AI; Cột checklist sản phẩm bên trái khóa cố định 100% bằng HTML/CSS, chỉ lật thẻ 3D nhẹ khi nhân vật đổi look.
- **Đi bộ biến đổi trang phục (Seq 012)**: Mẫu bước đi liên tục (walk cycle), đổi đồ ngay nhịp chân tiếp đất kết hợp icon doodle sinh động.

### 3. Năm Trụ Cột Video Ngắn Bền Vững Của Duy Muối (Evergreen Shortform - Seq 014)
- **"Quay được hơn quay đẹp"**: Tốc độ sản xuất và sự đều đặn quan trọng hơn thiết bị máy cơ đắt tiền.
- **Mô hình doanh thu đi trước**: Mọi video ngắn phải phục vụ một phễu bán hàng hoặc IP rõ ràng.
- **Tâm thế sửa sai theo dữ liệu retention**: Theo dõi sát sao giây thứ 3 của biểu đồ giữ chân để tinh chỉnh Hook.

### 4. Chỉ Số Lựa Chọn Ngách "New Channel Win Rate" & Khung Kịch Bản Series 30 Ngày (Seq 011)
- **Nguyên lý thuật toán**: "YouTube tìm video cho người xem, chứ không tìm người xem cho video".
- **Chỉ số NCWR**: Đo tỷ lệ kênh mới (<12 tháng) chiến thắng trong ngách. Ngách có NCWR > 35% là cơ hội vàng thâm nhập.
- **Series Hook**: Định dạng chuỗi "Hành trình 30 ngày..." giúp tăng tỷ lệ xem tiếp (binge-watching) và giữ chân khán giả trung thành.

### 5. Kỹ Thuật Đăng Bài Né Bóp Tương Tác Bằng First-Comment Link (Seq 013)
- Gắn link ngoài vào caption bài viết Facebook làm giảm 60-80% lượng hiển thị tự nhiên.
- Chiến lược chuẩn hóa: Đăng bài và video sạch; Sau 10 giây, hệ thống tự động đăng bình luận đầu tiên (First Comment) chứa link mua hàng/landing page và ghim lên đầu. Đã chuyển giao vào `requests_for_C.md`.

---

## 3. Các Mô Hình Phễu "Lùa Gà" Thường Gặp Cần Cảnh Giác

1. **Phễu "Agent 1 câu lệnh bán triệu đơn" (Seq 001)**: Gán mác AI Agent cho các thao tác ghép ảnh đơn giản trên Google Flow để bán khóa học Netlify 899k.
2. **Phễu "Zoom miễn phí buổi tối" (Seq 002)**: Chia sẻ bề nổi về InstantID/PuLID để chốt khóa coaching chục triệu đồng.
3. **Phễu "50K/tháng có KOC vô tận" (Seq 003)**: Web app bọc ngoài IDM-VTON mã nguồn mở nhưng giật tít đánh lừa người dùng.
4. **Phễu "Comment 333 nhận phần mềm video AI vô hạn" (Seq 009)**: Lấy bản ComfyUI Desktop portable tiếng Trung miễn phí, kêu gọi comment xin link để kéo leads vào nhóm kín.
5. **Phễu "Tool tự động đăng 16.000 bài/ngày" (Seq 013)**: Quảng cáo phần mềm spam dàn Fanpage rác số lượng lớn, tiềm ẩn nguy cơ bị quét checkpoint hàng loạt nếu không có cơ chế quản lý danh tính chuẩn.

---

## 4. Danh Mục Thẻ Kỹ Thuật Đã Xây Dựng (Techniques Library)
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
11. `techniques/niche-opportunity-index.md`
12. `techniques/walking-outfit-transition.md`
13. `techniques/first-comment-link-routing.md`
14. `techniques/evergreen-shortform-foundations.md`
15. `techniques/360-turntable-catalog.md`
16. `techniques/3-layer-knowledge-retention.md`
17. `techniques/high-status-color-contrast.md`
