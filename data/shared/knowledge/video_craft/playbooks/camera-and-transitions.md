# Playbook 02: Camera & Chuyển Cảnh Liền Mạch (Camera & Transitions Choreography)

> Áp dụng cho: Biên tập video HyperFrames GSAP, hoạt cảnh Sóc Nhỏ & KOC AI  
> Mục tiêu cốt lõi: Tạo chuyển động máy mượt mà, loại bỏ cảm giác cắt giật thô (jump-cut) và giữ nhịp thị giác ổn định.

---

## 1. Danh Sách Kỹ Thuật Sử Dụng
- [`camera-motion-choreography`](../techniques/camera-motion-choreography.md): 5 cú máy kinh điển (Push-In, Dolly-Out, Lateral Parallax, Dutch Angle, Punch-In).
- [`cinematography-camera-mechanics-cheatsheet`](../techniques/cinematography-camera-mechanics-cheatsheet.md): Bảng tra cứu tiêu cự ống kính (24mm, 50mm, 85mm), khẩu độ và tốc độ pan.
- [`transition-foresight-continuity`](../techniques/transition-foresight-continuity.md): Tiên liệu hướng chuyển động 0.5s cuối cảnh trước để chọn kiểu chuyển cho cảnh sau.
- [`walking-outfit-transition`](../techniques/walking-outfit-transition.md): Chuyển cảnh đập nhịp theo bước chân hoặc điểm rơi âm nhạc.
- [`rapid-montage-proof`](../techniques/rapid-montage-proof.md): Nhịp cắt dồn dập 0.3s - 0.5s giữa các chứng cứ hình ảnh.

---

## 2. Quy Trình Từng Bước (Step-by-Step Workflow)

### Bước 1: Xác Định Tiêu Cự & Vị Trí Camera Theo Cảnh
- **Cảnh thiết lập (Establishing Shot):** Dùng tiêu cự góc rộng 24mm - 35mm, dolly-in chậm để đưa khán giả vào thế giới câu chuyện.
- **Cảnh đối thoại / KOC chia sẻ:** Tiêu cự chuẩn 50mm, camera tĩnh hoặc push-in nhẹ 3-5% để tăng sự tập trung vào ánh mắt nhân vật.
- **Cảnh đặc tả sản phẩm (Macro/Detail Shot):** Tiêu cự 85mm - 100mm, độ sâu trường ảnh mỏng (shallow DOF), kết hợp orbit/turntable nhẹ.

### Bước 2: Lập Trình 5 Cú Máy HyperFrames Bằng GSAP
Trong composition HTML5, dùng `transform: scale() translate()` tất định:
1. **Push-In Dramatic:** `scale: 1.0 -> 1.08`, `ease: "power1.out"`, duration: toàn bộ thời lượng clip.
2. **Dolly-Out Reveal:** `scale: 1.1 -> 1.0`, mở rộng khung nhìn để hé lộ bối cảnh.
3. **Punch-In Accent:** Giật `scale: 1.0 -> 1.25` trong 0.15s ngay điểm rơi âm thanh quan trọng.
4. **Lateral Parallax Pan:** Di chuyển trục X kèm lệch tốc độ giữa tiền cảnh và hậu cảnh.
5. **Whip Pan:** Quét nhanh trục X `1500px/s` kèm `filter: blur(12px)`.

### Bước 3: Áp Dụng Quy Tắc Transition Foresight
- Đo vector vận tốc và hướng chuyển động ở **0.5 giây cuối của Cảnh N**:
  - Nếu nhân vật hoặc camera đang lướt sang **Phải (X > 0)** -> Cảnh N+1 bắt đầu bằng chuyển cảnh **Whip Right** hoặc **Push Right**.
  - Nếu camera đang **Zoom In** -> Cảnh N+1 bắt đầu bằng cú máy tiếp nối zoom-in cận cảnh hoặc **Zoom Punch**.
  - Nếu cảnh tĩnh kết thúc bằng điểm nhấn âm thanh -> Dùng **Hard Cut** hoặc **Flash Cut (1-2 frames trắng)**.

---

## 3. Khuôn Mẫu Cấu Hình Camera (Code Presets)

### Preset 1: HyperFrames Push-In Nhẹ (Dùng cho Lời Thoại)
```html
<div class="clip" data-start="0s" data-duration="4s">
  <img src="character.png" class="camera-push-in" />
</div>
<style>
.camera-push-in {
  transform-origin: center center;
  animation: pushIn 4s cubic-bezier(0.25, 1, 0.5, 1) forwards;
}
@keyframes pushIn {
  from { transform: scale(1.0); }
  to { transform: scale(1.08); }
}
</style>
```

### Preset 2: Transition Foresight Auto-Resolver (Python Logic)
```python
# Đo vector cảnh trước và chọn style chuyển cảnh
if prev_motion.direction == "right":
    next_transition = "whip-right"
elif prev_motion.direction == "zoom-in":
    next_transition = "zoom-match"
else:
    next_transition = "crossfade-fast"
```

---

## 4. Sai Lầm Thường Gặp (Pitfalls to Avoid)
1. **Camera zoom quá nhanh hoặc giật cục:** Gây chóng mặt cho người xem. Tốc độ zoom kịch bản thoại chỉ nên từ 5% đến 10% trong 3-5 giây.
2. **Xung đột hướng chuyển cảnh (Axis Collision):** Cảnh trước nhân vật chạy sang phải, cảnh sau chuyển cảnh quét sang trái làm đứt gãy dòng thị giác.
3. **Cắt hình không đúng nhịp nhạc (Off-beat cut):** Cắt cảnh lơ lửng giữa 2 phách nhạc làm giảm năng lượng video.

---

## 5. Checklist Trước Khi Xuất Bản (Pre-Publish Checklist)
- [ ] Không có cảnh tĩnh quá 3 giây mà không có chuyển động camera nhẹ.
- [ ] Mọi cú cắt cảnh đều khớp nhịp phách trống hoặc điểm nhấn thoại.
- [ ] Hướng chuyển cảnh Cảnh N → Cảnh N+1 tuân thủ đúng vector chuyển động (Transition Foresight).
- [ ] Các cảnh nhấn mạnh cảm xúc có cú punch-in đúng trọng tâm khuôn mặt nhân vật.
