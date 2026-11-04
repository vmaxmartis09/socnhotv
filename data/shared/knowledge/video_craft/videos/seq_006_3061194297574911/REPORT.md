# Báo cáo Phân tích Video — Seq 006

- **ID Video**: `3061194297574911`
- **Tiêu đề gốc**: "Cơm AI lo: Motion control của Google Flow"
- **Tác giả**: Toby
- **Quyết định**: `LEARN` (Học sâu kỹ thuật Camera Motion Control để ứng dụng vào hệ thống camera ảo của HyperFrames).

---

## 1. Tóm tắt phân tích
Video ngắn 32.83s, không có lời thoại (chỉ sử dụng nhạc nền điện tử 124 BPM), minh họa trực quan 5 quỹ đạo chuyển động camera kinh điển trong video thời trang:
1. **Horizontal Pan** (Quét ngang thiết lập bối cảnh)
2. **Push-In Zoom** (Đẩy thẳng vào mặt/áo)
3. **Arc Orbit 45°** (Xoay vòng cung quanh cơ thể)
4. **Pedestal Up / Outfit Scan** (Quét dọc từ giày lên đầu)
5. **Backward Tracking** (Đi lùi bám theo bước chân catwalk)

- **Giá trị cốt lõi**: Chứng minh rằng để làm video thời trang AI đẳng cấp, không nên trông cậy vào việc viết prompt dài dòng (text-only prompt rất dễ làm méo dáng hoặc camera chuyển động sai hướng), mà cần áp dụng **Camera Motion Control** định hướng hình học rõ ràng.

---

## 2. Công thức Blueprint
Thời lượng: **32.8s** | Nhịp cắt: **1.52 cuts/10s** | Nhạc nền: **124 BPM House**

```
[0.0s - 4.5s] PAN NGANG (Context Establish)
  └─ Pan ngang từ trái sang phải 30% chiều rộng khung hình
[4.5s - 9.2s] PUSH-IN ZOOM (Detail Focus)
  └─ Phóng to 1.15x vào phần áo và kính râm
[9.2s - 15.0s] ARC ORBIT (3D Parallax)
  └─ Xoay vòng cung 45 độ, bối cảnh trôi theo luật xa gần
[15.0s - 22.5s] OUTFIT SCAN (Pedestal Up)
  └─ Camera quét từ từ từ giày sneaker -> quần -> áo khoác
[22.5s - 32.8s] RUNWAY CATWALK (Backward Tracking)
  └─ Camera lùi dần đều khi người mẫu sải bước tự tin về phía trước
```

---

## 3. Những gì nên học
1. **[Camera Motion Choreography (Vũ đạo Chuyển động Camera)](file:///Volumes/Data/socnhotv/data/shared/knowledge/video_craft/techniques/camera-motion-choreography.md)**: Bộ 5 cú máy chuẩn mực cho video lookbook thời trang giúp tôn dáng và làm nổi bật chất liệu vải.
2. **[Outfit Scan via Pedestal Up](file:///Volumes/Data/socnhotv/data/shared/knowledge/video_craft/techniques/outfit-scan-pedestal.md)**: Cú máy quét dọc từ dưới lên là giải pháp hoàn hảo để giới thiệu trọn bộ trang phục (giày + quần + áo) trong một shot duy nhất liền mạch.
3. **[Beat-Matched Camera Accents](file:///Volumes/Data/socnhotv/data/shared/knowledge/video_craft/techniques/beat-matched-camera.md)**: Điểm bắt đầu và kết thúc của mỗi cú lia máy khớp chuẩn xác với phách mạnh (kick/snare) của bản nhạc nền.

---

## 4. Những gì nên làm TỐT HƠN (5 Cải tiến kiểm thử A/B)
1. **Thêm Kinetic Typography & Brand Tags**:
   - *Hiện trạng*: Video hoàn toàn không có chữ, người xem không biết thương hiệu hay sản phẩm gì.
   - *Cải tiến*: Thêm chữ kinetic pop-in bên cạnh các shot (tên brand, tên bộ sưu tập, tên item khi camera quét qua).
2. **Chuyển đổi sang định dạng dọc 9:16 Full HD**:
   - *Cải tiến*: Render chuẩn 1080x1920 tối ưu cho Reels/Shorts.
3. **Bổ sung Voiceover phong cách Fashion Magazine**:
   - *Cải tiến*: Lồng giọng đọc tiếng Việt ấm áp, chậm rãi mô tả chất liệu và cảm hứng phối đồ.
4. **Tích hợp Sound Effects (Whoosh / Shutter)**:
   - *Cải tiến*: Thêm âm thanh gió lướt (cinematic whoosh) khi camera chuyển góc quay.
5. **Lồng ghép nhân vật DNA của dự án**:
   - *Cải tiến*: Áp dụng bộ 5 cú máy này cho KOC Neau hoặc nhân vật Bi/Koala của SocNhoTV.

---

## 5. Cách tái tạo cho Dự án SocNhoTV & Gobi Social
- Đề xuất bổ sung bộ preset Camera Motion vào `HyperFramesEngine` và `hyperframes_adapter.py` của Session A.
- Đã tạo Technique Card:
  - `techniques/camera-motion-choreography.md`
- Đã cập nhật vào `harvest/accepted.md`.
