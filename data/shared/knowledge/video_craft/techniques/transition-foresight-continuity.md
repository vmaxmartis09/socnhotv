# Kỹ Thuật: Transition Foresight & 3-Angle Character Anchoring

- **Mã kỹ thuật**: `transition-foresight-continuity`
- **Nguồn cảm hứng**: Phân tích từ video `seq_n01_1834823671195631` (Jolie Mê Xem Phim)
- **Tags**: continuity | character-consistency | match-cut | infinite-canvas | storyboard | 3d-animation

---

## 1. Bản Chất Kỹ Thuật
Khi sản xuất phim ngắn hoặc hoạt hình AI gồm nhiều cảnh quay liên tiếp, hai lỗi nghiêm trọng nhất là:
1. **Biến dạng nhân vật (Character Drift)**: Cùng một nhân vật nhưng qua cảnh mới khuôn mặt bị thay đổi.
2. **Gãy chuyển động (Motion Jerk / Jump Cut)**: Cảnh 1 nhân vật đang quay sang trái, cảnh 2 camera đột ngột đảo sang phải khiến người xem chóng mặt.

---

## 2. Giải Pháp Chuẩn Hóa Cho Dự Án `socnhotv`

### 2.1. Bộ Neo 3 Góc Nhìn (3-Angle Character Master Anchor)
Đối với Sóc Nhỏ (Bi) và Bạn Koala:
- Khóa cứng 3 ảnh tham chiếu Master DNA:
  - `anchor_front.png`: Góc chính diện 0°.
  - `anchor_quarter.png`: Góc 45° ba phần tư.
  - `anchor_profile.png`: Góc nghiêng 90°.
- Bất kỳ prompt sinh hình ảnh hoặc video nào đều phải truyền cả 3 ảnh này qua ControlNet IP-Adapter / InstantID.

### 2.2. Quy Trình Khớp Nối Chuyển Cảnh (Transition Foresight Match-Cut)
Trước khi render video cảnh $N$:
1. Trích xuất **Khung hình cuối (Tail Frame)** của cảnh $N-1$.
2. Đọc vector chuyển động camera (Camera Motion Vector: Pan Left, Push In, Pedestal Up).
3. Đặt vector chuyển động của cảnh $N$ cùng hướng và cùng vận tốc tương đối để tạo cú nối chuyển cảnh liền mạch (Smooth Match Cut).
