# Sources & Technical Verification: Seq 015

- **Video URL**: `https://www.facebook.com/share/v/1DT6HAa3Uh/`
- **Canonical ID**: `1612875093634659`
- **Tác giả**: Xuân Linh
- **Quy trình công bố**: Quy trình thứ 15 (AI Flow Pro) - Phối đồ thời trang phong cách catalogue xoay người 360 độ.

---

## 1. Bản Chất Kỹ Thuật Đã Xác Thực
1. **Turntable Pose Sequence**:
   - `Pose (2s)` -> `Spin 360° (3s)` -> `In-rotation morph` -> `Hold & Next Look`.
   - Bằng cách biến đổi trang phục khi nhân vật đang xoay lưng về phía camera, các lỗi ghép nếp vải (warping/glitch) của AI video bị triệt tiêu hoàn toàn.
2. **Khóa Cố Định Giao Diện & Camera (Locked UI & Camera Rig)**:
   - Camera: Khóa tuyệt đối (No Zoom, No Pan, No Shake) để giữ tỷ lệ chuẩn catalog.
   - UI Layout: Checklist bên trái chia theo grid CSS cố định. Chỉ ảnh thumbnail sản phẩm bên trong xoay 3D nhẹ (CSS `rotateY(360deg)`), mang lại cảm giác thiết kế cao cấp (high-end editorial design).
