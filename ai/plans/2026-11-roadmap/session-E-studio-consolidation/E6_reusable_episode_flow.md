# E6 — Một flow chạy cho nhiều kịch bản (dàn nhân vật tự đổi) + cổng kiểm định

> Viết 2026-11-06. Trạng thái: **kế hoạch; chỉ cổng kiểm định (mục 3) đã làm.**
> Vấn đề: flow Tập 1 có 3 node Nhân vật cố định (Bi, Mun, Mẹ). Tập 2 có thể chỉ có Bi + Koala, tập 3 có 5 nhân vật. Hiện phải dựng lại flow mỗi tập, và flow không thể "lặp qua nhiều kịch bản".

## 1. Nguyên nhân

Số nhân vật nằm trong **cấu trúc đồ thị** (mỗi nhân vật = 1 node + 3 dây), nên đổi tập là đổi đồ thị. Muốn tái dùng thì số node phải **không phụ thuộc số nhân vật**: dàn nhân vật là **dữ liệu** chạy qua 1 node, không phải N node.

## 2. Thiết kế: node "Dàn diễn viên" (`cast`)

Một node thay cho N node Nhân vật:

| Cổng | Kiểu | Ý nghĩa |
|---|---|---|
| vào `script` | scenes / script | kịch bản của tập; node tự đọc `cast` (danh sách nhân vật xuất hiện) |
| vào `lines` | dialogue | lời thoại có người nói |
| ra `characters` | character[] | hồ sơ từng nhân vật trong tập (tên, chiều cao, giọng, aliases) |
| ra `reference_images` | image[] | ảnh DNA của **mọi** nhân vật trong tập (đã gắn `characterId`, ảnh node ảnh cảnh lọc theo từng cảnh như hiện nay) |
| ra `voice` | voice_clips | giọng từng câu của mọi nhân vật (chức năng Nói chạy cho cả dàn) |

- **Tự đổi theo kịch bản:** `cast` lấy danh sách nhân vật từ kịch bản (`episode_script.parse_episode_markdown` đã có trường `cast`/`characters`), ghép với hồ sơ dự án bằng `match_speaker`/aliases (đã làm ở E5 bước 3–4). Tập 2 ít/nhiều nhân vật hơn thì **đồ thị y nguyên**.
- **Ghi đè tay:** `params.include` / `params.exclude` (thêm nhân vật khách mời, bỏ nhân vật phụ), `params.voiceOverrides {characterId: voiceId}`.
- **Nhân vật không có trong hồ sơ dự án / chưa có giọng:** báo ngay trên node và trong báo cáo kiểm định (không đọc bằng giọng Sóc Nhỏ).
- Giữ nguyên node `character` (cho flow KOC 1 người hoặc khi muốn kiểm soát từng nhân vật). `cast` dùng lại cùng hàm `_character_info`, chức năng Nói và cache từng câu của E5, nên phần lớn là gom lại, không viết mới.

Flow Tập 1 sau E6: **Kịch bản → Dàn diễn viên → Ảnh cảnh → Kiểm định → Dựng → Xuất = 6 node**, dùng cho mọi tập.

## 3. Cổng kiểm định (ĐÃ LÀM 2026-11-06)

Node `quality_check` đã có từ trước (chấm ảnh + quét chính sách nội dung của dự án trên lời thoại/prompt/phụ đề) nhưng:
- không có trong flow Tập 1;
- kết quả "không đạt" chỉ là báo cáo, node sau vẫn chạy → vẫn dựng video.

Đã sửa:
- `quality_check.params.blockOnFail: true` → không đạt thì **node lỗi** (báo cáo vi phạm nằm trong thông báo lỗi) và mọi node phía sau bị bỏ qua, không tốn công dựng. Mặc định `false` (giữ hành vi cũ).
- `hyperframes_render` có cổng vào `gate` (text): nối `quality_check.pass_fail` vào đó để đặt kiểm định **trước** dựng.
- Flow Tập 1 hiện 8 node: thêm "Kiểm định chính sách (chặn trước khi dựng)" nhận `scenes` + `lines` (dialogue→text) từ Kịch bản, nối `gate` của Dựng.
- Test: `tests/test_dialogue_voice.py::test_quality_gate_*` (vi phạm → render bị bỏ qua; kịch bản sạch → qua).

Chưa làm: chấm điểm ảnh bằng model nhìn khi chạy thật (cần Gemini, tốn phí), tự sửa câu vi phạm, và hiển thị vi phạm ngay trên thẻ.

## 3b. Chính sách của dự án = 1 tệp, phải tuân thủ (ĐÃ LÀM 2026-11-06)

- Chính sách dự án là **một tệp** `data/projects/<id>/policy.json`. Tệp chính sách văn xuôi (vd. "chính sách youtube.md", 167 KB) nhập qua `POST /data/projects/{id}/policy/import` được nhận diện (`looks_like_prose`) và lưu thành **tài liệu** `policy/<tên>.md` + mục `documents` (id, file, chars, sha, sections) trong `policy.json`. Trước đây tệp này bị tách thành ~2300 "từ cấm" vô nghĩa và sẽ chặn mọi nội dung.
- Đã nhập chính sách YouTube cho `soc-nho-tv` (60 mục); 8 quy tắc từ cấm cũ giữ nguyên. Bản sao lưu: `policy_before_youtube.json` (scratchpad).
- **Tuân thủ:**
  - `hyperframes_render` luôn quét chính sách (từ cấm) trên lời thoại/prompt/phụ đề và **từ chối dựng** khi vi phạm, dù flow có node Kiểm định hay không (`policy.enforce`, mặc định bật).
  - `quality_check` đối chiếu nội dung với tài liệu chính sách bằng model AI ở **chế độ thật** (gửi tài liệu + nội dung, trả đạt/không đạt + mục vi phạm). Chế độ Mock chỉ báo "chưa kiểm theo tài liệu".
- Chưa làm: màn hình Policy hiện tài liệu/mục; tách tài liệu thành checklist nhỏ để giảm token; kiểm ảnh/thumbnail theo tài liệu.

## 4. Chạy lặp qua nhiều kịch bản

Hai cách, đề xuất làm cách A trước:

**A. "Chạy cho các tập" (batch, mức dự án)** — nút ở thanh chạy: chọn nhiều tập → với mỗi tập, runner **nhân bản đồ thị mẫu**, đặt `script.episodeId = <tập>`, chạy tuần tự (hoặc 2 tập song song), lưu kết quả vào `runs/<run>/<episodeId>/` và `output/<episodeId>/`. Đồ thị mẫu **không bị sửa**. Có chi phí tổng ước tính trước khi chạy (SpendGuard), tập lỗi không làm hỏng tập khác, báo cáo từng tập (đạt kiểm định / bị chặn / lỗi).
  - API: `POST /projects/{id}/run-episodes {graph, episodeIds[], mock, concurrency}` → danh sách `GraphRunSummary` theo tập.
  - Cache: kết quả node theo `(graphId, episodeId, nodeId)` để chạy lại tập đã làm không tốn phí.
  - UI: hộp chọn tập (đã có `fetchProjectScriptEpisodes`) + bảng tiến trình theo tập dùng lại thanh tiến trình đã làm.

**B. Node "Lặp theo tập" ngay trong đồ thị** — linh hoạt hơn nhưng đồ thị phải biểu diễn vòng lặp (cổng danh sách lồng nhau), validator, cache, tiến trình đều phức tạp. Để sau, khi cần lặp ở chỗ khác ngoài "cả flow".

## 5. Các bước làm

1. **Đọc dàn nhân vật từ kịch bản** (`cast` của `parse_episode_markdown`) + ghép hồ sơ: hàm thuần, có test trên 3 tập mẫu có số nhân vật khác nhau.
2. **Node `cast`** (đăng ký, handler gọi lại `_character_info` + chức năng Nói cho từng nhân vật, cổng ra danh sách); `image_gen.references` nhận `reference_images` của cả dàn (đã hỗ trợ nhiều ảnh gắn `characterAliases`).
3. **Dựng tay flow mẫu** "Tập (tái dùng)": 6 node; thử Tập 1 rồi tập có số nhân vật khác.
4. **`run-episodes`** (batch) + cache theo tập + hộp "Chạy cho các tập" trong Studio.
5. Chuyển preset "Tập hoạt hình" sang flow mới; ghi `NODE_PARAMS_CONTRACT.md`.

## 6. Cần bạn quyết

- Có muốn **một nhân vật thiếu giọng/hồ sơ làm cả tập dừng**, hay **bỏ qua nhân vật đó và báo**? (đề xuất: dừng ở kiểm định, vì đọc sai giọng là lỗi nặng)
- Chạy batch **tuần tự** hay song song 2 tập? (đề xuất: tuần tự — render HyperFrames đang chặn Core, song song sẽ không nhanh hơn)

## 7. Giới hạn đã biết liên quan

- Render HyperFrames chạy đồng bộ làm Core không phản hồi trong ~5 phút/10 phút video; batch nhiều tập cần đưa render ra tiến trình riêng trước (đã ghi ở E5 mục 10).
