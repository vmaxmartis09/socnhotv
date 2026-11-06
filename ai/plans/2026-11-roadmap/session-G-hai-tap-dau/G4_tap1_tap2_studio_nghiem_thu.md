# G4: Dữ liệu Tập 1–2, xem trong Studio, nghiệm thu (luồng tích hợp)

> Thuộc Session G. Đọc trước: `status/THUC_TRANG_2026-11-06.md` (N7, N8), `README.md` (toàn bộ, nhất là mục 5: Định nghĩa Done).
> G4 là **luồng tích hợp**: chạy các mốc M1–M4, viết báo cáo cuối `status/G.md`.
> Báo cáo tiến độ: `status/G4.md`.

## Tệp sở hữu
`core/engine/episode_script.py`, `script_parser.py`, `character_profile.py`, `core/api/data_routes.py`. Frontend: `components/studio/PreviewPane.tsx`, `components/studio/tabs/JobsCostTab.tsx`, `components/canvas/RunStatusBar.tsx`, `components/canvas/NodeBody.tsx`, `lib/graph-presets.ts`, `lib/preview.ts`, `messages/modules/video.*.json`. Ngoài ra: `tool/tests/conftest.py`, `tool/tests/test_g4_*.py`, `scripts/video/verify_episode.py` (mới), `status/G4.md`, `status/G.md`, cuối cùng là `ai/map/TOOLS.md` và `ai/memory/CONTINUITY.md`.
Dữ liệu (không commit): `data/projects/soc-nho-tv/content/episodes/ep01*/`, `ep02*/`, `graph.json`, `shots/G4_*`.

## Bước làm

### Pha 1 (song song với G1–G3)
1. **Tách test khỏi dữ liệu thật (N8):** sửa `tool/tests/conftest.py` để mọi test dùng repo/dự án tạm (`tmp_path`, biến môi trường trỏ `data/` tạm). Chạy toàn bộ `pytest`, sau đó `runs/` của `soc-nho-tv` **không có thư mục mới**. Không tự xoá 695 thư mục cũ: liệt kê lại và hỏi người dùng.
2. **Staging data/:** báo người dùng có 844 tệp `data/` nằm sẵn trong staging. Đề xuất `git restore --staged data/`, chỉ chạy khi người dùng đồng ý.
3. **Kiểm sẵn dàn nhân vật 2 tập:**
   - Tập 1: `soc_nho`, `de_mun`, `me_soc`. Tập 2: `de_mun`, `de_bong`, `ong_de_rau_bac`.
   - Với từng nhân vật: có ảnh DNA chính diện rõ (chọn 1–3 ảnh **tốt nhất** làm tham chiếu, ghi danh sách vào hồ sơ nếu cần), giọng gán (`studio_characters.json`), tỉ lệ khớp `SCALE_LOCK.md`.
   - Thu giọng mẫu 1 câu cho từng giọng (`voice_studio.py speak --voice <id>`) và nghe kiểm (đo `volumedetect`). Giọng nào lỗi thì ghi "Yêu cầu" vào `status/G4.md`.
4. **Dựng sẵn giọng thật cho 60 câu thoại** (30 shot × 2 tập), đưa vào cache giọng của runner. Mục đích: mốc M1 chạy nhanh, không chờ OmniVoice từng câu. Đo tổng thời gian.
5. **Kịch bản:** sửa `videoPrompt` có chữ "8-second clip" để khớp thực tế (G3 cũng chỉnh lúc chạy, nhưng dữ liệu gốc nên đúng). Đặt `"locked": true` trong `script.json` khi đã sửa tay (theo quy tắc E6 §3c). Mỗi shot gắn `priority` (1 = shot chính: mở đầu, cao trào, bài hát, kết) để G3 chọn shot làm clip ở Mức B.
6. **Xem và tua video trong Studio:**
   - Kiểm route trả video (`data_routes.py`, `FileResponse`) trả `206` khi có header `Range` cho tệp hơn 200 MB.
   - `PreviewPane` và nút Play ở node Xuất phát được, tua được tới phút 9. Có `thumb.jpg` làm poster.
   - Kết quả tập hiện trong tab Jobs với thời lượng, engine dựng (hyperframes hoặc ffmpeg-fallback) và cảnh báo nếu có.
7. **`scripts/video/verify_episode.py <episodeId>`:** chạy tự động các mục 1–5 của "Định nghĩa Done" (README mục 5): ffprobe, volumedetect/loudnorm, số hash ảnh khác nhau, provenance không mock, giọng đúng voiceId. Xuất JSON và in BẢNG ĐẠT/KHÔNG ĐẠT.

### Mốc M1 (khi G2 pha 1 và G3 pha 1 đã vào main)
8. Chạy flow Tập 1 trong Studio bằng **chế độ lai** (ảnh mock, giọng local). Kỳ vọng: MP4 600 giây **có tiếng** (đúng giọng từng nhân vật), có chuyển động camera theo shot, xem được trong Studio. Chạy `verify_episode.py`: mục 3 (ảnh) **được phép KHÔNG ĐẠT** ở mốc này. Chụp `shots/G4_M1_*.png`.

### Pha 2
9. **Preset "Tập hoạt hình (tái dùng)"** trong `lib/graph-presets.ts`: Kịch bản (episode) → Dàn diễn viên → Keyframe (`image_gen`, model mặc định = nguồn free chính của G1) → [Video theo shot (`video_gen`, `perShot`, `clipSource: auto`, `maxClips: 5`), tắt sẵn ở Mức A] → Kiểm định → Dựng (16:9) → Xuất (tên tệp tự theo tập).
10. **Đổi tập bằng 1 chỗ:** chọn tập ở node Kịch bản (danh sách từ `fetchProjectScriptEpisodes`) là đủ. Tên tệp xuất tự theo tập (C6 của G3). Không phải dựng lại graph.
11. **Xuất "gói shot" để làm clip tay (C5):** nút trên node Kịch bản hoặc Video xuất ZIP gồm `S01.png` (ảnh khung đầu), `S01.txt` (`videoPrompt` + thời lượng), `README.txt` hướng dẫn đặt tên `clips/S01.mp4`. Người dùng mang lên web có credit free (G1 ghi danh sách), làm clip, rồi thả lại vào `clips/`.

### Mốc M2 → M4
12. **M2:** Tập 1 Mức A, ảnh thật từ nguồn free của G1, chọn qua ModelPicker của G2. `verify_episode.py` ĐẠT các mục 1–5. Gửi contact sheet cho người dùng duyệt mục 6.
13. **M3:** Tập 2, cùng flow, chỉ đổi tập. ĐẠT như M2.
14. **M4 (Mức B):** mỗi tập ≥ 5 shot `priority = 1` có clip thật (API free hoặc làm tay). Liệt kê `shotId → nguồn`.
15. **Báo cáo cuối `status/G.md`:** bảng các mốc, số đo thật, đường dẫn video, ảnh chụp, những gì CHƯA đạt. Cập nhật `ai/map/TOOLS.md` (nguồn mới, chế độ chạy, lệnh verify) và `ai/memory/CONTINUITY.md` (sửa lại ghi chép "Session V hoàn thành" cho đúng sự thật).

## Done khi
- `output/ep01-nui-lua-trong-bung-bi/ep01-nui-lua-trong-bung-bi.mp4` và tệp tương ứng của ep02 **ĐẠT** `verify_episode.py`. Người dùng đã xem contact sheet và nói đạt.
- Cả hai phát và tua được trong Studio. Có ảnh chụp `shots/G4_M2_*.png`, `G4_M3_*.png`.
- `pytest` toàn bộ pass, không ghi vào dữ liệu thật.
