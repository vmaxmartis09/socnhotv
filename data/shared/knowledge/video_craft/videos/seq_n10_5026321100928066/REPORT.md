# Phân Tích Chuyên Sâu: Seq N10 - Phân Biệt Cú Máy Điện Ảnh & Tác Động Tâm Lý (Ftano Editor)

## 1. Tổng Quan
- **ID**: `seq_n10_5026321100928066`
- **Kênh**: Ftano Editor
- **Thời lượng**: 31.27 giây (9:16)
- **Chủ đề**: Bảng đối chiếu chính xác giữa chuyển động máy vật lý (Dolly) và thay đổi tiêu cự (Zoom), kèm tác động tâm lý điện ảnh tương ứng.

---

## 2. Sự Khác Biệt Cốt Lõi: Dolly (Vật lý) vs Zoom (Quang học/Scale)
Rất nhiều prompt creator AI nhầm lẫn giữa Dolly và Zoom, dẫn đến chuyển động video không đạt hiệu quả cảm xúc:

1. **Dolly In (Máy di chuyển tới)**:
   - *Cơ chế*: Máy quay di chuyển tịnh tiến qua không gian vật lý, tạo ra hiệu ứng thị sai (parallax - vật gần chuyển động nhanh hơn vật xa).
   - *Tác động*: Kéo khán giả bước vào không gian của nhân vật, phóng đại cảm xúc nội tâm sâu sắc và tự nhiên.
2. **Zoom In (Thu phóng tiêu cự / Scale)**:
   - *Cơ chế*: Vị trí máy đứng yên, chỉ nén phối cảnh (flattening perspective).
   - *Tác động*: Tạo điểm nhấn giật mình (dramatization / sudden shock), tập trung gay gắt vào chi tiết.
3. **Dolly Out (Máy lùi xa)**:
   - *Cơ chế*: Máy lùi lại, để lại nhân vật nhỏ bé giữa bối cảnh rộng lớn.
   - *Tác động*: Tạo cảm giác cô đơn, lạc lõng, hoặc giới thiệu môi trường bao quanh.
4. **Zoom Out (Thu nhỏ)**:
   - *Cơ chế*: Mở rộng góc nhìn quang học tức thì.
   - *Tác động*: Phơi bày sự thật bất ngờ (reveal), giải mã bức tranh toàn cảnh.

---

## 3. Ứng Dụng Trong Hệ Thống Sóc Nhỏ TV
- Dùng cho `hyperframes-keyframes`:
  - Trong HyperFrames composition HTML5, dùng thuộc tính `transform: scale()` mô phỏng Zoom, còn kết hợp `perspective: 1000px; transform: translateZ()` để mô phỏng Dolly 3D thực thụ.
- Chuẩn hóa prompt camera cho Session B (`tool/src/socnhotv/video/prompts/`):
  - Phân tách rõ các keyword: `slow cinematic dolly in tracking shot` (cho cảnh cảm xúc) vs `fast optical crash zoom` (cho khoảnh khắc giật mình).
- Đóng gói thành kỹ thuật: `techniques/cinematography-camera-mechanics-cheatsheet.md`.
