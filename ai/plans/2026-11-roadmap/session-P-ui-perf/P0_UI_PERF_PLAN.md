# SESSION P — TỐI ƯU HIỆU NĂNG, RESPONSIVE & TUÂN THỦ STYLE CHO DASHBOARD
# Mã nhiệm vụ: P-00 … P-12. Lập: 2026-11-05. Giao cho Antigravity (Ag).

## 0. Mục tiêu
UI **nhẹ, mượt, co giãn tốt, đúng chuẩn style**. Mọi kết luận "đã nhanh hơn" phải kèm **số đo trước/sau** (không tin cảm giác). Không đổi hành vi nghiệp vụ.

## 1. Quy tắc làm việc (bắt buộc)
1. **Làm trực tiếp trên `main`** (checkout `D:\socnhotv`). Không tạo nhánh/worktree.
2. **KHÔNG BAO GIỜ dùng `git checkout`** (mọi dạng, kể cả `git checkout -- file`). Hoàn tác file của chính mình bằng cách sửa lại, hoặc `git restore <file đã tự sửa>`.
3. **Xong toàn bộ thì push luôn, không hỏi lại**: `git pull --rebase origin main` rồi `git push origin main`. Trong lúc làm, commit nhỏ theo mã (`perf(ui): P-03 …`), mỗi commit phải qua `tsc --noEmit` + build.
4. **Main đang có việc dở của người khác** (file `graph.json`, `NodeBody.tsx`, `StudioNode.tsx`, dữ liệu kho…). Chỉ `git add` đúng file mình sửa; **không** `git add -A`. Nếu file bạn cần sửa đang có thay đổi chưa commit của người khác: sửa chồng lên cẩn thận, không ghi đè, không revert phần của họ.
5. **Không chạm backend** (`tool/src/socnhotv/**`), session F/T/U, `data/projects/**`.
6. **Không format hàng loạt** (tránh nhiễu CRLF/LF, diff khổng lồ). Chỉ sửa dòng cần thiết. Tách file = di chuyển nguyên văn, không viết lại logic.
7. Build kiểm bằng `NEXT_DIST_DIR=.next-build npx next build` (KHÔNG build vào `.next` khi dev server cổng 3000 đang chạy). Chạy `npm run check:icons`.
8. Tuân thủ `ai/rules/ui-rules.md`: tween 0.15–0.25s ease-out `[0.22,1,0.36,1]`, `enterOnce`, `scroll-quiet`, icon qua `@/components/ui/icons`, `overflow-clip` cho UI nổi, tooltip cho nút icon, `confirm()` dùng chung.
9. **Thật, không giả:** không báo "nhanh hơn" khi chưa đo; không báo "responsive" khi chưa mở ở các cỡ màn hình; lỗi thì ghi lỗi.

## 2. Điểm xuất phát (quét tĩnh `tool/dashboard` ngày 2026-11-05; Ag phải xác minh bằng đo thật)
| # | Dấu hiệu | Số liệu quét | Nghi vấn / cần đo |
|---|---|---|---|
| P1 | File khổng lồ | `StudioCanvas.tsx` 1940 dòng; `PublishCenterModal.tsx` 1187; `ProjectTab.tsx` 1186; `CreateVideoModal.tsx` 1126; `NodeInputs.tsx` 1109; `canvasSlice.ts` 863; `StudioNode.tsx` 827; `ToolboxPanel.tsx` 762 | Một thay đổi state nhỏ render lại cả khối; khó memo; bundle lớn |
| P2 | Đăng ký trọn store | `useStudioStore()` không selector: **48 chỗ** (`NodeInputs.tsx:61,190,511,748,818,954,1048`, `NodeBody.tsx:301`…) | Mọi ô nhập/node render lại khi bất kỳ phần nào của store đổi (kéo node, tiến độ chạy…) |
| P3 | Hầu như không memo | `React.memo` chỉ **1** chỗ trong `components/` | Canvas nhiều node bị render thừa |
| P4 | Không tách bundle | `next/dynamic`/`React.lazy`: **0**. Modal lớn (Publish, CreateVideo), Toolbox, Social Hub nạp ngay | First Load JS nặng |
| P5 | Nạp icon | `components/ui/icons.ts`: `import * as lucide from "lucide"` + 113 `createMorphIcon` | Có thể kéo cả thư viện vào bundle; kiểm tra tree-shaking bằng bundle analyzer |
| P6 | Ảnh | `<img>` **45** chỗ, chỉ **12** có `loading="lazy"`; `images.unoptimized: true` | Gallery nhân vật/kho/cutout tải ảnh lớn cùng lúc; cần `decoding="async"`, kích thước, thumbnail |
| P7 | Timer render cấp canvas | `StudioCanvas.tsx:294` `setInterval` 1s cập nhật state `activeRunState` ở cấp canvas khi chạy; `JobsCostTab.tsx:71` polling 3s | Render lại cả canvas mỗi giây; polling cả khi tab/panel ẩn |
| P8 | Fetch không huỷ | `AbortController`: **0** trong `components/`+`lib/`, trong khi có **115** `useEffect` | Race khi đổi dự án/tab nhanh (dữ liệu dự án cũ ghi đè dự án mới), rò request |
| P9 | `key` bằng index | `key={i}`/`idx`/`index`: **20** chỗ | Danh sách đổi thứ tự/xoá bị remount sai, mất state ô nhập |
| P10 | Style cứng & vi phạm chuẩn | `alert(` / `confirm(` gốc ở ≥ 12 file (`AccountDetailSheet.tsx` 5 chỗ, `PublishCenterModal.tsx` 4, `PostRow.tsx` 2, `QueueView.tsx` 2…); màu cứng (hex / `bg-red-500`…) **46** chỗ (nhiều nhất: `StatusBadge.tsx`, `StudioCanvas.tsx`, `RunStatusBar.tsx`, `AccountChip.tsx`); `overflow-hidden` **72** chỗ (quy tắc 14: UI nổi dùng `overflow-clip`) | Vi phạm `ui-rules` 1b, 14; hỏng theme tối |
| P11 | Responsive / co giãn | `w-[NNNpx]`/`min-w-[NNNpx]` cố định **32** chỗ; breakpoint `sm/md/lg/xl` chỉ **113** lần cho toàn app; icon nút `h-4..6 w-4..6` **186** chỗ (mục tiêu chạm nhỏ) ; `overflow-y-auto` thiếu `scroll-quiet` **30** chỗ | Vỡ bố cục ở 375/768px; thanh cuộn thô; khó bấm trên cảm ứng |
| P12 | Truy cập | `<button>` **357** vs `aria-label|data-tip|title` **283** (ước lượng); `div onClick` ít (2) | Nút chỉ-icon thiếu nhãn/tooltip (quy tắc 4) |
| P13 | Animation | `layout`/`layoutId` framer **6** chỗ; spring thô **0** (tốt) | Kiểm tra layout animation trên danh sách dài |

*Các con số là bước khởi đầu, có thể thiếu: Ag phải tự quét lại kỹ hơn (React Profiler, bundle analyzer, mở trình duyệt) và bổ sung phát hiện mới vào `status/P.md`.*

## 3. Giao thức đo (làm TRƯỚC khi sửa, lưu vào `status/P.md` mục "Baseline")
Chạy production build (`NEXT_DIST_DIR=.next-build npx next build && next start -p 3200`, không đụng cổng 3000) và ghi:
1. **Bundle:** bảng `Route / Size / First Load JS` từ output `next build`; thêm `@next/bundle-analyzer` bằng biến môi trường `ANALYZE=1` (không commit nếu phải thêm dependency nặng; ưu tiên cách không cần dependency như đọc `.next-build/analyze` hoặc `next build --profile` + so file chunk).
2. **Canvas:** nạp graph mẫu ≥ 50 node (`data/projects/soc-nho-tv/graph.json` hoặc tạo cái giả trong bộ nhớ, không ghi vào dữ liệu thật). Dùng React Profiler (hoặc `performance.mark` trong dev) để đếm **số lần render của `StudioNode`/`NodeInputs`** khi: (a) kéo 1 node 3 giây, (b) đổi 1 tham số node, (c) chạy graph đang `isRunningGraph` 10 giây.
3. **Tương tác:** đo INP/độ trễ nhấn qua `performance` observer (event timing) khi mở/đóng panel dock, đổi tab, nhập chữ vào ô prompt.
4. **Mạng:** số request lặp/bị bỏ khi đổi dự án nhanh 5 lần (tab Network).
5. **Responsive:** chụp ảnh ở 375×812, 768×1024, 1024×768, 1440×900, 1920×1080 cho: Sảnh, Studio (canvas + dock), tab Dự án, Nhân vật, Toolbox, Social Hub, `CreateVideoModal`, `PublishCenterModal`. Ghi mọi chỗ: tràn ngang, bị cắt, chồng lấp, nút < 32px.
6. Lưu ảnh/số liệu vào `ai/plans/2026-11-roadmap/session-P-ui-perf/baseline/` (ảnh nén vừa phải, không commit file > 1MB).

## 4. Nhiệm vụ
| Mã | Việc | Cổng nghiệm thu (bằng số/ảnh thật) |
|---|---|---|
| **P-00** | Đọc tài liệu mục 0; quét lại toàn bộ dashboard (không chỉ bảng mục 2); tạo `status/P.md` với bảng phát hiện đầy đủ + mức độ ảnh hưởng | `status/P.md` có ≥ phát hiện mục 2 và phần Ag tự tìm thêm |
| **P-01** | Đo **Baseline** theo mục 3 | Số liệu + ảnh trong `baseline/` |
| **P-02** | **Selector hoá store (P2):** thay 48 chỗ `useStudioStore()` bằng selector hẹp (`useStudioStore(s => s.x)`) hoặc `useShallow`; hành động (`updateNodeParams`…) lấy qua selector ổn định | Số lần render node khi kéo/đổi tham số giảm (ghi số trước/sau) |
| **P-03** | **Memo hoá canvas (P3):** `React.memo` cho `StudioNode`, các `NodeInputs` con, thẻ danh sách; ổn định `useCallback`/`useMemo` cho props truyền xuống; `nodeTypes`/`edgeTypes` hằng số ngoài component | Kéo 1 node không render lại node khác (đếm bằng Profiler) |
| **P-04** | **Cô lập timer (P7):** đưa bộ đếm giây ra component riêng (hiển thị thời gian chạy) thay vì state cấp canvas; polling `JobsCostTab` dừng khi tab/panel ẩn hoặc `document.hidden`, dùng backoff | Khi chạy graph, canvas không render mỗi giây (Profiler) |
| **P-05** | **Huỷ request & chống race (P8):** `AbortController` + kiểm tra `activeProjectId` còn khớp trước khi `set` state, cho các `useEffect` fetch chính (đổi dự án, nhân vật, vault, publish, templates); hook dùng chung `useAbortableFetch` nếu hợp | Đổi dự án nhanh 5 lần: không còn dữ liệu dự án cũ hiện lên; số request bị huỷ ghi lại |
| **P-06** | **Tách bundle (P4, P5):** `next/dynamic` (ssr:false) cho `PublishCenterModal`, `CreateVideoModal`, `ToolboxPanel`, Social Hub views, `PreviewPane` nặng; kiểm tra `icons.ts` có kéo cả `lucide` không và sửa (import theo tên); loại dependency không dùng | First Load JS các route giảm (ghi % trước/sau); `check:icons` sạch |
| **P-07** | **Ảnh (P6):** component `Img` dùng chung (lazy + `decoding="async"` + width/height/aspect + placeholder), áp cho gallery nhân vật/kho/cutouts/thumbnail; thumbnail kích thước nhỏ cho danh sách (nếu cần thì thêm route resize nhẹ, cache) | Mở tab Nhân vật/Toolbox kho: số byte ảnh tải lúc đầu giảm (Network) |
| **P-08** | **Danh sách (P9, P13):** sửa `key` index thành id ổn định; ảo hoá (windowing nhẹ hoặc `content-visibility: auto`) cho danh sách dài (jobs, queue, kho, chat); bỏ `layout` animation khỏi danh sách dài | Danh sách ≥ 200 mục cuộn mượt, không giật (đo frame/INP) |
| **P-09** | **Tuân thủ style (P10):** thay mọi `alert()`/`window.confirm()` bằng `confirm()` (`lib/confirm.ts`) + thông báo trong UI (`StatusIsland` hoặc dòng lỗi chuẩn); màu cứng → token (`semantic-*`, `brand`, `muted`…) hỗ trợ sáng/tối; `overflow-hidden` → `overflow-clip` ở UI nổi (quy tắc 14); `overflow-y-auto` → thêm `scroll-quiet`; nút chỉ-icon thiếu `aria-label`/`data-tip` (P12) | `grep` các mẫu vi phạm = 0 (hoặc ngoại lệ có chú thích); ảnh sáng/tối trước-sau |
| **P-10** | **Responsive & linh hoạt (P11):** thay `w-[NNNpx]` cố định bằng `min()/clamp()/%`/container query khi cần; panel dock/modal co theo viewport (≤ 768px: dock thành thanh dưới hoặc panel toàn chiều rộng, kiểm tra `BottomNav`); không cuộn ngang trang; vùng chạm tối thiểu 32px (dùng padding, không phình icon); form/hộp thoại không tràn màn hình thấp | Ảnh ở 375/768/1024/1440/1920 cho 8 màn trong mục 3.5: không tràn, không chồng, không cắt |
| **P-11** | **Chốt chặn chống thoái lui:** viết `tool/scripts/check_ui_style.mjs` (+ script `check:style` trong `package.json`): fail khi có `lucide-react`, `window.confirm`/`alert(`, màu cứng ngoài ngoại lệ, `key={index}` mới, `useStudioStore()` không selector, `<img>` thiếu lazy; thêm vào quy trình (ghi trong `ai/rules/ui-rules.md` mục cuối "Hiệu năng") | `npm run check:style` chạy được và pass; thử cố tình vi phạm thì fail |
| **P-12** | Đo **After** (cùng giao thức mục 3), bảng so sánh Trước/Sau, cập nhật `ai/rules/ui-rules.md` + `ai/map/TOOLS.md`, `git pull --rebase origin main` rồi **push `main`** | `status/P.md` có bảng So sánh; push thành công |

**Thứ tự:** P-00 → P-01 → P-02 → P-03 → P-04 → P-05 → P-06 → P-07 → P-08 → P-09 → P-10 → P-11 → P-12. Mỗi mã: tsc + build pass, mở UI kiểm tay các màn bị ảnh hưởng (console không lỗi, sáng + tối) rồi commit.

## 5. Điều không được làm
- Không đổi giao diện/luồng người dùng nhìn thấy (trừ sửa vỡ bố cục và thay `alert/confirm`).
- Không thêm thư viện UI/animation mới; không thay framer-motion/Morphicons.
- Không tối ưu sớm mù quáng: mỗi thay đổi phải gắn với 1 số đo ở baseline; thay đổi không cải thiện số đo thì bỏ.
- Không sửa dữ liệu thật trong `data/` khi đo; dùng dữ liệu giả trong bộ nhớ.
- Không bỏ qua lỗi: nếu một mục không thể làm (rủi ro/xung đột), ghi `blocked` + lý do vào `status/P.md`.

## 6. Báo cáo cuối (`ai/plans/2026-11-roadmap/status/P.md`)
Bảng phát hiện, từng mã (done/partial/blocked), **bảng Trước/Sau** (First Load JS, số render canvas, INP, số request huỷ, byte ảnh lúc đầu, số vi phạm style), đường dẫn ảnh responsive, danh sách việc còn lại. Cấm báo "xuất sắc/pass" không kèm số đo.
