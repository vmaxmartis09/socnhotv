# Kỹ Thuật: Local Pipeline & Workflow Management UX (Học từ ComfyUI Portable)

- **Mã kỹ thuật**: `local-comfyui-pipeline`
- **Nguồn cảm hứng**: Phân tích từ video `seq_009_2140905429860884` (ComfyUI Desktop Portable)
- **Mức độ ứng dụng**: Cao trong kiến trúc Dashboard và Engine Render của dự án `socnhotv`.

---

## 1. Vấn Đề Thực Tế
- Khi triển khai các luồng xử lý AI đa bước (TTS audio, sinh ảnh KOC, tách nền, video inpainting, render video HyperFrames), các file cấu hình và kịch bản dễ bị phân tán, khiến người dùng hoặc operator bị bối rối và gặp lỗi phụ thuộc (dependency hell).
- Người dùng thường bị hấp dẫn bởi các gói "portable cài sẵn 500 template" trên mạng nhưng thực tế các gói này cồng kềnh (hàng chục GB), khó nâng cấp và tiềm ẩn mã độc.

---

## 2. Giải Pháp Chuẩn Hóa Cho Dự Án `socnhotv`

### 2.1. Cây Quản Lý Mẫu Dựng (Template Catalog Architecture)
Thay vì các file kịch bản rời rạc, tổ chức toàn bộ mẫu video HyperFrames theo phân cấp logic trực quan:
```
templates/
├── fashion_koc/
│   ├── split_canvas_lookbook_v1.html
│   ├── rapid_montage_proof_v1.html
│   └── walking_outfit_transition_v1.html
├── product_showcase/
│   ├── 360_rotation_spec_v1.html
│   └── camera_motion_cinematic_v1.html
└── education_story/
    └── comic_panel_talking_head_v1.html
```

### 2.2. Giám Sát Tài Nguyên Hệ Thống (Hardware Telemetry Gauge)
Tích hợp widget đo lường phần cứng nhẹ nhàng trên Dashboard (Web hoặc CLI bar):
- **CPU / RAM Usage**: Đo mức sử dụng khi tổng hợp TTS và render animation.
- **GPU VRAM Tracker**: Cảnh báo khi nạp model Whisper / Stable Diffusion / Rembg vượt ngưỡng an toàn của máy.

### 2.3. Quy Chuẩn Độc Lập Môi Trường (Zero Environment Contamination)
Tuân thủ nghiêm ngặt nguyên tắc của dự án:
- Toàn bộ dependencies Python chạy qua `uv` hoặc isolated virtual environment.
- Không tải hay chạy các file `.exe` / `.bat` trôi nổi không rõ nguồn gốc từ các bài đăng trên mạng xã hội.
