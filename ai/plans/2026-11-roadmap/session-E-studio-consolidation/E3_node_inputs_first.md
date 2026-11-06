# E3 — ƯU TIÊN SỐ 1: Node phải NHẬP ĐƯỢC liệu (text, ảnh mẫu, kịch bản) và chạy ra video thật

Bạn là SESSION E3 (Node nhập liệu), session ĐỘC LẬP chạy SONG SONG với session E2 (`E2_lean_studio.md`), không chờ nhau. Đọc `NODE_PARAMS_CONTRACT.md` cùng thư mục TRƯỚC: nó chốt tên tham số node và phân vùng file giữa E3 và E2 (bạn sở hữu `components/canvas/**` trừ `StudioStickToolbar.tsx`, `NodeTab.tsx`, `canvasSlice.ts`, `i18n/request.ts`, backend engine/registry/validator). Việc đầu tiên (trong 10 phút, commit riêng): viết lại `i18n/request.ts` thành loader tổng quát nạp thêm `nodes.*` và `studio.*`. Được sửa `graph_runner.py` ở mức tối thiểu cần thiết, có test. Làm đến cùng, tự debug, không hỏi lại. Đọc: `CLAUDE.md`, memory UI dự án (spacing gọn; nút thêm = thẻ nét đứt; cùng thực thể = chung component), skill `ui-ux-pro-max`.

## 0. Vấn đề thật (đã đọc code 2026-11-04)
Các session trước làm nhiều chức năng phụ nhưng **cốt lõi Studio còn thiếu: không nhập được dữ liệu vào node.**
- `components/canvas/NodeBody.tsx`: thân card **chỉ đọc** (node `text` chỉ in `line-clamp-5`, node `image/character_image/scene` chỉ `ImagePreview`, node `script` chỉ liệt kê dòng). Không có ô nhập trên card.
- `components/studio/tabs/NodeTab.tsx` (panel phải) chỉ có textarea cho `text`/prompt; **không có chỗ tải ảnh** (không `type="file"`, không dán, không chọn từ thư viện) → node `image` (`params.uri` luôn rỗng) và ảnh mẫu tham chiếu không dùng được. Chỉ `ProjectTab` có upload thư viện, node không nối được.
- Node `script` (`registry.py`): cổng vào chỉ là `text` "ý tưởng" rồi AI viết; **không có cách dán kịch bản có sẵn**. Params chỉ `targetSceneCount/targetDurationSec`.
- Kéo-thả trên canvas chỉ nhận nhân vật/loại node (`StudioCanvas.tsx` ~1054–1070), không nhận file ảnh/video/văn bản từ máy.
Hậu quả: người dùng không thể làm video từ nội dung của chính mình, dù đã có template, social, intel…

## 1. Yêu cầu (làm đúng thứ tự, mỗi mục kiểm trình duyệt thật rồi commit)

### 1.1 Mỗi node có "vùng NHẬP" ngay trên card (không cần mở panel phải)
Quy tắc chung: với mỗi cổng vào mà **chưa nối dây**, card hiện ô nhập trực tiếp ("nối dây hoặc nhập tay"); đã nối dây thì ô nhập mờ/ẩn và hiện "Nhận từ <tên node>". Mọi ô nhập có `nodrag nowheel` để không kéo nhầm canvas; lưu qua `updateNodeParams` (debounce 300ms) và đánh dấu node `stale` đúng cơ chế sẵn có.
- **`text`**: textarea ngay trên card (tự co giãn 3–10 dòng, đếm từ/ký tự), nút dán, nút "mở rộng" sang editor lớn (modal) cho văn bản dài.
- **`image` / `character_image` / `scene`**: vùng thả ảnh trên card: **kéo-thả file**, bấm **"Chọn ảnh"**, **dán Ctrl+V**, **chọn từ Thư viện dự án**, hoặc **dán URL ảnh**. Upload qua API có sẵn `POST /projects/{pid}/library/upload` (body `{name, data(base64)}`), lấy `uri` trả về gán vào `params.uri`/`name`; xem trước bằng `/projects/{pid}/files/<uri>`. Nút đổi/xoá ảnh. Kiểm tra định dạng png/jpg/webp, giới hạn dung lượng, hiện lỗi rõ.
- **`script`**: công tắc 2 chế độ ngay trên card — **"AI viết từ ý tưởng"** (hiện textarea ý tưởng nếu cổng `text` chưa nối) và **"Dán kịch bản có sẵn"** (textarea lớn). Có chỉ dẫn định dạng chấp nhận: mỗi cảnh ngăn bằng dòng trống hoặc `---` hoặc dòng `Cảnh N:`; trong cảnh dòng `Tên nhân vật: lời thoại` là thoại, các dòng còn lại là mô tả hình ảnh/hành động. Xem trước ngay danh sách cảnh đã tách (số cảnh, thoại, mô tả) trước khi chạy.
- **`voice_tts`**: ô lời đọc trực tiếp nếu cổng `text` chưa nối (mặc định rỗng, không dùng câu mặc định giả); chọn giọng ngay trên card (dùng `VoiceSelectorWithClone`).
- **`image_gen` / `image_edit` / `video_gen`**: ô prompt trực tiếp + vùng **ảnh mẫu tham chiếu** (kéo-thả/chọn thư viện/chọn nhân vật, nhiều ảnh). Kiểm trong `registry.py` các cổng vào ảnh tham chiếu (`image`, `first_frame`, `reference`…): nếu thiếu cổng cho ảnh mẫu thì thêm, và nối xuống provider (`google_provider`/`fal_provider`/`replicate_provider`) khi provider hỗ trợ ảnh tham chiếu; provider nào không hỗ trợ thì báo rõ trong UI "model này không dùng ảnh mẫu".
- **`character`**, **`captions`**, **`export`**, **`transition`**: chỉnh tham số chính ngay trên card (chọn nhân vật, kiểu chữ, tên file, kiểu chuyển), không chỉ ở panel phải.
- Panel phải `NodeTab` giữ vai trò "chi tiết nâng cao", dùng **chung component** với card (không viết 2 bản).

### 1.2 Kéo-thả file vào canvas
Thả file từ máy lên canvas: ảnh → tạo node `image` đã có ảnh (nhiều file → nhiều node, xếp lưới gọn); video → node nguồn video (dùng `video_gen`/đầu vào video hiện có nếu có, nếu chưa có thì chỉ thông báo chưa hỗ trợ); `.txt`/`.md` → node `text` hoặc `script` (hỏi bằng 1 popover nhỏ "Dùng làm: Văn bản / Kịch bản"); thả vào đúng node ảnh/script đang có thì gán vào node đó. Dán từ clipboard (ảnh/văn bản) khi canvas đang focus cũng tạo node tương ứng.

### 1.3 Backend: kịch bản dán sẵn không cần AI
Trong `core/engine/graph_runner.py` (nhánh `node_type == "script"`, ~dòng 514): nếu `params.mode == "paste"` thì **tách kịch bản bằng bộ phân tích tất định** (không gọi LLM, chi phí 0), xuất đúng `scenes`, `prompt`, `dialogue` như chế độ AI. Đặt bộ phân tích ở `tool/src/socnhotv/core/engine/script_parser.py` (hàm thuần, có `test_script_parser.py`: nhiều kiểu ngăn cảnh, tiếng Việt có dấu, thoại nhiều nhân vật, kịch bản 1 đoạn không ngăn → tách theo câu/độ dài). Thêm vào `registry.py` default_params của `script`: `mode: "ai" | "paste"`, `rawScript: ""`. Bỏ các giá trị mặc định giả trong runner (ví dụ câu "Sóc Nhỏ và Chiếc Răng Sâu", "Chào các bạn, mình là Sóc Nhỏ Bi nè!" khi không có đầu vào): thiếu đầu vào thì node báo lỗi rõ "thiếu nội dung" (validator `core/engine/validator.py` cũng cảnh báo trước khi chạy), không tự bịa nội dung.

### 1.4 Chạy ra video thật, kiểm chứng đầu-cuối bằng chính các ô nhập mới
Tạo đồ thị mẫu **chỉ bằng thao tác UI** (không sửa file graph.json bằng tay): `text`(ý tưởng) → `script`(chế độ dán) → `voice_tts` → `captions` → (`image` tải ảnh mẫu của bạn) → `hyperframes_render` → `export`. Chạy bằng nút Chạy sẵn có; kiểm ra file mp4 thật (ffprobe: kích thước đúng nền tảng 1080×1920, có audio, có phụ đề, thời lượng khớp giọng) và phát được ngay trong card `export`. Thử thêm: 3 ảnh mẫu → 3 cảnh. Lỗi thiếu đầu vào phải hiện ở đúng node.
Viết `tool/tests/test_script_parser.py` và 1 test API chạy đồ thị mock có `script.mode=paste`.

### 1.5 Báo tiến độ cho E2 (không chờ nhau)
E2 chạy song song và sinh preset đồ thị theo `NODE_PARAMS_CONTRACT.md`. Ngay khi runner chế độ `paste` + `script_parser` xong và test pass, ghi dòng `RUNNER_PASTE_DONE` vào `status/E3.md` và commit. Đừng đổi tên/kiểu tham số đã chốt trong hợp đồng; cần đổi thì ghi `status/REQUESTS.md` và giữ tương thích ngược.

## 2. Nghiệm thu (làm thật trong trình duyệt 1440px và 375px, dark + light)
1. Thêm node Văn bản → gõ trực tiếp trên card → lưu, reload còn nguyên.
2. Thêm node Ảnh → kéo 1 ảnh từ máy vào card → hiện xem trước; Ctrl+V dán ảnh khác → đổi được; chọn từ Thư viện được; file sai định dạng báo lỗi.
3. Thả 3 ảnh lên canvas → ra 3 node ảnh xếp gọn.
4. Node Kịch bản: dán 1 kịch bản 5 cảnh có thoại → xem trước tách đúng 5 cảnh → chạy không gọi LLM (chi phí $0, kiểm log).
5. Đồ thị đầu-cuối ở 1.4 ra mp4 thật đúng kích thước, có tiếng + phụ đề.
6. `cd tool && .venv/bin/python -m pytest -q` pass; `npx tsc --noEmit` không lỗi mới ở phần đã sửa; không còn Next "Issues" ở Studio.
7. Chụp ảnh vào `data/projects/soc-nho-tv/shots/E3_*.png`; ghi `status/E.md` (đã làm/chưa làm/chưa kiểm chứng).

## 3. Luật
- Không thêm trang/tab/tính năng ngoài danh sách trên. Không động tới social/intel/sources/products ở file này (E2 lo việc cắt).
- Chỉ sửa backend ở `graph_runner.py` (nhánh script, bỏ mặc định giả), `registry.py` (params/cổng), `validator.py`, `script_parser.py` mới, providers chỉ khi nối ảnh mẫu; kèm test. Không xoá dữ liệu người dùng.
- Cổng 3000 không được tắt; cổng 8000 chạy lại bằng `--reload` (core đang chạy bản cũ). `git add` theo đường dẫn, không `git add -A` (session D còn ghi `data/shared/knowledge`).
- Icon: Morphicons, không `lucide-react`. i18n vi/en cho mọi nhãn mới.
