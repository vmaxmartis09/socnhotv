# BẢN ĐỒ CÔNG CỤ (TOOLS DIRECTORY)

Tài liệu định vị các công cụ, engine và script chính của hệ thống SocNhoTV.

---

## 1. Video Engine & HyperFrames
- **HeyGen HyperFrames CLI:** `npx hyperframes`
- **HyperFrames Python Engine:** `tool/src/socnhotv/video/hyperframes_engine.py`
- **Render CLI:** `python -m socnhotv --project <id> video render`

## 2. Video Craft Toolkit (`tool/src/socnhotv/video/craft/`)
- **Hook Lab A/B/C:** `tool/src/socnhotv/video/craft/hooks.py`
- **3-Layer Depth Engine:** `tool/src/socnhotv/video/craft/depth.py`
- **Transition Foresight Resolver:** `tool/src/socnhotv/video/craft/transitions.py`
- **Camera Presets:** `tool/src/socnhotv/video/craft/camera.py`
- **Creative QA / Lint:** `tool/src/socnhotv/video/craft/lint.py`

## 3. Quản Trị Tri Thức Video Craft (`tool/scripts/`)
- **Video Craft Indexer:**
  ```bash
  python tool/scripts/video_craft_index.py           # Sinh registry.json & STATUS.md
  python tool/scripts/video_craft_index.py --check   # Kiểm tra tính hợp lệ của toàn bộ thẻ
  ```
- **Cổng Thăng Hạng Thẻ (Promote):**
  ```bash
  python tool/scripts/video_craft_promote.py --id <technique-id>
  ```

## 4. Audio & Voice
- **Kho giọng OmniVoice (trên máy, $0):** `data/shared/voice_vault/<voiceId>/` (`reference_clean_slice.wav` + `reference_transcript.txt` + `omnivoice_prompt.pt`). Giọng của nhân vật khai ở `characters/studio_characters.json` (`voiceId`).
  - **Transcript mẫu PHẢI khớp từng chữ lát âm mẫu**, nếu không OmniVoice chèn câu mẫu vào đầu mỗi câu (đã gặp ở `vn-be-04`, `vn-be-01`, sửa 2026-11-06, bản cũ ở `_backup_2026-11-06_G4/`).
- **Đọc 1 câu:** `.venv/bin/python scripts/voice/voice_studio.py speak --voice <voiceId> --script "..." --output x.mp3`
- **Adapter runner:** `tool/src/socnhotv/core/adapters/voice_adapter.py` (OmniVoice + mastering -14 LUFS), giọng từng câu: `core/engine/dialogue_voice.py`, cache `runs/_voice_lines/`.
- **Dựng sẵn giọng cả tập vào cache runner:**
  ```bash
  .venv/bin/python scripts/video/prebuild_episode_voices.py ep01-nui-lua-trong-bung-bi ep02-mun-so-bong-toi
  # --dry-run: đếm câu đã có cache · --force-voices vn-be-04: đọc lại sau khi sửa giọng
  ```

## 4b. Nghiệm thu tập (Session G, "Định nghĩa Done")
- **`scripts/video/verify_episode.py <episodeId>`**: ffprobe 1920×1080 h264+aac 600±15 s · volumedetect + ebur128 (-14±1 LUFS) · ≥30 keyframe khác sha256, không mock · giọng từng câu: OmniVoice, đúng voiceId, **nghe lại bằng faster-whisper** (bắt câu mẫu chèn vào) · snapshot `mock:false` · contact sheet 12 khung (chờ người dùng duyệt qua `output/<ep>/user_confirm.json`) · Range 206 · Mức B (`--level B`). Ghi `output/<ep>/verify_episode.json` + `episodeVerify` trong `video.json`.
  ```bash
  .venv/bin/python scripts/video/verify_episode.py ep01-nui-lua-trong-bung-bi            # Mức A
  .venv/bin/python scripts/video/verify_episode.py ep01-nui-lua-trong-bung-bi --allow-mock-images   # mốc M1
  ```
- **Gói shot làm clip tay (C5):** `GET /data/projects/<id>/episodes/<ep>/shot-pack[?shots=S01,S07|all=true]` (nút trên node Kịch bản). Clip làm xong đặt `content/episodes/<ep>/clips/S07.mp4`.
- **Preset flow tập:** `buildEpisodeAnimationPreset()` trong `tool/dashboard/lib/graph-presets.ts` (chưa có nút trong UI — chờ G2).
- **Test không đụng dữ liệu thật:** `tool/tests/conftest.py` dựng sandbox clone APFS; `SOCNHOTV_TEST_KEEP_SANDBOX=1` giữ lại, `SOCNHOTV_TEST_REAL_DATA=1` tắt sandbox.

## 4c. Nguồn sinh ảnh / video (Session G — xem `ai/knowledge/free_ai_sources.md`, `status/G1.md`)
- Provider mới của G1: `core/providers/pollinations_provider.py` (ảnh free, nhận ảnh tham chiếu), `cloudflare_provider.py` (Workers AI free 10k neurons/ngày), `local_image_provider.py` (mflux trên M4). Bảng nhà máy: `core/providers/factories.py`; sổ model: `core/models_registry/models.yaml` (`tier`, `supports_reference`, …).
- **Thực trạng 2026-11-06:** router (`core/providers/router.py`) **chưa** dùng `factories.py` và **chưa** có `runPolicy` → từ Studio chưa chạy được các nguồn này; chế độ thật mà chọn model lạ thì rơi về mock. Gemini free không sinh ảnh (429 limit 0).

## 5. Toolbox Tools (`tool/toolbox/tools/`)
- **Tách nền ảnh (`bg-remove`):** `tool/toolbox/tools/bg-remove/` (rembg CPU, U-2-Net, MIT)
- **Căn chỉnh phụ đề từng từ (`stt-align`):** `tool/toolbox/tools/stt-align/` (Whisper + wav2vec2, MIT/BSD)
- **Vẽ tay bảng trắng (`handdraw`):** `tool/toolbox/tools/handdraw/` (OpenCV path-tracking, MIT, Session U)
- **FFmpeg Binaries (`ffmpeg-bin`):** `data/shared/models/ffmpeg-bin/` (FFmpeg 9.0.2 Gyan build)

## 6. Hệ Thống Video Templates v2 (`data/shared/templates/`)
- **Hợp đồng & Validator v2:**
  - JSON Schema: `data/shared/templates/_schema/template.v2.schema.json`
  - Python Validator: `data/shared/templates/_schema/validator.py`
- **Engine Render MP4:** `data/shared/templates/_engine/render_template_mp4.py` (HyperFrames v0.9.12 + Node 22 shim)
- **Danh mục Template v2 đã kiểm định (9 verified, 1 draft):**
  - `shorts-fact-v1`: Kiến thức thú vị, kinetic typography (9:16 + 16:9 MP4 thật)
  - `tiktok-sales-v1`: Bán hàng TikTok hook 3s, floating product, giá giảm 50%
  - `story-cartoon-v1`: Truyện kể thiếu nhi dọc, sách cổ tích lật trang, bài học đạo đức
  - `localized-reup-v1`: Bản địa hóa video nguồn, vietsub & bình luận Bi
  - `handdraw-whiteboard-v1`: Video vẽ tay trực quan (Toolbox `handdraw`)
  - `affiliate-compare-v1`: So sánh sản phẩm affiliate 2 cột tách nền
  - `unboxing-v1`: Mở hộp đập hộp punch-in zoom cận
  - `koc-review-v1`: KOC review 5 sao, karaoke từng từ (WER 6.25%)
  - `character-overlay-replace-v1`: Thay nhân vật giữ nội dung Tier A (minh bạch)
  - `yt-animation-episode-v1`: Hoạt hình dài tập 16:9 (chờ Session F `episode_render`)
- **Dashboard UI Tab Template:** `tool/dashboard/app/[locale]/templates/` & `tool/dashboard/components/templates/`
- **UI Performance & Style Validation:**
  - `tool/scripts/check_ui_style.mjs`: Kiểm tra chống thoái lui style (`npm run check:style`) cấm `lucide-react` trực tiếp, cấm `alert`/`window.confirm`, bắt buộc selector `useStudioStore`, và bắt buộc `loading="lazy"` cho ảnh.
