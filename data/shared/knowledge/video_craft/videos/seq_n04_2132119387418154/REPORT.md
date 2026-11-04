# Phân Tích Chuyên Sâu: Seq N04 - Dự Đoán Giữ Chân Người Xem Bằng AI (Hong Phuong)

## 1. Tổng Quan
- **ID**: `seq_n04_2132119387418154`
- **Kênh**: Hong Phuong
- **Thời lượng**: 70.67s (9:16)
- **Chủ đề**: Tiền kiểm tra (pre-publish testing) các biến thể Hook bằng mô hình dự đoán độ chú ý (Virality Predictor + LLM).

---

## 2. 3 Tín Hiệu Đánh Giá Hook Trước Khi Đăng
Thay vì "đoán mò" hoặc đăng video lên rồi mới biết flop:
1. **Virality Score (0 - 100)**: Chỉ số tổng hợp đánh giá sức bật lan truyền của 3 giây đầu tiên.
2. **Second-by-Second Attention Curve**: Biểu đồ hiển thị chính xác giây thứ mấy (giây 1.2s, 2.5s...) người xem có nguy cơ lướt đi (drop-off point) do nhịp nói chậm, từ ngữ thừa, hoặc visual tĩnh.
3. **Brain Activation Heatmap**: Mô phỏng mức độ kích hoạt các vùng thần kinh thính giác/thị giác để đảm bảo hook có đủ xung động cảm xúc (novelty stimulus).

---

## 3. Quy Trình Vòng Lặp Phản Hồi (Closed-Loop Feedback)
1. Tạo 3-5 biến thể hook (A/B/C/D) cho cùng 1 nội dung.
2. Nạp vào engine dự đoán.
3. Chuyển biểu đồ phân tích sang LLM (Claude) kèm prompt: *"Tại giây 2.1s có độ rơi chú ý 15%, hãy đề xuất thay thế visual hoặc cắt gọn từ ngữ để giữ đường cong phẳng trên 85%"*.
4. Cắt gọt lại hook trước khi xuất bản master.

---

## 4. Ứng Dụng Vào Sóc Nhỏ TV
- Tích hợp vào quy trình biên tập tự động của `socnhotv`:
  - Trước khi render video hoàn chỉnh, sinh 3 biến thể hook 3s đầu cho Sóc Nhỏ (Bi).
  - Dùng LLM đánh giá độ nén thông tin (WPM, cognitive load, visual contrast) để chọn hook tối ưu.
- Đóng gói thành kỹ thuật: `techniques/pre-publish-hook-retention-prediction.md`.
