---
name: vietnamese-voice-clone
description: "Nhân bản bất kỳ giọng nói nào từ Video hoặc MP3 sang Tiếng Việt thuần Việt chuẩn ngữ điệu bằng OmniVoice SOTA, và dùng các giọng đã lưu trong kho (Voice Vault) để đọc kịch bản, content, văn bản review KOC TikTok/Reels. Dùng ngay khi user yêu cầu: 'sử dụng <voice-id> đọc đoạn văn / đọc content...', 'clone file này...', hoặc 'nạp giọng vào kho giọng'."
---

# Vietnamese Voice Clone & Voice Vault Suite (OmniVoice Packaged)

Kỹ năng chuyên biệt để trích xuất, nhân bản bất kỳ giọng nói nào từ Video/MP3 thành một Sound Profile vĩnh viễn trong **Kho Giọng (Voice Vault)** và sử dụng động cơ SOTA **OmniVoice** (Apple Silicon Metal MPS) để đọc kịch bản tiếng Việt chuẩn ngữ điệu cảm xúc.

---

## 📁 1. KHO GIỌNG TRUNG TÂM (VOICE VAULT)

Toàn bộ các giọng nói được lưu trữ độc lập tại `assets/voice_vault/`.

Mỗi thư mục giọng bao gồm cấu trúc chuẩn:
```
assets/voice_vault/[voice-id]/
├── omnivoice_prompt.pt        # ⚡ Cache OmniVoice Prompt (tái sử dụng tức thì, không cần encode lại)
├── source_original_preview.mp3 # 🎧 File source gốc giọng đọc (Mastered -14 LUFS)
├── cloned_default_sample.mp3   # 🎤 File giọng đọc đã clone đọc câu chào mặc định
├── reference_clean_slice.wav   # Lát cắt vàng 3.5s - 6.0s (Trọn câu hoàn chỉnh, không cụt âm)
├── raw_extracted_clean.wav     # Full audio vocal sạch sau lọc nhiễu
├── reference_transcript.txt    # Text đối chiếu khớp 100% với lát cắt
├── speaker_emb.npy             # Speaker Embedding dự phòng cho VieNeu
└── profile.json                # Metadata đầy đủ
```

### Các giọng trong kho hiện tại:
* **`voice-fm-1-mb`**: **Giọng nữ 1 miền Bắc** (Reviewer KOC thời trang trẻ trung, nhịp nói dồn dập, tự nhiên, cuốn hút, phát âm chuẩn thanh điệu Bắc Bộ).
* **`voice-fm-lyly`**: **Giọng nữ LyLy Studio** (Phương ngữ miền Nam ngọt ngào, ấm áp, sâu lắng, truyền cảm xúc, phù hợp podcast, tâm sự, review phong cách sống).
* **`voice-fm-an-nhien`**: **Giọng nữ An Nhiên** (Phương ngữ miền Bắc, podcast chữa lành, radio tâm sự nhẹ nhàng, thư thái).
* **`voice-fm-tue-lam`**: **Giọng nữ Tuệ Lâm** (Phương ngữ miền Nam, tư duy bản lĩnh, sắc sảo, dứt khoát, chuyên content kinh doanh/mindset).

---

## 💎 2. QUY TẮC BẮT BUỘC: BỘ ĐÔI PREVIEW (FILE GỐC + FILE CLONE MẪU)

> [!IMPORTANT]
> **ĐIỀU KHOẢN BẮT BUỘC:** Đối với MỌI giọng nói trong Kho Giọng, hệ thống **LUÔN LUÔN CÓ 2 FILE**:
> 1. **File source gốc giọng đọc**: `source_original_preview.mp3` (Đoạn audio thực tế của người nói nguyên bản).
> 2. **File giọng đọc đã được clone**: `cloned_default_sample.mp3`
>    - Luôn luôn đọc chính xác câu nói mặc định:
>      **"Hello gô bi thúi của em , em là Gô bi của anh đây nè !"**
>
> Mỗi khi hoàn tất clone giọng mới hoặc khi người dùng yêu cầu nghe thử giọng, Agent **BẮT BUỘC** hiển thị thông tin và đường dẫn clickable đến cả hai file này.

---

## ⚡ 3. CÁC CÂU LỆNH MẪU CỦA NGƯỜI DÙNG & CÁCH AGENT XỬ LÝ

Động cơ mặc định cho toàn bộ hệ thống là **`omnivoice`** (tự động tăng tốc GPU Apple Silicon Metal MPS).

### Trường hợp 1: Yêu cầu Đọc Kịch bản / Đoạn văn
* **Câu lệnh người dùng:**
  - *"sử dụng voice-fm-lyly đọc đoạn văn: [Nội dung văn bản]"*
  - *"đọc content này bằng giọng voice-fm-1-mb: [Nội dung]"*
  - *"dùng voice-fm-lyly tạo audio cho bài review này"*
* **Hành động bắt buộc của Agent:**
  Chạy ngay lệnh sau qua terminal:
  ```bash
  uv run python scripts/voice/voice_studio.py speak --voice [voice-id] --script "[Nội dung văn bản]" --output "output/[ten_file].mp3"
  ```
  *(Mặc định `--engine omnivoice` đã được đóng gói sẵn)*.

---

### Trường hợp 2: Yêu cầu Clone & Nạp vào Kho Giọng
* **Câu lệnh người dùng:**
  - *"clone file này [path_to_video_or_mp3] thành voice-fm-lyly"*
  - *"nạp giọng từ video này [path] vào kho giọng với tên voice-nam-1"*
  - *"clone giọng bạn nữ trong file [path]"*
* **Hành động bắt buộc của Agent:**
  Chạy ngay lệnh clone tự động:
  ```bash
  uv run python scripts/voice/voice_studio.py clone --input "[duong_dan_file]" --name "[voice-id]" --dialect [north|south|central]
  ```
  Hệ thống sẽ tự động trích xuất, làm sạch, cắt lát câu trọn vẹn, trích xuất prompt `omnivoice_prompt.pt`, và **tự động sinh ngay 2 file**:
  - `assets/voice_vault/[voice-id]/source_original_preview.mp3`
  - `assets/voice_vault/[voice-id]/cloned_default_sample.mp3` (đọc: *"Hello gô bi thúi của em , em là Gô bi của anh đây nè !"*)
  Đồng thời tự động copy ra `output/` để người dùng nghe trực tiếp.

---

### Trường hợp 3: Tra cứu Danh sách Kho Giọng
* **Câu lệnh người dùng:**
  - *"danh sách giọng"* / *"trong kho đang có những giọng nào?"* / *"xem voice vault"*
* **Hành động bắt buộc của Agent:**
  Chạy lệnh:
  ```bash
  uv run python scripts/voice/voice_studio.py list
  ```
  Hiển thị danh sách kèm link file Source gốc và Clone mẫu câu mặc định.

---

## 🛠️ 4. QUY TRÌNH HẬU KỲ TỰ ĐỘNG (TIKTOK MASTERING)
Mọi file âm thanh sau khi sinh ra từ OmniVoice đều tự động đi qua chuỗi xử lý âm thanh:
1. **De-Esser:** Khử chói các âm xì *x, s, ch*.
2. **Presence Boost EQ:** `+3.5dB` tại dải `3.2kHz` giúp giọng nói sáng rõ trên nền nhạc.
3. **Dynamic Compressor:** Tỉ lệ `4:1` tạo độ nảy dồn dập.
4. **Loudness Normalization:** Chuẩn hóa `-14 LUFS` (chuẩn âm lượng TikTok Shop & Reels).
Output mặc định luôn là định dạng MP3 192kbps 44.1kHz chất lượng cao.
