# PROMPT DÁN CHO ANTIGRAVITY (Ag) — SESSION T: TOOLBOX

Bạn là Ag, phụ trách **Session T**. Làm việc trong repo SocNhoTV, nhánh riêng `session-t/toolbox`.

**Bước 0 (bắt buộc, trước khi làm gì):** đọc theo thứ tự
1. `ai/AGENTS.md` và `ai/rules/ui-rules.md`, `ai/rules/morphicons.md`
2. `ai/plans/2026-11-roadmap/session-T-toolbox/T0_TOOLBOX_PROMPT.md` (tài liệu chính: thiết kế, nhiệm vụ T-00…T-13, bảng tool đã kiểm, giao thức báo test)

**Mục tiêu:** tạo `tool/toolbox/` chứa các tool video **miễn phí, nhẹ, chạy CPU, cài độc lập**, cùng kho dùng chung trong `data/shared/` (voice_vault, assets/cutouts, models). Mỗi tool là một tiến trình con có venv riêng và hợp đồng `toolbox run <id> --in in.json --out out.json`.

**Luật không thương lượng**
1. **Cách ly:** chỉ ghi vào các thư mục được liệt kê ở mục 1 của T0_TOOLBOX_PROMPT. Không sửa `tool/src/socnhotv/**`, session F/K, `data/projects/**`, và không sửa file có sẵn của dashboard. Cần thay đổi ngoài phạm vi → ghi `status/REQUESTS.md`, đừng tự làm.
2. **Chỉ dùng tool trong bảng mục 4** (đã kiểm giấy phép repo). Trước khi tải, đọc LICENSE của code **và weights**, ghi vào `tool.json`. Weights non-commercial: không đặt làm mặc định. Không dùng tool trong danh sách "Bỏ qua".
3. **Thật, không giả:** tool lỗi thì trả lỗi thật (exit code theo hợp đồng). Cấm file mock, cấm báo pass khi chưa có file đầu ra đo được.
4. **UI (T-13) phải theo chuẩn dự án:** token theme trong `globals.css` (sáng/tối), icon chỉ từ `@/components/ui/icons` + `MorphIcon` (cấm `lucide-react`), `Button/Card/AiLoading/confirm()` dùng chung, animation framer-motion tween 0.15–0.25s, `enterOnce`, tooltip cho nút icon, căn trái, trạng thái trống theo quy tắc 13/20/22. Chạy `npm run check:icons` và build với `NEXT_DIST_DIR=.next-build`.
5. **Không cài toàn cục**, không sửa PATH hệ thống, không commit weights/venv/mẫu giọng.
6. **Làm TỪNG tool một.** Xong tool nào: ghi `data/shared/toolbox/ready/T-XX.md` (lệnh chạy thử 1 dòng + đường dẫn kết quả + số đo + giới hạn), đặt `READY_FOR_USER_TEST` trong `status/T.md`, **báo người dùng 1 câu rồi DỪNG chờ**. Chỉ làm tool kế khi người dùng trả "OK T-XX".

**Thứ tự:** T-00 → T-01 → T-02 → T-03 → T-04 + T-08 (hạ tầng, không cần chờ) → T-05 tách nền → T-07 phiên âm → T-06 clone giọng → T-11 cắt cảnh → T-10 độ sâu → T-09 (tuỳ chọn) → T-13 giao diện → T-12 báo cáo cuối.

**Bắt đầu ngay với T-00**, rồi tiếp tục theo thứ tự. Báo cáo cuối vào `ai/plans/2026-11-roadmap/status/T.md`.
