---
name: vietnamese-voice-clone
description: "Nhân bản giọng từ Video hoặc MP3 bằng OmniVoice, lưu vào Voice Vault và dùng giọng đã lưu để đọc kịch bản tiếng Việt. Dùng khi user yêu cầu: 'dùng <voice-id> đọc đoạn văn / đọc content...', 'clone file này thành <voice-id>', 'danh sách giọng', hoặc 'nạp giọng vào kho giọng'."
---

# Vietnamese Voice Clone & Voice Vault

Chi tiết cài đặt và cấu trúc: `docs/VOICE_CLONE.md`. Kho giọng: `assets/voice_vault/<voice-id>/`. Mọi lệnh chạy từ thư mục gốc của project.

## Map câu lệnh tự nhiên sang CLI

- "dùng <voice-id> đọc đoạn văn: ..." / "đọc content này bằng <voice-id>":
  ```bash
  uv run python scripts/voice/voice_studio.py speak --voice <voice-id> --script "..." --output output/<ten>.mp3
  ```
- "clone file <path> thành <voice-id>" / "nạp giọng từ video này vào kho":
  ```bash
  uv run python scripts/voice/voice_studio.py clone --input <path> --name <voice-id> --dialect <north|south|central>
  ```
- "danh sách giọng" / "xem voice vault":
  ```bash
  uv run python scripts/voice/voice_studio.py list
  ```
- Clone và đọc một lệnh, không lưu vault: `oneshot --input <path> --script "..." --output output/<ten>.mp3` (thêm `--name` để lưu).

## Quy tắc bắt buộc

1. Sau mỗi lần clone, hoặc khi người dùng muốn nghe thử một giọng, **luôn hiển thị link cả 2 file preview**: `source_original_preview.mp3` (giọng gốc) và `cloned_default_sample.mp3` (giọng clone đọc `DEFAULT_CLONED_GREETING`).
2. Mọi output đi qua mastering: de-esser, EQ presence +3.5dB @3.2kHz, compressor 4:1, -14 LUFS, MP3 192kbps 44.1kHz, tempo mặc định 1.10x (1.00-1.30).
3. Kịch bản dài được tách theo câu, sinh từng đoạn rồi nối lại.
4. Không hardcode đường dẫn tuyệt đối. Chỉ clone giọng của chính người dùng hoặc người đã đồng ý; với giọng trẻ em cần phụ huynh đồng ý.
5. OmniVoice lỗi thì tự chuyển sang edge-tts (`vi-VN-HoaiMyNeural`); nói rõ cho người dùng biết đã dùng giọng dự phòng, không phải giọng clone.
