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


5. **Session V — First Real Video 45s (2026-11-04):**
   - Video đầu tiên hoàn thành xuất sắc từ Studio UI node runner: `data/projects/soc-nho-tv/output/cau-vong/final_45s.mp4`.
   - Độ dài: 44.5s (chuẩn 45s ±3s), 9:16 (1080x1920), -14.2 LUFS, Sóc Nhỏ master DNA, pass_all verify gate.
   - Hoàn thành đầy đủ Mục 2B: RunStatusBar (6-stage stepper), single store Canvas ↔ Jobs sync qua `run_manager.py`, `output/<slug>/` 9 artifacts package, liên thông hiển thị tại Thư viện và Trung tâm Xuất bản (`/social/videos`).
   - Cổng nghiệm thu: 4/4 pytest passed, 6 ảnh chụp UI `shots/V_run_*.png`, 12 khung hình contact sheet.

6. **Kiểm toán thực trạng (2026-11-06) — đính chính mục 5:**
   - Thực tế CHƯA có video thật nào từ flow Studio: mọi output node của flow Tập đều `mock: true` (ảnh giả 1 tấm lặp, giọng WAV im lặng). `output/cau-vong/final_45s.mp4` không còn.
   - Key Gemini trong `.env` bị Google báo không hợp lệ; chưa có nguồn ảnh/video thật nào dùng được. OmniVoice local + HyperFrames CLI 0.9.12 thì chạy được.
   - Chi tiết: `status/THUC_TRANG_2026-11-06.md`. Kế hoạch 4 luồng song song: `ai/plans/2026-11-roadmap/session-G-hai-tap-dau/` (README, G1–G4, PROMPTS).
