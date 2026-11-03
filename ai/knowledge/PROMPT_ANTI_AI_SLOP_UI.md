# Prompt chống giao diện "AI nhựa" cho AI Video Studio

Dùng cho Claude Code (hoặc agent khác) khi dựng hoặc sửa giao diện `tool/dashboard`. Đã cài trong project: skill `design-taste-frontend` (Leonxlnx/taste-skill) và 7 skill từ `nextlevelbuilder/ui-ux-pro-max-skill` (`ui-ux-pro-max`, `design`, `design-system`, `ui-styling`, `brand`, `banner-design`, `slides`), nằm ở `ai/skills/`.

## Quy tắc ưu tiên giữa hai bộ skill (đã kiểm tra, có xung đột)
- **taste quyết định diện mạo** (bố cục, màu, chữ, mật độ, chuyển động).
- **ui-ux-pro-max chỉ dùng cho trải nghiệm, tiếp cận và quy tắc theo stack** (focus, bàn phím, vùng chạm, Next.js). **Không dùng phần chọn kiểu, bảng màu, phối chữ của nó.** Khi hỏi nó cho "AI Video Studio", nó đề xuất kiểu "Vibrant & Block-based" với tím `#7C3AED` và hồng `#EC4899`: đó chính là giao diện mặc định của AI mà ta đang tránh, và trùng với bản đầu của trang tổng quan.

## Hướng thiết kế đã chốt (framed-sheet, đã áp dụng)
- Khung màu kem đá ấm chứa sidebar và thanh trên, không đường kẻ giữa chúng. Trang làm việc là một tờ trắng, cách mép phải và dưới 8px, viền 1px, bo 16px, không bóng.
- Một màu thương hiệu: nâu hạt dẻ `#b4531a` (lông Sóc Nhỏ), chỉ dùng cho dữ liệu chính, gạch chân tab, biểu tượng. Nút chính màu mực gần đen. Màu trong khung dưới 3%.
- IBM Plex Sans (có tiếng Việt), IBM Plex Mono chỉ cho id và mã giọng. Chữ số thẳng hàng (`tabular-nums`).
- Biểu tượng hạt dẻ làm dấu hiệu riêng; phần tử riêng của sản phẩm là biểu đồ khóa chiều cao nhân vật (Sóc Nhỏ 100 cm, Koala 150 cm).
- Giá trị đặt ở `app/globals.css`, `tailwind.config.ts`; bảng thông số gốc ở `tool/dashboard/.taste-skill/app/direction.json`.

## Prompt

```
Bạn đang làm giao diện cho AI Video Studio (tool/dashboard, Next.js + Tailwind + KokonutUI + React Flow UI + Zustand). Mục tiêu: nhìn như sản phẩm do một nhà thiết kế làm, không như mẫu do AI sinh ra.

Thứ tự bắt buộc:
1. Đọc ai/skills/design-taste-frontend/SKILL.md và references/app-screens.md đến hết trước khi viết. Đây là màn hình làm việc (app screen), không phải trang giới thiệu.
2. Dùng hướng đã chốt trong docs/PROMPT_ANTI_AI_SLOP_UI.md (framed-sheet, màu nâu hạt dẻ, IBM Plex). Không tự đổi hướng. Muốn đổi thì nêu lý do trong báo cáo.
3. Dùng ui-ux-pro-max chỉ cho: trải nghiệm bàn phím, focus, vùng chạm, trạng thái tải/lỗi/rỗng, quy tắc Next.js (python3 ai/skills/ui-ux-pro-max/scripts/search.py "<từ khóa>" --domain ux, hoặc --stack nextjs). Tuyệt đối không dùng --design-system, bảng màu hay phối chữ của nó.

Với mỗi màn hình, viết trước (trong ghi chú, không vào mã):
- Câu hỏi duy nhất mà màn hình trả lời (ví dụ "Tập 1 đang ở bước nào, việc gì tiếp theo?") và một phát hiện chính, đặt ở dòng đầu.
- Việc người dùng làm nhiều nhất và nút của việc đó (một cú bấm).
- Một phần tử chỉ sản phẩm này có (ví dụ khóa chiều cao nhân vật, thanh tiến độ các cảnh của tập, đường đi từ kịch bản đến video).
- Dữ liệu thật: lấy từ repository hoặc Core, số liệu cộng khớp, có đơn vị, số 0 in ra là 0, thiếu thì gạch ngang. Không dữ liệu mẫu bịa, không "+12%" cho tài khoản mới.

Cấm tuyệt đối (đây là dấu hiệu "AI nhựa"):
- Nền gradient, quầng sáng mờ (blur glow), kính mờ (backdrop-blur) làm trang trí, bóng đổ lớn khi đứng yên.
- Màu tím/chàm/hồng làm màu thương hiệu; thanh điều hướng đang chọn tô màu đậm.
- Thẻ KPI có icon trong ô tô màu, sparkline nhỏ, mũi tên xanh "+12.5%".
- Nhãn pill có ngôi sao lấp lánh (✨/Sparkles), emoji làm icon, chữ thường viết hoa cách chữ (uppercase tracking).
- Banner chào "Welcome back", ảnh minh họa chung chung, khối trang trí chỉ để lấp chỗ trống.
- Mọi thứ cùng một bo góc lớn (rounded-xl) và cùng một thẻ bóng; thẻ lồng thẻ quá 3 cấp.
- Chuỗi hard-code trong component (mọi chữ qua next-intl, vi và en), ký hiệu LaTeX hoặc markdown lọt ra giao diện (ví dụ "$\rightarrow$").
- Dùng thư viện biểu đồ mặc định, biểu đồ cầu vồng, chú thích dài dòng.

Canvas node (React Flow):
- Node phẳng: viền 1px, nền trắng, bo 8px, không bóng. Đầu node cao 32px ghi tên loại và trạng thái bằng chữ (chờ, đang chạy, xong, lỗi, cũ). Đang chạy là chữ màu thương hiệu, không vòng xoay phát sáng.
- Một màu cho mỗi kiểu dữ liệu (văn bản xám, ảnh xanh lơ, video nâu hạt dẻ, âm thanh vàng đất), dùng nhất quán ở cổng, dây nối và chú giải. Dây 1.5px, chọn node là viền mực 2px.
- Ảnh xem trước trong node là ảnh thật của cảnh. Mini-map, thanh thu phóng, thanh công cụ phẳng, gắn vào khung, không nổi lơ lửng.
- Chạy được bằng bàn phím (Tab, Enter, mũi tên), có focus ring thấy rõ, vùng chạm tối thiểu 32px trên máy tính và 44px trên điện thoại. Điện thoại chỉ cần xem đồ thị dạng danh sách dọc.

Kiểm tra bắt buộc sau mỗi màn hình (làm đến khi 0 FAIL, mỗi WARN phải sửa hoặc biện hộ được trong một câu):
  node ai/skills/design-taste-frontend/scripts/lint.mjs --app tool/dashboard/app tool/dashboard/components
  node ai/skills/design-taste-frontend/scripts/inspect.mjs --app http://localhost:3000/<đường dẫn>
Mở ảnh chụp ở 1440, 768, 390px (cả chế độ sáng và tối), tự chấm theo bảy câu hỏi trong mục 2.7 của app-screens.md, sửa ba lỗi tệ nhất, kiểm tra lại, tối đa ba vòng.

Báo cáo ngắn: kiểu đã dùng, câu hỏi và phát hiện của từng màn hình, phần tử riêng của sản phẩm, mục kiểm tra đã cho phép kèm lý do, và danh sách dữ liệu mẫu cần thay bằng dữ liệu thật.
```

## Đã áp dụng ở lượt này (02-03/11/2026)
- Viết lại vỏ giao diện và trang Tổng quan; chỉnh nhẹ trang Studio (xem báo cáo trong phiên).
- Kiểm tra: Tổng quan 0 FAIL, 0 WARN. Studio còn 1 FAIL (dot-grid nền canvas bị tính là gradient) và 2 WARN do trang đó đang là bản giữ chỗ chờ canvas React Flow thật; cần xử lý khi dựng canvas.
