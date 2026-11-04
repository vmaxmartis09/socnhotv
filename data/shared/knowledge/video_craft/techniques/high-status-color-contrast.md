---
id: high-status-color-contrast
title: High-Status Color Contrast (Bảng Màu Tương Phản Chuẩn Sang Trọng)
status: in-studio
build: 'yes'
reproducible_with_our_stack: 'yes'
needs:
- HyperFrames CSS
- Lint
implemented_in:
- tool/src/socnhotv/video/craft/lint.py
- data/shared/knowledge/video_craft/playbooks/depth-and-composition.md
evidence_videos:
- seq_016
confidence: high
last_verified: '2026-11-04'
expires_at: never
tags:
- color-palette
- contrast
- luxury-branding
- wcag
- aesthetic
---

# Kỹ Thuật: High-Status Color Contrast & 5-Beat Comparison Blueprint

- **Mã kỹ thuật**: `high-status-color-contrast`
- **Nguồn cảm hứng**: Phân tích từ video `seq_020_1580543193234985` (Layr Layr - 4.5M Views)
- **Tags**: viral-formula | fashion-koc | color-theory | high-status-words | save-rate | hyperframes

---

## 1. Bản Chất Kỹ Thuật
Kỹ thuật tạo video thời trang có tỷ lệ lưu trữ (Save Rate) và chia sẻ (Share Rate) cao nhất bằng cách so sánh 2 cách phối cùng một màu chủ đạo: Một cách phối cơ bản thông thường (`Okay`, `Clean`, `Cute`) đối chiếu với một cách phối nâng tầm phong cách sang trọng (`Luxurious`, `Expensive`, `Classy`, `Chic`, `Elegant`).

---

## 2. Công Thức Kịch Bản 5 Nhịp (Script Matrix)

| Nhịp (Beat) | Thời Lượng | Màu Chủ Đạo | Cách Phối Cơ Bản (Cấp 1) | Cách Phối Sang Trọng (Cấp 2) | Từ Khóa Địa Vị (Status Keyword) |
|---|---|---|---|---|---|
| **Beat 1** | `0.0s - 5.5s` | Xanh Rêu / Green | Green + Black (Đậm) | **Green + Cream** | **Luxurious (Sang trọng)** |
| **Beat 2** | `5.5s - 11.0s` | Đỏ Rượu / Red | Red + White (Tạm) | **Red + Beige** | **Classy (Đẳng cấp)** |
| **Beat 3** | `11.0s - 16.5s`| Đen / Black | Black + White (Sạch sẽ) | **Black + Brown** | **Expensive (Đắt tiền)** |
| **Beat 4** | `16.5s - 22.0s`| Hồng Pastel / Pink| Pink + White (Dễ thương) | **Pink + Gray** | **Chic (Sành điệu thời thượng)** |
| **Beat 5** | `22.0s - 27.5s`| Xanh Dương / Blue| Blue + White (Tươi sáng) | **Blue + Beige** | **Elegant (Quý phái)** |

---

## 3. Mã Mẫu Bố Cục HyperFrames HTML/CSS/GSAP
```html
<div class="color-contrast-comp" style="width: 1080px; height: 1920px; position: relative; background: #121212;">
  <!-- Header: Title & Beat Indicator -->
  <header style="position: absolute; top: 120px; width: 100%; text-align: center;">
    <h2 style="font-family: 'Playfair Display', serif; color: #FFF; font-size: 42px; letter-spacing: 2px;">COLOUR COMBINATIONS</h2>
    <p id="rule-text" style="color: #D4AF37; font-size: 28px; text-transform: uppercase;">Green with Cream = Luxurious</p>
  </header>

  <!-- Split Screen: Left (Basic) vs Right (Elevated) -->
  <div class="comparison-stage" style="position: absolute; top: 260px; left: 60px; right: 60px; height: 1400px; display: flex; gap: 30px;">
    <!-- Side A: Basic Look -->
    <div class="look-card basic" style="flex: 1; border-radius: 24px; overflow: hidden; position: relative;">
      <img id="img-look-a" src="assets/look_green_black.jpg" style="width: 100%; height: 100%; object-fit: cover;">
      <div class="badge" style="position: absolute; bottom: 30px; left: 30px; background: rgba(0,0,0,0.7); color: #fff; padding: 12px 24px; border-radius: 50px;">
        LOOKS BOLD
      </div>
    </div>

    <!-- Side B: High-Status Look -->
    <div class="look-card elevated" style="flex: 1; border-radius: 24px; overflow: hidden; position: relative; border: 2px solid #D4AF37;">
      <img id="img-look-b" src="assets/look_green_cream.jpg" style="width: 100%; height: 100%; object-fit: cover;">
      <div class="badge gold" style="position: absolute; bottom: 30px; left: 30px; background: #D4AF37; color: #000; font-weight: bold; padding: 12px 24px; border-radius: 50px;">
        LOOKS LUXURIOUS ✨
      </div>
    </div>
  </div>
</div>
```
