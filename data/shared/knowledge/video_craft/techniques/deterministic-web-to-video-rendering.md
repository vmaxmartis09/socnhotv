---
id: deterministic-web-to-video-rendering
title: Deterministic Web-to-Video Rendering Architecture
status: in-studio
build: 'yes'
reproducible_with_our_stack: 'yes'
needs:
- HyperFrames Engine
- Chrome Headless
- FFmpeg
implemented_in:
- tool/src/socnhotv/video/hyperframes_engine.py
evidence_videos:
- seq_N03
confidence: high
last_verified: '2026-11-04'
expires_at: never
tags:
- hyperframes
- deterministic-render
- ffmpeg
- virtual-clock
- gsap
---

# Technique: Deterministic Web-to-Video Rendering Pipeline

## Tóm Tắt Kỹ Thuật
Quy trình biến mã nguồn Web (HTML5, CSS, SVG, GSAP/Anime.js) thành video MP4 chất lượng cao thông qua cơ chế can thiệp đồng hồ ảo (Virtual Clock) trên trình duyệt không đầu (Headless Browser) kết hợp đường ống dữ liệu FFmpeg image2pipe, cho phép kết xuất song song theo phân đoạn (parallel chunking) mà không bao giờ bị rớt frame hay nhoè hình.

---

## 1. Vấn Đề Giải Quyết
- **Bất định của Diffusion Models**: Các mô hình sinh video AI (Runway, Kling, Sora) thường biến dạng chữ, bố cục trôi dạt và không thể chỉnh sửa chi tiết.
- **Rớt frame khi quay màn hình**: Quay màn hình (screen capture) phụ thuộc vào hiệu năng máy tại thời điểm quay, dễ giật lag, drop frame.
- **Thời gian render lâu**: Render tuần tự từng frame trên 1 luồng rất chậm cho video dài.

---

## 2. Nguyên Lý Vận Hành Cốt Lõi

```mermaid
flowchart TD
    A["HTML5/CSS/GSAP Composition"] --> B["Virtual Clock Stepper (1/fps increments)"]
    B --> C1["Worker 1 (Frames 0 - 300)"]
    B --> C2["Worker 2 (Frames 301 - 600)"]
    B --> C3["Worker 3 (Frames 601 - 900)"]
    C1 --> D1["Frame Buffers -> FFmpeg stdin pipe"]
    C2 --> D2["Frame Buffers -> FFmpeg stdin pipe"]
    C3 --> D3["Frame Buffers -> FFmpeg stdin pipe"]
    D1 --> E1["Chunk_1.mp4"]
    D2 --> E2["Chunk_2.mp4"]
    D3 --> E3["Chunk_3.mp4"]
    E1 & E2 & E3 --> F["FFmpeg Concat Demuxer"]
    F --> G["Final Master 4K/60fps MP4"]
```

### Các bước thực thi:
1. **Khóa đồng hồ thời gian (Deterministic Timeline)**:
   - Thay vì dùng `requestAnimationFrame` hay `setInterval` chạy theo thời gian thực (wall-clock time), trình duyệt headless điều khiển timeline qua hàm `timeline.seek(t)` hoặc mock `window.performance.now()`.
2. **Xuất frame dạng Stream Pipe**:
   - Chụp frame dưới dạng raw buffer hoặc PNG và pipe trực tiếp vào tiến trình FFmpeg qua CLI:
     ```bash
     ffmpeg -y -f image2pipe -vcodec png -r 30 -i - -c:v libx264 -pix_fmt yuv420p output.mp4
     ```
3. **Phân đoạn song song (Chunking)**:
   - Chia tổng thời lượng video thành $K$ phân đoạn tương ứng với số CPU cores.
   - Mỗi worker render độc lập một phân đoạn.
   - Nối nhanh các file bằng `ffmpeg -f concat -safe 0 -c copy`.

---

## 3. Khả Năng Ứng Dụng Trong Sóc Nhỏ TV
- Tích hợp trực tiếp vào module dựng `HyperFramesEngine` (`tool/src/socnhotv/video/hyperframes_engine.py`).
- Đảm bảo các video giải thích kiến thức, hoạt hình 3D kết hợp motion graphics, và video bán hàng KOC đạt độ phân giải chuẩn nét 1080x1920 không tốn chi phí render GPU đám mây.
