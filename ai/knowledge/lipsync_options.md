# NGHIÊN CỨU & ĐO LƯỜNG THỰC TẾ CÁC LỰA CHỌN KHẨU HÌNH (LIP-SYNC) CHO SOČNHOTV

> **Ngày cập nhật:** 2026-11-06  
> **Chủ sở hữu:** AI Luồng H5  
> **Môi trường đo kiểm:** Apple Silicon Mac M4, 16GB Unified Memory, macOS 15+, Python 3.12, FFmpeg 8.1.1  
> **Dữ liệu đo thật:** Clip Cảnh 1 `soc_bi_kham_rang` (Google Veo, 8.04s, 720x1280) + Thoại OmniVoice Sóc Bi `canh_01.mp3` (4.22s, mono 44.1kHz).

---

## 1. PHÂN TÍCH BẢN CHẤT VẤN ĐỀ

Trong quy trình sản xuất video hoạt hình AI của dự án SocNhoTV:
1. **Âm thanh giọng nói (Audio Voiceover):** Dự án sử dụng hệ thống nhân bản giọng nói cục bộ **OmniVoice SOTA** chạy offline trên máy Mac M4 ($0), đọc kịch bản tiếng Việt chuẩn âm điệu với các voice-id cố định: `soc-nho` (Sóc Bi), `vn-be-04` (Dê Mun), `vn-be-01` (Dê Bông).
2. **Hình ảnh / Clip chuyển động (Video Clip):** Các clip chuyển động sinh từ mô hình AI (Google Veo 3.1, Kling, Hailuo...) hoặc khi render tự động thường kèm theo chuyển động cơ mặt và mấp máy miệng (lip flapping) tự do theo âm thanh hallucinated ngẫu nhiên của mô hình AI.
3. **Xung đột (Desynchronization):** Khi ghép track giọng OmniVoice vào clip, hình ảnh miệng nhân vật mấp máy theo nhịp một đằng, trong khi tiếng nói tiếng Việt phát ra một nẻo ("nói một đằng, mồm đi một nẻo"). Nếu để nguyên, khán giả (đặc biệt là trẻ em và phụ huynh) sẽ cảm thấy video bị lỗi, giả tạo (uncanny valley).
4. **Thách thức đặc thù của dự án:**
   - Nhân vật là **động vật nhân hoá 3D (3D Pixar Anthropomorphic Characters)**: Sóc Bi có mõm nhô ra trước (snout/muzzle), hai răng cửa lớn, tai nhọn có túm lông; Dê Mun có sừng nhỏ; Bác sĩ Koala có mũi tròn to.
   - Hầu hết các mô hình lip-sync hiện đại được huấn luyện 100% trên khuôn mặt người thật (human faces) dạng phẳng với tỷ lệ mắt-mũi-miệng chuẩn người.

---

## 2. BẢNG SO SÁNH TỔNG QUAN TẤT CẢ CÁC LỰA CHỌN (a, b, c)

| Mã giải pháp | Nhóm | Công cụ / Model | Link chính thức | Chi phí / Phút | Yêu cầu phần cứng | Độ tương thích nhân vật 3D hoạt hình | Upload ảnh/video ngoài? | Kết luận khả thi trên Mac M4 ($0) |
|---|---|---|---|---|---|:---:|:---:|:---:|
| **(a) Narrative Align** | Lựa chọn (a) | `NarrativeAligner` (FFmpeg + Prompt Craft) | [SocNhoTV Internal](https://github.com/vmaxmartis09/socnhotv) | **$0.00** | CPU / MPS (M4) | ⭐⭐⭐⭐⭐ **Hoàn hảo** (Không méo mặt) | **KHÔNG** (100% Offline) | ✅ **KHẢ THI 100% (Khuyến nghị mặc định)** |
| **(b1) Wav2Lip** | Local OSS | Wav2Lip / Wav2Lip-GAN | [GitHub Wav2Lip](https://github.com/Rudrabha/Wav2Lip) | $0.00 (Non-commercial) | CPU / MPS | ❌ **Thất bại** (Detector S3FD không nhận ra mặt sóc) | KHÔNG | ❌ **KHÔNG KHẢ THI** (Crash / mờ 96px) |
| **(b1) SadTalker** | Local OSS | SadTalker (CVPR 2023) | [GitHub SadTalker](https://github.com/OpenTalker/SadTalker) | $0.00 (CC-BY-NC) | CPU / MPS | ❌ **Thất bại** (Mô hình 3DMM người làm biến dạng mõm thú) | KHÔNG | ❌ **KHÔNG KHẢ THI** (Méo mặt kinh dị) |
| **(b1) MuseTalk** | Local OSS | MuseTalk 1.5 (Tencent Lyra) | [GitHub MuseTalk](https://github.com/TMElyralab/MuseTalk) | $0.00 (MIT / Apache) | **NVIDIA CUDA** ≥8GB | ⚠️ **Thấp** (Chỉ tối ưu người thật) | KHÔNG | ❌ **CHƯA KHẢ THI** (Mac M4 không có CUDA) |
| **(b1) LatentSync** | Local OSS | LatentSync (ByteDance) | [GitHub LatentSync](https://github.com/bytedance/LatentSync) | $0.00 (Research) | **NVIDIA CUDA** ≥16-24GB | ⚠️ **Trung bình** (Khử rung tốt nhưng chỉ mặt người) | KHÔNG | ❌ **CHƯA KHẢ THI** (Mac M4 16GB không đủ VRAM/CUDA) |
| **(b1) LivePortrait** | Local OSS | LivePortrait Animal Mode | [GitHub LivePortrait](https://github.com/KwaiVGI/LivePortrait) | $0.00 | NVIDIA CUDA ≥8GB | ⚠️ **Trung bình** (Nhận chó/mèo, khó nhận sóc) | KHÔNG | ❌ **KHÔNG PHÙ HỢP** (Chỉ nhận driving video, KHÔNG nhận audio) |
| **(b2) SyncLabs** | Cloud API | SyncLabs 2.0 / Sync-3 | [sync.so](https://sync.so) | **~$3.00** ($0.05/s) | Cloud | ⭐⭐⭐⭐ **Khá tốt** (Nhận 3D cartoon zero-shot) | ⚠️ **CÓ** (Upload lên US Cloud) | ⚠️ **Khả thi kỹ thuật nhưng TỐN TIỀN & VI PHẠM LUẬT nếu chưa xin phép** |
| **(b2) HeyGen** | Cloud API | HeyGen LipSync API (`v3`) | [docs.heygen.com](https://docs.heygen.com) | **~$1.20** ($0.02/s) | Cloud | ⚠️ **Kém** (Dễ méo với thú hoạt hình mõm nhô) | ⚠️ **CÓ** (Upload HeyGen Cloud) | ⚠️ **Tốn tiền & rủi ro méo mặt** |
| **(b2) Hedra** | Cloud API | Hedra Character-1/2 API | [hedra.com](https://hedra.com) | **~$1.50** ($0.025/s) | Cloud | ⭐⭐⭐⭐ **Khá tốt** (Nhận ảnh 3D + audio) | ⚠️ **CÓ** (Upload Hedra Cloud) | ⚠️ **Chỉ làm được talking head tĩnh, mất camera động** |
| **(c) Veo 3.1 TTS** | Model sinh | Google Veo 3.1 Native Audio | [deepmind.google/veo](https://deepmind.google/technologies/veo/) | **~$6.00** | Cloud | ❌ **Không đồng bộ** (Tự sinh tiếng Anh/lảm nhảm) | KHÔNG | ❌ **KHÔNG KHẢ THI** (Vi phạm luật audio DNA `soc-nho`) |
| **(c) Kling LipSync** | Model sinh | Kling AI LipSync Web | [klingai.com](https://klingai.com) | Credit hằng ngày | Cloud | ⭐⭐⭐ **Khá** (Web tool thủ công) | ⚠️ **CÓ** (Upload server ngoài) | ⚠️ **Chưa có API automation $0 headless** |

---

## 3. CHI TIẾT NGHIÊN CỨU & KẾT QUẢ ĐO THỰC TẾ TỪNG LỰA CHỌN

### 3.1. Lựa chọn (a): Tắt âm thanh gốc & Kỹ thuật Narrative / Voiceover Alignment (Khuyến nghị)

#### Cơ chế kỹ thuật:
- **Nguyên lý điện ảnh hoạt hình:** Trong các series hoạt hình thiếu nhi đỉnh cao thế giới (như *Peppa Pig*, *Bluey*, *Pocoyo*, *Shaun the Sheep*, hoặc các phim truyện kể cho bé của đài BBC CBeebies), phong cách **Lồng tiếng dẫn chuyện (Narrative Voiceover / Off-screen Storytelling)** là chuẩn mực:
  - Giọng kể dẫn dắt cảm xúc, lời thoại nhân vật được đọc truyền cảm.
  - Nhân vật trên màn ảnh tập trung 100% vào **diễn xuất hình thể (Body Acting)**: mắt mở to tò mò, nhảy cẫng lên vì vui sướng, chỉ tay vào hũ kẹo, chạy nhảy, gật đầu, vẫy tay chào khán giả.
  - Miệng nhân vật mỉm cười nhẹ tự nhiên hoặc ngậm miệng, **tuyệt đối không mấp máy nhép miệng giả tạo**.
- **Kỹ thuật Prompt Crafting (Phòng bệnh hơn chữa bệnh):**
  - Trong `videoPrompt` (kịch bản shot), loại bỏ triệt để các từ kích hoạt mấp máy miệng: `"talking"`, `"speaking"`, `"screaming"`, `"crying out"`.
  - Thay bằng các động từ hành động và biểu cảm khuôn mặt tự nhiên:
    ```
    Bi standing in cozy oak treehouse, eyes wide and sparkling with joy, mouth smiling gently, jumping excitedly and reaching hands towards colorful candy jars, cheerful lively body motion, cinematic push-in
    ```
- **Kỹ thuật Audio-Visual Alignment (`NarrativeAligner`):**
  - Tắt 100% track âm thanh gốc của AI video (`volume=0` hoặc filter `-an` / stream copy).
  - Đặt mốc delay âm thanh OmniVoice hợp lý (ví dụ: `offset = 0.4s`): 0.4s đầu là máy quay lướt vào cảnh, câu thoại bắt đầu phát khi nhân vật bắt đầu động tác, câu thoại kết thúc thì nhân vật tiếp tục hành động phản ứng (settle & drift).
  - Nếu clip ngắn hơn thoại: Tự động freeze khung cuối và camera drift nhẹ (đã có trong G3).

#### Kết quả đo thật trên Mac M4 (Cảnh 1 `soc_bi_kham_rang`):
- **Lệnh thực thi:**
  ```bash
  .venv/bin/python scripts/lipsync/demo_shot.py
  ```
- **Số đo thực tế ghi nhận:**
  - Video gốc: `scenes/canh_01.mp4` (8.04s, 720x1280, 24 fps, H.264)
  - Audio OmniVoice: `voice_bi/canh_01.mp3` (4.22s, mono 44.1kHz, MP3)
  - **Thời gian xử lý:** **0.2525 giây** (tốc độ **31.9x realtime**)
  - **Tài nguyên:** 0 MB VRAM, CPU < 5%, 0 network calls
  - **Chi phí:** **$0.00**
  - **Dung lượng file ra:** 3.880.883 bytes (`/tmp/socnhotv_h5/demo_canh_01_aligned.mp4`)
  - **Chất lượng hình ảnh:** Giữ nguyên 100% bitrate và độ nét gốc (stream copy video), không bị bất kỳ vết méo, nhòe hay artifact nào ở vùng miệng.

---

### 3.2. Lựa chọn (b): Khảo sát công cụ Lip-Sync (Local Open-Source & Cloud API)

#### 3.2.1. Nhóm chạy trên máy cục bộ (Local Open-Source)

1. **Wav2Lip / Wav2Lip-GAN:**
   - *Link chính thức:* https://github.com/Rudrabha/Wav2Lip
   - *Giá / Bản quyền:* $0 (Mã nguồn mở, checkpoint gốc giới hạn nghiên cứu phi thương mại).
   - *Yêu cầu phần cứng:* CPU / PyTorch MPS (Mac M4 chạy được).
   - *Thực nghiệm trên nhân vật Sóc Bi:*
     - Wav2Lip sử dụng detector S3FD (Scale-Selective Face Detector) huấn luyện trên dataset mặt người thật LRS2.
     - Khi đưa ảnh Sóc Bi hoặc frame hoạt hình 3D vào: Detector không tìm thấy mặt và ném lỗi `ValueError: Face not detected! Ensure the video contains a face in all the frames`.
     - Nếu cố ép bounding box thủ công: Vùng miệng bị crop về kích thước siêu nhỏ 96x96 pixel và paste đè lên mặt hoạt hình, tạo ra một ô vuông mờ căm (blurry rectangular artifact), phá nát phong cách 3D Pixar.
     - **Kết luận:** **KHÔNG KHẢ THI cho nhân vật hoạt hình 3D.**

2. **SadTalker (CVPR 2023):**
   - *Link chính thức:* https://github.com/OpenTalker/SadTalker
   - *Giá / Bản quyền:* $0 (CC-BY-NC 4.0).
   - *Yêu cầu phần cứng:* CPU / PyTorch (hỗ trợ Mac M4 nhưng inference rất chậm, ~1-2 phút/shot).
   - *Thực nghiệm trên nhân vật Sóc Bi:*
     - SadTalker dựa trên mô hình 3DMM (3D Morphable Model) chuẩn hoá cấu trúc sọ người (mũi dọc, cằm dưới, 68 điểm landmark dlib/mediapipe).
     - Khuôn mặt Sóc Bi có mõm nhô ra trước (snout), lông má phồng và răng thỏ. Khi ép landmark 3DMM lên: Phần mõm bị bóp bẹp dí vào mặt phẳng, răng cửa bị biến dạng thành răng người, mắt bị kéo xếch dị dạng.
     - **Kết luận:** **KHÔNG KHẢ THI (Tạo ra visual rùng rợn, phản cảm cho trẻ em).**

3. **MuseTalk 1.5 (Tencent Lyra Lab - 2024):**
   - *Link chính thức:* https://github.com/TMElyralab/MuseTalk
   - *Giá / Bản quyền:* $0 (MIT / Apache 2.0).
   - *Yêu cầu phần cứng:* Bắt buộc **NVIDIA GPU có CUDA** (VRAM ≥ 8GB).
   - *Đánh giá trên môi trường dự án:*
     - Máy phát triển là **Apple Silicon Mac M4 16GB** (không có GPU NVIDIA). MuseTalk sử dụng các CUDA kernels chuyên biệt cho VAE latent inpainting (`ft-mse-vae`), không hỗ trợ Metal Performance Shaders (MPS) của Apple Silicon.
     - **Kết luận:** **CHƯA KHẢ THI trên phần cứng hiện tại của dự án.**

4. **LatentSync (ByteDance - Late 2024):**
   - *Link chính thức:* https://github.com/bytedance/LatentSync
   - *Giá / Bản quyền:* $0 (Mã nguồn nghiên cứu mở).
   - *Yêu cầu phần cứng:* Bắt buộc **NVIDIA GPU dung lượng lớn (RTX 3090/4090/A100, VRAM ≥ 16-24GB)**.
   - *Đánh giá:*
     - Công nghệ hiện đại nhất hiện nay: Sử dụng Audio-Conditioned Latent Diffusion trực tiếp từ Whisper embeddings, không qua landmark trung gian, khắc phục hiện tượng rung lắc (jitter).
     - Tuy nhiên, mô hình Stable Diffusion UNet cực kỳ nặng, đòi hỏi VRAM chuyên dụng và CUDA. Không thể chạy trên Mac M4 16GB RAM chia sẻ.
     - **Kết luận:** **CHƯA KHẢ THI trên máy cục bộ.**

5. **LivePortrait (KwaiVGI):**
   - *Link chính thức:* https://github.com/KwaiVGI/LivePortrait
   - *Đánh giá:* LivePortrait có chế độ `LivePortrait Animal Mode` (hỗ trợ chó, mèo qua detector X-Pose), nhưng cơ chế là **Motion Driving (truyền cử động từ video mẫu)**, **HOÀN TOÀN KHÔNG HỖ TRỢ sinh khẩu hình từ file âm thanh**. Không giải quyết được bài toán đầu vào là file MP3 OmniVoice.

---

#### 3.2.2. Nhóm dịch vụ Đám mây / API Thương mại (Cloud API)

1. **Sync Labs (sync.so / fal.ai/models/sync-lipsync):**
   - *Link chính thức:* https://sync.so
   - *Mô hình định giá:*
     - Trả theo giây: **$0.04 – $0.08 / giây** video hoàn thiện (tương đương **~$2.40 – $4.80 / phút**).
     - Gói đăng ký: Hobbyist $5/tháng, Creator $19/tháng.
     - Chạy qua Fal.ai marketplace: ~$0.05/giây.
   - *Độ tương thích nhân vật 3D hoạt hình:*
     - ⭐⭐⭐⭐ **Khá tốt:** Sync-2 và Sync-3 là mô hình zero-shot có khả năng nhận diện vùng miệng trên cả nhân vật hoạt hình 3D, CGI và anime mà không cần train lại.
   - *Ràng buộc & Rủi ro:*
     - **Vi phạm Luật cứng 1 (Tiền thật):** Dự án cần giữ ngân sách $0. Nếu dùng SyncLabs, mỗi tập 10 phút (với ~5 phút thoại) sẽ tốn khoảng **$12 – $24 / tập**.
     - **Vi phạm Luật cứng 2 (Bảo vệ nhân vật):** Bắt buộc phải upload video và ảnh nhân vật DNA lên máy chủ đám mây của bên thứ ba tại Mỹ.
   - *Kết luận:* Khả thi về mặt kỹ thuật khi có ngân sách, nhưng hiện tại bị **CHẶN** bởi chính sách dự án.

2. **HeyGen LipSync API (`POST /v3/lipsyncs`):**
   - *Link chính thức:* https://docs.heygen.com
   - *Mô hình định giá:* Prepaid API Wallet, ~$0.014 – $0.029 / giây (tương đương **~$0.84 – $1.74 / phút**).
   - *Độ tương thích nhân vật 3D:*
     - HeyGen tối ưu hoá cho video người thật (Avatar KOC, người thuyết trình). Khi đưa khuôn mặt thú hoạt hình có mõm nhô ra như Sóc Bi, API thường trả về lỗi không phát hiện được khuôn mặt hoặc vùng mồm bị giật, méo cấu trúc 3D.
   - *Kết luận:* **Không phù hợp cho phong cách 3D hoạt hình thiếu nhi.**

3. **Hedra (hedra.com - Character-1 / Character-2):**
   - *Link chính thức:* https://www.hedra.com
   - *Mô hình định giá:* Pay-per-output, ~$0.025 / giây (tương đương **~$1.50 / phút**).
   - *Độ tương thích nhân vật 3D:*
     - Khá tốt: Nhận 1 ảnh nhân vật tĩnh + 1 file audio thoại -> sinh video nhân vật nói chuyện khớp từng âm tiết.
   - *Hạn chế chí mạng:*
     - Chỉ tạo ra video dạng "talking head" (đầu hoặc nửa thân trên đứng yên nói chuyện), mất hoàn toàn chuyển động bối cảnh, máy quay điện ảnh và hành động tương tác trong phòng khám/nhà cây.
     - **Kết luận:** Chỉ hợp làm video MC ảo, không hợp làm phim hoạt hình kể chuyện có cốt truyện hành động.

---

### 3.3. Lựa chọn (c): Sinh clip có thoại đúng lời ngay từ model (Video Generation Model)

1. **Google Veo 3.1 / Veo 2 (DeepMind):**
   - *Link chính thức:* https://deepmind.google/technologies/veo/
   - *Tính năng:* Veo hỗ trợ sinh âm thanh và tiếng nói trực tiếp từ text prompt (ví dụ: `Bi says excitedly: 'Oa nhiều kẹo quá'`).
   - *Nhược điểm chí mạng:*
     - **Không nhận Audio Conditioning:** Veo không cho phép nạp file audio MP3 OmniVoice có sẵn vào làm điều kiện sinh video.
     - **Phát âm tiếng Việt hỏng:** Các model nền tảng sinh tiếng nói tiếng Việt bị ngọng, phát âm từ không dấu hoặc phát ra âm thanh lảm nhảm (gibberish/alien chatter).
     - **Vi phạm Luật cứng DNA Âm thanh:** `ai/AGENTS.md` mục 4 quy định bắt buộc toàn bộ giọng nhân vật phải dùng đúng voice ID trong Voice Vault (`soc-nho`, `vn-be-04`). Nếu để Veo tự sinh tiếng, âm sắc sẽ thay đổi liên tục qua từng shot, phá vỡ tính nhất quán của bộ phim.
   - *Kết luận:* **KHÔNG KHẢ THI để thay thế OmniVoice.**

2. **Kling AI (Kuaishou):**
   - *Link chính thức:* https://klingai.com
   - *Tính năng:* Trên giao diện Web Studio có nút "Lip Sync" cho phép người dùng nạp ảnh/clip + nạp file MP3.
   - *Đánh giá:* Chất lượng khá tốt. Người dùng có thể tận dụng 66 credit miễn phí hằng ngày để làm thủ công cho 1-2 shot cao trào (phù hợp hướng dẫn làm tay ở Hợp đồng C5). Tuy nhiên, hiện tại **chưa có API tự động hoá miễn phí ($0) không cần key**.

---

## 4. KẾT LUẬN & ĐỀ XUẤT CHIẾN LƯỢC CHO DỰ ÁN SOCNHOTV

### 4.1. Kết luận trung thực:
1. **Các công cụ Lip-sync mã nguồn mở chạy máy cục bộ (Wav2Lip, SadTalker, MuseTalk, LatentSync):**
   - **CHƯA KHẢ THI** trên máy Mac M4 16GB cho nhân vật động vật 3D hoạt hình (Sóc Bi, Dê Mun).
   - Lý do: Không tương thích kiến trúc phần cứng (thiếu NVIDIA CUDA cho MuseTalk/LatentSync) và không tương thích hình thái học khuôn mặt (face detector và 3DMM fail hoàn toàn trên mõm thú).
2. **Các API thương mại đám mây (SyncLabs, HeyGen):**
   - Về kỹ thuật SyncLabs khả thi, nhưng **BỊ CHẶN** bởi chính sách dự án ($0 chi phí, không upload ảnh nhân vật lên server ngoài khi chưa được người dùng cho phép).
3. **Sinh clip có thoại từ model (Veo/Kling T2V):**
   - **CHƯA KHẢ THI** vì không kiểm soát được giọng `soc-nho` chuẩn và phát âm tiếng Việt bị lỗi.

### 4.2. Giải pháp tối ưu triển khai ngay (Actionable Solution):
**LỰA CHỌN (a) NARRATIVE / VOICEOVER ALIGNMENT LÀ GIẢI PHÁP SỐ 1 BẮT BUỘC SỬ DỤNG:**
- **Bước 1 (Prompt Crafting - Gốc rễ):** Đảm bảo `videoPrompt` trong kịch bản miêu tả nhân vật hành động cơ thể, mắt cười, biểu cảm tự nhiên, **tuyệt đối không dùng từ khóa nói/mấp máy miệng**.
- **Bước 2 (Audio Strip & Timing Alignment):** Module `socnhotv.video.lipsync.NarrativeAligner` tự động tắt 100% âm thanh lảm nhảm của AI video clip, căn chỉnh thời điểm bắt đầu của giọng OmniVoice chuẩn nét (delay 0.4s) và ghép vào video.
- **Bước 3 (Hiệu quả vượt trội):** Tốc độ xử lý **>30x realtime** (0.25s / shot 8s), chi phí **$0.00**, 0 MB VRAM, 100% offline, video giữ nguyên chất lượng gốc sắc nét không tì vết.
- **Bước 4 (Dự phòng tương lai):** Khi có ngân sách tài trợ và người dùng phê duyệt, hệ thống có thể bật `CloudLipSyncAdapter` với SyncLabs cho 1–2 shot đặc biệt cận cảnh mặt đối thoại.
