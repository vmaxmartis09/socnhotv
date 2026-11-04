# Session V — First Real Video 45s (Session V1)

**Trạng thái:** ĐANG THỰC HIỆN
**Bắt đầu:** 2026-11-04 22:45
**Mục tiêu:** 1 video 9:16, 45 giây (±3s), chủ đề mới "Vì sao cầu vồng có nhiều màu?", dựng từ Studio UI (bấm Chạy), hoàn thành đầy đủ mục 2B (hoạt ảnh tiến độ thật, Jobs sync, output rõ ràng, liên thông thư viện/publishing), vượt qua toàn bộ cổng nghiệm thu.

---

## 1. Preflight Check (Kiểm tra điều kiện ban đầu)

| Mục kiểm tra | Trạng thái | Chi tiết kiểm chứng |
| :--- | :---: | :--- |
| Core API (port 8000) | CÓ | Đang chạy `--reload`, phản hồi `/providers`, `/video/templates` |
| Studio Dashboard (port 3000) | CÓ | Đang chạy Next.js dev server |
| HyperFrames CLI | CÓ | `npx hyperframes` v0.9.12, test test_core_step4_hyperframes.py pass 5/5 |
| OmniVoice local (`soc-nho`) | CÓ | Sinh audio thật `output/preflight_voice.mp3` (44.1kHz MP3, 2.51s, -14 LUFS) |
| Ảnh DNA Sóc Nhỏ (Bi) | CÓ | 18 ảnh master DNA (`soc_nho_01.png` - `soc_nho_18.png`), tất cả đều là RGBA (nền trong suốt), kích thước 1024x572 |
| Ảnh Bác sĩ Koala | CÓ | Master scene `canh_04.jpg`, `canh_05.jpg` (RGB) |
| Nhà cung cấp AI (Providers) | CỤC BỘ (Tier 0) | Chưa có API key trong key_vault, chạy Tier 0 thuần local (HyperFrames + OmniVoice + DNA) |
| Templates | CÓ | Có sẵn `shorts-fact-v1`, `story-cartoon-v1`, `yt-animation-episode-v1`,... |

---

## 2. Nhật ký công việc & Tiến độ
- [x] **Bước 1: Preflight**: Hoàn thành kiểm tra môi trường, audio engine, HyperFrames CLI, DNA assets.
- [ ] **Bước 2: Chuẩn bị kịch bản 45s chuẩn khoa học thiếu nhi ("Vì sao cầu vồng có nhiều màu?")**
- [ ] **Bước 3: Hoàn thiện mục 2B TRƯỚC (SSE events, Jobs tab sync, Cancel runner, Output manifest & Thư viện, Publishing Center)**
- [ ] **Bước 4: Dựng trong Studio, bấm Chạy từ UI và ghi lại bằng chứng shots/V_run_*.png**
- [ ] **Bước 5: Cổng nghiệm thu (verify.py, 12 khung contact sheet, test tự động)**
- [ ] **Bước 6: Lưu Video mẫu preset & Tổng kết**
