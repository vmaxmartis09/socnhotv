# Sóc Nhỏ và Chiếc Răng Sâu (45s, 9:16)

Mục tiêu: dạy bé đánh răng, hạn chế kẹo. Giọng đọc ghép sau (chưa làm). Mỗi cảnh 7-8s (khớp clip Veo 8s), 6 cảnh = 45s.

## 1. Character Bible (GIỮ NGUYÊN Ở MỌI CẢNH, copy nguyên văn)

**[STYLE]** `3D Pixar-style animated film, soft warm lighting, vibrant pastel colors, rounded cute shapes, shallow depth of field, children's storybook look, 9:16 vertical`

**[SÓC NHỎ - "Sóc Bi"]** Ảnh chuẩn: `assets/soc_nho/soc_nho_01.png`, hồ sơ: `assets/soc_nho/soc_nho_profile.json`. Luôn đính kèm ảnh chuẩn khi tạo cảnh.

`a slim, agile 3-4 year old boy squirrel named Bi, NOT fat, flat belly, short slender limbs, head about 1/4 of body height, reddish orange-brown fur, big round glossy black eyes, light pink cheeks, two front teeth, small pointed ears with tufts, very large bushy tail curving up behind his back, darker red-brown toward the tip, fitted yellow crew-neck t-shirt, black shorts, dark sneakers with white soles`

**[BÁC SĨ KOALA - "Bác sĩ Gấu Túi"]** `a gentle elderly koala doctor, soft gray fur, large round black nose, fluffy round ears, kind small eyes behind round gold glasses, wearing a clean white doctor coat with a green cross badge, a head mirror on his forehead, a stethoscope around his neck`

**[NHÀ CÂY]** `a cozy treehouse built inside a huge oak tree, round wooden door, warm yellow window lights, a small balcony with a rope ladder, green leaves and tiny fairy lights, a shelf full of colorful candy jars inside`

**[PHÒNG KHÁM]** `a cute forest clinic inside a giant tree stump, a green wooden sign with a tooth icon, a small dentist chair with a cushion, shelves of tiny tools, soft mint-green walls, a big window with sunlight`

Quy tắc: không đổi màu áo, thể hình thon gọn, đuôi, kính, huy hiệu giữa các cảnh. Mỗi prompt ghi đủ khối nhân vật nguyên văn, không viết tắt.

## 2. Kịch bản (lời thoại + hình)

| # | Giây | Cảnh | Lời thoại / âm thanh |
|---|------|------|---------------------|
| 1 | 0-7 | Sóc Bi ở nhà cây, kệ đầy hũ kẹo, mắt sáng rực | Bi: "Oa, nhiều kẹo quá! Hôm nay Bi sẽ ăn thật nhiều!" |
| 2 | 7-15 | Bi ăn kẹo liên tục, má phồng, vỏ kẹo chất đống, quên đánh răng, đi ngủ | Dẫn: "Bi ăn kẹo cả ngày, tối lại quên đánh răng." |
| 3 | 15-22 | Sáng hôm sau, Bi ôm má, nhăn mặt, răng đau (hiệu ứng sao đỏ nhấp nháy) | Bi: "Ôi đau quá! Răng của Bi đau lắm!" |
| 4 | 22-30 | Bi đến phòng khám, bác sĩ Koala soi răng, thấy một chấm đen nhỏ trên răng | Bác sĩ: "Cháu bị sâu răng rồi. Do ăn quá nhiều kẹo ngọt đấy." |
| 5 | 30-38 | Bác sĩ chữa răng nhẹ nhàng, rồi dạy Bi cầm bàn chải đánh răng đúng cách | Bác sĩ: "Hãy đánh răng sáng và tối, ăn ít kẹo, uống nhiều nước nhé." |
| 6 | 38-45 | Bi cười tươi, răng sáng bóng, hũ kẹo thay bằng táo và cà rốt, vẫy tay chào | Bi: "Cảm ơn bác sĩ! Từ nay Bi sẽ chăm sóc răng thật tốt!" |

Nhạc nền: nhẹ, vui, tiết tấu chậm. SFX: lạo xạo vỏ kẹo, "ting" khi răng sáng.

## 3. Prompt batch (`Image Prompt | Video Prompt`, mỗi dòng một cảnh)

Thay `[STYLE]`, `[SÓC NHỎ]`, `[BÁC SĨ KOALA]`, `[NHÀ CÂY]`, `[PHÒNG KHÁM]` bằng nguyên văn khối ở mục 1 trước khi dán vào tool.

```
[STYLE]. [SÓC NHỎ] standing in [NHÀ CÂY], eyes sparkling, staring at shelves full of candy jars, wide shot | Bi gasps happily, jumps with joy and reaches toward the candy jars, camera slowly pushes in, cheerful mood
[STYLE]. [SÓC NHỎ] sitting on the wooden floor of [NHÀ CÂY], cheeks puffed full of candy, a pile of colorful wrappers around, medium shot | Bi eats candy nonstop, wrappers pile up, then yawns and falls asleep on the floor, camera pans gently
[STYLE]. [SÓC NHỎ] holding his cheek with one paw, grimacing in pain, small red star sparkles near the cheek, morning light in [NHÀ CÂY], close-up | Bi winces and cries out softly, rubs his cheek, shoulders slump, camera slowly pushes in
[STYLE]. [BÁC SĨ KOALA] examining [SÓC NHỎ] in [PHÒNG KHÁM], the squirrel sits in the dentist chair with mouth open, a small black spot visible on one tooth, two-shot | The koala doctor gently looks at the tooth with a small mirror, nods kindly and speaks, Bi looks worried, soft camera push-in
[STYLE]. [BÁC SĨ KOALA] holding a big toothbrush and showing [SÓC NHỎ] how to brush a giant model tooth in [PHÒNG KHÁM], medium shot | The koala demonstrates brushing in small circles, Bi imitates him carefully, both smile, camera holds steady
[STYLE]. [SÓC NHỎ] with a bright shining smile, teeth sparkling, standing at the door of [NHÀ CÂY], the candy jars replaced by apples and carrots, wide shot | Bi smiles with a sparkle on his teeth, waves happily to the camera, camera pulls back slowly, warm ending
```

## 4. Kiểm tra nhất quán trước khi tạo clip

- Tạo trước 1 ảnh mẫu Bi (đứng thẳng, nền trắng) và 1 ảnh Bác sĩ Koala, dùng làm Ingredients cho mọi cảnh.
- Sau khi tạo ảnh cảnh 1-6, so từng cảnh: màu áo, đuôi, kính, huy hiệu phải giống nhau. Cảnh nào lệch thì tạo lại ảnh trước khi chuyển sang video.
- Ghi chú: Veo/Omni có thể sinh chữ trên biển hiệu sai, nên tránh yêu cầu chữ trong ảnh.
