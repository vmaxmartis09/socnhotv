# SỔ THEO DÕI REPOSITORY VIDEO & TEMPLATE (REPO WATCH)

- **Ngày kiểm toán gần nhất:** 2026-11-05
- **Công cụ kiểm:** GitHub REST API v3 (xác thực trực tiếp sao, giấy phép SPDX, ngày commit mới nhất)
- **Mục đích:** Theo dõi công nghệ tạo video, animation, kinetic typography, và pipeline tự động hóa; sàng lọc giấy phép nghiêm ngặt (MIT, Apache-2.0, BSD; cảnh báo AGPL-3.0 và NOASSERTION).

---

## 1. Bảng Tổng Hợp Repositories Đã Kiểm Định

| # | Repository | Sao (Stars) | Giấy phép | Push mới nhất | Tình trạng áp dụng trong SocNhoTV | Kết luận & Giới hạn |
|---|---|---|---|---|---|---|
| 1 | `heygen-com/hyperframes` | **79,229★** | **Apache-2.0** | 2026-11-05 | **Đang dùng làm engine chính** | Render HTML/CSS/GSAP ra video tất định qua headless Chrome. Được phép thương mại. |
| 2 | `remotion-dev/remotion` | **70,899★** | **NOASSERTION** | 2026-11-05 | **Chỉ học phong cách, CẤM làm engine** | Giấy phép tuỳ chỉnh (giới hạn doanh nghiệp > 3 người). Dự án thay thế hoàn toàn bằng HyperFrames + GSAP. |
| 3 | `masihsultani/whiteboard-animator` | **261★** | **MIT** | 2026-09-08 | **Đã tích hợp vào Toolbox `handdraw`** | Thuật toán quét pixel vẽ tay whiteboard bằng Python + OpenCV + FFmpeg trên CPU. An toàn thương mại. |
| 4 | `subroy13/handanim` | **50★** | **MIT** | 2026-11-05 | **Đã tích hợp vào Toolbox `handdraw`** | Thư viện tạo hoạt ảnh tay cầm bút marker / phấn vẽ hình phác thảo. An toàn thương mại. |
| 5 | `harry0703/MoneyPrinterTurbo` | **139,520★** | **MIT** | 2026-11-01 | **Học ý tưởng pipeline** | Luồng sinh video ngắn tự động (hook 3s, phụ đề từ). Tự viết composition bằng HyperFrames, không dùng mã ngoài. |
| 6 | `FujiwaraChoki/MoneyPrinterV2` | **32,303★** | **AGPL-3.0** | 2026-09-15 | **CẤM CHÉP MÃ (Chỉ đọc ý tưởng)** | Giấy phép AGPL-3.0 lây nhiễm mã nguồn. Tuyệt đối không import hoặc sao chép mã nguồn vào dự án. |
| 7 | `3b1b/manim` | **96,153★** | **MIT** | 2026-09-09 | **Đang theo dõi (Template U-H)** | Engine diễn hoạt toán học kinh điển của 3Blue1Brown. Yêu cầu Python + Cairo/FFmpeg. An toàn MIT. |
| 8 | `ManimCommunity/manim` | **42,262★** | **MIT** | 2026-11-05 | **Đang theo dõi (Template U-H)** | Bản cộng đồng tối ưu của Manim với tài liệu và CLI phong phú. An toàn MIT. |
| 9 | `openai/whisper` | **111,998★** | **MIT** | 2026-08-31 | **Đang dùng (stt-align, whisper-small)** | Mô hình nhận dạng giọng nói chuẩn công nghiệp. An toàn MIT. |
| 10 | `m-bain/whisperX` | **25,097★** | **BSD-2-Clause** | 2026-10-22 | **Đang dùng (stt-align)** | Căn chỉnh phụ đề từng từ bằng wav2vec2 forced-alignment. WER cực thấp, an toàn BSD. |
| 11 | `danielgatis/rembg` | **25,344★** | **MIT** | 2026-11-02 | **Đang dùng (bg-remove)** | Tách nền sản phẩm/nhân vật qua model U-2-Net chạy mượt trên CPU. An toàn MIT. |
| 12 | `Breakthrough/PySceneDetect` | **5,383★** | **BSD-3-Clause** | 2026-11-02 | **Đang theo dõi (T-11 / U-J)** | Nhận diện cắt cảnh video tự động trên CPU. An toàn BSD. |
| 13 | `jianchang512/pyvideotrans` | **19,644★** | **GPL-3.0** | 2026-11-03 | **Chỉ tham khảo quy trình dịch/lồng tiếng** | Giấy phép GPL-3.0. Không nhúng mã vào core SocNhoTV. |

---

## 2. Quy Tắc Ứng Xử Với Mã Nguồn Mở (Luật Không Thương Lượng)

1. **Kiểm tra trước khi clone:** Bắt buộc truy vấn GitHub API kiểm tra giấy phép SPDX trước khi tải hay nhúng bất kỳ thư viện nào.
2. **Loại trừ rủi ro bản quyền:**
   - Cấm sao chép bất kỳ đoạn mã nào từ các kho lưu trữ AGPL-3.0 (như MoneyPrinterV2) hoặc GPL-3.0 vào lõi độc quyền của ứng dụng.
   - Tránh xa các repo/model có điều khoản "Non-Commercial" hoặc không có giấy phép (Wav2Lip, SadTalker weights không rõ nguồn gốc).
   - Không dùng Remotion làm runtime rendering vì điều khoản thương mại độc quyền; dùng HyperFrames (Apache-2.0) làm giải pháp thay thế hoàn hảo.
