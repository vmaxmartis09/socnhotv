---
id: handdrawn-whiteboard-rendering
title: Progressive Handdraw Whiteboard Rendering via Pixel-Difference Path Tracking
status: in-studio
build: 'yes'
reproducible_with_our_stack: 'yes'
needs:
  - Toolbox tool handdraw
  - FFmpeg
  - Python PIL/Numpy
confidence: high
last_verified: '2026-11-05'
expires_at: never
tags:
  - whiteboard
  - handdraw
  - animation
  - cpu-render
  - education
---

# Kỹ Thuật Diễn Hoạt Vẽ Tay Bảng Trắng (Handdraw Whiteboard)

## 1. Bản Chất Kỹ Thuật

Kỹ thuật tạo cảm giác một nghệ sĩ đang vẽ trực tiếp lên bảng trắng bằng bút lông hoặc bút chì:
1. **Lớp ảnh gốc (Target Artwork):** Ảnh đồ họa hoặc chữ nét đen/màu trên nền trắng tách biệt.
2. **Quét vi sai điểm ảnh (Pixel-Difference Progressive Mask):** Thuật toán chia ảnh thành các dải tiến trình từ trái sang phải, từ trên xuống dưới, tính toán tọa độ đầu ngòi bút `(hand_x, hand_y)` cho từng khung hình.
3. **Lớp tay cầm bút (Hand Overlay):** Tấm ảnh tay cầm bút marker tách nền trong suốt PNG được di chuyển bám sát ngòi bút với độ rung nhẹ tự nhiên (subtle hand jitter) tạo cảm giác chân thực 100%.
4. **Ghép nối FFmpeg thời gian thực:** Render trực tiếp từng frame qua `ffmpeg-bin` trên CPU không cần GPU rời.

## 2. Nguồn Gốc & Giấy Phép

- Kế thừa và học tập giải pháp từ `masihsultani/whiteboard-animator` (MIT) và `subroy13/handanim` (MIT).
- Được đóng gói độc lập trong Toolbox tool `tool/toolbox/tools/handdraw/` và template `handdraw-whiteboard-v1`.
