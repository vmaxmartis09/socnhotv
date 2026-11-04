# SỔ TAY TIẾP NỐI & BỘ NHỚ HOẠT ĐỘNG (CONTINUITY MEMORY)

## Trạng thái gần nhất: 2026-11-03

### Quyết định kiến trúc & Quy chuẩn bắt buộc:
1. **Quy chuẩn Icon:**
   - Đã chuẩn hóa toàn bộ dự án sang thư viện **Morphicons** (`https://www.morphicons.com/`, `morphicons/react`).
   - Mọi icon được quản lý tập trung tại `tool/dashboard/components/ui/icons.ts` và `tool/dashboard/components/ui/MorphIcon.tsx`.
   - Đã gỡ bỏ vĩnh viễn `lucide-react`. Các agent tuyệt đối không dùng lại `lucide-react`.

2. **Quy chuẩn Video Editor:**
   - HeyGen HyperFrames (`tool/src/socnhotv/video/hyperframes_engine.py`, `ai/skills/hyperframes*`) là công cụ biên tập và hậu kỳ chính thức.

3. **Quy chuẩn Voice & Âm thanh:**
   - OmniVoice cho Sóc Nhỏ Bi (`voice-id: soc-nho`).
   - Chuỗi mastering audio chuẩn TikTok: -14 LUFS, presence EQ, de-esser, compressor.

4. **Tri thức Video Craft thường trực (Session K):**
   - Kho thẻ: `data/shared/knowledge/video_craft/techniques/` (26 thẻ, `registry.json`, `STATUS.md`).
   - Playbooks & Skill: 7 playbooks tại `playbooks/`, skill chính `ai/skills/video-craft/`.
   - Module Studio: `tool/src/socnhotv/video/craft/` (`hooks`, `depth`, `transitions`, `camera`, `lint`).
   - Lệnh cập nhật/kiểm tra: `python tool/scripts/video_craft_index.py [--check]`.
   - Thăng hạng thẻ mới: `python tool/scripts/video_craft_promote.py --id <id>`.

