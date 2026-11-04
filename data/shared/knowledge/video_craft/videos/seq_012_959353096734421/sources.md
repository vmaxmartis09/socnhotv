# Sources & Technical Verification: Seq 012

- **Video URL**: `https://www.facebook.com/share/v/1DKAH18dBg/`
- **Canonical ID**: `959353096734421`
- **Tác giả**: Xuân Linh (AI Flow App / OmniFlash)
- **Quy trình công bố**: Quy trình thứ 23 - Fashion Lookbook Walking Transition.

---

## 1. Bản Chất Kỹ Thuật Đã Xác Thực
- **Nguyên lý sinh chuyển động**:
  - Dùng video khung xương di chuyển (ControlNet Openpose / DensePose walk cycle) làm anchor cố định.
  - Áp dụng kỹ thuật inpainting trang phục theo từng mốc thời gian (frame-range inpainting) để thay đổi texture áo quần mà không làm gãy nhịp bước đi.
- **Lớp phủ Đồ họa Động (Motion Graphics Overlay)**:
  - Các icon thời trang, nhãn mác, doodle vẽ tay và thông số outfit được định vị theo tọa độ nhân vật (point tracking / bounding box) và kích hoạt theo beat nhạc.
  - Đây chính là thế mạnh tuyệt đối của **HyperFrames HTML/CSS/GSAP**: Tách video nền thành 1 track video mượt mà và toàn bộ icon/typography động thành các layer HTML/CSS có thể seek và đồng bộ chính xác tới từng mili-giây.
