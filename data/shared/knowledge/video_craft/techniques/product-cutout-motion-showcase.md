---
id: product-cutout-motion-showcase
title: Automated E-Commerce Product Cutout Motion Showcase with Dynamic Price Badges
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
  - product-showcase
  - e-commerce
  - affiliate
  - bg-remove
  - sales-hook
---

# Kỹ Thuật Trình Diễn Sản Phẩm E-Commerce & Affiliate Nổi Bật

## 1. Bản Chất Kỹ Thuật

Biến ảnh chụp sản phẩm thô (trên nền lộn xộn hoặc nền trắng) thành video ngắn bán hàng TikTok bắt mắt trong 3 giây đầu:
1. **Bóc tách vật thể tự động:** `bg-remove` tách sản phẩm sạch viền và lưu thành PNG trong suốt.
2. **Hiệu ứng nổi 3D & Ánh sáng xuyên:** Đặt sản phẩm lên nền gradient chuyển động với bóng đổ `filter: drop-shadow(0 20px 30px rgba(0,0,0,0.7))` và chuyển động nổi bềnh bồng (`yoyo: true, ease: "sine.inOut"`).
3. **Badge ưu đãi kích thích mua sắm:** Hộp giá ưu đãi nổi bật với giá gốc gạch ngang, phần trăm giảm màu đỏ neon, và nút bấm giỏ hàng TikTok nằm chuẩn xác trong vùng an toàn (Safe Zone 9:16).
