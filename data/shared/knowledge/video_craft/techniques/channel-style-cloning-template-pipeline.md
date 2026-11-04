---
id: channel-style-cloning-template-pipeline
title: Channel Style Cloning & Template Pipeline
status: knowledge
build: partial
reproducible_with_our_stack: yes (Định hình style thông qua template HyperFrames JSON
  + CSS)
needs:
- HyperFrames
- Template Engine
implemented_in:
- tool/src/socnhotv/video/templates/
evidence_videos:
- seq_015
confidence: high
last_verified: '2026-11-04'
expires_at: '2027-11-04'
tags:
- template-pipeline
- style-cloning
- youtube-shorts
- branding
---

# Technique: Channel Style Decomposition & Template Cloning Pipeline

## Tóm Tắt Kỹ Thuật
Quy trình dịch ngược (Reverse-engineering) phong cách nhận diện của một kênh video thành công (Visual, Voice, Narrative Structure) thành bộ khung mẫu bất biến (Channel Template Blueprint), cho phép tự động hoá sản xuất hàng loạt video nhất quán 100% thương hiệu từ một câu lệnh ý tưởng duy nhất.

---

## 1. Bản Chất Kỹ Thuật
- Thay vì sáng tạo tự do mỗi video một kiểu (dễ mất nhận diện thương hiệu và tốn thời gian cân chỉnh), các kênh lớn luôn vận hành trên một **Template Framework** cố định:
  - Khung thời lượng mỗi cảnh cố định (ví dụ: Hook 3s, Intro 5s, Scene 1 12s...).
  - Bảng màu và ánh sáng cố định (Master Look LUT).
  - Giọng đọc và âm nhạc nền theo công thức ducking cố định.

---

## 2. 4 Bước Bóc Tách Một Kênh Mẫu

```mermaid
flowchart TD
    A["URL Kênh Đối Thủ Thành Công"] --> B["Bóc tách 4 yếu tố"]
    B --> C1["Voice DNA: Tần số, tốc độ, nhịp thở"]
    B --> C2["Visual DNA: Màu sắc, bố cục, góc quay"]
    B --> C3["Story DNA: Hook, xung đột, giải pháp, CTA"]
    B --> C4["Packaging DNA: Font thumbnail, cấu trúc tiêu đề"]
    C1 & C2 & C3 & C4 --> D["Master Project Template (.json / .html)"]
    D --> E["Input 1 Ý Tưởng Mới"]
    E --> F["Tự động Render Video Hoàn Chỉnh + Gói Xuất Bản YouTube/TikTok"]
```

---

## 3. Ứng Dụng Trong Sóc Nhỏ TV
- Lưu trữ cấu hình template tại `data/projects/<project-id>/templates/`.
- Khi cần sản xuất một tập phim mới cho Sóc Nhỏ:
  1. Chỉ nạp chủ đề giáo dục / phiêu lưu vào CLI.
  2. Engine tự động dùng kịch bản chuẩn, nạp nhân vật Bi (100cm) và Koala (150cm) với prompt DNA đã khóa.
  3. Xuất video qua HyperFrames và tạo kèm ảnh bìa YouTube đúng font chữ nhận diện thương hiệu.
