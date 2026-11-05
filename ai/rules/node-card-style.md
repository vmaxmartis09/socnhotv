# Quy chuẩn style card node (Studio canvas)

Áp dụng trước cho card **Text** (`typeName === "text"`); các card khác làm sau, theo cùng nguyên tắc.

## 2 chế độ xem
1. **Mặc định (xem)**: chỉ hiện nội dung (text tối đa ~4 dòng, không viền; hover mới hiện viền input). Phần "Trả" chỉ còn một đường gạch ngang. Ẩn nhãn "Cung cấp", mô tả, thống kê, footer.
2. **Chỉnh sửa (mở rộng)**: input giãn vừa đủ nội dung (nhiều thì card cao thêm, không modal, không nút phóng to). Hiện "Cung cấp", mô tả, số từ/ký tự, "Lưu tự động", nút dán, phần "Trả", footer.

## Chuyển chế độ
- Bấm **tiêu đề** card: đổi qua lại 2 chế độ liên tục.
- Click/focus vào input: vào chế độ chỉnh sửa. Bỏ chọn card: về chế độ xem.
- State `expanded` nằm ở `StudioNode`, truyền xuống `NodeBody` → `NodeTextInput`.

## Hiệu ứng
- Mọi phần hiện/ẩn dùng `Reveal` (grid-rows 0fr↔1fr + opacity, 200ms ease-out).
- Chiều cao textarea chuyển bằng CSS transition (đo đích, trả về chiều cao cũ rồi đặt mới).

## Cổng (port)
- Cổng kiểu `text`: dùng **icon file-text làm chính handle** (không ô vuông xám, không chữ "text", không lặp icon ở hàng cổng). Tên cổng chỉ hiện nếu khác tên kiểu.
- Node chỉ có đầu ra (nguồn): không hiện phần "Nhận". Ở chế độ xem, handle ra nằm giữa mép phải card.

## Nhãn
- Không hiện nhãn phụ trùng nghĩa (vd. "Source" cạnh "Cung cấp"); nhãn category chỉ hiện ở node có đầu vào.
- Chi phí `$0.00` ẩn khi bằng 0.

## Bố cục flow
- Khi tải đồ thị luôn `autoLayout` hàng ngang trái → phải theo thứ tự chạy (`lib/graph-layout.ts`).

## Bổ sung
- Cổng text ở hàng "Nhận" cũng chỉ hiện icon (handle), không chữ "text".
- Card Text không có chân card (không `$0.00`, không nút "chạy từ đây xuống").
- Tiêu đề card không cắt "..." — cho xuống tối đa 2 dòng (`line-clamp-2`).
- Không hiện icon trạng thái "ready"/"idle" ở header; chỉ hiện khi running, thành công, lỗi, stale.
- Click vào input: luôn đặt con trỏ ở cuối văn bản khi vừa vào chế độ chỉnh sửa.

## Nhóm card nguồn (đã áp dụng)
`SOURCE_TYPES` trong `StudioNode.tsx` = text, image, character — dùng chung cơ chế xem/chỉnh sửa; `Reveal` ở `components/canvas/Reveal.tsx`.
- **Tải ảnh**: xem = chỉ ảnh (hoặc vùng kéo thả); chỉnh sửa = thêm "Chọn từ Thư viện", "Dán URL".
- **Nhân vật**: xem = ảnh + tên + chip; chỉnh sửa = ô chọn nhân vật, tỉ lệ/gallery, nút mở hồ sơ.
- Icon cổng theo kiểu: text → file-text, image/image[] → images, character → users (làm chính handle). Kiểu khác vẫn dùng ô màu + chữ.
- Nhiều cổng ra ở chế độ xem: handle chia đều theo chiều dọc mép phải card.
- Các card xử lý (Kịch bản, Tạo ảnh/video, Giọng đọc…) giữ nút "chạy từ đây xuống".

## Nhóm card xử lý (đã áp dụng)
`PROCESS_TYPES` trong `StudioNode.tsx` = script, image_gen, video_gen, voice_tts, image_edit, quality_check, vision_analyze, captions, hyperframes_render, export. Dựng phim: chế độ xem giữ timeline (luôn là nội dung chính); Xuất: xem = video hoặc tên file + chip nền tảng.
- Xem: chỉ header + kết quả (tóm tắt phân cảnh / ảnh / video / trình phát âm thanh, hoặc ô trống gợi ý). Ẩn "Nhận", "Làm", mô tả, "Trả". Giữ chân card (chi phí nếu >0, nút chạy từ đây xuống).
- Chỉnh sửa: hiện đủ "Nhận", "Làm" + tham số, "Trả".
- Chế độ xem: handle vào/ra chia đều dọc hai mép card (đỏ nếu thiếu đầu vào bắt buộc).

## Bổ sung (card Văn bản thành giọng nói, áp dụng chung)
- Handle có icon: nhỏ, mờ, nền muted khác màu nền canvas, viền rất nhạt (viền đỏ khi thiếu đầu vào bắt buộc, viền xanh brand khi có thể nối). Icon theo kiểu: text, image, character, audio, video, scenes.
- Không còn nút "chạy từ đây xuống" ở mọi card; chân card chỉ hiện khi chi phí > 0 hoặc có lịch sử tạo.
- Card giọng, chế độ xem: rê chuột thì đọc — ưu tiên văn bản nhận từ node nối vào cổng `text`, nếu không có thì văn bản của chính card; có file audio kết quả thì phát file.
- Bộ chọn giọng responsive: `min-w-0` + nút nghe thử chỉ icon (tooltip), không tràn card.
- Tên card `voice_tts` = "Văn bản thành giọng nói".

## Mặc định & độc lập
- Mặc định mở chế độ **chi tiết**: Nhân vật (`character`), Dựng phim (`hyperframes_render`), Xuất & Phân phối (`export`) — `DETAIL_DEFAULT_TYPES` trong `StudioNode.tsx`. Các card khác mặc định ở chế độ xem.
- Mỗi card toggle độc lập (state cục bộ): mở/đóng card này không ảnh hưởng card khác; bỏ chọn card không tự đóng.
- Card giọng, chế độ xem, không có lời thoại và chưa có audio: rê chuột phát mẫu giọng mặc định (`/voices/<voiceId>/sample`, mặc định soc-nho).

## Tuỳ biến cổng & loại node mới (thanh bên phải → tab Node → "Cổng vào / ra")
- Mỗi node có thể ghi đè cổng riêng: `params._ports = {inputs, outputs}` (+ `_customName`). Node vẫn thuộc loại gốc nên dùng chung bộ chạy.
- Cổng tuỳ biến có `mapTo`: ánh xạ về cổng/tham số của node gốc (vào) hoặc bí danh cổng ra gốc (ra). Cổng không ánh xạ chỉ để nối dây, không ảnh hưởng kết quả chạy.
- "Lưu cho node này" = chỉ node đang chọn (gỡ dây nối vào cổng đã xoá). "Lưu thành loại node mới" = tạo `custom:<tên>` (`baseType` = loại gốc), lưu theo dự án (`data/projects/<id>/custom_node_types.json`) hoặc dùng chung (`data/shared/custom_node_types.json`) qua `/custom-node-types`; xuất hiện trong menu thêm node.
- Backend: `NodeRegistry.effective_ports` dùng ở validator và graph_runner. Hạn chế: bí danh cổng ra chưa áp dụng cho kết quả ghim (pinned generation).

## Đầu vào nhập tay & giá trị mặc định
- Cổng vào không chỉ nhận dây nối: thanh bên phải → tab Node → mục "Đầu vào" cho phép gõ text, **tải lên** hoặc **chọn từ dự án** (ảnh/video/âm thanh) — component `PortValueInput`. Giá trị lưu ở `params[tên cổng]` (đường dẫn tệp trong dự án).
- Backend dựng Artifact từ đường dẫn tệp (`_literal_artifact`) nên bộ chạy xử lý như đầu vào nối dây. Upload/kho dự án hỗ trợ thêm âm thanh (mp3/wav).
- Cổng vào có `defaultValue` (text): dùng khi không nối dây và chưa nhập; validator coi là đã thoả cổng bắt buộc.
- Form tuỳ biến cổng dùng cùng kiểu điều khiển với phần thông số: ô `h-8 rounded-md border bg-card text-xs`, nhãn `text-[13px] text-muted-foreground`.

## Nguồn cho cổng vào (tab Node → "Đầu vào")
Mỗi cổng vào chọn được nguồn bất kỳ, bằng cùng một khối `PortValueInput`:
- **Node**: output của node khác (lọc theo kiểu tương thích, không tạo vòng) → tạo dây nối ngay.
- **Tải lên** / **Dự án**: tệp ảnh/video/âm thanh (cổng media).
- **Nhân vật**: thuộc tính nhân vật (text: tên, mô tả, prompt lock, mã giọng, chiều cao; ảnh: ảnh chính/tham chiếu; audio: giọng mẫu). Sao chép giá trị vào cổng.
- **Gõ trực tiếp** cho cổng text.
- Đang nối dây thì hiện nguồn + nút **Gỡ dây**; có giá trị nhập tay thì có nút bỏ (X). Các panel nguồn mở inline bằng `Reveal`, mỗi lúc chỉ mở một panel.

## Dây nối & nhận giá trị trên card
- Bấm vào dây → dây được chọn và hiện nút xoá (icon thùng rác) ở giữa dây (`StudioEdge`, đăng ký làm edge type `default`).
- Không cho nối ngược: kéo dây phải bắt đầu từ cổng ra (source) sang cổng vào (target); kéo từ cổng vào về cổng ra bị từ chối kèm thông báo.
- Chế độ chi tiết của card: bấm một dòng ở "Nhận" để mở khung chọn nguồn ngay dưới (node khác / tải lên / dự án / nhân vật / gõ trực tiếp, và gỡ dây) — cùng component `PortValueInput` với tab Node.

## Chuẩn dữ liệu đầu vào (kiểu `script` & `character`)
**Kịch bản tập** (`content/episodes/<tập>/KICH-BAN-*.md`) được `engine/episode_script.py` phân tích thành dữ liệu chuẩn (API: `GET /data/projects/{id}/script-data/{tập}`):
- `Script`: id, episodeNumber, title, series, season, durationSec, aspect, style, leadCharacter, cast[{name,heightCm}], setting{name,code,timeOfDay}, lesson, mantra, summary, environmentPromptLock, characters[{name,heightCm,species,personality,catchphrase,voiceDirection,do,dont,promptLock}], scenes[].
- `Scene`: index, title, startSec, endSec, location, purpose, shots[].
- `Shot`: id (S01…), sceneIndex, sceneTitle, startSec, endSec, durationSec, shotSize, camera, characters[], action, expression, actingNotes, speaker, dialogue, voiceDelivery, sfx, bgm, imagePrompt, videoPrompt, negativePrompt.
- Mỗi shot cũng xuất sang `scenes` (cổng `scenes`) với `sceneNumber, shotId, title, imagePrompt, videoPrompt, dialogue, speaker, durationSec, characters, shotSize, camera, sfx, bgm`.

**Chọn kịch bản làm đầu vào** (nút "Kịch bản" ở `PortValueInput`): lưu tham chiếu `{"$ref":"script", episode, facet, shot?, label}` trong `params[cổng]`; backend giải ra giá trị thật khi chạy (`_resolve_script_ref`) nên luôn khớp file kịch bản mới nhất.
- Cổng `text`: fulltext, summary, lesson, mantra, dialogue_all, environment; hoặc một shot cụ thể (dialogue, imagePrompt, videoPrompt, action, expression).
- Cổng `scenes`: facet `scenes`. Cổng `script`: facet `script` (toàn bộ cấu trúc).

**Nhân vật**: thuộc tính chọn được theo nhóm — Thông tin (tên, vai trò, mô tả, chiều cao, tỉ lệ), Prompt (prompt lock), Tính cách & bộ nhớ (tính cách, câu cửa miệng, thói quen, sự kiện), Giọng (mã giọng, tốc độ, giọng mẫu, file giọng), Ảnh (chính, tham chiếu, kho hình ảnh theo góc), Clip đã tạo, Xuất hiện theo tập. Giá trị nhân vật được sao chép vào cổng tại thời điểm chọn.
- Màu dây luôn theo kiểu dữ liệu của cổng ra nguồn (`StudioEdge` tự tính, kể cả dây nạp từ file): text/script/scenes/captions xám, character xám đậm, image xanh lam, video/composition cam, audio vàng.

## Chính sách nội dung (policy) — xuyên suốt dự án
- Kiểu cổng mới `policy` (màu đỏ nâu `#9f3a38`, icon ShieldCheck) và node `policy` ("Chính sách nội dung", nguồn không đầu vào, ra cổng `policy`; `extraTerms` = từ khoá bổ sung riêng của node).
- Chính sách của dự án lưu ở `data/projects/<id>/policy.json` (tự có mặc định "Made for Kids"); API `GET/PUT /data/projects/{id}/policy`, `POST .../policy/check`. Sửa ở **Project tab → Chính sách nội dung** hoặc tab Node của card Kiểm tra chất lượng / Chính sách (`PolicyEditor`).
- Cấu trúc: `mode` (`standard` chỉ chặn mức `block`; `strict` cảnh báo cũng chặn), `scopes` (lời thoại, caption, kịch bản, prompt), `rules[{id,category,label,severity,enabled,terms[],note}]`, `allowlist[]`. Khớp theo ranh giới từ, không phân biệt hoa/thường, GIỮ dấu tiếng Việt (nhập thêm biến thể không dấu nếu cần).
- Card **Kiểm tra chất lượng** luôn kiểm chính sách: nhận `text`, `captions`, `scenes`, `policy` (tuỳ chọn, mặc định chính sách dự án); mặc định tự quét (`policyAutoScan`) mọi lời thoại/prompt/caption đã sinh ra trong flow; xuất `pass_fail` (kèm vi phạm) và `violations`. Có vi phạm chặn → không đạt. `media` không còn bắt buộc (kiểm chính sách thuần văn bản được).
- Hạn chế: khớp từ khoá không hiểu ngữ cảnh (vd. "không đánh nhau" vẫn khớp "đánh nhau" — dùng `allowlist` hoặc mức "cảnh báo").
- Chính sách có mục điều hướng riêng **"Chính sách"** (icon khiên) trong khung phải, giữa Node và Công cụ (Alt+7); nội dung là `PolicyTab` → `PolicyEditor`.
