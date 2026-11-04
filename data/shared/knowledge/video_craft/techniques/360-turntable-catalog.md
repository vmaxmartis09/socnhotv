# Kỹ Thuật: 360 Turntable Fashion Catalog & Rigid UI Overlay

- **Mã kỹ thuật**: `360-turntable-catalog`
- **Nguồn cảm hứng**: Phân tích từ video `seq_015_1612875093634659` (Xuân Linh - Quy trình 15)
- **Tags**: fashion-ai | catalog | 360-turntable | rigid-ui | editorial | hyperframes

---

## 1. Bản Chất Kỹ Thuật
1. **Chuyển Động Nhân Vật (Character Turntable Move)**:
   - `0s - 2s`: Pose tĩnh trước máy quay.
   - `2s - 4.5s`: Xoay 360 độ trên bục xoay studio quanh trục Y.
   - `Điểm morph`: Khi lưng quay về camera (ở góc 180°), thực hiện swap trang phục.
   - `4.5s - 6.5s`: Quay lại mặt trước với trang phục mới, tiếp tục pose tĩnh.
2. **Khóa Cứng Giao Diện Sản Phẩm (Rigid UI Grid)**:
   - Cột bên trái (chiếm 30-35% chiều ngang) chứa các thẻ checklist sản phẩm (SKU, giá, chất liệu) được cố định 100% bằng CSS Flexbox/Grid.
   - Khi nhân vật xoay xong, các ảnh item nhỏ bên trong thẻ checklist lật 3D (`transform: rotateY(360deg)`) bằng GSAP.

---

## 2. Mã Mẫu HyperFrames HTML/CSS/GSAP
```html
<div class="catalog-composition" style="width: 1080px; height: 1920px; display: flex; position: relative;">
  <!-- Cột Trái: UI Checklist Cố Định -->
  <aside style="width: 380px; padding: 40px; z-index: 10; display: flex; flex-direction: column; gap: 20px;">
    <div class="brand-header">
      <h2>LOOKBOOK 2026</h2>
      <span id="look-counter">01 / 03</span>
    </div>
    
    <div class="product-item" id="item-top">
      <div class="thumb-box"><img id="img-top" src="assets/top_01.png" style="width: 80px; height: 80px; object-fit: contain;"></div>
      <div class="meta"><h4>Áo Lụa Satin</h4><p>350.000đ</p></div>
    </div>
    
    <div class="product-item" id="item-bottom">
      <div class="thumb-box"><img id="img-bottom" src="assets/bottom_01.png" style="width: 80px; height: 80px; object-fit: contain;"></div>
      <div class="meta"><h4>Chân Váy Chữ A</h4><p>420.000đ</p></div>
    </div>
  </aside>

  <!-- Cột Phải: Video Mẫu Xoay 360 -->
  <div class="turntable-stage" style="flex: 1; height: 100%;">
    <video id="spin-video" class="clip" src="assets/spin_master.mp4" style="width: 100%; height: 100%; object-fit: cover;"></video>
  </div>
</div>

<script>
  const tl = gsap.timeline({ paused: true });
  // Tại thời điểm xoay xong (t = 4.5s), lật thẻ sản phẩm
  tl.to(".thumb-box img", { rotateY: 360, duration: 0.6, ease: "back.out(1.7)" }, 4.5);
</script>
```
