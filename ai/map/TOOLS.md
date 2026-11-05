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
- **OmniVoice Local:** `data/shared/voice_vault/soc-nho/`
- **Voice Engine:** `tool/src/socnhotv/core/engine/voice.py`

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
