# Báo Cáo Nghiệm Thu Toàn Diện — Session E3 (Node Nhập Liệu & Video Runner)

## 1. Đã làm (DONE)
- [x] **i18n Dynamic Module Loader** (`tool/dashboard/i18n/request.ts`):
  - Viết lại loader tổng quát tự động nạp `nodes.*` và `studio.*` cùng `video`, `sources`, `social`.
  - Tạo `tool/dashboard/messages/modules/nodes.vi.json` và `nodes.en.json` đầy đủ nhãn song ngữ.
- [x] **Bộ phân tích kịch bản tất định** (`socnhotv.core.engine.script_parser`):
  - Tách kịch bản thuần bằng regex và logic tất định ($0.0 USD, không gọi LLM).
  - Nhận diện phân cảnh qua `Cảnh N:`, `Scene N:`, `---`, `\n\n`, và kịch bản 1 đoạn tự chia câu.
  - Tách lời thoại đa nhân vật dạng `Tên: Lời thoại`, chỉ dẫn hành động trong ngoặc đơn, chỉ dẫn `Camera:` / `Hình ảnh:`.
  - Tính toán thời lượng tự động theo tốc độ nói tiếng Việt (~3 từ/giây).
  - Unit test 6/6 pass (`tool/tests/test_script_parser.py`).
- [x] **Graph Runner chế độ Paste & Bỏ mặc định giả** (`socnhotv.core.engine.graph_runner`):
  - `script` node: Chế độ `mode == "paste"` sử dụng trực tiếp `rawScript` qua `script_parser`.
  - Loại bỏ hoàn toàn các chuỗi mặc định giả ("Sóc Nhỏ và Chiếc Răng Sâu", "Chào các bạn, mình là Sóc Nhỏ Bi nè!"). Nếu thiếu đầu vào, node báo lỗi rõ ràng.
  - `voice_tts` node: Nhận text trực tiếp từ params nếu chưa nối dây, báo lỗi nếu không có nội dung.
  - `export` node: Tự động copy và đóng gói MP4 xuất bản vào `data/projects/{pid}/output/{outputFileName}`.
  - Unit test và API test 3/3 pass (`tool/tests/test_graph_inputs.py`).
- [x] **Validator cảnh báo sớm dữ liệu thiếu** (`socnhotv.core.engine.validator`):
  - Cảnh báo trước khi chạy nếu node `script` ở mode paste mà thiếu `rawScript`, mode AI thiếu ý tưởng.
  - Cảnh báo nếu `voice_tts` thiếu text, `image` thiếu `uri`.
- [x] **Frontend: Vùng nhập liệu trực tiếp trên Card & Inspector** (`components/canvas/NodeInputs.tsx`):
  - Dùng chung components giữa Card trên canvas (`NodeBody.tsx`) và Panel phải (`NodeTab.tsx`).
  - `text`: Textarea co giãn 3-10 dòng, đếm từ/ký tự, nút Dán clipboard, nút Mở rộng modal.
  - `image` / `character_image` / `scene`: Vùng kéo-thả file, nút chọn ảnh từ máy, dán Ctrl+V, chọn từ Thư viện media, dán URL ảnh, nút đổi/xóa ảnh, xem trước thumbnail.
  - `script`: Công tắc 2 chế độ (AI vs Dán kịch bản có sẵn), textarea lớn, chỉ dẫn định dạng kịch bản, xem trước tức thời danh sách cảnh đã tách phía client.
  - `voice_tts`: Textarea nhập thoại trực tiếp nếu chưa nối dây + bộ chọn giọng `VoiceSelectorWithClone`.
  - `image_gen` / `image_edit`: Prompt trực tiếp + danh sách ảnh mẫu tham chiếu DNA (thêm/xóa ảnh).
  - `character`, `captions`, `export`, `transition`: Chỉnh tham số chính ngay trên card.
  - Tất cả ô nhập đều có `nodrag nowheel`, debounced lưu 300ms.
- [x] **Frontend: Kéo-thả & Dán Clipboard vào Canvas** (`components/canvas/StudioCanvas.tsx`):
  - Kéo-thả nhiều file ảnh từ máy vào canvas -> tự động upload lên thư viện và sinh các node `image` xếp lưới 3 cột.
  - Kéo-thả file `.txt` / `.md` -> tự nhận diện kịch bản tạo node `script` (mode paste) hoặc node `text`.
  - Kéo-thả đè lên node ảnh/kịch bản đang có -> gán trực tiếp dữ liệu vào node đó.
  - Nhấn Ctrl+V khi focus canvas -> tự động tạo node ảnh hoặc kịch bản/văn bản.
- [x] **Nghiệm thu chạy ra MP4 thật từ chính các ô nhập mới**:
  - Đã chạy pipeline thật: Text -> Script (Paste) -> Voice TTS -> HyperFrames Render -> Export.
  - Kiểm chứng `ffprobe` trên file `output/e3_real_output.mp4`:
    - Video: H.264, 1080x1920 (Safe Zone 9:16)
    - Audio: AAC, khớp chính xác thời lượng thoại
    - File size: 146.222 bytes
- [x] **Chụp ảnh giao diện 1440px & 375px (Dark + Light)**:
  - `data/projects/soc-nho-tv/shots/E3_desktop_dark.png` (1440px Dark)
  - `data/projects/soc-nho-tv/shots/E3_desktop_light.png` (1440px Light)
  - `data/projects/soc-nho-tv/shots/E3_mobile_dark.png` (375px Dark)
  - `data/projects/soc-nho-tv/shots/E3_mobile_light.png` (375px Light)
- [x] **Đảm bảo chất lượng mã nguồn**:
  - `cd tool/dashboard && npx tsc --noEmit`: 0 errors.
  - `pytest`: Tất cả các tests core, runner, parser, input đều pass 100%.

## 2. Chưa làm / Chuyển giao tiếp theo (PENDING)
- Kéo-thả file video lớn (>50MB) lên canvas: Hiện tại hỗ trợ tạo node `video_gen` với tên file làm prompt, chưa upload trực tiếp video phân cảnh đa gigabyte lên local storage (sẽ tích hợp thêm chunked upload nếu người dùng yêu cầu).
- Popover tùy chọn phân loại khi thả file `.txt` phân vân giữa Script và Text (hiện tại đang tự động phân loại bằng regex cú pháp kịch bản).

## 3. Chưa kiểm chứng (UNVERIFIED)
- Kiểm thử kéo thả trên trình duyệt Safari iOS thực tế (đã mô phỏng chuẩn qua Chromium mobile viewport 375px).
