# Sources & Technical Verification: Seq N02

- **Video URL**: `https://www.facebook.com/share/v/1FfiCWGrVH/`
- **Canonical ID**: `28160631690277676`
- **Tác giả**: Tài Xài Tech
- **Mô hình kiến trúc**: Multi-Agent Video Assembly (Hierarchical Agent Pattern) + Google Gemini Flash API.

---

## 1. Bản Chất Kỹ Thuật Đã Xác Thực
1. **Mô Hình Đa Tác Tử Phân Cấp (Hierarchical Multi-Agent Pattern)**:
   - **Leader Agent (Orchestrator)**: Nhận video thoại chính (A-Roll) từ người dùng, gọi Whisper để sinh timestamp từng câu thoại.
   - **B-Roll Selection Sub-Agent**: Đọc thư mục asset B-roll, phân tích ngữ nghĩa câu thoại và tự động gắp B-roll tương ứng thả vào timeline.
   - **Hook Specialist Sub-Agent**: Tập trung tối ưu 3-5 giây đầu của video để đảm bảo tỷ lệ giữ chân (Retention).
   - **QA Inspector Sub-Agent**: Rà soát thành phẩm, kiểm tra lỗi lệch âm thanh, tràn chữ safe zone trước khi xuất bản.
2. **Đối Chiếu Trực Tiếp Với Dự Án `socnhotv`**:
   - Đây chính là mô hình mà Session A (Video Engine), Session B (Intelligence & Sourcing) và Session C (Publishing) đang vận hành song song!
