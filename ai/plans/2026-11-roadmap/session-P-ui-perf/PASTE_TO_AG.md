# PROMPT DÁN CHO ANTIGRAVITY (Ag) — SESSION P: TỐI ƯU HIỆU NĂNG & UI

Bạn là Ag, phụ trách **Session P**. Làm TRỰC TIẾP trên nhánh `main` (checkout `D:\socnhotv`), không tạo nhánh/worktree.

**Bước 0 (bắt buộc):** đọc `ai/AGENTS.md`, `ai/rules/ui-rules.md`, `ai/rules/morphicons.md`, rồi **toàn bộ** `ai/plans/2026-11-roadmap/session-P-ui-perf/P0_UI_PERF_PLAN.md` (phát hiện ban đầu P1–P13, giao thức đo, nhiệm vụ P-00…P-12).

**Mục tiêu:** làm UI dashboard nhẹ, mượt, co giãn tốt mọi cỡ màn hình và đúng chuẩn style dự án; mọi cải thiện phải có số đo trước/sau.

**Luật không thương lượng**
1. **KHÔNG BAO GIỜ chạy `git checkout`** (mọi dạng, kể cả `git checkout -- file`). Hoàn tác file của chính mình bằng cách sửa lại hoặc `git restore <file mình đã sửa>`.
2. **Main đang có việc dở của người khác** (`graph.json`, `NodeBody.tsx`, `StudioNode.tsx`, dữ liệu kho…). Chỉ `git add` đúng file bạn sửa, **không `git add -A`**. Không ghi đè/revert phần của người khác.
3. **Xong toàn bộ thì push luôn, không hỏi lại:** `git pull --rebase origin main` rồi `git push origin main`. Trong lúc làm, commit nhỏ theo mã (`perf(ui): P-03 …`), mỗi commit phải qua `tsc --noEmit` + build.
4. **Đo trước, sửa sau.** Làm P-01 (baseline) trước mọi thay đổi. Thay đổi nào không cải thiện số đo thì bỏ. Cấm báo "nhanh hơn/responsive" khi chưa có số đo hoặc ảnh ở 375/768/1024/1440/1920px.
5. **Không đổi hành vi nghiệp vụ, không đổi luồng người dùng nhìn thấy** (trừ sửa vỡ bố cục và thay `alert()/confirm()` gốc bằng `confirm()` dùng chung). Không thêm thư viện UI/animation mới. Không chạm backend `tool/src/socnhotv/**`, session F/T/U, `data/projects/**`.
6. **Không format hàng loạt**, không viết lại logic khi tách file (chỉ di chuyển nguyên văn). Tránh nhiễu CRLF/LF.
7. **Chuẩn style bắt buộc** (`ui-rules.md`): tween 0.15–0.25s `[0.22,1,0.36,1]`, `enterOnce`, `scroll-quiet`, icon qua `@/components/ui/icons` (cấm `lucide-react`), `overflow-clip` cho UI nổi, tooltip cho nút icon, token màu (không hard-code), hỗ trợ sáng/tối.
8. Build kiểm bằng `NEXT_DIST_DIR=.next-build npx next build` và chạy `next start` ở **cổng khác 3000** (đang có dev server); chạy `npm run check:icons`.
9. **Thật, không giả:** mục nào không làm được thì ghi `blocked` + lý do trong `status/P.md`, không giấu.

**Thứ tự:** P-00 (quét & lập bảng phát hiện) → P-01 (baseline) → P-02 (selector store, 48 chỗ) → P-03 (memo canvas) → P-04 (cô lập timer/polling) → P-05 (AbortController, chống race) → P-06 (tách bundle, kiểm icons) → P-07 (ảnh lazy/thumbnail) → P-08 (key, ảo hoá danh sách) → P-09 (alert/confirm, màu cứng, overflow, aria) → P-10 (responsive 375–1920) → P-11 (script `check:style` chống thoái lui) → P-12 (đo After, bảng Trước/Sau, cập nhật rules, **push main**).

**Báo cáo cuối** vào `ai/plans/2026-11-roadmap/status/P.md`: bảng phát hiện, từng mã (done/partial/blocked), bảng **Trước/Sau** bằng số (First Load JS, số render canvas, INP, request bị huỷ, byte ảnh lúc đầu, số vi phạm style), đường dẫn ảnh responsive, việc còn lại.

**Bắt đầu ngay với P-00.**
