# V1 — MỤC TIÊU TỐI THƯỢNG: tạo ra 1 video AI 45 giây, chủ đề MỚI, hoàn toàn từ Studio (flow editor chạy thật)

Bạn là SESSION V, session DUY NHẤT đang sửa code lúc này (E2/E3/S đã xong). Làm đến cùng; dùng MỌI cách hợp lệ để flow trong editor chạy ra video thật; "chưa đẹp" được, "không ra video" thì không. Tự debug tận gốc, không hỏi lại điều có thể tự suy ra, không báo xong khi chưa vượt cổng kiểm ở mục 3.
Đọc trước: `CLAUDE.md`, `data/projects/soc-nho-tv/characters/SCALE_LOCK.md`, `status/{E,E2,E3}.md`, skill `hyperframes`, `hyperframes-core`, `hyperframes-cli`, `hyperframes-animation`, `hyperframes-audio`, `embedded-captions`, `vietnamese-voice-clone`.

## 0. Thực trạng đã kiểm chứng (2026-11-04 22:40)
- Core 8000 và Studio 3000 đang chạy (`--reload`). 142 test backend báo pass. Bộ "Tạo video 3 bước", `script_parser` (paste), nhập liệu trên card, kéo-thả đã có.
- **Nhưng "video thật" mà E3 báo (`output/e3_real_output.mp4`) chỉ dài 2,57 giây** — chưa ai chứng minh 1 video hoàn chỉnh 45 giây. Các lần "chạy hoàn thành" của E2 chỉ là `isSuccess: true`, không kiểm nội dung.
- **Chưa có provider AI thật**: `/providers` → chỉ `mock` configured; `google`, `fal`, `replicate` = false (chưa có khoá trong key_vault). Mock không phải AI thật. HyperFrames CLI có (`cd tool/dashboard && npx --no-install hyperframes --version` → 0.9.12); `ffmpeg/ffprobe` có; `torch` + MPS có; `edge-tts`, `faster-whisper` có; voice `soc-nho` ở `data/shared/voice_vault/soc-nho`; ảnh DNA nhân vật ở `data/projects/soc-nho-tv/characters/{soc_nho,koala}`.
- Phiên trước bị cắt vì "Individual quota reached" giữa chừng → **làm theo từng bước nhỏ, ghi checkpoint vào `status/V.md` sau MỖI bước, commit nhỏ, không đọc lại file lớn vô ích, không chụp ảnh thừa**, để bị cắt vẫn chạy tiếp được.

## 1. Đích (cụ thể, đo được)
Một video **9:16, 45 giây (±3s)**, **chủ đề MỚI** không trùng các chủ đề đã có (Sóc Nhỏ & chiếc răng sâu, hạt dẻ thần kỳ, đếm số tiếng Anh, bàn chải điện, đuôi sóc…). Chủ đề mặc định: **"Vì sao cầu vồng có nhiều màu?"** (Sóc Nhỏ Bi dẫn, Koala phụ hoạ; giải thích đúng khoa học ở mức trẻ em: ánh sáng trắng gồm nhiều màu, giọt mưa khúc xạ/tán sắc, đỏ ngoài–tím trong, quy ước 7 màu). Tự kiểm sự thật trước khi dựng.
Bắt buộc tạo bằng **thao tác trong Studio** (Tạo video / hoặc dựng đồ thị trên canvas bằng các ô nhập mới) rồi bấm **Chạy**; kết quả hiện ở node `export` và tab Jobs. Điều khiển UI bằng trình duyệt (Ego Lite theo CLAUDE.md, hoặc trình duyệt tích hợp) và chụp bằng chứng. **Không** dựng video bằng script ngoài rồi chép file vào `output/`.

## 2. Thang chất lượng — luôn có đường ra video
- **Tier 0 (đảm bảo, 100% cục bộ, làm TRƯỚC):**
  - Giọng: `soc-nho` bằng OmniVoice cục bộ (MPS); lỗi/quá chậm sau 3 cách → `edge-tts` giọng vi-VN và ghi rõ `voice_fallback` trong báo cáo. Qua chuỗi mastering chuẩn (de-esser, EQ presence, nén 4:1, -14 LUFS).
  - Hình: nền/minh hoạ từng cảnh dựng bằng **HyperFrames HTML/CSS/SVG/GSAP** (cầu vồng vẽ dần bằng SVG draw-on, mặt trời, mưa, lăng kính tán sắc, thanh 7 màu, kính lúp…), + **ảnh DNA nhân vật thật** của Sóc Nhỏ/Koala (không vẽ nhân vật mới, đúng tỉ lệ Bi 100cm/Koala 150cm) với chuyển động nhẹ (nhún, nghiêng, zoom Ken Burns). ≥ 6 cảnh khác nhau rõ rệt.
  - Phụ đề từ khoá word-level đồng bộ giọng (karaoke), trong safe-zone TikTok (trên 180px, dưới 320px); nhạc nền nhỏ có ducking (từ `data/shared/music_sfx`, hoặc tạo bed đơn giản bằng ffmpeg nếu thiếu).
- **Tier 1 (nâng cấp nếu có khoá):** nếu key_vault có Gemini/fal/Replicate → `image_gen` với ảnh tham chiếu nhân vật cho nền từng cảnh (trong hạn mức `spend_guard`, xác nhận ước tính chi phí trong UI một lần). Không có khoá thì BỎ QUA, không dừng, không đòi người dùng.
- **Tier 2 (tuỳ chọn):** 1–2 clip `video_gen` hero nếu provider hỗ trợ và còn hạn mức.
- Mock provider chỉ để kiểm đường ống; **không được gọi video mock là "AI"**; báo cáo ghi rõ mỗi cảnh dùng nguồn nào (local-HTML / ảnh DNA / provider X).
- Render bằng **HyperFrames CLI** (`HyperFramesEngine`); chỉ cho phép fallback FFmpeg sau khi CLI lỗi 3 lần với 3 cách sửa khác nhau, và phải ghi `FALLBACK_USED` + nguyên nhân gốc vào báo cáo (và sửa nguyên nhân nếu làm được).

## 2B. Trải nghiệm chạy & lưu sản phẩm — BẮT BUỘC, kiểm bằng chính giao diện
Video phải ra từ chính tool đang xây, và người dùng phải **thấy** tool đang làm gì, **thấy** job đang chạy, và **thấy** thành phẩm nằm ở đâu trong dự án.

### A. Các công đoạn chạy tuần tự, có hoạt ảnh, phản ánh việc thật
- Chuỗi công đoạn chuẩn (stepper): **Kịch bản → Giọng đọc → Phụ đề → Hình cảnh → Dựng (HyperFrames) → Xuất & Lưu**. Trên canvas mỗi node có trạng thái `chờ / đang chạy / xong / lỗi`: node đang chạy có hoạt ảnh rõ (viền chạy/xung nhịp/spinner + % nếu có), dây đang truyền dữ liệu có hoạt ảnh, node xong có dấu tích, node lỗi đỏ kèm lý do ngắn + nút "Chạy lại từ node này". Chạy theo đúng trục trái→phải, node phụ thuộc không chạy sớm, trạng thái không nhảy cóc.
- **Thanh tiến độ tổng** ở Studio (đầu canvas hoặc PreviewPane): `Bước 3/6 · Đang đọc giọng Sóc Nhỏ · cảnh 2/8 · đã chạy 00:41`. Cập nhật liên tục.
- Hoạt ảnh phải đi theo **sự kiện thật** của runner (SSE `GET /projects/{pid}/events` hoặc tương đương: bắt đầu node / tiến độ / kết thúc node / lỗi), **cấm timer hay phần trăm giả**. Nếu runner chưa phát đủ sự kiện (đặc biệt `voice_tts` theo từng cảnh, `hyperframes_render` theo % khung, `export`), bổ sung phát sự kiện ở backend và có test thứ tự sự kiện. Tôn trọng `prefers-reduced-motion`; icon trạng thái dùng Morphicons (`MorphIcon`, chuyển chờ→chạy→xong bằng biến hình).

### B. Đồng bộ canvas ↔ Jobs (một nguồn sự thật)
- Bấm **Chạy** → trong ≤ 1 giây tab **Jobs** có job **"Đang chạy"** (kể cả khi đang mở tab khác: chấm/badge số job đang chạy trên tab Jobs). Job hiện: tên dự án/tập, công đoạn hiện tại, % tổng, thời gian đã chạy, chi phí, và danh sách từng công đoạn/node (xong · đang · chờ) cập nhật trực tiếp. Bấm 1 công đoạn trong job → canvas nhảy tới đúng node (focus) và ngược lại.
- **Huỷ job** (có xác nhận) phải dừng runner thật. **Tải lại trang giữa lúc đang chạy** → job vẫn hiện đúng trạng thái (khôi phục từ `runs/` của backend), không mất, không chạy lặp.
- Canvas, tab Jobs và PreviewPane dùng **chung 1 store trạng thái chạy** (không 3 bản trạng thái riêng lệch nhau). Job xong chuyển "Xong" kèm nút Xem / Tải / Đăng; job lỗi nêu node lỗi + lý do.

### C. Sản phẩm được lưu rõ ràng trong dự án
- Mỗi lần chạy xong ghi vào `data/projects/<id>/output/<slug>/` (slug theo chủ đề; không ghi đè lần trước: dùng hậu tố `-2`… hoặc lưu `runs/<run_id>/` và để `output/<slug>/` trỏ bản mới nhất — chọn 1 cách, ghi rõ trong `status/V.md`):
  `final_45s.mp4`, `thumb.jpg`, `script.md` (kịch bản đã dùng), `voice.mp3`, `captions.srt` + `captions.words.json`, `scenes/` (ảnh/clip từng cảnh + ghi nguồn), `composition/` (bundle HyperFrames để dựng lại), `verify_report.json`, và **`video.json` (manifest)**: `{id, title, topic, created_at, duration_s, size_mb, platforms, template_id, graph_ref, run_id, voice_id, providers_per_scene, cost_usd, files{…}, verify{pass, scores}}`.
- Không để file rơi ngoài dự án (không `/tmp`, không ở gốc repo). Mọi đường dẫn đi qua module `workspace`.
- **Thành phẩm phải hiện trong UI** (không thêm tab mới): (1) tab Jobs có mục **"Thành phẩm"** — danh sách video đã xong của dự án (thumb, tên, thời lượng, ngày, nút Phát / Tải / Mở thư mục / Đăng / Chạy lại); (2) Project tab → Thư viện có mục "Video thành phẩm"; (3) node `export` hiển thị "Đã lưu: output/<slug>/final_45s.mp4" + nút "Mở thư mục". Video cũng được đăng ký vào thư viện (assets meta) để làm đầu vào cho node khác.
- Liên thông với Trung tâm đăng: `GET /projects/{pid}/social/videos` phải trả video này kèm thumbnail, thời lượng, tỉ lệ; chọn được trong wizard đăng. Kiểm bằng gọi API và bằng UI.

## 3. Cổng nghiệm thu (tự động + nhìn thật; không vượt cổng = chưa xong)
Viết `tool/src/socnhotv/video/verify.py` + `tool/tests/test_video_verify.py` (hàm `verify_video(path, expect_duration=45, tol=3, expect_size=(1080,1920)) -> Report`), chạy trên video kết quả:
1. `ffprobe`: h264 + aac, 1080×1920, thời lượng 45±3s.
2. Âm thanh: có giọng (mean volume > -30 dB, không im lặng quá 1,5s liên tục ở phần lời), loudness -14 LUFS ±2 (`loudnorm`).
3. Hình: không có khung đen/đứng hình > 0,5s (`blackdetect`, `freezedetect`); ≥ 6 cảnh khác biệt (so băm hình các khung ở mỗi 5s: không có 2 cảnh liền kề giống nhau > 95%).
4. Phụ đề: có chữ hiển thị trên ≥ 80% thời lượng có lời; chữ nằm trong safe-zone (kiểm bằng thống kê vùng pixel/ OCR nhẹ nếu cài được, không thì kiểm trong HTML composition).
5. Đồng bộ: chạy `faster-whisper` lên audio kết quả, so với kịch bản (WER ≤ 25%); tổng thời lượng giọng khớp thời lượng video ±1,5s.
6. Nhìn thật: trích **12 khung hình đều nhau** → ghép `contact_sheet.jpg`, **mở xem từng khung** và ghi nhận xét thật vào `status/V.md`: nhân vật đúng DNA? hình có đúng nội dung câu đang nói? chữ có bị che/cắt?
7. Chấm thủ công 1–5 cho: rõ giọng, khớp phụ đề, đa dạng hình, nhất quán nhân vật, nhịp. Mức đạt tối thiểu **≥ 3/5 mỗi mục** ("chưa tốt" chấp nhận, "hỏng" thì sửa tiếp). Mục thấp nhất được sửa và chạy lại ít nhất 1 vòng.
8. **Bằng chứng trải nghiệm chạy (mục 2B), làm thật trong trình duyệt khi video đang chạy:** chụp ≥ 5 ảnh `data/projects/soc-nho-tv/shots/V_run_*.png` ở các thời điểm khác nhau: (a) vừa bấm Chạy — tab Jobs đã có job "Đang chạy" kèm thanh tiến độ tổng; (b) node giọng đang chạy có hoạt ảnh, stepper đang ở bước 2; (c) node dựng HyperFrames đang chạy với % khác; (d) job xong + node export hiện "Đã lưu: …"; (e) mục "Thành phẩm" hiển thị video. Thử thêm: tải lại trang giữa lúc chạy (job vẫn đang chạy, không nhân đôi) và huỷ 1 lần chạy thử (runner dừng thật, trạng thái "Đã huỷ").
9. **Test tự động**: `test_run_events.py` (thứ tự sự kiện node theo đúng phụ thuộc, có progress cho voice/render, kết thúc đủ), `test_output_manifest.py` (đủ file, `video.json` hợp lệ, không ghi đè lần trước, đường dẫn trong dự án), `test_social_videos_lists_output.py` (API `/social/videos` thấy video mới).
Lưu: `data/projects/soc-nho-tv/output/cau-vong/` đúng cấu trúc mục 2B-C, trong đó có `final_45s.mp4`, `thumb.jpg`, `contact_sheet.jpg`, `verify_report.json`, `video.json`.

## 4. Quy trình (mỗi bước xong: ghi checkpoint `status/V.md`, commit nhỏ theo đường dẫn)
1. **Preflight** (≤10 phút): xác nhận 3000/8000, HyperFrames CLI render thử composition 3s ra mp4 thật, OmniVoice tạo 1 câu `soc-nho`, liệt kê ảnh DNA dùng được (cắt nền/trong suốt hay không), `GET /providers`, `GET /video/templates`. Ghi bảng "có/không" vào `status/V.md`.
2. **Kịch bản 45s**: ~115–130 từ tiếng Việt (nhịp đọc kể chuyện trẻ em ≈ 2,6–2,9 từ/s), 7–8 cảnh: hook 3s → câu hỏi → mưa+nắng → giọt mưa tán sắc → thứ tự màu → mẹo nhớ 7 màu → câu hỏi tương tác/CTA. Mỗi cảnh: mô tả hình + lời. Soạn đúng định dạng dán sẵn (`Cảnh N:` + `Tên: lời thoại`).
3. **Dựng trong Studio**: dùng **Tạo video** (mẫu `shorts-fact-v1` hoặc `story-cartoon-v1`) hoặc dựng tay trên canvas: `text`(chủ đề) → `script`(paste) → `character`(Bi, Koala) → `voice_tts` → `captions` → cảnh/ảnh → `hyperframes_render` → `export`. Dán kịch bản vào node script bằng chính ô nhập trên card. Bấm Chạy từ UI. **Trước khi tối ưu chất lượng hình/tiếng, làm xong mục 2B trước** (hoạt ảnh công đoạn theo sự kiện thật, job hiện ngay ở tab Jobs, thành phẩm lưu đúng chỗ) — vì mọi vòng chạy thử sau đó đều cần quan sát được tiến trình.
4. **Sửa tận gốc** mọi chỗ gãy trên đường (nhập liệu, preset đồ thị, validator, runner, thiếu cổng/sai kiểu dữ liệu, thời lượng cảnh không theo giọng, composition HTML lỗi, render treo, preview không hiện, export không ghi file, tab Jobs không cập nhật…). Mỗi lỗi: nguyên nhân gốc → sửa → test hồi quy. Liệt kê toàn bộ lỗi đã sửa ở `status/V.md`.
5. **Timeline theo giọng**: thời lượng mỗi cảnh = thời lượng câu thoại của cảnh (từ audio thật), tổng 45±3s; lệch → rút/kéo kịch bản hoặc tempo ≤ ±8%, không kéo giãn hình vô nghĩa.
6. **Cổng nghiệm thu mục 3** → sửa → chạy lại cho tới khi đạt.
7. **Lưu thành "Video mẫu"**: lưu đồ thị làm preset ở `data/shared/templates/…` hoặc nút/lệnh tải lại trong Tạo video ("Video mẫu 45s – Cầu vồng"), để người dùng mở lên, đổi chủ đề/kịch bản và chạy lại được. Kiểm: đổi chủ đề thứ hai (ví dụ "Vì sao trời có sấm?") chỉ bằng đổi văn bản/kịch bản → chạy → ra video khác trong ≤ 15 phút (không cần đạt cổng đầy đủ, nhưng phải ra file hợp lệ; ghi thời gian và lỗi).
8. **Tổng kết**: thời gian render, chi phí ($ nếu có provider), độ dài từng bước, điểm yếu còn lại; cập nhật `ai/memory/CONTINUITY.md` (≤ 15 dòng: quy trình chuẩn đã chạy được, lệnh/đường dẫn, lỗi hay gặp). Commit cuối.

## 5. Luật
- Chỉ sửa những gì cần để flow chạy; không thêm tính năng ngoài mục tiêu. Không đụng `components/social/**`, `publishing/**`, `intel/**`, `sources/**`.
- Nhân vật: chỉ dùng DNA có sẵn, không tự vẽ nhân vật mới, giữ tỉ lệ khoá. Voice: `soc-nho`.
- Không đòi người dùng nhập khoá hay cấp thêm quyền; thiếu khoá thì chạy Tier 0 và ghi "thêm khoá X vào Cài đặt để nâng lên Tier 1". Không gửi dữ liệu ra dịch vụ ngoài khi chưa có khoá được người dùng cấu hình.
- Git: `git add` theo đường dẫn, không `git add -A`/stash/reset (session D còn ghi `data/shared/knowledge/video_craft`). Không tắt cổng 3000; cổng 8000 đã `--reload` (đừng tắt, trừ khi treo — khi đó chạy lại đúng lệnh `cd tool && .venv/bin/python -m uvicorn socnhotv.core.api.app:app --app-dir src --host 127.0.0.1 --port 8000 --reload`).
- Báo cáo trung thực: cái gì đã kiểm chứng bằng số liệu/khung hình thật, cái gì chưa, cái gì còn là mock. Cuối cùng gửi tóm tắt tiếng Việt + đường dẫn file mp4, contact sheet và `verify_report.json`.
