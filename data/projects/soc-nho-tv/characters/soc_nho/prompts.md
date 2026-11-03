# Bộ prompt mẫu cho Sóc Nhỏ (viết riêng cho project)

Rút từ cấu trúc quy trình trong video TikTok của Huan.academy, xem [TIKTOK_AI_ANIMATION_WORKFLOW_LESSONS.md](TIKTOK_AI_ANIMATION_WORKFLOW_LESSONS.md). Nội dung dưới đây là bản viết lại của project, không phải prompt gốc của tác giả.

Dùng với nhân vật chuẩn trong [SOC_NHO_CHARACTER_PROFILE.md](SOC_NHO_CHARACTER_PROFILE.md) và `assets/soc_nho`. Không vẽ nhân vật mới.

## Prompt 1: Lên 30 ý tưởng

```
Bạn là người lên kế hoạch nội dung cho kênh YouTube hoạt hình 3D dành cho trẻ 3-6 tuổi, nhân vật chính là bé sóc nhỏ (Sóc Nhỏ) cùng bạn bè và người lớn giúp đỡ.
Mỗi tập là một tình huống đời thường gần gũi với trẻ Việt Nam (đi chợ, đi học, nhà bà ngoại, công viên...), có một sự cố nhỏ, có cảm xúc (tò mò, sợ, xấu hổ, nhẹ nhõm) và kết bằng một bài học nhẹ nhàng.
Chủ đề lần này: {{CHỦ_ĐỀ}}
Hãy viết 30 ý tưởng. Chỉ trả về tiêu đề, mỗi tiêu đề một dòng, theo kiểu gợi tò mò, kèm 1-3 emoji. Không giải thích, không đánh số.
```

## Prompt 2: Viết kịch bản (tuyển tập mini-story)

```
Bạn là biên kịch cho kênh hoạt hình thiếu nhi, dàn nhân vật cố định: Sóc Nhỏ, {{NHÂN_VẬT_PHỤ}}, cùng một người lớn giúp đỡ khi cần.
Viết kịch bản đầy đủ bắt đầu từ chủ đề: {{TIÊU_ĐỀ_ĐÃ_CHỌN}}
Quy tắc quan trọng nhất: video là một TUYỂN TẬP 4-6 truyện ngắn độc lập nối tiếp nhau. Truyện đầu bám chủ đề chính, kết gọn rồi cắt sang truyện mới ở bối cảnh khác, cùng nhân vật.
Độ dài mục tiêu: {{SỐ_TỪ}} từ thoại. Câu ngắn, từ đơn giản, lặp lại, có lời trấn an.
Định dạng đầu ra: chỉ lời thoại, mỗi câu một dòng, bắt đầu bằng "Tên nhân vật:". Không tiêu đề, không đề mục, không chỉ dẫn sân khấu, không đếm từ, không bình luận.
```

## Prompt 3: Bộ prompt hình ảnh và video

### 3A. Style bible (dán nguyên văn vào mọi prompt ảnh và video)
```
3D Pixar-style animation, bóng mượt, ánh sáng studio mềm ấm, nền sạch, màu rực nhưng cân bằng, mắt to bóng có highlight, tỉ lệ 16:9, không chữ, không watermark, không phụ đề trong ảnh
```
Cụm style phải giữ đúng một cách viết; xem quy tắc trong skill `flow-auto-video`.

### 3B. Bước 1, ảnh tham chiếu nhân vật
```
Với mỗi nhân vật lặp lại trong kịch bản, viết một prompt ảnh tham chiếu: toàn thân, đứng chính diện, tư thế trung tính, nhìn vào camera, nền trắng thuần #FFFFFF, ánh sáng đều, không đạo cụ, không nhân vật khác.
Dùng đúng mô tả cố định (lông, mắt, trang phục, giày). Với Sóc Nhỏ dùng nguyên prompt khóa trong hồ sơ nhân vật.
Kèm một dòng "từ khóa nhất quán" ngắn để dán lại khi cần.
```

### 3C. Bước 2, bộ prompt từng beat
```
Phủ toàn bộ kịch bản, không tóm tắt, không bỏ beat. Mỗi beat theo mẫu:

Câu thoại: "..."
Nhân vật trong khung: ...
Prompt ảnh: ... (ảnh tĩnh, không chữ trong ảnh)
Prompt video: ... (chuyển động + thoại trong ngoặc kép, ghi rõ ai nói)

Quy tắc:
- Mỗi prompt tự đứng được, dán thẳng vào model là chạy.
- Mỗi câu thoại xuất hiện nguyên văn trong prompt video của beat đó, gán đúng người nói.
- Mỗi beat dài 3-8 giây; thoại quá dài thì tách beat.
- Không đổi trang phục, kiểu lông hay giọng của nhân vật giữa các beat.
Kịch bản: {{DÁN_KỊCH_BẢN}}
```

### 3D. Voice bible (thêm vào hồ sơ nhân vật)
Mỗi nhân vật một dòng giọng cố định (tuổi, âm sắc, tốc độ). Sóc Nhỏ: giọng bé trai khoảng 4 tuổi, trong, tinh nghịch (chốt lại khi chọn giọng, liên kết `vietnamese-voice-clone`).

## Đưa vào Google Flow
Dán danh sách beat theo dạng `[Prompt ảnh] | [Prompt video]` mỗi dòng. Nhân vật tải từ ảnh chuẩn `assets/soc_nho/soc_nho_01.png`, không sinh mới.
