# Requests & Dependencies Log

> [!NOTE]
> **LƯU Ý QUAN TRỌNG (SESSION E — 2026-11-04):**
> Các con số phân tích (12.4K views, 78.5% giữ chân, khung giờ vàng Thứ 2/Thứ 6, v.v.) bên dưới là **DỮ LIỆU MẪU (SEED DEMO)** sinh từ kịch bản kiểm thử, không phải số liệu đo lường thực tế từ người dùng thật. Không dùng các con số này để làm căn cứ quyết định sản phẩm.

Danh sách yêu cầu phụ thuộc giữa các session:

- **Session C (2026-11-04) -> 99_FINAL (Đề xuất cập nhật CONTINUITY.md):**
  - Vòng tự học xuất bản: Dữ liệu phân tích 30 ngày cho thấy khung giờ vàng hiệu quả nhất là **Thứ 2 (20:00-22:00)** và **Thứ 6 (19:00-21:00)** với median views đạt từ 12.4K đến 21.3K views.
  - Khuyến nghị mẫu Video cho Session A: Ưu tiên tiếp tục sản xuất các biến thể của `remake-v1` và `tiktok-sales-v1` do đạt tỷ lệ giữ chân cao nhất (78.5%).
  - Khuyến nghị Kịch bản cho Session B: Tập trung chủ đề review trực diện sản phẩm với Hook 3s giật gân, tránh các chủ đề lý thuyết đếm số thiếu kịch tính.
  - Trạng thái phân hệ Social: C1 (Data/Storage/API), C2 (UI Social Manager), C3 (Publishing Adapters & Scheduler), C4 (Analytics, Heatmap, Automation Rules, Learning Loop) đã hoàn thành 100%.

- **Session S (2026-11-04) -> Session E2:** Đổi nhãn tiếng Anh của các tab phải trong Studio sang tiếng Việt: Dự án / Nhân vật / Chat / Lịch đăng / Công việc / Node / Phím tắt (thay cho Project / Characters / Chat / Schedule / Jobs / Node / Shortcuts).


- **Session I5 (2026-11-07) -> chủ `core/engine/graph_runner.py` (G2/I0):** thêm nhánh chạy cho 6 node Toolbox (`bg_remove`, `word_captions`, `scene_cut`, `depth_layers`, `handdraw`, `voice_clone`). Hiện loại node lạ rơi vào `else` của `_execute_node_handler` và sinh ảnh mock "Generic execution". Thêm trước `else`:
  ```python
  elif node_type in TOOLBOX_NODE_TYPES:
      outputs, primary_artifact, cost_usd = await execute_toolbox_node(
          node_type, node.id, node.params, resolved_inputs, self.store, run_id, is_mock)
  ```
  với `from socnhotv.core.nodes.plugins.toolbox import TOOLBOX_NODE_TYPES, execute_toolbox_node`. Hàm trả đúng khuôn `(outputs, primary_artifact, cost)`, cost 0 (chạy cục bộ). Chi tiết và số đo: `status/I5.md`.
