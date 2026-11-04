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
