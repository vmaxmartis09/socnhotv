# 3 lớp prompt (tiếng Anh, [STYLE] nguyên văn)

## Character reference (Image mode)
```text
CHARACTER REF — [Tên]:
Character reference sheet for [mô tả] named [Tên]: [tuổi], [ngoại hình + đặc điểm nhận diện + trang phục]. Multiple angles (front, 3/4, side), full body and close-up face, consistent [STYLE], neutral background, consistent soft lighting, no text.
```

## Storyboard từng cảnh (Image mode)
```text
STORYBOARD — CẢNH [N] (attach: [Character Ref]):
Single cinematic frame for [bối cảnh + hành động], featuring [Tên] exactly as in the attached reference. [Góc máy]. Consistent [STYLE], consistent lighting and color palette, [tỉ lệ], no text.
```

## Video từng cảnh (Video mode)
```text
VIDEO — CẢNH [N]:
Animate this frame into an [8]-second cinematic clip. CRITICAL: preserve EXACTLY the same [STYLE], lighting, and color palette shown. Scene: [chuyển động + camera]. [The character says "..."]. Smooth natural motion, no jump cuts, no text.
```

## Cú pháp nhập hàng loạt (theo video của Huan.academy)
Mỗi cảnh một dòng: `image prompt | video prompt`. Chạy "phân tích cảnh" để tách cảnh và gắn đúng nhân vật, rồi render ảnh, sau đó render video.
