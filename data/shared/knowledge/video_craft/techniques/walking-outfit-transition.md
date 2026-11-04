# Kỹ Thuật: Walking Outfit Continuous Transition (Biến Đổi Trang Phục Bước Đi Liền Mạch)

- **Mã kỹ thuật**: `walking-outfit-transition`
- **Nguồn cảm hứng**: Phân tích từ video `seq_012_959353096734421` (Xuân Linh - Quy trình 23)
- **Tags**: fashion-ai | koc | lookbook | walk-cycle | in-stride-morph | hyperframes | gsap

---

## 1. Bản Chất Kỹ Thuật
Kỹ thuật giữ nguyên một chuyển động bước đi liên tục (continuous walk cycle) của nhân vật thời trang, sau đó áp dụng biến đổi trang phục (in-stride outfit morphing) tại các nhịp beat nhạc chính xác, kết hợp lớp phủ nhãn dán SVG và thông số sản phẩm.

---

## 2. Cấu Trúc Khung Thời Gian (Timeline Architecture)
Thời lượng chuẩn: **24s - 28s** (Tương ứng 4 nhịp 6.5s hoặc 8 nhịp 3.2s):

```
0s ────(Outfit 1: Trench Coat)────> 6.5s ────(Outfit 2: Work Dress)────> 13.0s ────(Outfit 3: Casual Jeans)────> 19.5s ────(Summary 3-Look Carousel)────> 26s
       ▲ Pop-up Tag 1                      ▲ Pop-up Tag 2                       ▲ Pop-up Tag 3                        ▲ Brand Lockup & CTA
```

---

## 3. Cách Tái Tạo Bằng HeyGen HyperFrames (Code Blueprint)
Cấu trúc composition HTML5/GSAP:

```html
<div class="composition" style="width: 1080px; height: 1920px; position: relative; overflow: hidden;">
  <!-- Track 1: Nền video đi bộ liên tục -->
  <video id="koc-walk" class="clip" src="assets/neau_walk_master.mp4" style="width: 100%; height: 100%; object-fit: cover;"></video>

  <!-- Track 2: Lớp phủ flash chuyển đổi trang phục tại mốc 6.5s và 13.0s -->
  <div id="flash-overlay" style="position: absolute; inset: 0; background: white; opacity: 0; pointer-events: none;"></div>

  <!-- Track 3: Kinetic Sticker Tag & SKU Callout -->
  <div id="tag-outfit-1" class="tag-card" style="position: absolute; top: 380px; right: 80px; opacity: 0;">
    <span class="badge">OUTFIT 01</span>
    <h3 class="title">Đầm Dạ Hội NuNu</h3>
    <p class="price">489.000đ</p>
  </div>

  <div id="tag-outfit-2" class="tag-card" style="position: absolute; top: 380px; right: 80px; opacity: 0;">
    <span class="badge">OUTFIT 02</span>
    <h3 class="title">Set Blazer Công Sở</h3>
    <p class="price">520.000đ</p>
  </div>
</div>

<script>
  // GSAP seekable timeline
  const tl = gsap.timeline({ paused: true });
  
  // Transition 1 @ 6.5s
  tl.to("#flash-overlay", { opacity: 0.8, duration: 0.15, yoyo: true, repeat: 1 }, 6.45);
  tl.fromTo("#tag-outfit-1", { opacity: 0, x: 50 }, { opacity: 1, x: 0, duration: 0.4 }, 1.0);
  tl.to("#tag-outfit-1", { opacity: 0, x: -50, duration: 0.3 }, 6.2);
  
  // Transition 2 @ 13.0s
  tl.to("#flash-overlay", { opacity: 0.8, duration: 0.15, yoyo: true, repeat: 1 }, 12.95);
  tl.fromTo("#tag-outfit-2", { opacity: 0, x: 50 }, { opacity: 1, x: 0, duration: 0.4 }, 7.0);
  tl.to("#tag-outfit-2", { opacity: 0, x: -50, duration: 0.3 }, 12.8);
</script>
```
