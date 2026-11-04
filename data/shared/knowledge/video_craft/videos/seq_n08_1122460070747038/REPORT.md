# Phân Tích Chuyên Sâu: Seq N08 - Kỹ Thuật Che Khuất Tiền Cảnh Xóa Bỏ Cảm Giác 'Phẳng AI' (Jolie)

## 1. Tổng Quan
- **ID**: `seq_n08_1122460070747038`
- **Kênh**: Jolie Mê Xem Phim
- **Thời lượng**: 2 phút 40 giây (160.23s)
- **Chủ đề**: Khắc phục hiện tượng hình ảnh AI bị phẳng, thiếu chiều sâu thực tế bằng cách ép cấu trúc 3 tầng (Foreground Occlusion / Depth Layering) vào prompt.

---

## 2. Vì Sao Video AI Hay Bị "Phẳng" & Giả Tạo?
- Các mô hình Diffusion (Midjourney, Runway, Kling, Flux) khi nhận prompt chung chung thường đặt chủ thể ở chính giữa, lấy nét toàn bộ khung hình từ trước ra sau (infinite depth of field).
- Trong điện ảnh thực tế, mắt người hoặc máy quay vật lý luôn có **khoảng cách vật thể**: vật ở quá gần sẽ bị mờ nhoè (foreground blur/bokeh), tạo điểm neo thị giác (visual anchor) giúp não bộ nhận biết khoảng cách không gian 3 chiều.

---

## 3. Công Thức Prompt 3 Tầng Chiều Sâu (3-Layer Depth Partitioning)
Thay vì viết một prompt liên tục, cấu trúc prompt bắt buộc chia làm 3 tầng:

1. **Layer 1: Tiền cảnh (Foreground - Out of focus / Blurred)**:
   - Các vật thể thuộc môi trường đặt sát ống kính: ngọn cỏ (`low-angle wheat stalks brushing past camera`), cánh hoa (`soft blurred flower petal in extreme foreground`), khung lưới sắt (`blurred chain-link fence`), vai người (`over-the-shoulder blurred silhouette`).
2. **Layer 2: Trung cảnh (Midground - In-focus Subject)**:
   - Chủ thể chính đang thực hiện hành động cụ thể (`sharp focus on character running towards camera`, `detailed facial expression`).
3. **Layer 3: Hậu cảnh (Background - Atmospheric Depth)**:
   - Không gian phía xa (`soft hazy mountains in distant background`, `cinematic bokeh city lights`).

---

## 4. Ứng Dụng Trong Hệ Thống Sóc Nhỏ TV
- Module sinh ảnh và video của Sóc Nhỏ (`characters/soc_nho/`, `data/shared/templates/`):
  - Áp dụng ngay kỹ thuật này vào prompt generator của Session B: Mọi cảnh Sóc Nhỏ khám phá rừng xanh phải có ngọn lá cây rừng hoặc thân cây mờ ở tiền cảnh (`blurred tropical leaf in extreme foreground framing`).
  - Video review thời trang của LyLy/Neau: Luôn có giá treo đồ mờ hoặc gương phản chiếu ở tiền cảnh để tạo cảm giác không gian phòng thay đồ cao cấp.
- Đóng gói thành kỹ thuật: `techniques/foreground-occlusion-spatial-depth-layering.md`.
