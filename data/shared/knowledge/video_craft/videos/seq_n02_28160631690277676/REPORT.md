# Báo Cáo Nghiên Cứu Video: Seq N02 (Multi-Agent B-Roll Orchestration)

- **Mã mục**: `seq_n02_28160631690277676`
- **Kênh/Tác giả**: Tài Xài Tech
- **Tựa đề**: App AI tự cắt ghép video bằng Sub-Agents (A-Roll & B-Roll)
- **Thời lượng**: 02:11 (131.9s)
- **Đánh giá Triage**: `LEARN` (Cực kỳ giá trị — Chứng minh kiến trúc Multi-Agent phân cấp là xu hướng chuẩn mực nhất hiện nay cho video AI automation).

---

## 1. Tóm Tắt & Phân Tích Kỹ Thuật
1. **Phân Rã Trách Nhiệm Chuyên Biệt (Separation of Concerns via Sub-Agents)**:
   - Không bắt 1 LLM prompt duy nhất làm từ A đến Z.
   - Chia nhỏ thành các Sub-Agents độc lập: Agent trích xuất câu thoại, Agent ghép B-roll, Agent làm Hook, và Agent QA kiểm duyệt chất lượng.
2. **Chiến Lược Tối Ưu Chi Phí Token (Model Tiering Strategy)**:
   - Tác giả sử dụng Gemini 1.5 Flash cho tác vụ phân tích B-roll số lượng lớn nhờ chi phí cực rẻ và cửa sổ ngữ cảnh (Context Window) lên tới 1M tokens.

---

## 2. Ứng Dụng Cho Hệ Sinh Thái `socnhotv`
- Khẳng định tính đúng đắn tuyệt đối của mô hình phân công hiện tại: Session A (Video/HyperFrames), Session B (Dữ liệu/Kịch bản/KOC), Session C (Xuất bản mạng xã hội) và Session D (Nghiên cứu/Phân tích).
- Thẻ Kỹ Thuật: [multi-agent-broll-orchestration.md](../../techniques/multi-agent-broll-orchestration.md).
