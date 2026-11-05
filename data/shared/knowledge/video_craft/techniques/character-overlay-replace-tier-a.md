---
id: character-overlay-replace-tier-a
title: Transparent Character Overlay-Replace with Breathing Idle Animation (Tier A)
status: in-studio
build: 'yes'
reproducible_with_our_stack: 'yes'
needs:
  - Toolbox tool bg-remove
  - HyperFrames Engine
  - FFmpeg
confidence: high
last_verified: '2026-11-05'
expires_at: never
tags:
  - replace
  - character
  - tier-a
  - overlay-replace
  - bg-remove
---

# Kỹ Thuật Thay Nhân Vật Giữ Nội Dung Tier A (Overlay-Replace)

## 1. Bản Chất Kỹ Thuật & Giới Hạn Minh Bạch

Trong môi trường không có GPU NVIDIA phần cứng (chỉ có CPU đa nhân), việc chạy các mô hình AI Diffusion Reenactment / Face Swap (Tier C) là bất khả thi hoặc mất hàng giờ đồng hồ mỗi frame.

**Giải pháp chuẩn Tier A "Overlay-Replace":**
1. **Tách nền thông minh:** Sử dụng công cụ `bg-remove` (model rembg U-2-Net CPU) để bóc tách nhân vật mục tiêu ra khỏi ảnh gốc với kênh alpha trong suốt đạt chuẩn méo viền < 1px.
2. **Ghép lớp thời gian thực:** Đặt nhân vật làm lớp phủ đồ họa (overlay) đè lên video nền đã loại bỏ chủ thể cũ.
3. **Diễn hoạt thở tự nhiên (Idle Breathing Loop):** Dùng CSS Transforms hoặc GSAP để tạo chu kỳ thở nhẹ nhàng (`scale: 1.0 -> 1.02`, `translateY: 0 -> -6px`), loại bỏ cảm giác ảnh tĩnh dán thô.
4. **Minh bạch giao diện:** Thông báo rõ cho người dùng đây là giải pháp ghép lớp đồ họa chất lượng cao Tier A, không phải AI swap giả mạo.
