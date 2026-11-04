# Tài liệu & Nguồn truy vết (Sources & Verification) — Seq 006

Video ID: `3061194297574911` | Tiêu đề: "Motion control của Google Flow" | Kênh: Toby (Cơm AI lo)

## Chuỗi truy vết 3 tầng (3-Tier Investigation)

### Tầng 1: Dấu vết từ Kênh & Cộng đồng
1. **Nhóm Facebook "Cơm AI lo"**:
   - Cộng đồng chuyên chia sẻ workflow ComfyUI, Google Flow, Kling AI và ứng dụng video AI thực chiến tại Việt Nam.
   - Luận điểm của Toby: Thay vì tốn hàng giờ viết prompt miêu tả chuyển động (dễ bị ảo ảnh hallucination), sử dụng công cụ **Motion Control** (bảng điều khiển tham số camera) để định hình góc quay.
   - Độ tin cậy: Cao.

### Tầng 2: Công nghệ Camera Motion Control trong AI Video
2. **CameraCtrl & Trajectory Conditioning**:
   - Cơ chế: Thay vì chỉ dùng text prompt để dẫn dắt mô hình khuếch tán video, CameraCtrl tiêm một chuỗi ma trận camera 3D (3x4 camera pose matrices) vào các lớp self-attention thời gian (temporal self-attention).
   - Bằng chứng tài liệu:
     - Paper: *CameraCtrl: Enabling Camera Control for Text-to-Video Generation* (2024).
     - Repo: `https://github.com/hehao98/CameraCtrl`
   - Độ tin cậy: Rất cao.

### Tầng 3: Tái tạo bằng HyperFrames Keyframes Engine
3. **HyperFrames 3D Camera Simulation**:
   - Kỹ năng `hyperframes-keyframes` của dự án cung cấp đầy đủ các toán tử camera ảo:
     - `pan`: `gsap.to(".scene", { xPercent: -15, ease: "none" })`
     - `push-in`: `gsap.to(".character", { scale: 1.15, ease: "power1.out" })`
     - `pedestal`: `gsap.to(".canvas", { yPercent: -20, ease: "power2.inOut" })`
     - `orbit`: CSS 3D `rotateY(25deg)` kết hợp `perspective(1000px)`.
   - Lợi thế: Tất định 100%, render tức thì, không bị artifact nhòe hay biến dạng phom dáng cơ thể như video sinh từ mô hình khuếch tán.

## Bảng tổng hợp nguồn

| URL / Định danh | Loại | Điều học được | Độ tin cậy |
|---|---|---|---|
| `https://www.facebook.com/share/v/19mmDY1tzR/` | Video gốc | 5 cú máy chuẩn điện ảnh: Pan, Push-in, Orbit, Pedestal, Tracking | Cao |
| `https://github.com/hehao98/CameraCtrl` | Nghiên cứu AI | Cơ chế ma trận camera 3D điều khiển hướng nhìn trong video AI | Rất cao |
| `ai/skills/hyperframes-keyframes/SKILL.md` | Skill nội bộ | Cách lập trình quỹ đạo camera bằng GSAP và CSS 3D perspective | Tuyệt đối |
