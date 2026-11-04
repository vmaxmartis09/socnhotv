# Quy Trình Sản Xuất Video Faceless Tự Động Hoá (Faceless TTS HyperFrames Pipeline)

- **Slug:** `faceless-tts-hyperframes`
- **Trạng thái tái tạo trong Studio:** `đã thử tái tạo` (Sẵn sàng 100% trong `tool/src/socnhotv/video/hyperframes_engine.py` và OmniVoice)
- **Tần suất xuất hiện:** Xuất hiện ở 4 kênh độc lập (@anongvn, @nhueit, @bahuy.henry, @ngoc.agi)
- **Độ tin cậy:** Tuyệt đối (Quy trình sản xuất chủ lực của hệ thống)

---

## 1. Đầu vào (Inputs)
1. **Chủ đề & Dàn ý kịch bản (Topic / Narrative Script):**
   - File Markdown hoặc văn bản kịch bản phân đoạn 3 phần: Hook 3s → Giá trị cốt lõi / Kể chuyện → Call-to-action.
2. **Cấu hình Giọng đọc (Voice Profile):**
   - Giọng độc quyền dự án: `soc-nho` (OmniVoice SOTA tại `data/shared/voice_vault/soc-nho/`).
3. **Thư viện Hình ảnh / B-Roll:**
   - Ảnh minh họa nhân vật Bi & Koala hoặc ảnh Stock 4K bám sát từng câu chuyện.

---

## 2. Công cụ & Kiến trúc (Tools & Architecture)
- **Script Structuring:** LLM Generator (Claude 3.7 / Gemini 2.5 Flash) xuất JSON Timeline.
- **Voiceover Synthesis:** OmniVoice SOTA (tiếng Việt truyền cảm, chuẩn -14 LUFS, presence +3.5dB @3.2kHz).
- **Speech-to-Text Alignment:** `faster-whisper` (large-v3) trích xuất timestamp từng từ (word-level timestamps).
- **Video Assembly Engine:** HeyGen HyperFrames (HTML5/CSS/GSAP timeline tất định, seek-safe).
- **Dynamic Icons & Graphics:** Morphicons (`morphicons/react` / SVG spring physics).

---

## 3. Các bước thực hiện & Thông số kỹ thuật (Step-by-Step & Parameters)

### Bước 1: Sinh Giọng Đọc & Mastering (OmniVoice Pipeline)
- Chạy lệnh CLI sinh âm thanh:
  `python -m socnhotv voice synthesize --voice-id soc-nho --text "..." --output audio/voice.mp3`
- Chuỗi xử lý TikTok Audio Mastering:
  - De-esser cắt xì ở tần số 6.5kHz.
  - EQ boost nhẹ +3.5dB tại dải hiện diện 3.2kHz.
  - Compressor tỷ lệ 4:1, attack 15ms, release 120ms.
  - Chuẩn hóa âm lượng: -14 LUFS, True Peak -1.0 dBTP.

### Bước 2: Trích xuất Dòng Thời Gian Phụ Đề (Word-Level Timing)
- Dùng Whisper bóc tách phụ đề thành JSON:
  ```json
  [
    {"word": "Chào", "start": 0.12, "end": 0.35},
    {"word": "các", "start": 0.36, "end": 0.52},
    {"word": "bạn", "start": 0.53, "end": 0.78}
  ]
  ```

### Bước 3: Lắp ráp Composition HeyGen HyperFrames
- Tạo file `index.html` composition với các track độc lập:
  - `Track 0 (BGM)`: Nhạc nền ducking -4dB khi có voiceover.
  - `Track 1 (VO)`: File `voice.mp3`.
  - `Track 2 (Background B-Roll)`: Ảnh hoặc video AI cắt chuyển cảnh mỗi 2.5–3.5 giây.
  - `Track 3 (Kinetic Captions)`: Chữ nổi bật giữa màn hình với hiệu ứng bung chữ (Pop-in GSAP ease `back.out(1.7)`).
  - `Track 4 (Safe-Zone Overlays)`: Giữ an toàn 180px top và 320px bottom.

### Bước 4: Render Tự Động Hàng Loạt
- Lệnh thực thi:
  `python -m socnhotv --project soc-nho-tv video render --composition composition.html --output output.mp4`
- Renderer khởi chạy trình duyệt Headless tàng hình, đọc từng frame bằng cờ `--enable-begin-frame-control`, đảm bảo không bao giờ rơi rớt một khung hình nào.

---

## 4. Đầu ra (Deliverables)
- Video MP4 1080x1920 (9:16), 30fps CFR.
- File kịch bản JSON hoàn chỉnh có thể tái sử dụng hoặc dịch sang các ngôn ngữ khác.

---

## 5. Lỗi thường gặp & Cách khắc phục (Troubleshooting)
1. **Lỗi phụ đề bị nhảy chữ quá nhanh làm người xem mỏi mắt:**
   - *Khắc phục:* Nhóm cụm từ (Chunking) từ 2 đến 4 từ mỗi cụm thay vì hiện từng từ đơn lẻ.
2. **Lỗi nhạc nền lấn át tiếng nhân vật:**
   - *Khắc phục:* Bắt buộc dùng sidechain compressor tự động hạ BGM xuống -18 LUFS khi voiceover phát và tăng lên -12 LUFS khi hết câu thoại.
