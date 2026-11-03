# Prompt dựng "AI Video Studio" (dán cho AI lập trình)

Dùng với Claude Code hoặc công cụ tương tự, chạy trong một thư mục mới. Prompt do project tự viết, tham khảo quy trình canvas node trong các video đã xem và chức năng của Google Flow; không sao chép mã của bên nào.

## Prompt

```
Hãy xây một ứng dụng web tên "AI Video Studio": nơi một người làm nội dung quản lý nhiều kênh và nhiều dự án video, tạo video bằng quy trình canvas node gọi các model AI trả phí, lưu video theo dự án và đăng lên nền tảng.

# 1. Công nghệ bắt buộc
- Next.js bản mới nhất (App Router, TypeScript strict), Tailwind CSS.
- Thư viện UI chính: KokonutUI (https://kokonutui.com/docs), cài component theo hướng dẫn của họ. Dùng cho layout, nút, thẻ, form, dialog, sidebar.
- Canvas node: React Flow và các component React Flow UI (https://reactflow.dev/ui). Mọi node tùy biến dựng trên các component này.
- Điểm nhấn: React Bits "Swarm Cursor" (https://reactbits.dev/animations/swarm-cursor), chỉ dùng ở trang chủ hoặc trang đăng nhập, tắt khi người dùng bật "giảm chuyển động" (prefers-reduced-motion) và trên thiết bị cảm ứng.
- Quản lý state: Zustand, chia slice (workspace, project, canvas, jobs, ui). Dùng persist cho cài đặt giao diện.
- Supabase là tùy chọn: Postgres cho dữ liệu, Storage cho ảnh/video, Auth cho đăng nhập. Phải có lớp trừu tượng Repository với hai cài đặt: LocalRepository (IndexedDB + thư mục tệp, mặc định, chạy không cần tài khoản) và SupabaseRepository (bật bằng biến môi trường). Giao diện không được biết đang dùng cái nào.
- i18n: next-intl, hai ngôn ngữ vi và en, mặc định theo trình duyệt, đổi được trong cài đặt. Không để chuỗi cứng trong component.

# 2. Giao diện
- Hai chế độ sáng và tối, theo hệ thống và đổi tay được. Cả hai theo phong cách dịu nhẹ: nền không đen tuyệt đối hoặc trắng tinh, độ tương phản chữ đạt WCAG AA, bo góc vừa, bóng mỏng, khoảng trắng rộng, một màu nhấn duy nhất lấy từ token. Mọi màu định nghĩa bằng CSS variable (token), không viết màu thẳng trong component.
- Responsive thật: điện thoại 360px, máy tính bảng, máy tính. Trên điện thoại sidebar thành thanh điều hướng dưới hoặc ngăn kéo; canvas dùng được bằng cảm ứng (kéo, chụm để thu phóng), thanh công cụ gọn lại.
- Trạng thái rỗng, đang tải, lỗi đều có thiết kế. Phím tắt cho thao tác chính. Hỗ trợ bàn phím và trình đọc màn hình ở mức cơ bản.
- Ngôn ngữ thiết kế: tinh tế, hiện đại, ít viền, ít chữ, biểu tượng nhất quán một bộ.

# 2b. Tận dụng tối đa thư viện UI để giao diện đẹp và tinh tế nhất
Mục tiêu là khai thác đầy đủ những gì ba thư viện cung cấp, nhưng "tinh tế" nghĩa là tiết chế: chọn đúng chỗ, không chất hiệu ứng.
1. Trước khi viết giao diện, đọc tài liệu và danh mục component của cả ba thư viện (KokonutUI, React Bits, React Flow UI), kể cả các mẫu, khối ghép sẵn, hiệu ứng nền, hiệu ứng chữ, node mẫu. Tạo tệp docs/UI_CATALOG.md liệt kê: component nào có, dùng cho màn hình nào, vì sao chọn, vì sao bỏ qua. Không đoán tên component từ trí nhớ, chỉ dùng những gì có thật trong tài liệu.
2. Ưu tiên theo thứ tự: component có sẵn của KokonutUI cho layout, form, thẻ, nút, ô nhập prompt, thanh điều hướng; component React Flow UI cho mọi thứ trong canvas (node nền, chỉ báo trạng thái node, thanh thu phóng, điều khiển, mini-map, vùng nhóm); React Bits cho một số ít điểm nhấn (nền trang chủ, hiệu ứng chữ tiêu đề, con trỏ Swarm Cursor). Chỉ tự viết component khi thư viện không có, và khi đó theo đúng phong cách của thư viện.
3. Một hệ thiết kế duy nhất: token màu, bo góc, bóng, khoảng cách, cỡ chữ, độ dày nét, thời lượng và đường cong chuyển động đặt ở một nơi, mọi component thư viện được chỉnh theo token này để ba thư viện nhìn như một sản phẩm. Hai chế độ sáng/tối đều đi qua cùng token.
4. Chuyển động có quy tắc: một bộ thời lượng và easing dùng chung, chuyển động chỉ để chỉ hướng hoặc báo trạng thái (vào trang, mở panel, node chạy xong), mỗi màn hình tối đa một hiệu ứng nổi bật. Hiệu ứng nặng (nền động, con trỏ) chỉ ở trang chủ và đăng nhập, không ở canvas làm việc. Tôn trọng prefers-reduced-motion, tắt trên thiết bị cảm ứng và máy yếu.
5. Chi tiết hoàn thiện: trạng thái hover, focus, active, disabled cho mọi thứ bấm được; skeleton khi tải; trạng thái rỗng có minh họa nhẹ; thông báo (toast) và hộp thoại xác nhận cùng một phong cách; icon một bộ duy nhất, cùng độ dày nét; chữ có phân cấp rõ (tối đa ba cỡ chữ chính mỗi màn hình), căn lưới khoảng cách 4px hoặc 8px.
6. Canvas phải đẹp như một sản phẩm chứ không phải bản demo: node đồng nhất kích thước và padding, dây nối mượt có màu theo loại dữ liệu (ảnh, văn bản, video), ảnh xem trước trong node bo góc, thanh công cụ nổi gọn, chuyển động nhẹ khi node chạy.
7. Hiệu năng và truy cập: điểm Lighthouse hiệu năng và truy cập từ 90 trở lên ở trang chính, không giật khi canvas có 100 node (ẩn node ngoài khung nhìn, không render lại không cần thiết), tải font và ảnh tối ưu.
8. Tự kiểm tra bằng mắt: sau mỗi bước giao, chụp ảnh màn hình các trang chính ở ba chiều rộng (360px, 768px, 1280px) và cả hai chế độ sáng/tối, tự soát lỗi lệch hàng, tràn chữ, thiếu tương phản, rồi sửa trước khi báo.

# 3. Mô hình dữ liệu và phạm vi
Workspace > Kênh (Channel) và Dự án (Project).
- Channel: nền tảng (YouTube, TikTok, Facebook, Instagram...), tên, trạng thái kết nối OAuth, mặc định đăng (tiêu đề mẫu, hashtag, khung giờ).
- Project (ví dụ "Sóc Nhỏ", "Gobi"): có riêng nhân vật, cảnh, kịch bản, thư viện ảnh/video, cài đặt giọng, style bible, và liên kết tới một hoặc nhiều Channel. Dữ liệu của dự án này không lẫn sang dự án khác.
- Character: tên, mô tả khóa (prompt lock), ảnh tham chiếu nhiều góc, giọng nói (voice id), tỉ lệ cơ thể, "bộ nhớ nhân vật" (tính cách, thói quen, câu cửa miệng, những gì đã xảy ra ở các tập trước) được nạp vào prompt kịch bản tập sau để nhân vật nhất quán.
- Script và Scene: kịch bản chia thành cảnh; mỗi cảnh có prompt ảnh, prompt video, thoại, nhân vật có mặt, thời lượng, kiểu chuyển cảnh.
- Asset: ảnh, video, âm thanh, kèm thông tin sinh ra nó (model, prompt, đầu vào, giá) để tái lập.
- Video: sản phẩm cuối, tỉ lệ khung, trạng thái (nháp, đã dựng, đã lên lịch, đã đăng), liên kết Channel và bài đăng.
- Job: mỗi lần gọi model, có trạng thái, log, chi phí ước tính và thực tế.

# 4. Chức năng tạo video
Màn hình "Tạo video" cho chọn:
1. Tỉ lệ khung có sẵn theo nền tảng: 16:9 (YouTube), 9:16 (TikTok, Shorts, Reels), 1:1, 4:5. Đổi tỉ lệ cập nhật cả canvas và prompt gửi đi.
2. Kiểu nội dung: video ngắn (short), phim hoạt hình ngắn, phim hoạt hình dài (nhiều tập hoặc nhiều đoạn, quản lý theo chương), video giới thiệu sản phẩm/thời trang, nội dung tự do.
3. "Tạo từ video có sẵn": người dùng dán đường dẫn hoặc tải video lên, hệ thống phân tích cấu trúc (mở đầu, nhịp cảnh, lời thoại, góc máy, thời lượng) và dựng thành kịch bản và bộ prompt MỚI cho nhân vật của dự án. Chỉ sao chép ý tưởng và cấu trúc, không dùng lại hình ảnh, âm thanh hay lời thoại của người khác. Hiện cảnh báo bản quyền và chỉ cho đăng khi người dùng xác nhận mình có quyền.
4. "Nhân vật ảo": tạo nhân vật mới từ mô tả hoặc ảnh, sinh bộ ảnh tham chiếu nhiều góc, lưu vào dự án kèm bộ nhớ nhân vật.
Mỗi kiểu đều ra một đồ thị node có sẵn (mẫu), người dùng chỉnh được.

# 5. Canvas node (trọng tâm)
Mô phỏng quy trình thấy trong video: ảnh gốc và ảnh tham chiếu nối vào node tạo ảnh, kết quả nối tiếp sang node tạo video.
- Node cơ bản: Văn bản/Prompt, Ảnh (tải lên hoặc từ thư viện), Nhân vật, Kịch bản (tách thành N cảnh), Tạo ảnh, Sửa ảnh, Tạo video, Giọng đọc, Nhóm (gom nhiều node), Dựng, Xuất.
- Node Tạo ảnh có: ô prompt, cổng "Reference images" nhận nhiều ảnh, chọn model, chọn tỉ lệ khung và độ phân giải, nút "Run" có menu (chạy node này, chạy từ đây trở xuống, chạy cả đồ thị), các ảnh kết quả lướt qua lại được, nút thay ảnh, tải về, xóa.
- Mỗi node sinh bằng model giữ danh sách các lần sinh để duyệt, người dùng ghim một lần làm đầu ra. Đổi đầu vào của một node chỉ làm các node phía sau hiện nhãn "cũ", không tự chạy lại và không tự tốn tiền; "chạy cả chuỗi" chỉ chạy node cũ hoặc chưa có đầu ra. Quy tắc đầy đủ ở PROMPT_AI_VIDEO_CORE.md mục 3 và 11.
- Node "Kiểm tra" (cổng chấm điểm) đặt trước bước tạo video để chỉ tốn tiền khi ảnh đạt tiêu chí.
- Hiện trạng thái từng node (chờ, đang chạy, xong, lỗi), ước tính giá, tổng giá trước khi chạy cả đồ thị, và hộp xác nhận khi vượt ngưỡng do người dùng đặt.
- Chạy song song theo số luồng người dùng chọn, có nút Dừng, bảng nhật ký, lưu và nạp đồ thị, undo/redo, thu phóng, minimap, căn lưới, copy/paste node, đồ thị mẫu.

# 6. Model AI và khóa API
- Lớp Provider với giao diện chung: image.generate, image.edit, video.generate (ảnh khung đầu, thời lượng), voice.speak, text.complete (viết kịch bản, phân tích video). Mỗi nhà cung cấp là một adapter (ví dụ Google Gemini/Veo, fal.ai, Replicate; thêm nhà khác chỉ cần thêm adapter).
- Khóa API chỉ ở phía máy chủ (route handler hoặc server action), không bao giờ gửi xuống trình duyệt, không ghi vào mã. Có trang cài đặt nhập khóa, mã hóa khi lưu.
- Chế độ "Chạy thử" (mock) tạo ảnh/video giả, bật khi chưa có khóa, để thử giao diện không tốn tiền.
- Việc dài (tạo video) chạy nền qua hàng đợi, thăm dò trạng thái, thử lại có giới hạn, không treo giao diện.

# 7. Đăng bài và tự động
- Kết nối kênh bằng OAuth chính thức của từng nền tảng (YouTube Data API, TikTok Content Posting API...). Không lưu mật khẩu, không dùng điều khiển trình duyệt trái phép để đăng.
- Mỗi dự án đặt: kênh đích, tiêu đề/mô tả/hashtag mẫu, khung giờ, chế độ "đăng tay" hoặc "tự động đăng theo lịch". Mặc định là duyệt tay trước khi đăng; tự động chỉ bật khi người dùng chủ động.
- Lịch đăng dạng lịch tuần, trạng thái bài (đã lên lịch, đang đăng, đã đăng, lỗi), thử lại khi lỗi, nhật ký.
- Ghi chú trong giao diện: một số nền tảng yêu cầu duyệt ứng dụng trước khi cho phép đăng tự động.

# 8. Yêu cầu chất lượng
- Cấu trúc thư mục rõ: app/, components/, features/ (workspace, projects, canvas, jobs, publish), lib/providers/, lib/repositories/, store/, messages/ (vi, en).
- Kiểu dữ liệu bằng TypeScript và kiểm tra đầu vào bằng Zod ở mọi biên (form, API).
- Kiểm thử đơn vị cho bộ chạy đồ thị (thứ tự phụ thuộc, danh sách lần sinh và đánh dấu cũ, bộ nhớ đệm của node xác định, xử lý lỗi), và kiểm thử giao diện cho luồng tạo dự án đến chạy đồ thị ở chế độ mock.
- README: cách cài, biến môi trường, cách bật Supabase, cách thêm provider mới.

# 9. Giao hàng theo bước (dừng và báo sau mỗi bước)
1. Khung ứng dụng: Next.js, Tailwind, KokonutUI, theme sáng/tối, i18n vi/en, layout responsive, LocalRepository, và docs/UI_CATALOG.md (danh mục component của ba thư viện kèm bảng ánh xạ màn hình, theo mục 2b) cùng bộ token thiết kế.
2. Workspace: Channel và Project, tạo/sửa/xóa, chuyển dự án, dữ liệu tách theo dự án.
3. Nhân vật và kịch bản: Character (ảnh tham chiếu, bộ nhớ), Script/Scene, tải kịch bản từ máy.
4. Canvas node với React Flow: các node cơ bản, bộ chạy, lịch sử lần sinh và đánh dấu cũ, chế độ mock.
5. Provider thật (Gemini/Veo trước), hàng đợi việc, ước tính giá và xác nhận.
6. Tạo video theo kiểu: tỉ lệ khung, short, phim hoạt hình, tạo từ video có sẵn.
7. Kênh và đăng bài: OAuth, lịch, duyệt tay trước khi đăng.
8. Supabase tùy chọn, Swarm Cursor, hoàn thiện giao diện.

Không cần làm: thanh toán, mạng xã hội trong ứng dụng, chỉnh sửa video theo dòng thời gian như phần mềm dựng chuyên nghiệp.
```

## Điểm cần chốt trước khi giao cho AI
- **"2 theme đen trắng, theme dịu nhẹ":** mình hiểu là hai chế độ sáng và tối, cả hai đều tông dịu. Nếu bạn muốn ba theme (sáng, tối, và một theme dịu riêng) thì sửa mục 2.
- **Tự động đăng:** TikTok và vài nền tảng yêu cầu duyệt ứng dụng mới cho đăng qua API, nên bước 7 có thể chờ duyệt. Mặc định prompt để duyệt tay.
- **Sao chép video TikTok:** prompt giới hạn ở việc lấy ý tưởng và cấu trúc cho nhân vật của bạn, không dùng lại hình, tiếng hay lời của người khác.
- **Dựng cuối (ghép cảnh, phụ đề, 9:16):** HyperFrames của project này chạy riêng ở máy, không chạy trong Next.js. Nên coi đó là một bước sau (node "Dựng" gọi dịch vụ dựng riêng).
