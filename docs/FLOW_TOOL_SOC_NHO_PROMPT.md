# Prompt tạo Flow Tool "Sóc Nhỏ Director"

Dán khối prompt bên dưới vào Google Flow, mục Tools > Create Tool. Cần gói AI Plus, Pro hoặc Ultra. Prompt do project tự viết, mô tả chức năng cần có, không sao chép tool của bên nào.

Ý tưởng chức năng lấy từ giao diện hai giai đoạn (Nhân vật rồi Kịch bản) thấy trong video, xem [TIKTOK_AI_ANIMATION_WORKFLOW_LESSONS.md](TIKTOK_AI_ANIMATION_WORKFLOW_LESSONS.md). Bộ prompt nội dung nằm ở [SOC_NHO_PROMPT_TEMPLATES.md](SOC_NHO_PROMPT_TEMPLATES.md).

## Prompt dán vào Flow

```
Hãy tạo một công cụ tên "Sóc Nhỏ Director" để dựng video hoạt hình 3D thiếu nhi từ một kịch bản, giữ nhân vật nhất quán. Giao diện tiếng Việt, tối màu, bố cục hai cột: cột trái là cấu hình, cột phải là kết quả.

CỘT TRÁI
1. Hai nút chuyển giai đoạn: "Nhân vật" và "Kịch bản".
2. Cấu hình AI: chọn model ảnh, chọn model video, chọn thời lượng mỗi clip (4s, 6s, 8s). Mặc định 6s. Tiêu đề các nhóm: "Giai đoạn", "Cấu hình AI", "Model Ảnh", "Model Video", "Thời lượng", "Danh sách nhân vật (0)".
3. Hai nút "Mở dự án" và "Lưu dự án": lưu và nạp toàn bộ trạng thái (danh sách nhân vật, danh sách cảnh, ảnh và video đã tạo) dưới dạng tệp JSON.

GIAI ĐOẠN "NHÂN VẬT"
- Nút "Thêm nhân vật": mỗi nhân vật có tên, mô tả cố định (tối đa vài câu) và một ảnh tham chiếu.
- Với mỗi nhân vật: ô nhập prompt ảnh tham chiếu và nút "Tạo ảnh". Ảnh tạo ra phải toàn thân, đứng chính diện, nền trắng thuần.
- Cho phép tải ảnh có sẵn lên làm ảnh tham chiếu thay vì tạo mới.
- Danh sách nhân vật hiển thị tên và ảnh nhỏ; có nút xóa và sửa.

GIAI ĐOẠN "KỊCH BẢN"
- Một ô văn bản lớn để dán danh sách cảnh, mỗi dòng một cảnh theo mẫu: [Prompt ảnh] | [Prompt video], ngăn cách bằng dấu gạch đứng.
- Nút "Phân tích cảnh": tách ô văn bản thành từng thẻ cảnh. Mỗi thẻ cảnh có hai ô sửa được (prompt ảnh, prompt video), danh sách nhân vật xuất hiện trong cảnh (tự nhận theo tên) và trạng thái.
- Mỗi thẻ cảnh có nút "Tạo ảnh" rồi "Tạo video". Video tạo từ ảnh của chính cảnh đó, dùng ảnh tham chiếu của các nhân vật có mặt để giữ nhất quán.
- Nút "Tạo tất cả" chạy lần lượt từng cảnh, có thanh tiến độ, và nút "Dừng". Nếu một cảnh lỗi thì đánh dấu lỗi và chạy tiếp cảnh sau, không chạy lại các cảnh đã xong.
- Trước khi chạy hàng loạt, hiện cảnh báo số lượt tạo dự kiến sẽ tiêu credit và yêu cầu người dùng xác nhận.

CỘT PHẢI
- Lưới các thẻ cảnh theo thứ tự, mỗi thẻ có ảnh, video xem trước, số thứ tự, thời lượng.
- Nút "Tải tất cả" gom ảnh và video theo tên cảnh_01, cảnh_02...

QUY TẮC
- Không thêm chữ, logo hay phụ đề vào ảnh.
- Mọi prompt gửi đi phải nối thêm đúng nguyên văn một ô "Style bible" mà người dùng nhập ở đầu trang (mặc định để trống), để phong cách không đổi giữa các cảnh.
- Mọi thao tác tạo media phải báo rõ đang chạy, đã xong hay lỗi.
```

## Giá trị khởi tạo nên nhập sau khi tool chạy
- **Style bible:** 3D Pixar-style animation, ánh sáng studio mềm ấm, màu rực cân bằng, tỉ lệ 16:9, không chữ.
- **Nhân vật Sóc Nhỏ:** tải ảnh chuẩn `assets/soc_nho/soc_nho_01.png` lên làm ảnh tham chiếu; mô tả cố định lấy từ mục "Prompt khóa nhân vật" trong [SOC_NHO_CHARACTER_PROFILE.md](SOC_NHO_CHARACTER_PROFILE.md). Không để tool tạo nhân vật mới.

## Lưu ý khi dùng
- Tool chạy sinh video sẽ tốn credit Flow; thử với 2 cảnh trước khi chạy cả tập.
- Link chia sẻ tool cho người khác xem được toàn bộ mã của tool.
- Flow tự viết mã nên lần đầu có thể lệch ý; sửa bằng cách mô tả thay đổi ở mục Edit thay vì tạo lại.

## Đã tạo trên Flow (01/11/2026)
- Tool "Sóc Nhỏ Director" đã được tạo qua Ego Lite trong project Flow `Tháng 11 01 - 23:28`: https://flow.google.com/project/6977c01d-b438-4fb1-b9a8-b71fd9f3a491 (tool nằm ở mục Công cụ).
- Flow tự điền dữ liệu mẫu sai hồ sơ (Sóc Nhỏ áo len đỏ, thêm "Bạn Nhím", Style bible ghi "Disney Pixar"); đã nhờ Flow sửa lại: chỉ còn Sóc Nhỏ áo phông vàng quần short đen, Style bible theo mục trên.
- Chưa tạo ảnh hay video nào (không tốn credit). Chưa tải ảnh chuẩn `soc_nho_01.png` lên làm ảnh tham chiếu.

## Kết quả chạy thử 2 cảnh (01/11/2026)
- Tải `assets/soc_nho/soc_nho_01.png` lên làm ảnh tham chiếu cho nhân vật Sóc Nhỏ trong tool (qua hộp chọn thư viện của Flow, nút "Tải nội dung lên").
- Dán 2 cảnh, bấm "Phân tích cảnh": tách đúng 2 cảnh và tự gắn nhân vật Sóc Nhỏ cho cả hai.
- "Tạo tất cả" hiện hộp xác nhận credit; sau khi xác nhận, tool tạo ảnh rồi video từng cảnh (6 giây mỗi cảnh) và hoàn tất cả hai, có nút "Tải ảnh" và "Tải MP4".
- Ảnh khung đầu cảnh 1: nhân vật đúng áo phông vàng, quần short đen, đuôi xù. Chưa tải MP4 về máy; chưa nghe kiểm tra tiếng và khớp môi.
- Lưu ý kỹ thuật cho Ego Lite: giao diện tool nằm trong iframe, nút "Tải ảnh lên" mở hộp chọn thư viện của Flow thay vì mở thẳng hộp chọn tệp.

## Cập nhật tool "Remix of Sóc Nhỏ Director" (02/11/2026)
- Khung code trong Flow chỉ để xem. Sửa tool bằng khung chat "Trình tạo công cụ" bên phải, bấm "Xong" để lưu. Chưa thấy nút xuất mã; bản chép nguyên văn 6 file lưu ở `tools/flow_tool/soc_nho_director/` (chỉ để tham khảo, mã dùng `flow-sdk` nên không chạy riêng ở local).
- Đã thêm qua khung chat: nút "Chọn từ kho nhân vật"; nút "Tải kịch bản từ máy" (.txt/.md/.csv); công tắc "Khóa nguyên văn tất cả cảnh" và trường `locked` từng cảnh; trường `transition` (cut/fade/dissolve/wipe + giây); cảnh có ảnh sẵn thì bỏ qua bước tạo ảnh; "Tải tất cả" kèm `canh_chuyen_canh.json`; sửa lỗi nhân vật chỉ có base64 không được gửi làm ảnh tham chiếu (tự `Flow.upload` một lần).
- Hạn chế: "Chọn từ kho nhân vật" dùng cùng bộ chọn ảnh `Flow.media.select({filter:'image'})` như "Tải ảnh lên"; SDK không có API riêng cho mục Nhân vật. Chuyển cảnh chỉ ghi vào JSON và manifest, việc ghép thật làm ở HyperFrames.
- Gói trọn gói dựng ở local: `python3 scripts/flow_ai/build_flow_package.py --script <kich_ban.txt> --out <goi.json> [--scene-images <thư mục canh_01.png...>]`. Mẫu: `work/flow_package_demo/`.
- Chưa kiểm tra: nạp `goi_demo.json` qua "Mở dự án" (hộp chọn tệp trong iframe không điều khiển được bằng Ego Lite), chạy thật sau khi sửa.

## Bản chạy local (02/11/2026)
- `tools/flow_tool/soc_nho_director/`: project Vite + React, chạy `npm run dev` ở cổng 3000. Xem README trong thư mục đó.
- Đã kiểm tra ở chế độ chạy thử: nạp `goi_demo.json` ra 2 cảnh, "Tạo tất cả" tạo ảnh và video giả cho cả hai, huy hiệu chuyển cảnh (FADE/CUT) và khóa nguyên văn hiện đúng.
- Chưa kiểm tra: chế độ API thật (cần `GEMINI_API_KEY`).
