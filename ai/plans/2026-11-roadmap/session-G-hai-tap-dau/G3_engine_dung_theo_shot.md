# G3: Engine dựng theo shot (video_gen lặp, clip tay, camera, BGM/SFX, bỏ đường tốn tiền)

> Thuộc Session G. Đọc trước: `status/THUC_TRANG_2026-11-06.md` (N4, N5, N6), `README.md` (mục 3, 4, 6), skill `ai/skills/video-craft`, `data/shared/knowledge/video_craft/techniques/STATUS.md`, skill `hyperframes-core`.
> Báo cáo tiến độ: `status/G3.md`.

## Vấn đề
- `video_gen` chỉ làm 1 clip, không lặp theo shot. Flow Tập không có bước video.
- Shot dài 20 giây, clip AI chỉ 4–10 giây.
- Bộ dựng (`hyperframes_engine.generate_composition_html`): mỗi shot 1 ảnh tĩnh phủ kín khung, zoom 1.05→1.03. Không dùng trường `camera`. Không nhạc nền, không SFX. Module craft không được gọi.
- **Đường tốn tiền ngầm:** khi `hyperframes_render` lỗi, code gọi `provider.generate_video("Final rendered video composition", 45s)`.
- HyperFrames lỗi thì lặng lẽ chuyển sang FFmpeg. `npx -y hyperframes` có thể tải bản khác bản đã ghim 0.9.12.

## Tệp sở hữu
`core/engine/shot_video.py` (mới), `tool/src/socnhotv/video/**` (gồm `hyperframes_engine.py`, `fallback_ffmpeg.py`, `craft/**`), `core/adapters/hyperframes_adapter.py`, `core/adapters/audio_mastering.py`, `core/nodes/registry.py`. Trong `graph_runner.py` **chỉ** `_render_dialogue` và các nhánh `video_gen`, `hyperframes_render`, `export` của `_execute_node_handler`. Mỗi nhánh chỉ thêm vài dòng gọi sang module mới; logic nặng viết trong `shot_video.py` hoặc `video/`. Test `tool/tests/test_g3_*.py`.

## Bước làm

### Pha 1 (làm ngay, không phụ thuộc ai)
1. **Bỏ fallback tốn tiền:** trong nhánh `hyperframes_render`, dựng lỗi thì `raise` kèm log tail. Không gọi `generate_video`.
2. **Báo rõ khi dùng FFmpeg dự phòng:** output video ghi `provenance.model` là `hyperframes-<ver>` hoặc `ffmpeg-fallback` (đã có một phần), thêm `meta`/`outputs["engine"]` và `outputs["engineWarning"]` khi dùng dự phòng. Thêm tham số node `requireHyperFrames: true` (mặc định true cho preset Tập): HyperFrames lỗi thì node lỗi luôn, không âm thầm hạ chất lượng.
3. **Ghim HyperFrames:** gọi binary đã cài (`tool/dashboard/node_modules/.bin/hyperframes`, hoặc biến env `HYPERFRAMES_BIN`) thay cho `npx -y`. Ghi phiên bản vào log.
4. **Camera theo kịch bản:** mỗi shot có `camera` ("smooth push-in", "slow pan left", "static", "tilt up", …) và `shotSize`. Viết `video/craft/camera.py` (đã có, dùng lại hoặc mở rộng) để ánh xạ ra tween GSAP: push-in / pull-out / pan L-R / tilt / ken-burns theo điểm nhấn.
   - Shot 20 giây bằng ảnh tĩnh: chia **2–3 nhịp chuyển động** (ví dụ push-in chậm, rồi giữ, rồi pan nhẹ) để không đứng hình.
   - Chuyển cảnh giữa các cảnh lớn (`sceneIndex` đổi) dùng `video/craft/transitions`. Mọi animation phải tất định và tua được (seek-safe), đúng skill `hyperframes-animation`.
5. Test `test_g3_composition.py`:
   - HTML sinh ra có tween khác nhau cho các `camera` khác nhau.
   - Render lỗi thì node lỗi và **không gọi** `generate_video` (dùng provider giả để đếm số lần gọi).

### Pha 2
6. **`video_gen` lặp theo shot** (hợp đồng **C4**), logic trong `core/engine/shot_video.py`:
   - Đầu vào: `scenes` từ `image_gen` (có `image`). Với mỗi shot được chọn: `first_frame = image`, `prompt = videoPrompt` (sửa chữ "8-second" theo `durationSec` của model), `duration` = giá trị gần nhất trong `durations_sec` của model.
   - Chọn shot: `shotIds` nếu có. Không có thì xếp theo độ quan trọng: shot đầu của mỗi cảnh, shot có `bgm` hoặc bài hát, shot cuối. Dừng ở `maxClips`.
   - `clipSource`: `manual` thì chỉ dùng `clips/<shotId>.mp4` (**C5**). `ai` thì gọi provider. `auto` thì có clip tay dùng clip tay, không thì gọi AI, AI lỗi (QUOTA, AUTH) thì **giữ ảnh** và ghi cảnh báo (không làm hỏng cả run).
   - Cache theo `(episodeId, shotId, model, hash(prompt), hash(first_frame))` để chạy lại không tốn credit.
   - Cổng ra `scenes`: thêm `video`, `videoSource` (ai/manual) cho shot có clip. Tiến trình SSE "Clip i/N".
   - `core/nodes/registry.py`: khai báo các tham số mới cùng giá trị mặc định (G2 làm UI dựa trên đây).
7. **Bộ dựng xử lý clip ngắn hơn shot:** clip 5–8 giây trong shot 20 giây thì phát clip, sau đó **giữ khung cuối và chuyển động camera nhẹ** (hoặc đặt clip ở giữa, hai đầu là ảnh tĩnh có chuyển động). Không lặp clip giật cục. Kết quả phải tất định.
8. **Clip làm tay:** `hyperframes_render` và `shot_video` tự nhận `content/episodes/<ep>/clips/<shotId>.mp4` (C5) kể cả khi flow không có node `video_gen`.
9. **Nhạc nền + SFX:**
   - Bộ dựng nhận `bgm` (theo cảnh hoặc cả tập) từ `data/shared/music_sfx/` (G1 tìm nguồn free, người dùng tải về). Ducking khi có thoại (dùng `hyperframes-audio` hoặc `audio_mastering`). Mastering cuối -14 LUFS.
   - SFX theo trường `sfx` của shot nếu có tệp tương ứng; thiếu tệp thì bỏ qua và ghi cảnh báo.
10. **Tên tệp xuất (C6):** `export.outputFileName` trống thì `<episodeId>.mp4` trong `output/<episodeId>/`, kèm `video.json`, `thumb.jpg`, `contact_sheet.jpg` (12 khung).
11. **Hiệu năng 10 phút:** đo thời gian render 600 giây 1080p. Quá 30 phút thì thử render theo cảnh rồi ghép, hoặc `--quality` thấp hơn cho bản xem thử. Ghi số đo vào `status/G3.md`.
12. Test `test_g3_shot_video.py`:
    - Chọn shot theo `maxClips`.
    - Ưu tiên clip tay ở chế độ auto.
    - AI lỗi QUOTA thì giữ ảnh.
    - Cache trúng ở lần chạy thứ 2 (0 lần gọi provider).

## Done khi
- Render Tập 1 bằng ảnh mock + giọng thật (chế độ lai của G2) ra 600 giây, **có chuyển động camera khác nhau theo shot**, có nhạc nền nếu có tệp.
- Thả 2 clip tay `clips/S01.mp4`, `clips/S05.mp4` thì video cuối dùng đúng 2 clip đó ở đúng shot (kiểm bằng contact sheet).
- Không còn đường nào tự gọi `generate_video` khi đang lỗi (grep + test).
- `pytest tool/tests/test_g3_*` pass, test cũ không vỡ.
