# DANH MỤC THÀNH PHẦN GIAO DIỆN & BỘ QUY CHUẨN THIẾT KẾ (UI CATALOG & DESIGN SYSTEM)
## Ứng dụng: AI Video Studio

> Tài liệu này được tạo theo quy chuẩn mục 2b: khảo sát thực tế và phân loại toàn bộ thành phần từ 3 thư viện UI cốt lõi (**KokonutUI**, **React Flow UI**, **React Bits**). Tuyệt đối không suy đoán tên thành phần từ trí nhớ.

---

## PHẦN 1: BẢNG TRA CỨU & ÁNH XẠ THÀNH PHẦN (UI COMPONENT CATALOG)

### 1. KOKONUTUI (`kokonutui.com`) — Thư viện UI Chính (Layout, Form, Thẻ, Nút, Dialog)

| Tên Component thực tế | Phân loại | Màn hình áp dụng | Lý do chọn | Lý do bỏ qua (nếu có) |
| :--- | :--- | :--- | :--- | :--- |
| **Model Selector** | AI Component | Canvas Node (Tạo ảnh, Tạo video), Settings | Cho phép chọn nhanh model AI (Gemini, Veo, Fal, Replicate) kèm badge giá & thông số | — |
| **Tool Approval** | AI Component | Canvas Run, Job Queue, Cost Confirmation | Dùng cho hộp xác nhận phê duyệt chạy node/graph khi chi phí vượt ngưỡng an toàn | — |
| **Context Meter** | AI Component | Script & Persona Editor, Canvas Inspector | Hiển thị % token / bộ nhớ ngữ cảnh đã dùng cho nhân vật và kịch bản | — |
| **Voice** | AI Component | Node Giọng đọc, Quản lý Sound Profile | Visualizer sóng âm và điều khiển nghe thử giọng clone (OmniVoice `soc-nho`) | — |
| **Diff Review** | AI Component | Script Iteration, Node version diff | So sánh hai bản nháp kịch bản hoặc hai prompt khi người dùng tinh chỉnh | Không dùng cho màn hình chính, chỉ mở khi bấm "So sánh" |
| **Inline Citations** | AI Component | Knowledge & Script references | Hiển thị nguồn bài học, reference scenes khi phân tích video | Bỏ qua ở v1, dành cho v2 |
| **Slide to Confirm** | Button | Node Run All, Publish Trigger | Ngăn chặn bấm nhầm nút chạy tốn tiền hoặc đăng video tự động lên TikTok/YouTube | — |
| **Hold Button** | Button | Canvas Node "Run Selection", Reset Graph | Tạo cảm giác an toàn và chắc chắn cho thao tác quan trọng | — |
| **Undo Button** | Button | Canvas Top Toolbar | Undo / Redo các thao tác kéo thả node, nối dây | — |
| **Magnet Button** | Button | Primary CTA, Header Actions | Hiệu ứng hút chuột tinh tế trên desktop cho nút "Tạo video mới" | — |
| **Particle Button** | Button | Landing Page / Trang chủ CTA | Điểm nhấn nhẹ khi nhấn "Bắt đầu sáng tạo" | Bỏ qua ở Canvas làm việc để tránh gây mất tập trung |
| **Apple Activity Card** | Card | Workspace / Project Dashboard | Thẻ hiển thị chỉ số retention rate, view, completion % của các kênh | — |
| **Uptime Card** | Card | System Status, API Providers Status | Hiển thị tình trạng hoạt động và độ trễ của các provider (Google Veo, Fal, Replicate) | — |
| **Currency Transfer** | Card | Job Cost & Budget Tracker | Thẻ theo dõi chi phí ước tính vs chi phí thực tế đã thanh toán qua model API | — |
| **Receipt Printer** | Card | Job Details, Export Invoice | Thẻ in chi tiết từng job chạy (thời lượng, model, resolution, cost) | — |
| **Command Palette** | Navigation | Toàn ứng dụng (Phím tắt `Cmd+K` / `Ctrl+K`) | Tìm nhanh dự án, chuyển màn hình, thêm node nhanh vào canvas | — |
| **Smooth Drawer** | Navigation | Mobile (360px - 768px) Sidebar / Node Inspector | Ngăn kéo trượt mượt mà cho bảng điều khiển trên thiết bị di động | — |
| **Swipe Tabs** | Navigation | Mobile Tabs, Project Detail switcher | Vuốt chuyển đổi giữa các tab Cảnh, Nhân vật, Cài đặt trên điện thoại | — |
| **Status Island** | Navigation | Canvas Header, Job Queue Island | Thanh thông báo trạng thái nổi (đang render, chờ duyệt, hoàn tất) | — |
| **Clip Trimmer** | Media | Media Library, Video Ingest | Cắt ngắn video clip nạp vào để trích xuất cấu trúc hoặc làm reference | — |
| **Synced Transcript** | Media | Audio Sync, Subtitle Review | Cuộn kịch bản đồng bộ theo audio thoại khi nghe preview giọng | — |
| **Focal Point Picker** | Media | Character DNA, Reference Cropper | Chọn tâm điểm khuôn mặt/nhân vật khi cắt ảnh 16:9 sang 9:16 | — |
| **Prompt Input** | Input | Node Prompt, Script Generator | Ô nhập prompt chuyên dụng có phím tắt, gợi ý thẻ tag và nút run | — |
| **Time Zone Planner** | Input | Publishing / Scheduler | Lên lịch hẹn giờ đăng video theo múi giờ vàng của từng quốc gia/kênh | — |
| **Wheel Picker** | Input | Mobile Settings, Aspect Ratio Selector | Bộ chọn bánh xe tiện lợi trên màn hình cảm ứng điện thoại | — |

---

### 2. REACT FLOW UI (`reactflow.dev/ui`) — Thư viện Canvas & Node Editor

| Tên Component thực tế | Phân loại | Màn hình áp dụng | Lý do chọn | Lý do bỏ qua (nếu có) |
| :--- | :--- | :--- | :--- | :--- |
| **Base Node** (`BaseNode`, `BaseNodeHeader`, `BaseNodeHeaderTitle`, `BaseNodeContent`, `BaseNodeFooter`) | Node Utilities | Tất cả các node trong Canvas | Tạo khung node đồng nhất kích thước, padding, header, bo góc theo design token | — |
| **Status Indicator** | Node Utilities | Góc trên mỗi Node | Hiển thị 4 trạng thái chuẩn: Chờ (idle/gray), Đang chạy (running/blue pulse), Xong (done/green), Lỗi (error/red) | — |
| **Appendix** (Node Badge) | Node Utilities | Chân Node | Gắn nhãn chi phí ước tính ($0.04), thời lượng (8s), resolution (1080p) | — |
| **Node Tooltip** | Node Utilities | Handle & Nút chạy trong node | Hiện giải thích cổng vào/ra (Input: Ảnh tham chiếu; Output: Video MP4) | — |
| **Base Handle** & **Labeled Handle** | Handles | Điểm nối dây trên Node | Điểm neo có nhãn mô tả rõ loại dữ liệu (Image, Video, Text, Audio) | — |
| **Button Handle** | Handles | Cổng kết quả Node | Cho phép bấm nhanh để sinh node tiếp nối tự động (ví dụ từ Image -> spawn Video) | — |
| **Placeholder Node** | Custom Nodes | Canvas rỗng, điểm nối tiếp | Node dấu cộng `+` mời gọi người dùng click để thêm node kế tiếp vào luồng | — |
| **Labeled Group** | Custom Nodes | Gom nhóm Cảnh (Scene Group) | Khung bao gom các node thuộc cùng một Cảnh (Script + Image + Video + Audio) | — |
| **Database Schema Node** | Custom Nodes | — | — | Bỏ qua vì thiết kế cho DB ERD, không phù hợp luồng video |
| **Edge with Button** | Custom Edges | Dây nối Canvas | Nút xóa dây hoặc chèn node trung gian trực tiếp trên dây nối | — |
| **Edge with Node Data** | Custom Edges | Dây nối Canvas | Hiển thị loại dữ liệu truyền qua dây (PNG, MP4, WAV, JSON) | — |
| **Animated SVG Edge** | Custom Edges | Dây nối Canvas khi node đang chạy | Hiệu ứng dòng chảy hạt sáng biểu thị dữ liệu đang được truyền tải | Tắt khi bật `prefers-reduced-motion` |
| **Node Search** | Controls | Canvas Bottom/Top Toolbar | Tìm kiếm nhanh node trong đồ thị lớn (>50 node) | — |
| **Zoom Slider** & **Zoom Select** | Controls | Canvas Bottom Toolbar | Thu phóng mượt mà, căn giữa đồ thị, fit view | — |
| **DevTools** (`ViewportLogger`, `NodeInspector`) | Miscellaneous | Chế độ Debug của Studio | Theo dõi tọa độ viewport và inspector dữ liệu node | Chỉ bật khi ở môi trường development |

---

### 3. REACT BITS (`reactbits.dev`) — Điểm Nhấn Tinh Tế & Hiệu Ứng Tiết Chế

| Tên Component thực tế | Phân loại | Màn hình áp dụng | Lý do chọn | Lý do bỏ qua (nếu có) |
| :--- | :--- | :--- | :--- | :--- |
| **Swarm Cursor** | Cursor Animation | Landing Page / Trang Đăng nhập | Hiệu ứng đàn đom đóm/hạt lỏng bám đuôi trỏ chuột, uốn lượn quanh nút bấm. Tự tắt trên touch & reduced motion | **TUYỆT ĐỐI KHÔNG** dùng trong Canvas làm việc để tránh giật lag và phân tâm |
| **BlurText** / **DecryptedText** | Text Animation | Tiêu đề Hero Trang chủ & Dashboard Welcome | Hiệu ứng lộ chữ hiện đại, tinh tế khi tải trang | Không lạm dụng ở các tiêu đề node nhỏ |
| **Iridescence** / **Squares** | Background | Nền Hero Trang chủ | Nền gradient động nhẹ nhàng tạo chiều sâu công nghệ | Tắt trên canvas làm việc (canvas dùng lưới dot/cross tối giản) |
| **Hyperspeed** | Background | — | — | Bỏ qua vì quá chói và giật mắt, vi phạm nguyên tắc "dịu nhẹ, ít viền" |

---

## PHẦN 2: BỘ TOKEN THIẾT KẾ ĐỒNG NHẤT (UNIFIED DESIGN TOKENS)

Cả 3 thư viện đều được cấu hình ép kiểu qua một bảng biến CSS Variable (Design Token) duy nhất:

### 1. Bảng màu Dịu Nhẹ (Light & Dark Soft Palettes)
- **Không đen tuyệt đối (`#000000`), không trắng tinh (`#FFFFFF`):**
  - **Light Mode:**
    - Background chính: `hsl(220 20% 97%)` (`#F7F8FA`)
    - Surface Card: `hsl(0 0% 100%)` (`#FFFFFF` dịu)
    - Border / Divider: `hsl(220 13% 91%)` (`#E5E8ED`)
    - Chữ chính (Foreground): `hsl(222 47% 11%)` (`#0F172A` - Đạt chuẩn WCAG AAA tương phản > 12:1)
    - Chữ phụ (Muted): `hsl(215 16% 47%)` (`#64748B`)
  - **Dark Mode:**
    - Background chính: `hsl(224 25% 8%)` (`#0B0F17` - Nền than chì sâu)
    - Surface Card: `hsl(222 24% 12%)` (`#131924` - Xám xanh dịu)
    - Surface Card Elevated: `hsl(223 20% 16%)` (`#1B2332`)
    - Border / Divider: `hsl(220 18% 20%)` (`#242D3D`)
    - Chữ chính (Foreground): `hsl(210 30% 98%)` (`#F8FAFC` - Đạt chuẩn WCAG AAA)
    - Chữ phụ (Muted): `hsl(215 20% 65%)` (`#94A3B8`)
  - **Màu Nhấn Duy Nhất (Brand Accent Token):**
    - `Primary`: `hsl(252 85% 62%)` (`#6D4AFF` - Tím Indigo thông minh, công nghệ)
    - `Primary Hover`: `hsl(252 85% 56%)`
    - `Primary Soft`: `hsla(252, 85%, 62%, 0.12)`
  - **Màu Ngữ Cảnh (Semantic Tokens):**
    - Success (Done): `hsl(158 64% 45%)` (Emerald dịu)
    - Warning (Warning/Alert): `hsl(38 92% 50%)` (Amber ấm)
    - Danger (Error/Delete): `hsl(0 72% 51%)` (Rose đỏ không gắt)
    - Info / Running: `hsl(217 91% 60%)` (Sky Blue)
  - **Màu Dây Nối Dữ Liệu Canvas (Data Edge Tokens):**
    - Text / Prompt data: `hsl(215 20% 65%)` (Xám)
    - Image data: `hsl(158 64% 45%)` (Xanh ngọc)
    - Video data: `hsl(252 85% 62%)` (Tím Indigo)
    - Audio data: `hsl(38 92% 50%)` (Cam vàng)

### 2. Hình khối & Bo góc (Radius & Shadows)
- `radius-sm`: `6px` (Badge, button nhỏ, tag)
- `radius-md`: `10px` (Input, button chính, dropdown)
- `radius-lg`: `14px` (Card, dialog, node canvas)
- `radius-xl`: `20px` (Drawer, container ngoài)
- `shadow-sm`: `0 1px 2px 0 rgba(0, 0, 0, 0.05)`
- `shadow-md`: `0 4px 12px -2px rgba(0, 0, 0, 0.08)` (Bóng mỏng, không viền đen)
- `shadow-float`: `0 12px 28px -4px rgba(0, 0, 0, 0.12)` (Cho thanh công cụ nổi canvas)

### 3. Quy chuẩn Nhịp điệu Chuyển động (Motion & Easing)
- Thời lượng:
  - Micro-action (hover, click, toggle): `150ms`
  - Panel transition (drawer, dialog, tab switch): `250ms`
  - Page enter / Layout shift: `350ms`
- Easing: `cubic-bezier(0.16, 1, 0.3, 1)` (Ease-out springy dịu mắt)
- Quy tắc giảm chuyển động: Khi `prefers-reduced-motion: reduce`, toàn bộ transition đặt về `0ms`, tắt Swarm Cursor, tắt Animated Edge.

---

## PHẦN 3: BẢNG ÁNH XẠ MÀN HÌNH & TRẢI NGHIỆM ĐA THIẾT BỊ (SCREEN MAPPING)

| Màn hình | Desktop (1280px+) | Tablet (768px - 1024px) | Mobile (360px - 480px) |
| :--- | :--- | :--- | :--- |
| **1. Trang chủ / Landing** | Sidebar đầy đủ + Hero + Swarm Cursor | Sidebar thu gọn (icon only) + Hero | Thanh điều hướng dưới + Hero gọn, tắt Swarm Cursor |
| **2. Quản lý Dự án & Kênh** | Grid 3 cột thẻ Card KokonutUI | Grid 2 cột | Danh sách cuộn 1 cột + Smooth Drawer |
| **3. Nhân vật & Kịch bản** | 2 cột (Cột trái: DNA ảnh, Cột phải: Memory) | 2 cột cuộn độc lập | Swipe Tabs chuyển tab "Ảnh DNA" $\leftrightarrow$ "Bộ nhớ" |
| **4. Canvas Node Studio** | Full canvas + Topbar nổi + Minimap + Inspector phải | Canvas thu phóng cảm ứng + Inspector popover | Canvas cảm ứng (chụm/kéo) + Toolbar đáy + Drawer cài đặt |
| **5. Hàng đợi & Lịch đăng** | Bảng lịch tuần + Status Island | Lịch 3 ngày | Danh sách hàng đợi thẻ dọc (List Card) |
