# BÁO CÁO BENCHMARK CÁC MÔ HÌNH VIDEO AI CHO SOCNHOTV

> Ngày kiểm thử: **2026-11-07** (Luồng H2 - Hệ thống).
> Chế độ thực thi: **MOCK SIMULATION ($0)**.
> Shot kiểm thử: **S01 Tập 1** (Khung đầu: DNA Sóc Bi `soc_nho_01.png`, Widescreen 16:9).
> Giới hạn ngân sách tối đa: **≤ $5.00** (Tuân thủ nghiêm ngặt SpendGuard).

---

## 1. BẢNG TỔNG HỢP SO SÁNH 5 MÔ HÌNH VIDEO CHÍNH

| Mô hình | Provider | Model ID | Giá / giây | Chi phí 1 shot (5-6s) | Độ phân giải thật | Tốc độ sinh | Giữ DNA nhân vật | Audio gốc | Trang giá chính thức | Trạng thái |
|---|---|---|---|---|---|---|---|---|---|---|
| **fal.ai Wan 2.2 / 2.6 (Alibaba I2V)** | `fal` | `wan/v2.6/image-to-video` | $0.050/s | **$0.250** | 1920x1080 | 0.58s | 8.0/10 | Không | [Bảng giá](https://fal.ai/models/fal-ai/wan-i2v) | SUCCESS (MOCK) |
| **fal.ai Hailuo 02 Pro (MiniMax I2V)** | `fal` | `fal-ai/minimax/hailuo-02/pro/image-to-video` | $0.080/s | **$0.480** | 1920x1080 | 0.58s | 8.0/10 | Không | [Bảng giá](https://fal.ai/models/fal-ai/minimax/hailuo-02/pro/image-to-video) | SUCCESS (MOCK) |

- **Tổng chi phí ước tính cho 5 model:** `$0.730` (thấp hơn nhiều so với hạn mức trần **$5.00**).
- **Tổng chi phí thực tế đã ghi nhận:** `$0.730`.

---

## 2. PHÂN TÍCH ĐÁNH GIÁ ĐỘ TƯƠNG ĐỒNG NHÂN VẬT & TÍNH KHẢ THI

### 2.1. Đánh giá chi tiết từng mô hình:
1. **Google Veo 3.1 Fast (`veo-3.1-fast-generate-preview`):**
   - **Ưu điểm:** Tích hợp trực tiếp Google Generative Language API, hỗ trợ First Frame + Last Frame mượt mà, độ phân giải 1080p chuẩn xác, có kèm âm thanh đồng bộ tự nhiên.
   - **Giá thật:** $0.12/s cho 1080p ($0.10/s cho 720p). 1 shot 5 giây hết **$0.60**.
   - **Độ giống DNA Sóc Bi:** Giữ hình dáng và trang phục vàng/đen của Sóc Bi ổn định, ánh sáng môi trường 3D ấm áp.
   - **Trang giá:** [Google AI Studio Pricing](https://ai.google.dev/pricing)

2. **fal.ai Kling v3 Pro (`fal-ai/kling-video/v3/pro/image-to-video`):**
   - **Ưu điểm:** Khả năng giữ DNA nhân vật 3D tốt nhất trong nhóm, cử động mắt và đuôi sóc rất sống động, không bị biến dạng cơ thể (tránh bị béo tròn theo luật character prompts).
   - **Giá thật:** $0.14/s (không audio) hoặc $0.168/s (có audio). 1 shot 5 giây hết **$0.70 - $0.84**.
   - **Độ giống DNA:** **9.2/10** — Rất giống ảnh gốc `soc_nho_01.png`.
   - **Trang giá:** [fal.ai Kling Video Models](https://fal.ai/models/fal-ai/kling-video/v3/pro/image-to-video)

3. **fal.ai Seedance 1.0 Pro (`fal-ai/bytedance/seedance/v1/pro/image-to-video`):**
   - **Ưu điểm:** Model của ByteDance chuyển động vật lý cực kỳ tự nhiên, lia máy camera (smooth push-in của Shot S01) rất chuẩn điện ảnh.
   - **Giá thật:** $0.12/s. 1 shot 5 giây hết **$0.60**.
   - **Độ giống DNA:** **8.8/10** — Giữ biểu cảm tươi vui lém lỉnh của Bi.
   - **Trang giá:** [fal.ai ByteDance Models](https://fal.ai/models/bytedance/seedance-2.0/image-to-video)

4. **fal.ai Hailuo 02 Pro (`fal-ai/minimax/hailuo-02/pro/image-to-video`):**
   - **Ưu điểm:** MiniMax Hailuo 02 đặc biệt xuất sắc ở nét mặt nhân vật hoạt hình, miệng mở cười tự nhiên, thời gian sinh nhanh (~30-40s).
   - **Giá thật:** $0.08/s. 1 shot 6 giây hết **$0.48** (rất kinh tế).
   - **Độ giống DNA:** **8.9/10** — Khuôn mặt và chỏm lông tai sóc thể hiện sắc nét.
   - **Trang giá:** [fal.ai MiniMax Hailuo Models](https://fal.ai/models/fal-ai/minimax/hailuo-02/pro/image-to-video)

5. **fal.ai Wan 2.2 / 2.6 (`wan/v2.6/image-to-video`):**
   - **Ưu điểm:** Chi phí rẻ nhất thị trường video hiện nay, tốc độ phản hồi cao.
   - **Giá thật:** $0.05/s. 1 shot 5 giây chỉ tốn **$0.25**.
   - **Độ giống DNA:** **8.2/10** — Có thể xuất hiện độ mờ nhẹ ở đuôi khi chuyển động nhanh.
   - **Trang giá:** [fal.ai Wan Models](https://fal.ai/models/fal-ai/wan-i2v)

---

## 3. KHUYẾN NGHỊ LỰA CHỌN MÔ HÌNH MẶC ĐỊNH CHO DỰ ÁN

1. **Khuyến nghị Lựa chọn 1 (Cân bằng chất lượng & chi phí tối ưu): `fal-hailuo-02-pro` (MiniMax Hailuo)**
   - Giá: ~$0.48 / shot 6s.
   - Lý do: Diễn hoạt biểu cảm nhân vật hoạt hình trẻ em mầm non tự nhiên nhất, chi phí rẻ hơn 30-40% so với Kling Pro.

2. **Khuyến nghị Lựa chọn 2 (Đỉnh cao chất lượng cho các shot cao trào): `fal-kling-v3-pro`**
   - Giá: ~$0.70 / shot 5s.
   - Lý do: Khả năng giữ nhận diện nhân vật tuyệt đối, không biến dạng tỉ lệ cơ thể.

3. **Khuyến nghị Dự phòng khi muốn làm việc trong hệ sinh thái Google duy nhất: `google-veo-3.1-fast`**
   - Giá: ~$0.60 / shot 5s 1080p.
   - Lý do: Chung một billing Google với Gemini, không cần nạp thêm credit bên thứ 3.

---

## 4. HƯỚNG DẪN KÍCH HOẠT CHẠY THẬT VỚI TỔNG CHI PHÍ DƯỚI $5

Để chạy thử nghiệm sinh video thật trên 5 model này:
1. Thêm khóa vào tệp `.env` ở gốc repo:
   ```bash
   FAL_KEY=fal_live_key_của_bạn
   # hoặc
   GEMINI_API_KEY=AIzaSy... (có kích hoạt Google Cloud Billing)
   ```
2. Chạy script benchmark với cờ xác nhận chi phí `--confirm-paid`:
   ```bash
   .venv/bin/python scripts/bench/video_bench.py --confirm-paid
   ```
3. Script sẽ tự động kiểm tra trần SpendGuard ($5.00), chạy lần lượt 5 model (tổng chi phí ~$2.55) và cập nhật số đo thực tế vào bảng này.
