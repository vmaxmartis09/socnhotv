# Sources & Technical Verification: Seq 009

- **Video URL**: `https://www.facebook.com/share/v/19rAD6bSJy/`
- **Canonical ID**: `2140905429860884`
- **Tác giả chia sẻ**: Jolie Mê Xem Phim
- **Nguồn gốc nội dung gốc**: Cộng đồng ComfyUI mã nguồn mở Trung Quốc (được lồng tiếng Việt / voiceover).

---

## 1. Bản Chất Kỹ Thuật Đã Xác Thực
- **Phần mềm thực tế**: ComfyUI Desktop / Portable version (thường là bản đóng gói sẵn của秋葉 - Akiba hoặc các cộng đồng SD/ComfyUI Trung Quốc).
- **Cơ chế hoạt động**:
  1. Đóng gói sẵn môi trường Python nhúng độc lập (`python_embeded`), Git, Torch với CUDA runtime để người dùng không cần cài đặt dòng lệnh phức tạp.
  2. Tích hợp sẵn `ComfyUI-Manager` và bảng điều khiển `ComfyUI-Workspace-Manager` (quản lý cây thư mục workflow bên trái).
  3. Cài sẵn tiện ích mở rộng dịch đa ngôn ngữ giao diện (ComfyUI-Translation) và thanh theo dõi tài nguyên phần cứng (ComfyUI-System-Monitor: CPU/RAM/VRAM meter).

---

## 2. Bóc Tách Phễu Tương Tác (Scam / Lead Funnel Breakdown)
- **Mồi câu**: "Tạo video AI không giới hạn số lần, hoàn toàn miễn phí, không cần kết nối mạng hay trả phí theo tháng".
- **Hành động chuyển đổi**: "Bạn nào hứng thú thì điểm danh nhé" / "Comment 333 / chấm để nhận link tải".
- **Động cơ thực tế**: Kéo tương tác khổng lồ trên Facebook (hơn 1.4k comments, 3.2k likes), từ đó tự động gửi tin nhắn chatbot dẫn người dùng về nhóm Zalo/Telegram hoặc bán khóa học nâng cao/bán ổ cứng chứa model weights.
- **Giá trị học hỏi thực tế cho dự án**:
  - Không cần tải bản mod tiếng Trung hay tham gia nhóm.
  - Dự án `socnhotv` có thể tự tích hợp logic chạy node cục bộ tương đương hoặc sử dụng trực tiếp engine nội bộ `HyperFrames` + API pipeline tự động mà không phụ thuộc vào các gói cài đặt nặng nề trôi nổi trên mạng.
