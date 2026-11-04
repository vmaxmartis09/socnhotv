# Playbook 03: Chiều Sâu 3 Lớp & Bố Cục Không Gian (3-Layer Depth & Spatial Composition)

> Áp dụng cho: Bố cục hình ảnh, sinh prompt AI hình ảnh/video, và composition HyperFrames  
> Mục tiêu cốt lõi: Xóa bỏ cảm giác "phẳng và giả tạo của AI" (Flat AI effect), tạo chiều sâu quang học chuẩn điện ảnh.

---

## 1. Danh Sách Kỹ Thuật Sử Dụng
- [`foreground-occlusion-spatial-depth-layering`](../techniques/foreground-occlusion-spatial-depth-layering.md): Phân tách 3 tầng không gian (Tiền cảnh che khuất - Trung cảnh nét căng - Hậu cảnh mờ khí quyển).
- [`high-status-color-contrast`](../techniques/high-status-color-contrast.md): Độ tương phản màu sắc cao cấp, tỷ lệ tương phản chữ-nền đạt chuẩn WCAG AAA ≥ 7:1.
- [`3-layer-knowledge-retention`](../techniques/3-layer-knowledge-retention.md): Cấu trúc 3 tầng thông điệp thị giác bổ trợ cho chiều sâu hình ảnh.
- [`in-situ-koc-placement`](../techniques/in-situ-koc-placement.md): Hòa trộn nhân vật vào không gian thật qua ánh sáng và bóng đổ tiếp xúc (ambient occlusion).

---

## 2. Quy Trình Từng Bước (Step-by-Step Workflow)

### Bước 1: Cấu Trúc Prompt 3 Tầng Cho AI Generation
Khi tạo prompt cho `image_gen` hoặc `video_gen`, bắt buộc chia thành 3 phần:
1. **Layer 1: Tiền cảnh (Foreground Occlusion / Out-of-focus Bokeh):**
   - Các vật thể lướt sát ống kính che khuất một phần góc khung hình: cành lá mờ nhoè, giọt sương, ngọn cỏ đung đưa, hoặc vai người nhìn qua vai (OTS).
   - Từ khoá bắt buộc: `extreme shallow depth of field, blurred foreground element in close-up, foreground bokeh`.
2. **Layer 2: Trung cảnh (In-focus Midground):**
   - Chủ thể chính (Sóc Nhỏ Bi 100cm, Bác sĩ Koala 150cm, hoặc KOC LyLy).
   - Từ khoá: `sharp focus on subject, crystal clear details, natural rim lighting`.
3. **Layer 3: Hậu cảnh (Atmospheric Background):**
   - Chiều sâu phía xa mờ dần qua lớp sương mù hoặc ánh sáng xiên.
   - Từ khoá: `soft atmospheric haze, creamy background bokeh, cinematic depth`.

### Bước 2: Thiết Kế Parallax 3 Lớp Trong HyperFrames Tier-0
Với video 2D dựng từ ảnh master DNA trong suốt (RGBA):
1. **Lớp Background (Tầng 3):** Ảnh phong cảnh rừng xanh / căn phòng mờ, chuyển động pan cực chậm `speed: 0.2x`.
2. **Lớp Nhân vật (Tầng 2):** Ảnh DNA Sóc Nhỏ / KOC ở trung tâm, chuyển động nhẹ theo nhịp thoại `speed: 1.0x`.
3. **Lớp Foreground (Tầng 1):** Hạt bụi ánh sáng (dust particles) hoặc cành lá bokeh nổi phía trước, chuyển động nhanh hơn `speed: 1.8x`.

### Bước 3: Đảm Bảo Tương Phản Màu Sắc & An Toàn Safe-Zone
- Bảng màu tương phản chuẩn: Chủ thể màu ấm (vàng cam sóc nhỏ / da người) nổi bật trên nền lạnh (xanh lá cây, xanh dương đậm).
- Text phụ đề luôn có viền đổ bóng bán trong suốt `rgba(0,0,0,0.75)` hoặc nền badge sang trọng để luôn đọc rõ ở mọi khung hình.
- Tuân thủ vùng an toàn TikTok 9:16: Cách đỉnh 180px, cách đáy 320px.

---

## 3. Khuôn Mẫu Prompt & Code (Templates)

### Khuôn Prompt 3 Lớp Chuẩn Sóc Nhỏ (DNA Preservation):
```
[Foreground]: Softly blurred sunlit oak leaves and floating golden pollen flakes in the extreme foreground, out-of-focus optical bokeh.
[Midground]: Master character soc_nho (a cute 100cm cartoon squirrel with fluffy striped tail and bright curious eyes) in sharp focus, standing on a mossy branch, speaking excitedly, natural studio rim light.
[Background]: Lush enchanted forest softly fading into creamy morning mist, warm golden sunbeams breaking through tall pine canopies, deep cinematic focal falloff, 8k resolution.
```

### Component HyperFrames Parallax 3 Lớp:
```html
<div class="scene-3layer-depth">
  <div class="layer layer-bg" data-depth="0.2"></div>
  <div class="layer layer-mid" data-depth="1.0">
    <img src="soc_nho_dna.png" class="character-anchor" />
  </div>
  <div class="layer layer-fg" data-depth="1.8">
    <div class="bokeh-particle-field"></div>
  </div>
</div>
```

---

## 4. Sai Lầm Thường Gặp (Pitfalls to Avoid)
1. **Mọi vật thể đều nét đều (Infinite DOF):** Khiến video trông như ảnh cắt dán 2D nghiệp dư hoặc ảnh game cũ.
2. **Tiền cảnh che quá nhiều (>25% diện tích mặt nhân vật):** Làm mất chi tiết biểu cảm quan trọng. Tiền cảnh chỉ nên chiếm 5% - 15% ở mép ngoài khung hình.
3. **Bóng đổ tiếp xúc bị thiếu (No contact shadow):** Nhân vật trông như đang bay lơ lửng trên nền.

---

## 5. Checklist Trước Khi Xuất Bản (Pre-Publish Checklist)
- [ ] Bố cục khung hình phân tách rõ ràng 3 tầng không gian (Tiền cảnh - Trung cảnh - Hậu cảnh).
- [ ] Nhân vật chính nằm trong vùng nét căng và tuân thủ đúng tỷ lệ nhận diện DNA.
- [ ] Tỷ lệ tương phản chữ/nền phụ đề đạt chuẩn đọc rõ (WCAG ≥ 4.5:1, khuyến nghị ≥ 7:1).
- [ ] Không có chi tiết quan trọng nào rơi vào vùng che khuất của nút TikTok (vùng an toàn 9:16).
