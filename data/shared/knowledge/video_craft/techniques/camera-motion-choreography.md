---
id: camera-motion-choreography
title: Camera Motion Choreography (Vũ Đạo Chuyển Động Camera 5 Cú Máy Kinh Điển)
status: in-studio
build: 'yes'
reproducible_with_our_stack: 'yes'
needs:
- HyperFrames
- GSAP
implemented_in:
- tool/src/socnhotv/video/craft/camera.py
- data/shared/knowledge/video_craft/playbooks/camera-and-transitions.md
evidence_videos:
- seq_006
confidence: high
last_verified: '2026-11-04'
expires_at: never
tags:
- camera
- motion-design
- cinematography
- hyperframes
- lookbook
---

# Camera Motion Choreography (Vũ Đạo Chuyển Động Camera 5 Cú Máy Kinh Điển)

Tags: camera | motion-design | cinematography | hyperframes | fashion | lookbook

## Là gì
Hệ thống 5 quỹ đạo chuyển động camera cơ bản được lập trình tất định để giới thiệu thời trang và sản phẩm:
1. **Pan (Lia ngang)**: Quét từ trái sang phải hoặc ngược lại để thiết lập không gian.
2. **Push-In (Đẩy tới)**: Phóng to vào một vùng chi tiết để tạo điểm nhấn thị giác.
3. **Orbit (Xoay vòng cung)**: Xoay quanh đối tượng để tạo chiều sâu 3D và hiệu ứng thị sai (parallax).
4. **Pedestal Up (Quét dọc từ dưới lên)**: Di chuyển camera theo phương thẳng đứng từ chân lên đầu để quét trọn vẹn toàn bộ outfit.
5. **Tracking (Bám đuổi)**: Đi lùi hoặc tiến theo bước chân của nhân vật.

## Vì sao hiệu quả
- **Thay thế text prompt bất định**: Thay vì hy vọng AI hiểu câu chữ "camera đẹp", việc khóa cứng vector chuyển động camera bảo đảm 100% video ra đời có cú máy chuẩn điện ảnh, không bao giờ bị méo hình.
- **Tạo cảm giác cao cấp (High Production Value)**: Các chuyển động camera mượt mà tạo cho người xem cảm giác video được quay bởi ekip quay phim chuyên nghiệp với gimbal và ray trượt (dolly).

## Ví dụ trong video
- Video `seq_006` (`3061194297574911` - Toby) @ `t=0.0s -> 32.8s`:
  - Lần lượt trình diễn cả 5 cú máy: Pan (0-4.5s), Push-in (4.5-9.2s), Orbit (9.2-15s), Pedestal (15-22.5s), Tracking (22.5-32.8s).

## Cách làm lại trong HyperFrames (`hyperframes-keyframes`)
- **Bộ Preset GSAP chuẩn**:
  ```javascript
  const cameraMotions = {
    // 1. Pan Horizontal
    pan: (el, duration = 4.0) => 
      gsap.fromTo(el, { xPercent: 10 }, { xPercent: -10, duration, ease: "power1.inOut" }),
      
    // 2. Push-in Zoom
    pushIn: (el, duration = 4.0, scale = 1.15) => 
      gsap.fromTo(el, { scale: 1.0 }, { scale, duration, ease: "power1.out" }),
      
    // 3. Pedestal Up (Quét outfit)
    pedestalUp: (el, duration = 5.0) => 
      gsap.fromTo(el, { yPercent: 15 }, { yPercent: -15, duration, ease: "power2.inOut" }),
      
    // 4. Orbit 3D Parallax
    orbit: (el, duration = 6.0) => 
      gsap.fromTo(el, { rotateY: -15, perspective: 1000 }, { rotateY: 15, duration, ease: "sine.inOut" })
  };
  ```

## Mức độ tin cậy
Tuyệt đối · Cập nhật: 2026-11-04
