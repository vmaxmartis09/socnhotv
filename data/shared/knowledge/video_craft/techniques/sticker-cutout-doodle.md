---
id: sticker-cutout-doodle
title: Sticker Cutout & Motion Doodle (Viền Sticker Trắng Cắt Rời & Nét Vẽ Hoạt Hình)
status: knowledge
build: partial
reproducible_with_our_stack: 'yes'
needs:
- HyperFrames SVG
- CSS drop-shadow
implemented_in: []
evidence_videos:
- seq_006
confidence: high
last_verified: '2026-11-04'
expires_at: never
tags:
- sticker-cutout
- doodle
- motion-graphics
- 2d-overlay
---

# Sticker Cutout & Hand-drawn Doodle (Hiệu Ứng Bóc Tách Sticker & Nét Vẽ Tay)

Tags: graphic-design | animation | sticker | aesthetics | hyperframes | kinetic

## Là gì
Phong cách xử lý đồ họa mô phỏng những cuốn sổ tay dán ảnh (scrapbook) của giới trẻ:
1. **Sticker Cutout**: Tách nền sản phẩm và thêm một viền trắng dày 2px–3px bao quanh mép (`filter: drop-shadow(...)` hoặc stroke SVG), kèm bóng đổ nhẹ bên dưới.
2. **Hand-drawn Doodle**: Sử dụng các nét vẽ tay ngộ nghĩnh (mũi tên uốn lượn, ngôi sao lấp lánh, trái tim nhỏ, đường chỉ gạch nối) để nối từ chữ mô tả vào sản phẩm.

## Vì sao hiệu quả
- **Tạo cảm giác thân thiện, dễ thương (Cuteness & Approachability)**: Rất phù hợp với đối tượng khách hàng nữ, Gen Z, học sinh, sinh viên và dân văn phòng trẻ.
- **Dẫn dắt ánh nhìn tự nhiên (Visual Direction)**: Mũi tên doodle uốn lượn dẫn dắt mắt người xem từ khuôn mặt người mẫu sang chi tiết phụ kiện (túi, giày, khuyên tai) một cách êm ái mà không cần dùng hiệu ứng giật mắt khó chịu.

## Ví dụ trong video
- Video `seq_005` (`1780575939827550` - Xuân Linh) @ `t=5.16s -> 14.96s`:
  - Chiếc túi xách và giày búp bê xuất hiện với viền sticker trắng, một đường cong nét đứt màu nâu vẽ tay từ từ chạy ra từ chữ "Giày búp bê" chỉ thẳng vào mũi giày.

## Cách làm lại trong HyperFrames
- **Hiệu ứng Viền Sticker CSS**:
  ```css
  .sticker-cutout {
    filter: drop-shadow(0 0 1px #fff) 
            drop-shadow(0 0 2px #fff) 
            drop-shadow(0 4px 12px rgba(0,0,0,0.12));
  }
  ```
- **Animation Nét vẽ tay Doodle bằng SVG + GSAP**:
  ```html
  <svg class="doodle-arrow" viewBox="0 0 100 60" style="position: absolute; width: 100px;">
    <path id="arrowPath" d="M10,10 Q50,5 90,45" fill="none" stroke="#8C7A6B" stroke-width="2" stroke-dasharray="6,4" />
  </svg>
  ```
  ```javascript
  // GSAP vẽ đường nét dần dần (DrawSVG effect)
  const path = document.querySelector("#arrowPath");
  const length = path.getTotalLength();
  gsap.fromTo(path, 
    { strokeDashoffset: length, strokeDasharray: length },
    { strokeDashoffset: 0, duration: 0.8, ease: "power2.out" }
  );
  ```

## Mức độ tin cậy
Tuyệt đối · Cập nhật: 2026-11-04
