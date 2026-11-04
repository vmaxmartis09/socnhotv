# Split-Canvas Lookbook Layout (Bố Cục Lookbook Chia Đôi 45:55)

Tags: layout | lookbook | fashion | ecommerce | hyperframes | split-screen

## Là gì
Bố cục video dọc 9:16 được chia thành hai cột song song bất đối xứng:
- **Cột Trái (40% – 45% chiều rộng)**: Video người mẫu KOC AI (hoặc nhân vật hoạt hình Bi/Koala) đang tạo dáng, chuyển động tự nhiên với toàn bộ trang phục.
- **Cột Phải (55% – 60% chiều rộng)**: Bảng moodboard/sticker chứa từng món đồ bóc tách riêng lẻ (áo, quần, phụ kiện, giày) kèm tên gọi, giá tiền và nét vẽ tay doodle.

## Vì sao hiệu quả
- **Thỏa mãn đồng thời hai góc nhìn**: Khách hàng thời trang muốn thấy (1) tổng thể bộ đồ khi mặc lên người trông có tôn dáng, hợp màu không, VÀ (2) cận cảnh từng chi tiết của từng món đồ để quyết định mua lẻ hoặc mua cả set.
- **Phong cách Pinterest / Instagram Aesthetic**: Bố cục tạo cảm giác sang trọng, nhẹ nhàng, giống như một trang tạp chí thời trang sống động (living magazine), loại bỏ hoàn toàn cảm giác video bán hàng thô kệch.

## Ví dụ trong video
- Video `seq_005` (`1780575939827550` - Xuân Linh) xuyên suốt toàn bộ thời lượng 58.5 giây:
  - Cột trái: Người mẫu tạo dáng với set đồ denim, set đầm trắng, set váy hoa.
  - Cột phải: Các sticker áo khoác lửng, túi xách, giày búp bê nảy ra theo lời thoại.

## Cách làm lại trong dự án này (HyperFrames HTML5/GSAP)
- **Cấu trúc HTML HyperFrames**:
  ```html
  <div class="lookbook-split-container" style="display: flex; width: 1080px; height: 1920px; background: #F5EFEB;">
    <!-- Cột trái: Video Model -->
    <div class="col-model" style="width: 45%; height: 100%; position: relative; overflow: hidden;">
      <video class="clip model-video" src="koc_pose.mp4" loop muted playsinline style="width: 100%; height: 100%; object-fit: cover;"></video>
    </div>
    
    <!-- Cột phải: Bảng Sticker Moodboard -->
    <div class="col-stickers" style="width: 55%; height: 100%; padding: 40px 24px; display: flex; flex-direction: column; justify-content: center; gap: 32px;">
      <div class="sticker-item" data-item="top">
        <img src="item_top_cutout.png" style="max-height: 220px; filter: drop-shadow(0 8px 16px rgba(0,0,0,0.08));" />
        <span class="sticker-label">Áo khoác lửng</span>
      </div>
      <div class="sticker-item" data-item="bottom">
        <img src="item_skirt_cutout.png" style="max-height: 260px;" />
        <span class="sticker-label">Váy denim dáng A</span>
      </div>
    </div>
  </div>
  ```
- **Animation GSAP khi giọng đọc nhắc đến món đồ**:
  ```javascript
  // Khi giọng đọc nói tới 'áo khoác lửng' ở t=2.4s
  gsap.fromTo(".sticker-item[data-item='top']", 
    { scale: 0.8, opacity: 0, y: 20 },
    { scale: 1.0, opacity: 1, y: 0, duration: 0.6, ease: "back.out(1.7)" }
  );
  ```

## Bảng màu khuyên dùng (Korean Aesthetic)
- Nền chính: `#F5EFEB` (Màu kem ấm)
- Màu chữ / Nét vẽ: `#8C7A6B` (Nâu đất nhạt) hoặc `#2F3542` (Xám than chì)
- Màu nhấn (Accent / Badge): `#E8B4B8` (Hồng phấn) hoặc `#D9C3B0` (Be sữa)

## Mức độ tin cậy
Tuyệt đối · Cập nhật: 2026-11-04
