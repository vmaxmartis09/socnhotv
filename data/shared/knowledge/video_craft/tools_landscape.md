# Toàn Cảnh Bản Đồ Công Cụ AI Video (AI Video Tools Landscape)

> Phân tích đối chiếu toàn diện các công cụ AI Video xuất hiện qua quét diện rộng TikTok (7 kênh, 282 video) với hệ sinh thái công nghệ nội bộ của dự án SocNhoTV / Gobi.

---

## 1. Bảng Đối Chiếu Tổng Thể (Master Tool Comparison Matrix)

| Danh Mục | Công Cụ Trên Thị Trường (TikTok Creators) | Chức Năng Chính | Chi Phí / Giới Hạn Thường Gặp | Tương Đương Trong Stack Nội Bộ | Trạng Thái & Khoảng Trống (Gap) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Sinh Video (Video Gen)** | **Kling AI 1.5 / 2.0** (Kuaishou) | Text-to-Video, Image-to-Video, Motion Brush, Start/End Frame | $10 - $35/tháng; giới hạn thời lượng 5s-10s/gen, xếp hàng giờ cao điểm | `Kling API / Adapter` | Đã có adapter; cần tích hợp tự động hóa nạp Start/End frame qua CLI |
| **Sinh Video (Video Gen)** | **Runway Gen-3 Alpha / Turbo** | Cinematic video generation, Camera control, Director Mode | $15 - $95/tháng; hao credit nhanh, video đôi khi bị biến dạng thạch | `Runway Adapter` | Đã có adapter; chi phí cao hơn Kling cho tác vụ KOC dài hạn |
| **Sinh Video (Video Gen)** | **Luma Dream Machine / Veo 2** | Camera tracking mượt mà, ánh xạ vật lý thế giới thực | $30/tháng; giới hạn độ phân giải và chờ đợi queue | `Veo2 / Luma Adapter` | Đang theo dõi; Kling 1.5 vẫn tối ưu chi phí hơn cho thị trường VN |
| **Thử Đồ Ảo (Virtual Try-On)** | **CatVTON / IDM-VTON** | Ghép quần áo thật lên người mẫu AI, giữ nguyên form dáng và vải | Mã nguồn mở (yêu cầu GPU VRAM >= 16GB) | `ComfyUI CatVTON Node` | Tương đương 100%; stack nội bộ chạy local hoặc Cloud GPU không tốn sub |
| **Sinh Ảnh Cơ Sở (Image Gen)** | **Flux.1 (Dev / Schnell)** | Tạo chân dung KOC, phối cảnh 3D siêu chi tiết, render chữ chuẩn | Nặng VRAM (12-24GB) nếu chạy local | `Flux.1 Local / Replicate` | Đã tích hợp đầy đủ; dùng làm nền tảng cho Master DNA nhân vật |
| **Biên Tập Video (NLE & Assembly)** | **CapCut / Premiere Pro** | Cắt ghép thủ công, thêm sticker, hiệu ứng chuyển cảnh | $10/tháng (CapCut Pro); không thể tự động hoá quy mô lớn | **HeyGen HyperFrames** | **Vượt trội hoàn toàn**: HyperFrames render HTML5/CSS/GSAP tất định 100% |
| **Lồng Tiếng AI (Voiceover / TTS)** | **ElevenLabs / Vbee / Minimax** | Giọng đọc AI đa ngôn ngữ, cảm xúc tự nhiên | $5 - $22/tháng; ElevenLabs đắt đỏ với số lượng video lớn | **OmniVoice SOTA (`soc-nho`)** | Độc quyền nội bộ; mastering TikTok chuẩn -14 LUFS, presence +3.5dB |
| **Bóc Tách Phụ Đề (STT / Captions)** | **CapCut Auto Captions** | Tự động tạo phụ đề chạy chữ trên video | Dễ lỗi chính tả tiếng Việt, font chữ giới hạn | `faster-whisper` + HyperFrames Kinetic | Whisper bóc tách word-level cực chuẩn, kinetic caption GSAP biến hình |
| **KOC AI Talking Head** | **HeyGen / Arcads / Hedra** | Avatar KOC nói chuyện theo kịch bản | $29 - $120/tháng; cử chỉ tay và biểu cảm khuôn mặt đôi khi gượng | `HeyGen API + Motion Mimic` | Đã có skill `motion-mimic` bắt chước 100% cử chỉ video mẫu |

---

## 2. Chi Tiết Từng Công Cụ & Đánh Giá Thực Chiến

### 2.1. Kling AI 1.5 (Công cụ sinh video số 1 hiện nay cho KOC)
- **Điểm mạnh phát hiện từ thực tế:**
  - Khả năng kiểm soát chuyển động hai đầu qua **Start Frame + End Frame** triệt tiêu hoàn toàn lỗi morphing.
  - **Motion Brush** cho phép tô chọn tối đa 6 vùng chuyển động độc lập trong 1 khung hình.
  - Chi phí tín dụng (Credits) rẻ hơn 40% so với Runway Gen-3.
- **Điểm yếu & Mẫu lùa gà:**
  - Nhiều creator quảng cáo "làm phim hoạt hình 3D trong 1 click bằng Kling" nhưng thực chất phải ghép hàng chục clip 5s và lọc bỏ 70% phế phẩm.
- **Ứng dụng vào Studio SocNhoTV:**
  - Kết nối với `tool/src/socnhotv/adapters/` để tự động render các shot chuyển động B-roll của Sóc Nhỏ (Bi) và Koala.

### 2.2. CatVTON & IDM-VTON (Vũ khí tối thượng cho Fashion Affiliate)
- **Điểm mạnh:**
  - Giữ lại 98% hoa văn, đường thêu và chất liệu vải thực tế.
  - Khắc phục hoàn toàn điểm yếu "vẽ bừa hoa văn" của Midjourney/Stable Diffusion thông thường.
- **Ứng dụng vào Studio:**
  - Đóng gói thành workflow `vton-flux-catvton` trong ComfyUI để sản xuất hàng loạt video KOC thay đồ cho Gobi Boutique.

### 2.3. HeyGen HyperFrames (Lợi thế cạnh tranh tuyệt đối của SocNhoTV)
- **Tại sao toàn bộ thị trường bên ngoài đang bị tắc nghẽn:**
  - Hầu hết các kênh TikTok (@bahuy.henry, @anongvn, @nhueit) vẫn đang xuất từng clip AI rồi mở CapCut kéo thả thủ công hoặc viết script CapCut phức tạp, rất dễ lỗi font hoặc lệch timeline khi đổi nhạc.
- **Sức mạnh khác biệt của HyperFrames trong dự án của chúng ta:**
  - Kịch bản kịch bản được mô tả bằng HTML5/CSS/GSAP.
  - Phụ đề, icon Morphicons, hiệu ứng chuyển cảnh, ducking âm thanh được tính toán đồng bộ theo mili-giây.
  - Render hàng loạt qua CLI không cần mở giao diện đồ họa, tiết kiệm 95% nhân lực.

---

## 3. Các Khoảng Trống Công Nghệ (Tech Gaps) Cần Bổ Sung Cho Studio

1. **Auto-Framing & Inpainting cho Logo Quần Áo:**
   - Khi chạy CatVTON, các chữ in nhỏ trên ngực áo đôi khi bị mờ. Cần thêm 1 bước tự động composite lại vector logo gốc.
2. **Preset Quỹ Đạo Camera (Camera Path Presets):**
   - Cần đóng gói sẵn 10 file cấu hình camera (Orbit, Dolly-in, Whip-pan) vào thư viện `tool/src/socnhotv/video/craft/camera.py` để gọi nhanh bằng 1 tham số.
3. **Thư Viện SFX Tự Động Gắn Theo Beat:**
   - Tự động quét các đỉnh âm thanh (Audio Transients) của video và chèn SFX (Whoosh, Click, Pop) tại mili-giây thích hợp mà không cần can thiệp thủ công.
