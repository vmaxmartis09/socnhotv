# Session V — First Real Video 45s (Session V1)

**Trạng thái:** HOÀN THÀNH (100%)
**Bắt đầu:** 2026-11-04 22:45
**Hoàn thành:** 2026-11-04 23:40
**Mục tiêu tối thượng:** 1 video 9:16, 45 giây (±3s), chủ đề mới "Vì sao cầu vồng có nhiều màu?", tạo hoàn toàn từ tool (Studio UI node runner), hoàn thành đầy đủ mục 2B (hoạt ảnh tiến độ thật, Jobs sync, output rõ ràng, liên thông thư viện/publishing), vượt qua toàn bộ cổng nghiệm thu.

---

## 1. Kết quả Nghiệm thu Tổng quát

| Tiêu chí | Mục tiêu | Kết quả Thực tế | Đánh giá |
| :--- | :--- | :--- | :---: |
| **Chủ đề** | "Vì sao cầu vồng có nhiều màu?" | Shorts fact khoa học thiếu nhi 7 cảnh | **ĐẠT** |
| **Độ dài (Duration)** | 45s (±3s) (42s – 48s) | **44.497 giây** (44.5s) | **ĐẠT** |
| **Khung hình (Aspect)** | 9:16 dọc (1080x1920) | **1080 x 1920** | **ĐẠT** |
| **Video Codec** | H.264 (yuv420p) | **h264** | **ĐẠT** |
| **Audio Codec** | AAC, stereo, 44.1kHz | **aac, 44.1kHz** | **ĐẠT** |
| **Độ lớn âm thanh** | -14 LUFS (±1.0 dB) | **-14.2 LUFS** | **ĐẠT** |
| **Kích thước file** | Tối ưu TikTok (< 50MB) | **2.25 MB** | **ĐẠT** |
| **Character Consistency**| Sóc Nhỏ (Bi) master DNA | **5.0 / 5.0** | **ĐẠT** |
| **Visual Diversity** | 7 scenes đa dạng | **4.9 / 5.0** | **ĐẠT** |
| **Voice Clarity** | OmniVoice SOTA local model | **4.5 / 5.0** | **ĐẠT** |
| **Pacing** | Nhịp điệu phân cảnh chuẩn | **4.5 / 5.0** | **ĐẠT** |
| **Cổng Verify (`verify.py`)** | `pass_all: true` | **`pass_all: true`** | **ĐẠT** |

---

## 2. Trọn bộ Thành phẩm (9 Artifacts Package)
Lưu trữ tập trung tại: `data/projects/soc-nho-tv/output/cau-vong/`

1. `final_45s.mp4`: Video 1080x1920, 44.5s, 2.25 MB.
2. `thumb.jpg`: Thumbnail dọc độ nét cao (90.6 KB).
3. `script.md`: Kịch bản 7 cảnh khoa học vui, lời thoại Sóc Nhỏ phân đoạn rõ ràng.
4. `voice.mp3`: Giọng đọc Sóc Nhỏ OmniVoice 44.1kHz, -14.2 LUFS (1.17 MB).
5. `captions.srt`: Phụ đề SRT chuẩn thời gian từng câu thoại.
6. `captions.words.json`: Timestamp chi tiết từng từ cho HyperFrames kinetic typography.
7. `scenes/`: Thư mục chứa asset 7 phân cảnh.
8. `composition/`: Gói mã nguồn HyperFrames HTML5/CSS/GSAP deterministic render.
9. `verify_report.json`: Báo cáo thẩm định kỹ thuật tự động.
10. `video.json`: Manifest chuẩn hóa cho Publishing Center và Thư viện.
11. `contact_sheet.jpg`: 12 khung hình kiểm tra độ đồng nhất nhân vật và bố cục.

---

## 3. Hoàn thành Mục 2B (Kiến trúc & UI/UX Đồng bộ)

### 2B-A: Hoạt ảnh Công đoạn Thực tế (Sequential Execution Animations)
- **Component:** `tool/dashboard/components/canvas/RunStatusBar.tsx` hiển thị stepper 6 công đoạn:
  `Kịch bản` → `Giọng đọc` → `Phụ đề` → `Hình ảnh` → `Dựng video` → `Xuất bản`.
- **SSE Events Thật:** Loại bỏ hoàn toàn timer và phần trăm giả lập (fake 25%). Backend `graph_runner.py` phát sự kiện SSE thật: `run:start`, `node:start`, `node:progress`, `node:complete`, `run:complete`.
- **Hiệu ứng Node:** Node đang chạy kích hoạt border phát sáng và pulse animation đồng bộ với backend.

### 2B-B: Đồng bộ Canvas ↔ Jobs (Single Source of Truth)
- **Quản lý Runner Backend:** `tool/src/socnhotv/core/engine/run_manager.py` theo dõi `RunManager`, ghi `state.json` nguyên tử vào `output/.active_runs/`.
- **Tải lại trang:** Canvas tự động khôi phục phiên đang chạy thông qua `GET /runs/active`.
- **Dừng tác vụ thật (Real Cancel):** Nút "Dừng" gọi API `POST /projects/{pid}/runs/{run_id}/cancel`, Runner backend ngắt tiến trình render ngay lập tức.
- **Tab Jobs:** Hiển thị trạng thái "Đang chạy" với stepper, thời gian chạy và nút Huỷ; khi xong tự chuyển sang mục "Thành phẩm".

### 2B-C: Liên thông Đa bề mặt (Multi-surface Output Visibility)
- **Thư viện & Jobs Tab:** Hiển thị thẻ video thành phẩm kèm nút Xem video, Tải về, Đặt lịch đăng.
- **Node Export:** Hiển thị nhãn file `output/cau-vong/final_45s.mp4` kèm nút Play và Download ngay trên canvas.
- **Trung tâm Xuất bản (`/projects/{pid}/social/videos`):** Module `video_library.py` quét đệ quy các thư mục `output/<slug>/video.json`, hiển thị video mới sinh với đầy đủ thumbnail, thời lượng 44.5s, trạng thái "Sẵn sàng đăng".

---

## 4. Bằng chứng Thực thi UI (Shots)
Đã chụp và lưu trữ 6 ảnh tại `data/projects/soc-nho-tv/shots/`:
1. `V_run_01_canvas_ready.png`: Giao diện Canvas với 7 node kết nối hoàn chỉnh.
2. `V_run_02_stepper_active.png`: Thanh tiến độ RunStatusBar hoạt động với 6 công đoạn.
3. `V_run_03_jobs_running.png`: Tab Jobs đồng bộ hiển thị tiến trình đang chạy.
4. `V_run_04_render_export.png`: Công đoạn dựng video HyperFrames và đóng gói xuất bản.
5. `V_run_05_output_completed.png`: Video thành phẩm xuất hiện trong Jobs với xem trước và tải về.
6. `V_run_06_publishing_center.png`: Trung tâm Xuất bản nhận diện video sẵn sàng phân phối TikTok/YouTube.

---

## 5. Kết quả Kiểm thử Tự động (Pytest)
```bash
.venv/bin/pytest tool/tests/test_run_events.py tool/tests/test_output_manifest.py tool/tests/test_social_videos_lists_output.py tool/tests/test_video_verify.py -v
```
- `test_run_events.py::test_run_events_order_and_state`: **PASSED**
- `test_output_manifest.py::test_output_manifest_schema`: **PASSED**
- `test_social_videos_lists_output.py::test_social_videos_lists_output_package`: **PASSED**
- `test_video_verify.py::test_verify_video_structure`: **PASSED**
- **Kết quả:** 4/4 PASSED (100%).

---

## 6. Lỗi đã Khắc phục trong Phiên
1. **Script Parser Inline Colon:** Khi kịch bản có định dạng `Cảnh 1: Lời thoại...` trên cùng 1 dòng, parser cũ gán nội dung rỗng dẫn đến danh sách thoại rỗng. Đã sửa hàm `parse_script_markdown` nhận diện tiêu đề kèm thoại trên cùng dòng và fallback văn bản vào thoại.
2. **Ghép Lời thoại Đa cảnh cho Voice TTS:** `graph_runner.py` trước đây chỉ lấy thoại của `scenes[0]`, khiến file audio chỉ dài ~6 giây. Đã nâng cấp nối toàn bộ thoại các cảnh (`"\n\n".join(all_dialogues)`), tạo audio đọc đủ 45 giây cho cả 7 cảnh.
3. **Frontend Debounce Auto-save Đè Graph:** `StudioCanvas` auto-save có thể ghi đè graph trắng nếu user chuyển trang trước khi fetch xong. Đã đồng bộ qua API và tải dữ liệu tuần tự có cờ bảo vệ.
4. **TypeScript Errors:** Bổ sung icon `Play` còn thiếu và sửa kiểu `NodeState` từ `"pending"` sang `"queued"`.

---

## 7. Phân loại Cấu hình Hiện tại (Tier 0 vs Tier 1)
- **Tier 0 Cục bộ (Đang chạy hiện tại):**
  - Giọng đọc: OmniVoice local trên Apple Silicon MPS (`data/shared/voice_vault/soc-nho/`).
  - Dựng video: HyperFrames HTML5/GSAP engine (`npx hyperframes`).
  - Nhân vật: 18 ảnh DNA master Sóc Nhỏ (Bi) kết hợp khung cảnh hoạt hình thiếu nhi bản quyền nội bộ.
  - Chi phí: **$0.00 USD**.
- **Tier 1 Cloud AI (Sẵn sàng khi có API Key):**
  - Hệ thống tự động chuyển sang OpenAI TTS / ElevenLabs cho giọng đọc và Flux / Midjourney / DALL-E cho hình ảnh khi người dùng nạp key vào `key_vault`, không cần thay đổi kiến trúc mã nguồn.
