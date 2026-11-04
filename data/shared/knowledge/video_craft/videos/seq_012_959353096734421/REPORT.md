# Báo Cáo Nghiên Cứu Video: Seq 012 (Walking Outfit Transition)

- **Mã mục**: `seq_012_959353096734421`
- **Kênh/Tác giả**: Xuân Linh
- **Tựa đề**: Quy trình 23: Thời trang đi bộ biến đổi trang phục kết hợp icon sinh động
- **Thời lượng**: 26.12s
- **Đánh giá Triage**: `LEARN` (Xuất sắc — Đây là khuôn mẫu trực quan lý tưởng cho video KOC thời trang LyLy/Neau dựng bằng HyperFrames).

---

## 1. Tóm Tắt & Phân Tích Kỹ Thuật Cốt Lõi
1. **Liên Tục Về Chuyển Động (Continuous Motion Preservation)**:
   - Thay vì các video lookbook thông thường cắt cụt lủn giữa các ảnh tĩnh đứng yên, video duy trì một chu kỳ bước đi (walk cycle) liền mạch từ đầu tới cuối.
   - Nhờ sự liên tục này, mắt người xem bị cuốn theo nhịp chân của người mẫu, tạo cảm giác thôi miên thị giác (visual hypnotic flow).
2. **Biến Đổi Trang Phục Theo Nhịp Chân (In-stride Morphing)**:
   - Tại đúng thời điểm bàn chân tiếp đất (mỗi 6.5s), trang phục biến đổi sang set đồ mới với hiệu ứng lóa sáng nhẹ và sound effect vụt gió (whoosh).
3. **Lớp Đồ Họa Thông Minh (Smart Motion Overlay)**:
   - Các icon mô tả phong cách (Parisian Chic, Minimalist, Y2K) và giá tiền / mã SKU xuất hiện đồng bộ theo nhịp bước.

---

## 2. Ứng Dụng Thiết Thực Cho Dự Án `socnhotv`
- **Tạo Template HyperFrames**: Đề xuất tạo template mới `walking-outfit-transition-v1.html` cho Session A.
- **Workflow tự động hóa**:
  - Dùng 1 video loop bước đi chuẩn của LyLy / Neau.
  - Tự động thay đổi 3 bộ trang phục theo kịch bản bán hàng.
  - Lớp phủ chữ và nhãn dán SVG chạy bằng GSAP cực kỳ nhẹ và sắc nét ở độ phân giải 1080x1920.
- **Thẻ Kỹ Thuật Tương Ứng**: Xem chi tiết tại [walking-outfit-transition.md](../../techniques/walking-outfit-transition.md).
