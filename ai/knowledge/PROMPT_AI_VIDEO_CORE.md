# Prompt dựng "Core" cho AI Video Studio (động cơ chạy đồ thị, gọi model, nối OmniVoice và HyperFrames)

Đi cùng [PROMPT_AI_VIDEO_STUDIO.md](PROMPT_AI_VIDEO_STUDIO.md) (giao diện, kênh, dự án, canvas). File này mô tả phần bên dưới canvas: mỗi node nhận gì, trả gì, gọi model và công cụ local ra sao, đóng gói thành video MP4 thế nào.

## Hiện trạng project (đã kiểm tra) mà prompt dựa vào
- **Giọng:** `scripts/voice/voice_studio.py` có lệnh `clone`, `speak`, `oneshot`, `list`; chạy OmniVoice trong `integrations/OmniVoice/.venv`; kho giọng ở `assets/voice_vault/<voice-id>/` (giọng Sóc Nhỏ là `soc-nho`); đầu ra MP3 đã chuẩn hóa -14 LUFS. Xem [VOICE_CLONE.md](VOICE_CLONE.md).
- **Video qua API:** `src/gobi/services/media/video_gen_backends.py` gọi hàng đợi fal.ai bằng `FAL_KEY` (gửi việc, thăm dò, tải về), có ước tính giá theo giây và chế độ `--dry-run`.
- **Dựng:** `src/gobi/services/media/hyperframes_engine.py` sinh composition HTML và render MP4 qua HyperFrames; chuẩn nằm ở [HYPERFRAMES_POST_PRODUCTION_STANDARD.md](HYPERFRAMES_POST_PRODUCTION_STANDARD.md). **Lỗi cần sửa:** tệp này import `gobi.adapters.integrations.hyperframes_adapter` nhưng thư mục `src/gobi/adapters` không tồn tại trong repo, và còn gán cứng `PROJECT_ROOT = /Volumes/Data/gobi-social`. Phải viết lại adapter và bỏ đường dẫn tuyệt đối (quy tắc trong CLAUDE.md).
- **Cấu trúc thư mục** đang chuyển sang ba phần `ai/`, `tool/`, `data/`. Mã mới đặt trong `tool/`, dữ liệu dự án trong `data/projects/`. Đọc `ai/AGENTS.md` và `LEGACY_LINKS.md` trước khi tạo thư mục.

## Prompt

```
Hãy xây "Core" của AI Video Studio: động cơ chạy đồ thị node, gọi các model AI trả phí và các công cụ local (OmniVoice, HyperFrames, ffmpeg, Whisper), rồi ra video MP4 hoàn chỉnh. Giao diện canvas (Next.js, React Flow) đã có hoặc do bên khác dựng; Core chỉ phơi ra API và sự kiện để giao diện dùng. Không hardcode đường dẫn tuyệt đối; mọi đường dẫn tính từ gốc repo hoặc thư mục dự án.

# 1. Kiến trúc
- Core là một dịch vụ Python (FastAPI) chạy local ở tool/src/socnhotv/core, vì OmniVoice, Whisper, ffmpeg và adapter HyperFrames đều ở phía Python và cần chạy lâu. Giao diện Next.js gọi Core qua HTTP và nhận tiến độ qua SSE. Không chạy việc nặng trong tiến trình Next.js.
- Sơ đồ ranh giới:
  Giao diện -> API Core -> Bộ chạy đồ thị -> Node executor -> (Provider adapter | Tool adapter) -> Kho tệp.
- Dữ liệu kiểu chung định nghĩa một lần bằng JSON Schema (hoặc Pydantic) rồi sinh kiểu TypeScript cho giao diện, để hai phía không lệch nhau.
- Ngoài HTTP, Core cũng phơi cùng chức năng thành một MCP server (tạo dự án, thêm/sửa node, chạy đồ thị, xem trạng thái, tải kết quả) để một trợ lý AI (Claude Code, agent khác) điều khiển được toàn bộ studio từ xa.

# 2. Hợp đồng dữ liệu (input/output)
Kiểu cổng (port type): text, image, image[], video, audio, script, scenes, character, composition. Chỉ nối được cổng cùng kiểu (hoặc kiểu có quy tắc chuyển rõ ràng, ví dụ image -> image[]). Giao diện báo lỗi khi nối sai.

Artifact (mọi kết quả đều là artifact, không truyền base64 qua lại):
{ id, kind, uri (đường dẫn tương đối trong thư mục dự án), mime, size, hash, meta { width, height, duration, fps, aspect }, provenance { nodeId, runId, provider, model, params, inputHashes, costUsd, createdAt } }

Node:
{ id, type, params, inputs: { portName: artifactRef | literal }, position, ui }
Mỗi loại node khai báo: cổng vào, cổng ra, schema tham số (Zod/Pydantic), hàm ước tính giá, hàm thực thi, và có chạy được ở chế độ mock không.

Danh mục node và vào/ra:
| Node | Vào | Tham số | Ra |
|---|---|---|---|
| Văn bản | - | nội dung | text |
| Ảnh | - | tệp tải lên hoặc từ thư viện | image |
| Nhân vật | - | chọn từ dự án | character (ảnh tham chiếu image[], mô tả khóa, voiceId, bộ nhớ) |
| Kịch bản | text | cách tách cảnh | scenes (mỗi cảnh: prompt ảnh, prompt video, thoại, nhân vật, thời lượng, chuyển cảnh) |
| Phân tích | video hoặc image | mục tiêu | script hoặc scenes (dữ liệu có cấu trúc, qua model nhìn) |
| Tạo ảnh | text, image[] tham chiếu | model, tỉ lệ, độ phân giải, số ảnh, seed | image[] |
| Sửa ảnh | image, image[] tham chiếu, text | model, tỉ lệ | image |
| Tạo video | image (khung đầu), text, image[] tham chiếu tùy chọn | model, thời lượng, tỉ lệ, có âm thanh hay không | video |
| Giọng đọc | text, character | voiceId, tempo, mastering | audio (MP3) + meta.duration |
| Phụ đề | audio hoặc video, text tùy chọn | ngôn ngữ, kiểu | captions (từ, mốc thời gian) |
| Dựng (HyperFrames) | scenes + video[] + audio[] + captions + nhạc nền | tỉ lệ khung, mẫu, chuyển cảnh, ducking | video (MP4) |
| Xuất | video | nền tảng, tên tệp | thư mục thành phẩm + manifest |
Chạy theo từng cảnh: node "Kịch bản" ra N cảnh, các node tạo ảnh/video/giọng sau nó tự nhân bản theo cảnh (map) và cuối cùng gom lại (collect) trước node Dựng.

# 3. Bộ chạy đồ thị
- Kiểm tra đồ thị: không vòng lặp, cổng cùng kiểu, tham số hợp lệ. Sắp xếp theo thứ tự phụ thuộc.
- Bộ nhớ đệm theo mã băm: hash(loại node, phiên bản node, tham số, hash các đầu vào, model). Trùng hash thì dùng lại artifact, không gọi lại model. Có nút buộc chạy lại.
- Chạy: "chạy node này", "chạy từ node này trở xuống", "chạy cả đồ thị". Hàng đợi với số luồng song song tối đa chung và giới hạn riêng cho từng provider (rate limit). Việc dài (video) chạy dạng gửi -> thăm dò -> tải về, có hạn chót và hủy được.
- Trạng thái mỗi node: chờ, sẵn sàng, đang chạy, xong, lỗi, đã hủy, dùng bộ nhớ đệm. Lỗi một cảnh không dừng các cảnh khác; chạy lại chỉ làm phần lỗi. Thử lại có giới hạn với lùi thời gian cho lỗi tạm thời (429, 5xx, hết thời gian), không thử lại lỗi do nội dung bị chặn hay do tham số sai.
- Phát sự kiện qua SSE: node đổi trạng thái, tiến độ, log, chi phí. Lưu nhật ký mỗi lần chạy (run) vào thư mục dự án.
- Chi phí: trước khi chạy tính tổng ước tính từ các node chưa có trong bộ nhớ đệm, hiện cho người dùng xác nhận; có trần chi phí mỗi lần chạy và mỗi ngày do người dùng đặt, vượt trần thì dừng. Ghi sổ chi phí thực tế từng artifact.

# 4. Provider adapter (gọi model trả phí)
Giao diện chung, mỗi nhà cung cấp một adapter:
- image.generate({ prompt, references[], aspect, resolution, n, seed }) -> artifact[]
- image.edit({ image, references[], prompt, aspect }) -> artifact
- video.generate({ prompt, firstFrame, lastFrame?, references?, duration, aspect, audio }) -> artifact (bất đồng bộ: submit -> poll -> fetch)
- text.complete({ system, prompt, schema? }) -> văn bản hoặc JSON theo schema
- vision.analyze({ media[], prompt, schema }) -> JSON có cấu trúc
- voice.speak (dự phòng, ngoài OmniVoice)
Mỗi adapter phải khai báo: ma trận khả năng (nhận ảnh khung đầu không, có âm thanh không, thời lượng và tỉ lệ cho phép), bảng giá để ước tính, ánh xạ lỗi về một tập lỗi chung (xác thực, hết hạn mức, nội dung bị chặn, tạm thời, tham số sai), và chế độ mock.
- Sổ model (models.yaml): tên hiển thị -> provider + id model + khả năng + giá. Model đổi liên tục nên không viết cứng tên model trong mã; thêm hoặc đổi model chỉ sửa sổ này.
- Adapter đầu tiên: (a) Google Gemini API cho ảnh (họ Nano Banana) và Veo cho video; (b) fal.ai, tái sử dụng logic trong src/gobi/services/media/video_gen_backends.py (gửi hàng đợi, thăm dò, tải về, ước tính giá theo giây, FAL_KEY). Để sẵn khung cho Replicate và các nhà khác.
- Khóa API chỉ ở biến môi trường hoặc kho khóa phía máy chủ, không vào mã, không vào nhật ký, không gửi xuống giao diện. Kiểm tra khóa có hiệu lực khi người dùng nhập.
- Mock: ảnh giả có chữ "MOCK" trên ảnh, video giả ngắn, giọng giả. Mặc định bật khi thiếu khóa. Mọi kiểm thử đồ thị chạy bằng mock.

# 5. Tool adapter (công cụ local, điều khiển từ xa)
Mỗi công cụ là một manifest + adapter: { tên, cách gọi (mảng đối số, không ghép chuỗi shell), schema vào, schema ra, kiểm tra sức khỏe, thời gian tối đa, thư mục làm việc }. Chạy bằng subprocess với timeout, giới hạn đường dẫn trong thư mục dự án, truyền log về SSE. Không bao giờ ghép đầu vào của người dùng vào lệnh shell.

5.1 OmniVoice (giọng):
- Dùng scripts/voice/voice_studio.py: speak --voice <voice-id> --script <văn bản hoặc .txt> --output <mp3> [--tempo] [--no-master]. Clone giọng bằng lệnh clone, liệt kê bằng list.
- Chạy trong môi trường riêng integrations/OmniVoice/.venv (biến OMNIVOICE_PYTHON); kiểm tra sức khỏe: gọi list, và xác nhận có thư mục giọng trong assets/voice_vault/<voice-id>/.
- Node Giọng đọc: đầu vào là thoại của cảnh và voiceId của nhân vật (Sóc Nhỏ luôn là soc-nho, theo CLAUDE.md); đầu ra là MP3 kèm thời lượng đo bằng ffprobe. Việc đọc nhiều cảnh chạy tuần tự trên một tiến trình (model nặng, không chạy song song nhiều bản).
- Chỉ clone giọng của chính người dùng hoặc người đã đồng ý; giao diện có hộp xác nhận quyền trước khi clone.

5.2 HyperFrames (dựng và xuất):
- Viết lại adapter bị thiếu: gọi CLI HyperFrames (lint, check, render, preview) bằng npx, bắt log và mã thoát. Bỏ PROJECT_ROOT cứng trong HyperFramesEngine, nhận thư mục làm việc qua tham số.
- Node Dựng nhận: danh sách cảnh có video (hoặc ảnh + chuyển động Ken Burns), giọng đọc từng cảnh, nhạc nền, phụ đề, chuyển cảnh, tỉ lệ khung. Sinh composition HTML từ mẫu, theo HYPERFRAMES_POST_PRODUCTION_STANDARD.md: vùng an toàn 9:16, phụ đề dạng karaoke, ducking nhạc nền khi có giọng, xuất MP4 tất định.
- Thời lượng mỗi cảnh trên dòng thời gian lấy theo thời lượng giọng đọc (ưu tiên) hoặc thời lượng video; chuyển cảnh lấy từ trường transition của cảnh.
- Bắt buộc chạy lint và check trước khi render; lỗi composition trả về giao diện kèm nội dung lỗi.
- Một đồ thị xuất được nhiều tỉ lệ (16:9, 9:16, 1:1, 4:5) bằng cách render lại cùng nguồn, không tạo lại ảnh/video.

5.3 Công cụ phụ: ffmpeg/ffprobe (đo thời lượng, cắt, ghép âm), Whisper (phụ đề có mốc từ), có manifest và kiểm tra sức khỏe như trên.

# 6. Kho tệp và dự án
- data/projects/<projectId>/ gồm graph.json (đồ thị), assets/ (artifact theo hash), runs/<runId>/ (nhật ký, sổ chi phí), outputs/ (video thành phẩm), characters/, scripts/.
- Artifact lưu theo hash nội dung, không trùng lặp. Đồ thị tham chiếu artifact bằng id, không chứa base64. Có lệnh xuất "gói dự án" (đồ thị + artifact cần thiết) và nạp lại, để mang dự án đi nơi khác mà không lệch.
- Chỉ mục dự án trong SQLite cục bộ (mặc định); Supabase là tùy chọn qua lớp Repository, giao diện và Core không phụ thuộc cái nào.

# 7. Quy trình mẫu phải chạy được đầu cuối
Mẫu A, truyện Sóc Nhỏ: Văn bản -> Kịch bản (tách cảnh) -> Nhân vật (soc-nho, ảnh tham chiếu từ assets/soc_nho) -> Tạo ảnh từng cảnh (có tham chiếu) -> Tạo video từ ảnh khung đầu -> Giọng đọc từng cảnh (soc-nho) -> Phụ đề -> Dựng HyperFrames -> Xuất 16:9 và 9:16.
Mẫu B, thời trang lookbook như trong video tham khảo: Ảnh người mẫu -> Sửa ảnh (tách từng món đồ) -> Tạo ảnh bảng ba góc nhìn -> Tạo ảnh bối cảnh có mặc đồ mới -> Tạo video -> Giọng đọc -> Dựng.
Mẫu C, từ video có sẵn: Phân tích (cấu trúc, nhịp cảnh, thoại) -> Kịch bản mới cho nhân vật của dự án -> chạy như mẫu A. Chỉ lấy ý tưởng và cấu trúc, không dùng lại hình, tiếng, lời của người khác.

# 8. An toàn và chi phí
- Mọi lần gọi model trả phí phải qua bước ước tính và xác nhận; không có vòng tự động chạy lặp không giới hạn; có trần chi phí.
- Không đưa nội dung nhạy cảm của người dùng vào nhật ký. Che khóa API trong mọi thông báo lỗi.
- Đăng bài chỉ qua OAuth chính thức của nền tảng, mặc định duyệt tay trước khi đăng.

# 9. Kiểm thử và nghiệm thu
- Kiểm thử đơn vị: kiểm tra đồ thị (vòng lặp, sai kiểu cổng), thứ tự chạy, bộ nhớ đệm theo hash, thử lại và hủy, trần chi phí.
- Kiểm thử hợp đồng cho từng provider adapter bằng phản hồi ghi sẵn (không gọi mạng); kiểm thử tool adapter bằng lệnh giả.
- Kiểm thử đầu cuối bằng mock: mẫu A với 2 cảnh ra được MP4 ở hai tỉ lệ, đổi một node thì chỉ chạy lại phần phụ thuộc.
- Chạy thật có kiểm soát: 1 cảnh, 1 ảnh, 1 video ngắn, báo số tiền thực tế so với ước tính.
- Nghiệm thu: một lệnh API tạo dự án mẫu A, chạy, và trả về đường dẫn MP4 cùng sổ chi phí.

# 10. Giao hàng theo bước (dừng và báo sau mỗi bước)
1. Hợp đồng dữ liệu, Artifact, Node, sổ model, kho tệp, API và SSE tối thiểu, mock provider.
2. Bộ chạy đồ thị: thứ tự, bộ nhớ đệm, song song, hủy, thử lại, chi phí.
3. Tool adapter OmniVoice và ffmpeg/Whisper, node Giọng đọc và Phụ đề.
4. Tool adapter HyperFrames (viết lại adapter thiếu, bỏ đường dẫn cứng), node Dựng, xuất nhiều tỉ lệ.
5. Provider thật: Gemini (ảnh, Veo) và fal.ai, ước tính giá, xác nhận trước khi chạy.
6. Node Phân tích (video -> kịch bản) và mẫu A, B, C.
7. MCP server cho trợ lý AI điều khiển studio, gói dự án xuất/nạp.
8. Nối với giao diện canvas: ánh xạ cổng/loại node, hiển thị trạng thái và chi phí.

# 11. Bổ sung rút ra từ khảo sát các tool hiện có (xem RESEARCH_AI_VIDEO_TOOLS.md)
Các điểm sau ghi đè mục 3 khi mâu thuẫn:
- Kết quả sinh ra không tự bị ghi đè: mỗi node giữ danh sách các lần sinh (generation) kèm tham số và giá; người dùng ghim một lần làm đầu ra của node. Nút "tạo lại" thêm một lần sinh mới, không thay cái cũ. Khi đầu vào của node đổi, các node phía sau chỉ bị đánh dấu "cũ" (stale), không tự chạy lại. Bộ nhớ đệm theo mã băm chỉ dùng cho bước xác định (đo, cắt, ghép, dựng, phụ đề), không dùng để chặn việc tạo lại ảnh/video.
- Chạy một node không tự chạy các node phía trên; thiếu đầu vào thì báo rõ "chưa chạy được: đang chờ ảnh đầu vào". Có lệnh riêng "chạy cả chuỗi".
- Node "Kiểm tra" (cổng chấm điểm): hỏi model nhìn một câu có/không hoặc chấm điểm về ảnh hay video (ví dụ "nhân vật có đúng áo vàng, quần đen, đuôi xù không", "có chữ lạ trong ảnh không") và trả về đạt/không đạt kèm độ tin cậy. Đặt trước bước tạo video để chỉ tiêu tiền khi ảnh đạt; cho cấu hình tự thử lại tối đa N lần hoặc dừng chờ người duyệt.
- Hạn mức chi tiêu: trần mỗi lần chạy, mỗi phiên và mỗi 24 giờ, áp dụng riêng cho lệnh đến từ MCP/agent; vượt trần thì dừng và báo, không tự nâng.
- Địa điểm, đồ vật và giọng cũng là "thực thể" như nhân vật: có bộ ảnh tham chiếu, mô tả khóa, và được chọn vào cổng tham chiếu của node tạo ảnh/video.
- Workflow xuất/nạp dạng JSON mang đi được; về sau có thể đăng một workflow thành API hoặc công cụ MCP.
- Hỗ trợ một nhà cung cấp tổng hợp (fal, Replicate, KIE.ai hoặc OpenRouter) để tăng nhanh số model, ngoài adapter Gemini/Veo.
- Giấy phép: chỉ học ý tưởng từ các dự án mã nguồn mở khác; không chép mã từ dự án AGPL hoặc fair-code.
```

## Ghi chú khi giao cho AI
- **Lỗi có sẵn cần xử lý ở bước 4:** `hyperframes_engine.py` đang import module không tồn tại và gán cứng đường dẫn `gobi-social`. Nếu không sửa, node Dựng không chạy được.
- **Giọng nói và khớp môi:** model video có thể tự sinh tiếng nói, còn OmniVoice thì cho giọng `soc-nho` ổn định. Quy trình trên mặc định dùng giọng OmniVoice đè lên video không tiếng (nhất quán giọng qua các cảnh). Nếu cảnh cần khớp môi thì phải thử riêng, mình chưa kiểm tra khả năng này.
- **Tên model và giá** đổi nhanh, vì vậy prompt yêu cầu để trong sổ `models.yaml`, và cần kiểm tra bảng giá hiện hành trước khi chạy loạt lớn.
- **Quy tắc trong `ai/AGENTS.md`** (chạy đến cùng, tự động hóa trình duyệt) không áp dụng cho đăng bài: prompt yêu cầu đăng qua OAuth chính thức, không điều khiển trình duyệt để đăng.
