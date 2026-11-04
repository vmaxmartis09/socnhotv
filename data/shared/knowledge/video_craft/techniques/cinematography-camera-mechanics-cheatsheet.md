# Technique: Cinematography Camera Mechanics & Emotional Grammar Cheatsheet

## Tóm Tắt Kỹ Thuật
Bảng từ điển chuyển động máy quay điện ảnh (Camera Grammar) phân định rạch ròi giữa chuyển động vật lý không gian (Dolly / Tracking) và chuyển đổi quang học tiêu cự (Zoom / Scale), kèm theo ma trận ánh xạ cảm xúc (Emotional Mapping) dùng để điều khiển chuyển động GSAP/CSS trong HyperFrames hoặc sinh prompt AI video (Kling, Runway Gen-3, Luma).

---

## 1. Ma Trận Đối Chiếu Dolly vs Zoom

| Cú máy | Bản chất vật lý | Phối cảnh không gian | Hiệu quả tâm lý & Kịch bản | Prompt Keyword chuẩn |
|---|---|---|---|---|
| **Dolly In** | Máy tịnh tiến về phía trước | Parallax rõ rệt: Tầng tiền cảnh trôi nhanh, không gian mở rộng sang 2 bên | Thấu hiểu, đi sâu vào nội tâm, kéo người xem hoà vào cảm xúc nhân vật | `cinematic slow dolly-in, spatial parallax, physical camera forward movement` |
| **Zoom In** | Máy đứng yên, kéo tiêu cự | Không gian bị nén phẳng (compressed perspective) | Giật mình bất ngờ (shock), phát hiện manh mối, cú giật chú ý (punch-in) | `optical zoom-in, rapid focal length punch-in, zero parallax` |
| **Dolly Out** | Máy lùi dần về phía sau | Vật thể tiền cảnh trôi vào khung hình, nhân vật thu nhỏ dần trong không gian thật | Cô độc, nhỏ bé, lạc lõng giữa thế giới rộng lớn; kết thúc một chương | `slow dolly-out revealing vast environment, dramatic separation` |
| **Zoom Out** | Máy đứng yên, mở tiêu cự | Góc nhìn dãn rộng tức thì | Phơi bày sự thật toàn cảnh (The big reveal), kết thúc giải thích | `wide optical zoom-out, full frame reveal` |
| **Pan (Lia)** | Trục máy xoay ngang | Chuyển dịch góc nhìn tại chỗ | Kết nối nguyên nhân - kết quả giữa 2 chủ thể trong cùng 1 bối cảnh | `horizontal whip pan connecting subject A and B` |

---

## 2. Ứng Dụng Trong Code HyperFrames (GSAP)
- **Mô phỏng Dolly In (3D Parallax)**:
  ```css
  .viewport {
    perspective: 1200px;
    perspective-origin: center center;
  }
  .camera-rig {
    transform-style: preserve-3d;
  }
  ```
  ```javascript
  // GSAP Dolly Move
  gsap.to(".camera-rig", {
    z: 400, // Tiến sâu vào trục Z
    ease: "power2.out",
    duration: 3
  });
  ```
- **Mô phỏng Zoom In**:
  ```javascript
  // GSAP 2D Zoom Punch
  gsap.to(".frame-content", {
    scale: 1.25,
    transformOrigin: "center center",
    ease: "back.out(1.2)",
    duration: 0.4
  });
  ```
