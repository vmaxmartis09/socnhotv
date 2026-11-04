# Playbook 06: Tập Phim Hoạt Hình YouTube (YouTube Animation Episode Mastery)

> Áp dụng cho: Kênh hoạt hình dài 16:9 hoặc tập phim ngắn 9:16 của Sóc Nhỏ Bi & Bạn Koala  
> Mục tiêu cốt lõi: Duy trì tính nhất quán nhận diện nhân vật (DNA consistency), tối ưu nhịp kể chuyện dài tập và sản xuất tự động hàng loạt.

---

## 1. Danh Sách Kỹ Thuật Sử Dụng
- [`deterministic-web-to-video-rendering`](../techniques/deterministic-web-to-video-rendering.md): Dựng hoạt hình tất định từ HTML5/CSS/GSAP HyperFrames.
- [`channel-style-cloning-template-pipeline`](../techniques/channel-style-cloning-template-pipeline.md): Định hình cấu trúc tập phim thành template có thể tái sử dụng.
- [`frictionless-remix-workflow`](../techniques/frictionless-remix-workflow.md): Tái sử dụng kho background, biểu cảm nhân vật và SFX.
- [`3-layer-knowledge-retention`](../techniques/3-layer-knowledge-retention.md): Cấu trúc bài học khoa học thiếu nhi (Hiện tượng tò mò -> Giải thích trực quan -> Đúc kết ứng dụng).

---

## 2. Quy Trình Từng Bước (Step-by-Step Workflow)

### Bước 1: Khóa Cứng Nhận Diện & Tỉ Lệ Nhân Vật (Scale Lock)
- **Sóc Nhỏ (Bi):** Chiều cao khóa cứng **100cm**, tính cách lém lỉnh, tò mò, giọng `soc-nho`.
- **Bác sĩ Koala:** Chiều cao khóa cứng **150cm**, tính cách trầm tĩnh, thông thái, đóng vai trò giải thích khoa học.
- Master DNA assets lấy từ `data/projects/soc-nho-tv/characters/soc_nho/` (ảnh RGBA nền trong suốt).

### Bước 2: Phân Đoạn Cấu Trúc Tập Phim (Act Structure)
Một tập phim 45s - 90s chuẩn gồm 4 màn:
1. **Màn 1: Sự cố / Hiện tượng tò mò (0s - 10s):** Bi gặp một hiện tượng thiên nhiên kỳ lạ (cầu vồng, sấm sét, lá cây đổi màu).
2. **Màn 2: Giả thuyết ngây ngô của Bi (10s - 25s):** Bi đưa ra suy đoán hài hước, tạo tiếng cười cho khán giả nhỏ tuổi.
3. **Màn 3: Bác sĩ Koala giải thích khoa học (25s - 40s):** Xuất hiện đồ họa trực quan (lăng kính tán sắc, luồng điện...).
4. **Màn 4: Đúc kết & Kêu gọi chia sẻ (40s - 45s):** Bi hiểu ra vấn đề và cảm ơn bạn bè.

### Bước 3: Lập Trình Hoạt Ảnh Trên HyperFrames
- Sử dụng các sub-composition theo màn để timeline rõ ràng và dễ bảo trì.
- Đồng bộ khẩu hình và chuyển động nhân vật theo timeline audio của OmniVoice.
- Tự động hạ âm lượng nhạc nền (BGM ducking -12dB) khi có giọng thoại của nhân vật.

---

## 3. Khuôn Mẫu Cấu Trúc Kịch Bản Tập Phim

```
[Màn 1 - Hook]:
Bi: "Ủa chú Koala ơi! Cầu vồng có phải là đường trượt của các chú gấu bông trên mây không ạ?"

[Màn 2 - Đối thoại]:
Koala: "Haha, không phải đâu Bi nhỏ ơi! Đó là ánh sáng mặt trời đang chơi trò ảo thuật đó!"

[Màn 3 - Trực quan khoa học]:
Koala: "Mỗi giọt nước mưa giống như một lăng kính tí hon. Khi ánh sáng trắng đi qua giọt nước, nó bị tách thành 7 sắc cầu vồng rực rỡ!"

[Màn 4 - Kết thúc]:
Bi: "Ồ, thì ra là vậy! Lần sau trời mưa tạnh, Bi sẽ tìm xem giọt nước nào làm ra màu tím nhé!"
```

---

## 4. Sai Lầm Thường Gặp (Pitfalls to Avoid)
1. **Lệch tỷ lệ nhân vật giữa các cảnh:** Cảnh trước Bi cao bằng Koala, cảnh sau Bi lại nhỏ xíu -> Vi phạm `SCALE_LOCK.md`.
2. **Giải thích kiến thức quá hàn lâm, dùng từ khó hiểu:** Khán giả thiếu nhi sẽ nhanh chán nếu dùng thuật ngữ vật lý phức tạp không có ẩn dụ gần gũi.
3. **Nhạc nền quá to lấn át giọng nói:** Cần nén nhạc nền và giảm âm lượng tự động (Audio Ducking) chuẩn -14 LUFS cho toàn bộ tập phim.

---

## 5. Checklist Trước Khi Xuất Bản (Pre-Publish Checklist)
- [ ] Tỉ lệ chiều cao Bi (100cm) và Koala (150cm) đúng chuẩn quy định.
- [ ] Giọng đọc sử dụng đúng model OmniVoice `soc-nho`, audio mastering chuẩn TikTok.
- [ ] BGM ducking hoạt động chuẩn, giọng thoại rõ ràng trên mọi thiết bị loa điện thoại.
- [ ] Bài học khoa học ngắn gọn, chính xác và có tính giáo dục cao.
