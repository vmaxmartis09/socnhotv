# Prompt cập nhật Studio v2 (bỏ tab Nhân vật, canvas tương tác được, bong bóng người dùng, khung chat bên phải)

Dán khối dưới cho Claude Code đang làm `tool/dashboard`. Bám các tài liệu đã có: [PROMPT_AI_VIDEO_STUDIO.md](PROMPT_AI_VIDEO_STUDIO.md), [PROMPT_AI_VIDEO_CORE.md](PROMPT_AI_VIDEO_CORE.md), [PROMPT_ANTI_AI_SLOP_UI.md](PROMPT_ANTI_AI_SLOP_UI.md).

## Prompt

```
Cập nhật AI Video Studio (tool/dashboard) theo 4 thay đổi dưới đây. Trước khi viết, đọc: docs/PROMPT_ANTI_AI_SLOP_UI.md (hướng thiết kế, quy tắc ưu tiên giữa skill taste và ui-ux-pro-max, danh sách cấm), docs/PROMPT_AI_VIDEO_CORE.md (đặc biệt mục 2, 3, 11), tool/src/socnhotv/core/contracts/types.py và core/nodes/registry.py. Giữ nguyên hướng thiết kế đã áp dụng (framed-sheet, nâu hạt dẻ, IBM Plex, phẳng, không bóng). Mọi chữ hiển thị qua next-intl (vi và en), không hard-code chuỗi.

# Bố cục mới
- Trang chính "/" LUÔN là Studio canvas. Bỏ trang Tổng quan riêng, bỏ các route /characters, /projects, /publish, /settings (chuyển hướng về "/" và mở đúng tab ở khung bên phải).
- Cột trái mảnh: dấu hiệu sản phẩm, bộ chuyển dự án, danh sách tập/đồ thị của dự án (mỗi tập là một đồ thị canvas), và ở đáy là bong bóng người dùng (mục 3). Không còn mục Nhân vật, Cài đặt, Lịch đăng trong cột trái.
- Giữa: canvas. Phải: khung chat có tab (mục 4). Điện thoại: canvas chỉ đọc dạng danh sách node dọc, khung phải thành tấm trượt từ dưới lên, bong bóng người dùng nằm trong thanh điều hướng dưới.

# 1. Nhân vật nằm trong dự án, không có tab riêng
- Xóa mục điều hướng và trang Nhân vật. Nhân vật là một phần của Dự án, quản lý trong tab "Dự án" ở khung bên phải (mục 4). Dự án có nhiều nhân vật: danh sách thẻ, tìm kiếm, thêm, nhân bản, xóa (có xác nhận), kéo một nhân vật thả lên canvas để tạo node "Nhân vật" đã gắn sẵn hồ sơ.
- Bấm một nhân vật mở hồ sơ ĐẦY ĐỦ ngay trong khung phải (hoặc ngăn trượt rộng hơn), chia các phần:
  a. Hồ sơ: tên, vai (chính/phụ), mô tả, tính cách, câu cửa miệng, thói quen, sự kiện đã xảy ra ở các tập trước (bộ nhớ nhân vật, đưa vào prompt kịch bản các tập sau), prompt khóa nhân vật, chiều cao và tỉ lệ khóa (ví dụ Sóc Nhỏ 100 cm, Koala 150 cm), bảng so chiều cao giữa các nhân vật.
  b. Ảnh: thư viện ảnh tham chiếu nhiều góc (tải lên, sinh bằng node, đặt ảnh chính, xóa, xem lớn), mỗi ảnh ghi nguồn (tải lên hay model nào, prompt nào).
  c. Video: các clip đã sinh có nhân vật này (xem trước, tập và cảnh chứa nó).
  d. Giọng: voice-id (Sóc Nhỏ là soc-nho), nghe mẫu, ô nhập câu để thử đọc qua OmniVoice, tốc độ (tempo), nút nhân bản giọng có hộp xác nhận quyền (chỉ giọng của chính bạn hoặc người đã đồng ý).
  e. Dùng ở đâu: danh sách tập và cảnh nhân vật xuất hiện, các node đang tham chiếu hồ sơ này.
- Mở rộng kiểu Character và Repository cho phần này (thư viện ảnh, clip, mẫu giọng, lịch sử), lưu ở data/projects/<id>/characters/ theo cấu trúc dữ liệu hiện có. Không tạo nhân vật mới ngoài hồ sơ chuẩn: ảnh tham chiếu Sóc Nhỏ lấy từ assets/soc_nho.

# 2. Canvas studio: mỗi card nói rõ nó là gì, làm gì, nhận gì, và thao tác được
Vẽ card từ GET /node-types của Core (displayName, category, description, inputPorts, outputPorts, defaultParams), KHÔNG viết cứng từng loại node trong giao diện. Thêm loại node ở Core thì canvas tự có.

Giải phẫu một card (phẳng, viền 1px, bo 8px, không bóng):
- Đầu card (cao 32px): tên loại node, nhãn vai trò trong flow lấy theo category (Nguồn, Xử lý, Sinh, Kiểm tra, Dựng, Xuất), trạng thái bằng chữ (chờ, sẵn sàng, đang chạy, xong, lỗi, cũ). Đang chạy là chữ màu thương hiệu, không vòng xoay phát sáng.
- Một dòng "vai trò": description của loại node, viết cho người làm video ("Biến kịch bản thành danh sách cảnh", "Chấm điểm ảnh trước khi tốn tiền tạo video").
- Cột cổng vào bên trái: mỗi cổng ghi tên, kiểu dữ liệu chấp nhận (văn bản, ảnh, nhiều ảnh, video, âm thanh, kịch bản, cảnh, nhân vật), dấu bắt buộc hay tuỳ chọn, và đã nối hay chưa. Cột cổng ra bên phải tương tự. Màu cổng và dây theo kiểu dữ liệu (văn bản xám, ảnh xanh lơ, video nâu hạt dẻ, âm thanh vàng đất), có chú giải.
- Tham số chính rút gọn (model, tỉ lệ, thời lượng), bấm để sửa ở tab Node (mục 4).
- Xem trước kết quả thật khi có (ảnh, video, âm thanh), lần sinh đang ghim và số lần sinh. Dưới cùng: nút Chạy có menu (chạy node này, chạy từ đây trở xuống, chạy cả chuỗi), giá ước tính.

Tương tác bắt buộc:
- Thêm node: thanh công cụ và ô tìm "Thêm node" (gõ để lọc theo tên, category), danh sách mỗi loại kèm mô tả và cổng vào/ra; kéo thả hoặc bấm để đặt vào giữa khung nhìn.
- Nối bằng cách kéo từ cổng ra sang cổng vào. Khi đang kéo, chỉ làm nổi các cổng tương thích (dùng quy tắc is_port_compatible của Core); thả vào cổng sai thì từ chối kèm lý do ("Cần Ảnh, đang kéo Văn bản"). Không nối vòng. Xóa dây bằng cách chọn rồi Delete.
- Thêm trước, thêm sau: bấm dấu + ở cổng ra mở danh sách CHỈ các loại node nhận được kiểu dữ liệu đó, chọn thì tạo node và tự nối. Bấm + ở cổng vào hiện các loại node tạo ra được kiểu dữ liệu đó. Với node đang chọn có hai nút "Thêm bước trước" và "Thêm bước sau" làm đúng như vậy.
- Chọn nhiều node, kéo di chuyển, nhóm, nhân bản, xóa, hoàn tác và làm lại, thu phóng, mini-map phẳng, căn lưới, copy/paste, phím tắt (Delete, Ctrl+Z, Ctrl+Shift+Z, Ctrl+D, Enter để chạy node đang chọn). Điều khiển được bằng bàn phím và có focus ring rõ.
- Chạy: gọi POST /projects/{id}/run, nghe SSE (/events) để cập nhật trạng thái, tiến độ, log và chi phí lên từng card; hộp xác nhận chi phí tổng trước khi chạy; nút Dừng; chạy một node không tự chạy node phía trên (báo "chưa chạy được: đang chờ ảnh đầu vào"); đổi đầu vào chỉ đánh dấu node phía sau là "cũ".
- Kiểm tra đồ thị bằng POST /graph/validate: lỗi hiện ngay trên card hoặc dây liên quan (cổng bắt buộc chưa nối, sai kiểu, vòng lặp).
- Lưu tự động (có độ trễ) qua POST /projects/{id}/graph, hiện "đã lưu" hoặc "chưa lưu" bằng chữ.
- Canvas không bao giờ trống: khi chưa có đồ thị, hiện chọn mẫu (truyện Sóc Nhỏ: Văn bản, Kịch bản, Nhân vật, Tạo ảnh, Kiểm tra, Tạo video, Giọng đọc, Dựng, Xuất; và đồ thị trắng). Mẫu đặt sẵn node đã nối, chưa có kết quả, ghi rõ bước tiếp theo.
- Nếu Core chưa chạy (GET /health lỗi), hiện trạng thái này rõ ràng bằng chữ kèm cách bật Core, vẫn cho dựng đồ thị ở chế độ chạy thử bằng bản mock của giao diện.

# 3. Bong bóng người dùng ở góc dưới trái
- Một hình tròn 36px (ảnh đại diện hoặc chữ cái đầu, tải ảnh lên được) gắn đáy cột trái. Bấm mở một hộp nhỏ dạng sticky (rộng khoảng 320px, neo phía trên bong bóng, phẳng, viền 1px, bo 12px, đóng bằng Esc hoặc bấm ra ngoài, bẫy focus, có aria).
- Nội dung hộp, gọn nhưng đủ: hồ sơ người dùng (tên, email, ảnh), workspace hiện tại; ngôn ngữ (vi/en); giao diện (sáng/tối/theo máy); hạn mức chi tiêu (trần mỗi lần chạy, mỗi ngày); chế độ chạy thử (bật/tắt); trạng thái khóa API theo từng nhà cung cấp (đã đặt hay chưa, nút nhập khóa mở ô riêng, KHÔNG BAO GIỜ hiện lại khóa); nơi lưu dữ liệu (máy này hay Supabase) và dung lượng đã dùng; trạng thái kết nối Core (xanh/đỏ bằng chữ, phiên bản); phím tắt; xóa dữ liệu cục bộ (có xác nhận hai bước).
- Thay thế hoàn toàn trang Cài đặt và dòng "Lưu trên máy này" ở cột trái. Giá trị lưu qua store (persist) và Repository.

# 4. Khung chat bên phải, xử lý các tab; trang chính vẫn là Studio
- Khung phải rộng 380px mặc định, kéo đổi được từ 320 đến 560px, thu gọn bằng phím tắt và nút, nhớ trạng thái. Phẳng, viền trái 1px cùng tờ trắng với canvas.
- Tab (gạch chân 2px màu thương hiệu cho tab đang chọn): Chat, Node (thông số của node đang chọn: sửa prompt, model, tỉ lệ, xem các lần sinh và ghim, giá), Dự án (thông tin dự án, danh sách tập, nhân vật theo mục 1), Lịch đăng và Kênh (kênh YouTube/TikTok..., lịch tuần, trạng thái bài, duyệt tay trước khi đăng), Hàng đợi và Chi phí (việc đang chạy, lịch sử, chi phí so với trần).
- Chat là trợ lý điều khiển studio: hiểu lệnh tự nhiên (ví dụ "thêm bước kiểm tra nhân vật trước khi tạo video", "chạy từ cảnh 3", "đổi tỉ lệ sang 16:9", "lên lịch đăng tập 1 lúc 19:00 lên YouTube", "mở lịch đăng") và gọi các lệnh của Core qua cùng API/MCP (tạo/sửa node, nối dây, chạy, lập lịch). Mỗi hành động hiện thành thẻ gọn trong chat ("Đã thêm node Kiểm tra và nối với Tạo ảnh", nút Hoàn tác, nút Xem trên canvas); lệnh hiện cũng làm canvas nhấp nháy node bị tác động một lần (không hiệu ứng nặng).
- Lệnh tốn tiền hoặc đăng ra ngoài PHẢI qua hộp xác nhận kèm số tiền hoặc nền tảng; tuân hạn mức chi tiêu của Core; không bao giờ tự đăng nếu người dùng chưa xác nhận. Lệnh mở tab ("mở lịch đăng", "cho tôi xem nhân vật Koala") chuyển tab và mở đúng mục.
- Cần một nhà cung cấp văn bản (text.complete) qua lớp Provider của Core. Khi chưa có khóa hoặc đang chế độ chạy thử, dùng trợ lý theo quy tắc (nhận một số lệnh cố định) và nói rõ đó là chế độ thử. Lưu lịch sử chat theo từng dự án.
- Các tab cũng bấm trực tiếp được không cần chat; chat chỉ là đường tắt.

# Dữ liệu và kiến trúc
- Zustand: thêm slice cho khung phải (tab đang mở, độ rộng), chat, người dùng/cài đặt; canvas dùng chung slice hiện có.
- Không viết lại Core; chỉ gọi API sẵn có và thêm endpoint nếu thiếu (ghi rõ trong báo cáo): hồ sơ nhân vật mở rộng, lịch đăng, chat/tool-call.
- Dữ liệu mẫu phải thật theo dự án Sóc Nhỏ; liệt kê chỗ nào còn là mẫu.

# Kiểm tra và nghiệm thu
- Chạy ở cổng 3000 cùng Core. Mỗi thay đổi có kiểm thử giao diện chạy bằng trình duyệt: kéo nối hai node cùng kiểu thành công, sai kiểu bị từ chối kèm lý do, thêm bước sau từ dấu +, chạy mẫu Sóc Nhỏ ở chế độ mock ra đủ kết quả trên card, mở hồ sơ nhân vật đủ năm phần, bong bóng mở/đóng bằng bàn phím, chat thêm được một node và hoàn tác được.
- Chạy bộ kiểm tra của skill taste cho từng màn hình: node ai/skills/design-taste-frontend/scripts/lint.mjs --app và inspect.mjs --app, 0 FAIL ở 1440, 768, 390px (sáng và tối); nền chấm của canvas được phép (nêu lý do). Chụp ảnh và tự chấm theo mục 2.7 của app-screens.md.
- Báo cáo: các endpoint thêm mới, dữ liệu mẫu còn lại, mục đã cho phép ở bộ kiểm tra, việc chưa làm.

# Giao hàng theo bước (dừng và báo sau mỗi bước)
1. Bố cục mới: Studio ở "/", bỏ các route cũ, khung phải có tab rỗng, bong bóng người dùng.
2. Canvas: card từ /node-types, cổng có kiểu, nối, thêm trước/sau, mẫu Sóc Nhỏ, lưu tự động, kiểm tra đồ thị.
3. Chạy đồ thị từ canvas: SSE, trạng thái, chi phí, xác nhận, dừng, trạng thái cũ.
4. Tab Node và tab Dự án với hồ sơ nhân vật đầy đủ.
5. Tab Lịch đăng và Kênh, tab Hàng đợi và Chi phí.
6. Chat điều khiển studio, hoàn tác, xác nhận.
```

## Cách mình hiểu yêu cầu (sửa lại nếu sai)
- **Ý 1:** Nhân vật vẫn tồn tại, chỉ không còn là một trang riêng; chúng nằm trong tab "Dự án" và mỗi nhân vật có hồ sơ đủ ảnh, video, giọng, thông tin.
- **Ý 4:** "Trang chính luôn là Studio" nghĩa là canvas ở giữa không bao giờ bị thay bằng trang khác; Dự án, Lịch đăng và Kênh, Hàng đợi, Node đều mở ở khung phải. Nếu bạn muốn các tab này mở toàn màn hình khi cần thì sửa mục "Bố cục mới".
- **Bong bóng người dùng:** chỉ lưu cục bộ, chưa có đăng nhập thật; nếu cần tài khoản thì phải bật Supabase (đã nằm trong kế hoạch tùy chọn).
- **Chat:** trợ lý cần một model văn bản. Không có khóa thì chỉ chạy được vài lệnh cố định ở chế độ thử.
