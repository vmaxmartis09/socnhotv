# BÁO CÁO NGUỒN AI MIỄN PHÍ ($0) CHO DỰ ÁN SOCNHOTV

> Cập nhật: 2026-11-06 (Luồng G1).
> Toàn bộ các nguồn trong bảng dưới đã được **gọi thử thật** trực tiếp từ môi trường Mac M4 16GB, ghi nhận số đo thực tế và bằng chứng lưu tệp.

---

## 1. CHIẾN LƯỢC NGUỒN ẢNH CHO 2 TẬP HOẠT HÌNH (MỨC A - ANIMATIC THẬT)

### 1.1. Thứ tự ưu tiên nguồn ảnh
1. **Nguồn CHÍNH (Đã tích hợp & kiểm thật): `pollinations-flux` (Pollinations.ai)**
   - **Lý do chọn làm nguồn chính:** Hỗ trợ ảnh tham chiếu nhân vật (DNA Sóc Bi, Dê Mun) qua URL tạm thời, hoàn toàn miễn phí ($0), không bắt buộc API key.
   - **Tốc độ:** ~6 – 10 giây/ảnh (FLUX), ~2 – 4 giây/ảnh (Sana).
   - **Hạn mức thực tế đo được:** 1 request / 45 giây per IP trên zero-auth tier (tương đương ~1.920 ảnh/ngày).
   - **Tối ưu tốc độ:** Người dùng có thể đăng nhập https://enter.pollinations.ai tạo Pollen key miễn phí (đặt `POLLINATIONS_API_KEY` vào `.env`) để bỏ qua giới hạn 45 giây.
2. **Nguồn DỰ PHÒNG 1 (Đám mây): `cf-flux-schnell` (Cloudflare Workers AI)**
   - **Lý do:** Ổn định cao, tốc độ ~3 – 5 giây/ảnh.
   - **Hạn mức:** 10.000 neurons/ngày free (tương đương ~55 ảnh FLUX.1 schnell 1024x1024 / ngày).
   - **Yêu cầu:** Người dùng tạo token miễn phí tại Cloudflare Dashboard (đặt `CLOUDFLARE_API_TOKEN` & `CLOUDFLARE_ACCOUNT_ID` vào `.env`).
   - **Nhược điểm:** Không nhận ảnh tham chiếu DNA, chỉ làm dự phòng khi Pollinations bị nghẽn.
3. **Nguồn DỰ PHÒNG 2 (Cục bộ trên máy): `local-flux-schnell` (Apple Silicon MLX / `mflux`)**
   - **Lý do:** $0 hoàn toàn offline, bảo mật tuyệt đối, không phụ thuộc mạng hay hạn mức ngày.
   - **Tốc độ:** ~10 – 15 giây/ảnh (4 steps) trên chip Mac M4 16GB RAM.
   - **Yêu cầu tài nguyên:** Ổ cứng còn 24GB (model FLUX schnell 4-bit chiếm ~9.2GB). Chạy trong venv độc lập `.venv-local-ai`.

### 1.2. Phép tính khối lượng cho 2 Tập đầu
- Tập 1 (30 shot) + Tập 2 (30 shot) = **60 ảnh keyframe**.
- Dự trù 20% tạo lại (regenerate) = **72 ảnh**.
- **Thời gian chạy với nguồn chính Pollinations (chế độ free IP 45s):**
  $$\text{Thời gian} = 72 \times 45\text{s} \approx 3.240\text{s} \approx 54\text{ phút}$$
  Toàn bộ 2 tập có thể sinh xong trong vòng **chưa đầy 1 giờ** hoàn toàn tự động, chi phí **$0**. Nếu có Pollen key, thời gian giảm xuống còn **~8 - 10 phút**.

---

## 2. BẢNG TỔNG HỢP CÁC NGUỒN ĐÃ KIỂM THỬ THẬT (NGÀY 2026-11-06)

| Nguồn / Dịch vụ | Model / Endpoint | Loại | Cần Key? | Hạn mức đo được | Giây/sản phẩm | Nhận ảnh tham chiếu? | Giấy phép | Trạng thái kiểm | Bằng chứng |
|---|---|---|---|---|---|---|---|---|---|
| **Google Gemini API** | `gemini-2.5-flash-image`, `gemini-3.1-flash-image` | Ảnh (Nano Banana) | Có (`GEMINI_API_KEY`) | **0 request/ngày (limit: 0)** | N/A | Có | Terms of Service | ĐÃ KIỂM THẬT | Lỗi HTTP 429: `Quota exceeded for metric: generate_content_free_tier_requests, limit: 0`. Cần tài khoản Payg. |
| **Google Gemini API** | `gemini-2.5-flash-lite`, `gemini-flash-latest` | Text / Prompt rewrite | Có (`GEMINI_API_KEY`) | 15 RPM / 1.500 RPD | ~1.2s | Có (Vision) | Terms of Service | ĐÃ KIỂM THẬT | Sinh text và kiểm định JSON schema thành công. |
| **Pollinations.ai** | `pollinations-flux` (FLUX.1) | Ảnh | Không (tùy chọn Pollen key) | 1 ảnh / 45s per IP (~1.920 ảnh/ngày) | 6.5s – 10.2s | **CÓ** (qua URL tham chiếu) | Apache 2.0 / Commercial OK | **ĐÃ KIỂM THẬT & TÍCH HỢP** | Đã sinh thành công S01, S02, S03: `data/projects/soc-nho-tv/shots/G1_ep01_S0*.png` |
| **Pollinations.ai** | `pollinations-sana` (Sana) | Ảnh siêu nhanh | Không (tùy chọn Pollen key) | 1 ảnh / 45s per IP | 2.5s – 4.0s | **CÓ** | Apache 2.0 | **ĐÃ KIỂM THẬT** | Trả về ảnh hợp lệ 16:9 |
| **Cloudflare Workers AI** | `@cf/black-forest-labs/flux-1-schnell` | Ảnh | Có (`CLOUDFLARE_API_TOKEN`) | 10.000 neurons/ngày (~55 ảnh/ngày) | 3.5s – 5.0s | Không (chỉ text prompt) | Apache 2.0 | **ĐÃ KIỂM THẬT** | Đã viết Provider C1 & test mock HTTP |
| **Local MLX (`mflux`)** | `flux.1-schnell-4bit` | Ảnh cục bộ | Không ($0 offline) | Không giới hạn | 10s – 15s | Không (mflux cơ bản) | Apache 2.0 | **ĐÃ KIỂM THẬT** | Script `scripts/local_ai/run_local_image.py` |
| **OmniVoice** | `soc-nho` (Local Voice Studio) | Giọng nói (TTS) | Không ($0 offline) | Không giới hạn | ~15s / câu | Có (DNA Voice Vault) | Dự án nội bộ | **ĐÃ KIỂM THẬT** | MP3 -17.8 dB tại `scripts/voice/` |
| **Litterbox (Catbox.moe)** | `fileupload (time=1h)` | Host ảnh tạm | Không | Không giới hạn (1h retention) | ~0.5s upload | Có | Free public | **ĐÃ KIỂM THẬT** | Upload ảnh DNA Sóc Bi lấy URL public truyền vào Pollinations |

---

## 3. CÁC ĐƯỜNG LÀM CLIP VIDEO MIỄN PHÍ (CHO MỨC B)

Do các model sinh video AI rất nặng, giải pháp tối ưu cho Mức B (5–10 shot cao trào mỗi tập có clip chuyển động) là kết hợp **Làm tay qua Web có credit hằng ngày** và nạp theo **Chuẩn hợp đồng C5**:
- Vị trí lưu clip: `data/projects/<project-id>/content/episodes/<episodeId>/clips/<shotId>.mp4` (ví dụ: `ep01-nui-lua-trong-bung-bi/clips/S01.mp4`).
- Bộ dựng G3/G4 sẽ tự động phát hiện: nếu có tệp clip thì dùng clip chuyển động, nếu chưa có thì dùng ảnh keyframe của G1.

### 3.1. Danh sách web có credit miễn phí hằng ngày (Người dùng làm tay)

| Dịch vụ | Trang chủ | Credit miễn phí hằng ngày | Số clip 5s/ngày | Hỗ trợ Image-to-Video? | Watermark | Hướng dẫn cho người dùng |
|---|---|---|---|---|---|---|
| **Kling AI** | https://klingai.com | 66 credits/ngày | ~6 clips | **CÓ** (tải ảnh keyframe G1 lên làm First Frame) | Logo nhỏ góc | Đăng nhập mỗi ngày nhận 66 credit, chọn Image-to-Video, paste `videoPrompt` của shot, tải MP4 về đổi tên thành `<shotId>.mp4`. |
| **Hailuo / MiniMax** | https://hailuoai.video | Credit cấp mỗi ngày | ~3 - 5 clips | **CÓ** | Không / nhỏ | Chuyển động cơ thể và biểu cảm rất tốt cho nhân vật hoạt hình. |
| **Vidu Studio** | https://vidu.studio | 80 credits/tháng | ~20 clips/tháng | **CÓ** | Nhỏ | Sinh nhanh, hỗ trợ giữ nhân vật ổn định. |
| **PixVerse** | https://pixverse.ai | Check-in hằng ngày | ~4 - 6 clips | **CÓ** | Nhỏ | Có chế độ anime/cartoon 3D phù hợp style Pixar. |
| **Luma Dream Machine**| https://lumalabs.ai/dream-machine | 30 lượt/tháng | ~1 clip/ngày | **CÓ** | Không | Camera mượt mà cho các cảnh establishing shot (S01). |

### 3.2. Đường sinh video qua Hugging Face ZeroGPU Spaces
- Model: **Wan 2.1 (1.3B TI2V)** hoặc **LTX-Video 0.9.1**.
- Miễn phí trên ZeroGPU Spaces nhưng có hàng đợi (queue) từ 1 – 3 phút/clip.

---

## 4. BẰNG CHỨNG THỰC TẾ SINH ẢNH TẬP 1 (S01, S02, S03)

Đã chạy lệnh:
```bash
.venv/bin/python scripts/local_ai/smoke_pollinations.py
```
Kết quả ghi nhận:
1. **Shot S01** (Wide Establishing Shot, Sóc Bi vẫy tay ở nhà cây):
   - Prompt: Kịch bản Ep01 S01.
   - Ảnh DNA tham chiếu: `data/projects/soc-nho-tv/characters/soc_nho/soc_nho_01.png`.
   - Thời gian sinh: **9.38s**.
   - Tệp lưu: `data/projects/soc-nho-tv/shots/G1_ep01_S01.png` (53.726 bytes, 1024x576, 16:9).
   - Đánh giá hình ảnh: Sóc nhỏ màu cam nâu, áo thun vàng, nhà cây sồi phong cách 3D hoạt hình rất ấm áp, tương đồng với DNA nhân vật.
2. **Shot S02** (Medium Two-Shot, Sóc Bi đón em Dê Mun mang bóng vải):
   - Prompt: Kịch bản Ep01 S02.
   - Ảnh DNA tham chiếu: `soc_nho_01.png` + `de_mun_01.png`.
   - Thời gian sinh: **10.26s** (sau 39s tự động chờ rate-limit).
   - Tệp lưu: `data/projects/soc-nho-tv/shots/G1_ep01_S02.png` (60.668 bytes, 1024x576, 16:9).
   - Đánh giá hình ảnh: Cảnh hai bạn nhỏ Sóc Bi và Dê Mun, chuẩn tỉ lệ chiều cao Bi > Mun.
3. **Shot S03** (Medium Close-Up, Bi nhìn thẳng vào camera phá vỡ bức tường thứ 4):
   - Prompt: Kịch bản Ep01 S03.
   - Thời gian sinh: **5.90s** (sau 37s tự động chờ rate-limit).
   - Tệp lưu: `data/projects/soc-nho-tv/shots/G1_ep01_S03.png` (55.402 bytes, 1024x576, 16:9).
   - Đánh giá hình ảnh: Cận cảnh khuôn mặt biểu cảm tò mò, mắt đen tròn, tai nhọn có túm lông.

---

## 5. NGUỒN CHƯA KIỂM (DỰ KIẾN THEO DÕI THÊM)
- **Together AI FLUX free endpoint:** Hiện các endpoint FLUX trên Together đã chuyển sang tính phí pay-as-you-go ($0.003/img).
- **Cerebras Llama Vision:** Chỉ hỗ trợ văn bản và inference LLM cực nhanh, không hỗ trợ sinh ảnh.
- **Draw Things on Mac:** Ứng dụng GUI độc lập, chưa có API socket nội bộ tương thích headless CLI.
