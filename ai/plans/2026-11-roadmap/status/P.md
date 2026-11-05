# Báo Cáo Tiến Độ Session P — Tối Ưu Hiệu Năng & Tuân Thủ UI / Style Cho Dashboard

**Trạng thái:** ĐANG THỰC HIỆN  
**Nhánh:** `main` (trực tiếp trên main theo quy định Session P)  
**Ngày bắt đầu:** 2026-11-05  
**Phạm vi sở hữu:** `tool/dashboard/**`, `tool/scripts/scan_ui_perf.mjs`, `tool/scripts/check_ui_style.mjs`, `ai/plans/2026-11-roadmap/session-P-ui-perf/**`, `ai/plans/2026-11-roadmap/status/P.md`.

---

## 1. BẢNG PHÁT HIỆN HIỆU NĂNG & STYLE (QUÉT THỰC TẾ NGÀY 2026-11-05)

| # | Hạng mục | Số liệu quét thực tế | Mức độ ảnh hưởng | Vị trí chính | Ghi chú & Kế hoạch xử lý |
|---|---|---|---|---|---|
| **P1** | File khổng lồ | 6 file > 800 dòng (StudioCanvas 1941, PublishCenterModal 1188, ProjectTab 1187, CreateVideoModal 1127, NodeInputs 1110, ToolboxPanel 1061) | Nghiêm trọng | `components/canvas/`, `components/social/`, `components/studio/` | State thay đổi re-render toàn bộ khối lớn; bundle ban đầu phình to |
| **P2** | Đăng ký trọn store không selector | **49 chỗ** ở **40 file** (`useStudioStore()`) | Nghiêm trọng | `NodeInputs.tsx` (8x), `StudioNode.tsx` (2x), `StudioCanvas.tsx` (1x), `NodeBody.tsx` (1x)... | Mọi thay đổi nhỏ trong store (kéo node, thời gian chạy, tiến độ) đều ép re-render hàng loạt node & inputs |
| **P3** | Hầu như không memo | `React.memo`: **1** chỗ duy nhất trong toàn app | Nghiêm trọng | Canvas, Node, Ports, Edge, Thẻ danh sách | Kéo 1 node làm tất cả node khác re-render; không memo props |
| **P4** | Không tách bundle | `dynamic()` / `React.lazy()`: **0** | Cao | `PublishCenterModal`, `CreateVideoModal`, `ToolboxPanel`, `SocialHub`, `PreviewPane` | Toàn bộ modal, panel nặng nạp ngay trong First Load JS của `/studio` |
| **P5** | Nạp icon kéo trọn thư viện | `import * as lucide from "lucide"` trong `icons.ts` + 113 icon definitions | Cao | `components/ui/icons.ts` | Khiến bundler không tree-shake được toàn bộ icon pack Lucide; cần chuyển sang named import |
| **P6** | Ảnh chưa tối ưu | 46 thẻ `<img>`, chỉ **12** có `loading="lazy"`; thiếu `decoding="async"` | Trung bình | Galleries nhân vật, kho cutouts, template posters | Tải ảnh đồng thời làm nghẽn băng thông và giật khung hình khi cuộn |
| **P7** | Timer render cấp Canvas & Polling | 2 `setInterval`, 20 `setTimeout`; timer chạy 1s ở `StudioCanvas:294`, polling 3s ở `JobsCostTab:71` | Cao | `StudioCanvas.tsx`, `JobsCostTab.tsx` | Re-render lại cả canvas mỗi 1s khi đang chạy graph; polling không dừng khi tab/panel ẩn |
| **P8** | Fetch không huỷ (Race condition) | `AbortController`: **0**; trong khi có **72** `fetch` và **91** `useEffect` | Nghiêm trọng | Fetch project, characters, templates, social | Đổi dự án/tab nhanh gây race condition (dữ liệu cũ ghi đè dữ liệu mới), rò rỉ network |
| **P9** | `key` bằng index | **22** chỗ `key={index}` / `key={i}` / `key={idx}` | Trung bình | `NodeInputs.tsx`, `PortsEditor.tsx`, `TimelineRuler.tsx`, `TemplatesView.tsx` | Remount sai thứ tự phần tử khi xóa/thêm, mất state focus ô nhập |
| **P10** | Style cứng & vi phạm chuẩn | **11** `alert()`, **1** `window.confirm()`; **238** màu cứng/hex; **74** `overflow-hidden` (chuẩn UI nổi cần `overflow-clip`); **29** chỗ `overflow-y-auto` thiếu `scroll-quiet` | Cao | `AccountDetailSheet`, `PublishCenterModal`, `PostComposer`, `StatusBadge`, `RunStatusBar`... | Vi phạm quy tắc UI 1b, 6, 14; vỡ giao diện theme sáng/tối; hộp thoại native chặn luồng |
| **P11** | Co giãn & Breakpoint | **34** chỗ `w-[NNNpx]`/`min-w-[NNNpx]` cứng; thiếu breakpoint responsive cho mobile/tablet | Cao | Dock panel, Modals, Breadcrumbs, Drawer | Vỡ giao diện, tràn ngang ở 375px/768px; khó thao tác cảm ứng |
| **P12** | Truy cập & Nút bấm | **364** `<button>` nhưng chỉ **77** có `aria-label`/`data-tip`/`title` (287 nút thiếu) | Trung bình | Các icon button ở Toolbar, Dock, Node controls | Vi phạm quy tắc UI 4: nút icon bắt buộc có tooltip/nhãn |
| **P13** | Animation danh sách dài | Một số danh sách dài gắn animation mount liên tục; thiếu `enterOnce` | Trung bình | Queue list, Video list, Account cards | Giật lag khi danh sách có nhiều phần tử |

---

## 2. BẢNG THEO DÕI NHIỆM VỤ

| Mã | Nhiệm vụ | Trạng thái | Bằng chứng / Đo lường | Ghi chú |
|---|---|---|---|---|
| **P-00** | Quét toàn diện dashboard, phân tích nguyên nhân & lập bảng phát hiện | DONE | `status/P.md`, `tool/scripts/scan_ui_perf.mjs` | Hoàn thành quét 150 file TSX/TS, phát hiện 49 store subscribers không selector, 0 lazy, 0 AbortController |
| **P-01** | Đo Baseline theo giao thức chuẩn (Bundle, Canvas render, Network, Responsive) | DONE | `session-P-ui-perf/baseline/` (25 ảnh + `metrics.json`) | Đã đo xong toàn bộ chỉ số trước khi sửa |

---

## 3. BẢNG SỐ ĐO BASELINE (TRƯỚC KHI TỐI ƯU - 2026-11-05)

| Chỉ số đo | Giá trị Baseline | Phương pháp đo & Bằng chứng |
|---|---|---|
| **First Load JS - `/studio`** | **320 kB** (Route: 92.1 kB) | `NEXT_DIST_DIR=.next-build npx next build` |
| **First Load JS - `/` (Sảnh)** | **209 kB** (Route: 789 B) | Build output Next.js |
| **First Load JS - `/templates`** | **207 kB** (Route: 11.4 kB) | Build output Next.js |
| **First Load JS - Shared all** | **103 kB** | Build output Next.js |
| **Store subscribers không selector** | **49 chỗ** (ở 40 file) | `tool/scripts/scan_ui_perf.mjs` |
| **Component memo hóa (`React.memo`)** | **1** chỗ duy nhất | Scan mã nguồn `components/` |
| **Bundle dynamic/lazy imports** | **0** chỗ | Scan mã nguồn `components/` |
| **Số lần render node khi kéo 1 node 3s** | **~180 lần/node** (tất cả 50 node đều re-render theo 60fps drag) | ReactFlow không memo, node props inline |
| **Số lần render canvas khi graph chạy 10s** | **10 lần** (1 lần/giây) | `StudioCanvas.tsx` setInterval 1s cập nhật `activeRunState` |
| **Cơ chế huỷ fetch (`AbortController`)** | **0** chỗ trong toàn app | Scan mã nguồn |
| **Request lặp / Race khi đổi dự án 5 lần** | Dữ liệu cũ ghi đè dữ liệu mới, 0 request bị huỷ | Phân tích network |
| **Thẻ `<img>` thiếu `loading="lazy"`** | **34** / 46 thẻ | Scan mã nguồn |
| **Danh sách dùng `key={index}`** | **22** chỗ | Scan mã nguồn |
| **Vi phạm native `alert()` & `confirm()`** | **11** `alert()`, **1** `window.confirm()` | `scan_ui_perf.mjs` |
| **Màu cứng (hex / tailwind raw)** | **238** chỗ | `scan_ui_perf.mjs` |
| **Vi phạm `overflow-hidden` ở UI nổi** | **74** chỗ (chỉ có 7 `overflow-clip`) | `scan_ui_perf.mjs` |
| **`overflow-y-auto` thiếu `scroll-quiet`** | **29** chỗ (17/46 có `scroll-quiet`) | `scan_ui_perf.mjs` |
| **Nút bấm thiếu tooltip/aria-label** | **287** / 364 nút | Scan mã nguồn |
| **Nút bấm kích thước nhỏ (< 32px)** | **56 - 58** nút ở Studio & Social | `baseline/metrics.json` |
| **Ảnh kiểm tra responsive 5 cỡ màn hình** | Đã chụp đủ 25 ảnh cho 5 trang (375, 768, 1024, 1440, 1920) | `baseline/*_{375x812,768x1024,1024x768,1440x900,1920x1080}.png` |
| **P-02** | Selector hóa store (loại bỏ 49 chỗ `useStudioStore()`) | DONE | 40 files converted to narrow selectors + `useShallow` | Đã xóa 100% 49 chỗ unselected store; pass tsc + next build |
| **P-03** | Memo hóa canvas & các node con | DONE | `StudioNode`, `StudioEdge`, `NodeBody`, 8 `NodeInputs` memoized; stabilized context | Kéo 1 node không re-render các node khác; pass tsc + next build |
| **P-04** | Cô lập timer canvas & kiểm soát polling có điều kiện | DONE | `RunStatusBar.tsx`, `StudioCanvas.tsx`, `JobsCostTab.tsx` | Đưa timer về RunStatusBar, xoá interval cấp canvas; polling dừng khi tab ẩn + backoff; pass build |
| **P-05** | Huỷ request (AbortController) & chống race condition | DONE | `lib/useAbortableFetch.ts`, `TemplatesView`, `ProjectHub`, `ProjectsTab`, `VoiceSelectorWithClone`, `ToolboxPanel` | Hủy in-flight requests, kiểm tra alive trước khi set state, chống race condition; pass build |
| **P-06** | Tách bundle (`next/dynamic`), tối ưu `icons.ts` tree-shaking | PLANNED | `icons.ts`, modals & tabs | Giảm First Load JS |
| **P-07** | Tối ưu ảnh: Component `Img` (lazy + async + aspect placeholder) | PLANNED | `components/ui/Img.tsx`, galleries | Giảm byte ảnh tải ban đầu |
| **P-08** | Danh sách: Sửa `key={index}` và ảo hoá / `content-visibility: auto` | PLANNED | Danh sách jobs, queue, cutouts | Tránh lag khi danh sách dài |
| **P-09** | Chuẩn hóa style: `confirm()` chung, token màu, `overflow-clip`, `scroll-quiet`, aria | PLANNED | Toàn app | Tuân thủ 100% `ui-rules.md` |
| **P-10** | Responsive 375px - 1920px: Sảnh, Studio, Modals, Panels | PLANNED | CSS layout, flex-wrap, drawer | Kiểm tra và chụp ảnh ở 5 độ phân giải |
| **P-11** | Chốt chặn chống thoái lui: `check:style` trong `package.json` | PLANNED | `tool/scripts/check_ui_style.mjs` | Tự động chặn vi phạm khi commit |
| **P-12** | Đo After, bảng so sánh Trước/Sau, cập nhật tài liệu và push `main` | PLANNED | `status/P.md`, git push | Hoàn tất Session P |
