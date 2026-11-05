# PROMPT DÁN CHO ANTIGRAVITY (Ag) — SESSION U: TAB TEMPLATE

Bạn là Ag, phụ trách **Session U**. Nhánh riêng `session-u/templates`.

**Bước 0 (bắt buộc):** đọc `ai/AGENTS.md`, `ai/rules/ui-rules.md`, `ai/rules/morphicons.md`, rồi **toàn bộ** `ai/plans/2026-11-roadmap/session-U-templates/U0_TEMPLATES_PLAN.md` (hiện trạng, hợp đồng template v2, danh mục, UI, nhiệm vụ U-00…U-12, giao thức báo test).

**Mục tiêu:** tab **Template** trong dashboard với đủ loại: hoạt hình, làm phim, TikTok review KOC, review sản phẩm, thay nhân vật giữ nội dung, hoạt hình kiểu Remotion (dựng bằng HyperFrames), video vẽ tay, cùng các loại phụ trong bảng mục 3. Mỗi template phải **ra MP4 thật**, không phải vỏ.

**Luật không thương lượng**
1. **Thật, không giả.** 8 template hiện có từng ra ảnh mock. Chạy thử từng cái ở U-00, ghi lỗi thật. Template chỉ `verified` khi có MP4 mẫu đo bằng ffprobe và người dùng đã duyệt.
2. **Trước khi báo xong bất kỳ việc nào có API/UI:** (a) `curl` vào server đang chạy phải thấy JSON thật; (b) mở bằng trình duyệt, chụp ảnh sáng + tối, đọc console không lỗi. Bài học Session T: UI Toolbox hiện 0 công cụ vì `middleware.ts` chặn `/api/*` (đã được sửa); lần trước Ag báo xong mà chưa mở UI xem.
3. **Cách ly:** chỉ ghi vào thư mục ở mục 8 của tài liệu. Không sửa `tool/src/socnhotv/**`, session F/K/T, `data/projects/**`. Cần ngoài phạm vi → `status/REQUESTS.md`.
4. **Giấy phép:** chỉ học/clone repo đã kiểm trong bảng; đọc LICENSE code và weights trước khi dùng. **Cấm chép mã AGPL** (MoneyPrinterV2), **không dùng Remotion làm engine** (giấy phép tuỳ chỉnh), tránh Wav2Lip/SadTalker/weights non-commercial. Số liệu repo chưa kiểm (whiteboard-animator, handanim) phải kiểm bằng GitHub API trước khi clone.
5. **Thay nhân vật (U-E):** máy không có GPU NVIDIA. Làm Tier A "overlay-replace" bằng `bg-remove` + HyperFrames và ghi rõ trong UI đây là ghép, không phải AI thay thật. Không giả Tier C.
6. **UI theo chuẩn dự án:** token theme sáng/tối trong `globals.css`, icon `@/components/ui/icons` + `MorphIcon` (cấm `lucide-react`), `Button/Card/AiLoading/confirm()` dùng chung, framer-motion tween 0.15–0.25s + `enterOnce`, tooltip cho nút icon, căn trái, mục thiếu điều kiện thì mờ + tooltip lý do, trống thì ô nét đứt gợi ý; không hai nút cùng chức năng. Chạy `npm run check:icons`; build với `NEXT_DIST_DIR=.next-build` (không build vào `.next` khi dev server cổng 3000 đang chạy).
7. **Không ngừng học:** mỗi template kèm thẻ kỹ thuật (đủ front-matter) và cập nhật `repo_watch.md` với số liệu GitHub đã kiểm.
8. **Làm TỪNG template một.** Xong cái nào: ghi `data/shared/toolbox/ready/U-XX.md`, đặt `READY_FOR_USER_TEST` trong `status/U.md`, báo người dùng một câu rồi **DỪNG chờ "OK U-XX"**.

**Thứ tự:** U-00 → U-01 → U-02 → U-03 → U-04 (review sản phẩm) → U-05 (KOC) → U-06 (vẽ tay) → U-07 (motion graphics) → U-08 → U-09 (nối Session F nếu đã sẵn sàng, nếu chưa đánh `blocked_by: F`) → U-10 → U-11 → U-12.

**Bắt đầu với U-00.**
