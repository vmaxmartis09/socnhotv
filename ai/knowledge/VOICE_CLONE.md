# Vietnamese Voice Clone + Voice Vault

Clone giọng từ video/mp3 một lần, lưu vào `assets/voice_vault/<voice-id>/`, rồi đọc kịch bản nhiều lần.

## Cài đặt

```bash
uv sync                                                    # môi trường chính (whisper, ffmpeg, edge-tts...)
git clone https://github.com/k2-fsa/OmniVoice integrations/OmniVoice
cd integrations/OmniVoice && uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -e . soundfile numpy
```

Engine OmniVoice chạy trong `integrations/OmniVoice/.venv` (hoặc đường dẫn trong biến `OMNIVOICE_PYTHON`). Thiết bị tự chọn MPS > CUDA > CPU. Lần chạy đầu tải trọng số `k2-fsa/OmniVoice` và `openai/whisper-small` từ Hugging Face.

## Lệnh

```bash
uv run python scripts/voice/voice_studio.py clone --input <video|mp3> --name <voice-id> --dialect north|south|central [--text "..."] [--duration 4.5]
uv run python scripts/voice/voice_studio.py speak --voice <voice-id> --script "<text hoặc .txt>" --output output/x.mp3 [--tempo 1.10] [--no-master]
uv run python scripts/voice/voice_studio.py oneshot --input <mau> --script "..." --output output/x.mp3 [--name <voice-id>]
uv run python scripts/voice/voice_studio.py list
```

## Mỗi giọng trong vault

`omnivoice_prompt.pt`, `reference_clean_slice.wav` (3.5-6s, trọn câu), `reference_transcript.txt` (khớp lát), `raw_extracted_clean.wav`, `source_original_preview.mp3`, `cloned_default_sample.mp3`, `profile.json`.

Sau mỗi lần clone luôn có đủ 2 file nghe thử: giọng gốc và giọng clone đọc `DEFAULT_CLONED_GREETING` (sửa ở `src/gobi/services/voice/voice_cloner.py`). Cả hai được copy ra `output/`.

## Mastering (mọi output)

De-esser, EQ presence +3.5dB @3.2kHz, compressor 4:1, tempo 1.10x (1.00-1.30), chuẩn hóa -14 LUFS, MP3 192kbps 44.1kHz. Engine dự phòng: edge-tts `vi-VN-HoaiMyNeural`, rate +5%, pitch +2Hz.

## Lưu ý

Chỉ clone giọng của chính bạn hoặc người đã đồng ý. Với giọng trẻ em cần phụ huynh đồng ý.
