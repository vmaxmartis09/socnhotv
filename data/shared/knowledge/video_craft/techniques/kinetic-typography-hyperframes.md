---
id: kinetic-typography-hyperframes
title: Offline Kinetic Typography and Karaoke Captioning via HyperFrames GSAP
status: in-studio
build: 'yes'
reproducible_with_our_stack: 'yes'
needs:
  - HyperFrames Engine
  - Vendor GSAP
  - Toolbox tool stt-align
confidence: high
last_verified: '2026-11-05'
expires_at: never
tags:
  - kinetic-typography
  - typography
  - subtitles
  - karaoke
  - gsap
  - hyperframes
---

# Kỹ Thuật Đồ Họa Chữ Động (Kinetic Typography) Ngoại Tuyến

## 1. Bản Chất Kỹ Thuật

Thay thế Remotion (giấy phép thương mại hạn chế) bằng **HyperFrames v0.9.12 + GSAP ngoại tuyến** để render chữ động mượt mà 60fps/24fps:
1. **Ngoại tuyến 100%:** Nhúng trực tiếp `gsap.min.js` vào assets cục bộ của template, đảm bảo quá trình render trong Headless Chrome không bao giờ bị nghẽn mạng do CDN ngoài.
2. **Kinetic Pop & Split:** Tách từng cụm từ quan trọng, áp dụng easing `back.out(1.7)` và gradient fill (`#fbbf24`, `#ec4899`, `#38bdf8`) để tạo điểm nhấn thị giác giật giật đúng chuẩn TikTok/Reels.
3. **Karaoke Word-Level Timing:** Tích hợp với `stt-align` (Whisper + CTC aligner) để đổi màu chữ đồng bộ chính xác từng mili-giây theo phát âm của giọng đọc voiceover.
