# Báo cáo Phân tích Video — Seq 005

- **ID Video**: `1780575939827550`
- **Tiêu đề gốc**: "Quy trình biến một set đồ thành video giới thiệu thời trang phong cách Hàn Quốc - Fashion Lookbook Ai"
- **Tác giả**: Xuân Linh (AI Flow Pro)
- **Quyết định**: `LEARN` (Xuất sắc — Là nguồn cảm hứng và thiết kế mẫu mực cho Template thời trang HyperFrames của Session A).

---

## 1. Tóm tắt phân tích
Video dài 58.47s, trình diễn quy trình số 34 trong ứng dụng AI Flow Pro: biến hình ảnh một bộ quần áo thành video lookbook thời trang chuẩn phong cách Pinterest Hàn Quốc.
- **Bố cục màn hình dọc 9:16 chia đôi (Split Canvas 45:55)**:
  - **Bên trái (45%)**: Người mẫu AI (Virtual KOC) mặc trọn bộ outfit và chuyển động tạo dáng nhẹ nhàng (subtle posing loop).
  - **Bên phải (55%)**: Bảng moodboard dán sổ (Sticker Cutout Board) trên nền kem ấm (#F5EFEB). Từng món đồ (áo, váy, túi, giày) được bóc tách viền trắng 2px, kèm nét vẽ tay doodle và tên sản phẩm/giá tiền.
- **Nhịp cấu trúc 3-Set (3-Outfit Carousel)**:
  - Chia làm 3 set trang phục rõ rệt: Style Nữ tính (Denim) → Style Tiểu thư (Đầm trắng) → Style Nàng thơ (Váy hoa). Mỗi set kéo dài đúng ~19 giây, có lời thoại giới thiệu đồng bộ và kết thúc bằng câu kêu gọi bấm giỏ hàng.
- **Âm thanh & Lời thoại**: Giọng nữ Gen Z trẻ trung, nhịp nói 3.35 từ/giây cuốn hút, âm lượng -14.28 LUFS đạt chuẩn TikTok hoàn hảo.

---

## 2. Công thức Blueprint (Cấu trúc Lookbook 3-Set)
Thời lượng: **58.5s** | Bố cục: **Split Canvas 45/55** | Chu kỳ mỗi Set: **~19.5s**

```
SET 1: OUTFIT NỮ TÍNH (0.0s – 18.9s)
  ├─ [0.0s - 8.8s] Hook phong cách + Mẫu pose dáng + Sticker áo & váy nảy ra
  ├─ [8.8s - 15.0s] Chi tiết phụ kiện (túi xách + giày búp bê) + Nét vẽ nối
  └─ [15.0s - 18.9s] CTA chốt đơn: "Nhấn giỏ hàng chốt đơn ngay nha!"

SET 2: OUTFIT TIỂU THƯ (18.9s – 38.5s)
  ├─ [18.9s - 28.7s] Hook sang chảnh + Mẫu xoay nhẹ váy lệch vai + Sticker đầm trắng
  ├─ [28.7s - 35.2s] Chi tiết phối đồ (sandal đế xuồng màu be)
  └─ [35.2s - 38.5s] CTA chốt đơn: "Nhấn giỏ hàng chốt đơn ngay nha!"

SET 3: OUTFIT NÀNG THƠ (38.5s – 58.5s)
  ├─ [38.5s - 48.4s] Hook ngọt ngào đón hè + Mẫu dạo bước + Sticker váy hoa nhí
  ├─ [48.4s - 55.0s] Chi tiết phụ kiện (mũ cói + giày ren)
  └─ [55.0s - 58.5s] CTA chốt đơn: "Nhấn giỏ hàng chốt đơn ngay nha!"
```

---

## 3. Những gì nên học
1. **[Split-Canvas Lookbook Layout (Bố cục chia đôi Mẫu & Sticker)](file:///Volumes/Data/socnhotv/data/shared/knowledge/video_craft/techniques/split-canvas-lookbook.md)**: Giải quyết cùng lúc 2 nhu cầu của khách: xem cả set khi mặc lên người trông ra sao (cột trái) VÀ nhìn rõ từng chi tiết sản phẩm được bóc tách (cột phải).
2. **[Sticker Cutout & Hand-drawn Doodle](file:///Volumes/Data/socnhotv/data/shared/knowledge/video_craft/techniques/sticker-cutout-doodle.md)**: Hiệu ứng viền trắng giả sticker kết hợp đường nét vẽ tay doodle tạo cảm giác thủ công, tinh tế, đậm chất aesthetic Hàn Quốc.
3. **[Multi-Outfit Carousel Rhythm (Chu kỳ 3-Set)](file:///Volumes/Data/socnhotv/data/shared/knowledge/video_craft/techniques/multi-outfit-carousel.md)**: Mỗi set 19s là thời lượng chuẩn vàng (Golden Duration) để khách kịp ngắm đồ, nghe tư vấn và nhận tín hiệu CTA trước khi bị mệt mỏi.
4. **[Synchronized Spoken Item Highlighting](file:///Volumes/Data/socnhotv/data/shared/knowledge/video_craft/techniques/synced-item-highlight.md)**: Giọng đọc nói tới món nào thì sticker của món đó nảy lên (Spring animation) và phát sáng viền nhẹ, giúp người xem không bị rối mắt.

---

## 4. Những gì nên làm TỐT HƠN (5 Cải tiến kiểm thử A/B)
1. **Dựng trực tiếp bằng DOM HyperFrames thay vì Render Video toàn phần**:
   - *Hạn chế của video gốc*: Render nguyên video bằng AI khiến chữ tiếng Việt bị nhòe và nét vẽ doodle không sắc nét.
   - *Cải tiến*: Dùng HyperFrames HTML5. Cột phải là DOM thật với font chữ sắc nét 4K, đường doodle là SVG vector animate bằng `strokeDashoffset`, icon dùng `<MorphIcon>`.
2. **Tối ưu chuẩn dọc 9:16 Full HD (1080x1920)**:
   - *Cải tiến*: Xuất đúng khung hình 1080x1920 không có viền đen.
3. **Thêm bảng giá và voucher nổi (Live Price Tag)**:
   - *Cải tiến*: Cạnh mỗi sticker sản phẩm, thêm tag giá nhỏ nảy ra: `320.000đ` kèm tag giảm giá `[-20%]`.
4. **Hiệu ứng Morphing đổi trang phục ở cột trái**:
   - *Cải tiến*: Khi chuyển giữa Set 1 sang Set 2, người mẫu ở cột trái có hiệu ứng xoay người hoặc vệt sáng biến hình (Morph transition) sang bộ đồ mới thay vì cắt hình giật cục.
5. **Thêm Micro-Interactions cho nút Giỏ hàng**:
   - *Cải tiến*: Khi giọng đọc kêu gọi "Nhấn giỏ hàng", ở góc dưới màn hình xuất hiện bàn tay chỉ vào giỏ hàng nhấp nháy thu hút sự chú ý.

---

## 5. Cách tái tạo cho Dự án SocNhoTV & Gobi Social
- **Đề xuất Template cho Session A**: `lookbook-split-canvas-v1` (đã nạp vào `requests_for_A.md`).
- **Phối hợp với Dữ liệu Session B**:
  - Lấy trực tiếp sản phẩm `Seq 004` (Áo thun BodyFit NEAU NuNu) đưa vào làm Set 1!
- **Asset HyperFrames cần có**:
  - `koc_model_video`: Video clip 10s lặp của KOC Neau/LyLy.
  - `stickers`: Mảng các ảnh PNG tách nền của từng món đồ (`ao.png`, `vay.png`, `tui.png`, `giay.png`).
  - `voice_id`: `soc-nho` hoặc `neau` đọc kịch bản theo 3 set.

---

## 6. Checklist chất lượng trước khi xuất bản
- [x] Khung hình 9:16 dọc 1080x1920
- [x] Cột trái tỉ lệ 45%, cột phải 55%
- [x] Chữ và sticker nằm trong safe zone (>180px trên, >320px dưới)
- [x] Đường doodle SVG xuất hiện đồng bộ với giọng đọc
- [x] Âm lượng chuẩn TikTok (-14 LUFS ± 1 LUFS)

---

## 7. Yêu cầu & Kỹ thuật mới
- Đã tạo 2 Technique Cards:
  1. `techniques/split-canvas-lookbook.md`
  2. `techniques/sticker-cutout-doodle.md`
- Đã cập nhật vào `harvest/accepted.md`.
- Đã cập nhật đề xuất template `lookbook-split-canvas-v1` vào `requests_for_A.md`.
