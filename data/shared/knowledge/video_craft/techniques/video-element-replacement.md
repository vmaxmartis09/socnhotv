---
id: video-element-replacement
title: Video Element Replacement & AI Inpainting (Thay Thế Vật Thể Trong Video)
status: knowledge
build: 'no'
reproducible_with_our_stack: partial (Cần video inpainting model chuyên biệt)
needs:
- Runway Gen-3 / Ebsynth
implemented_in: []
evidence_videos:
- seq_008
confidence: medium
last_verified: '2026-11-04'
expires_at: '2027-11-04'
tags:
- inpainting
- element-replacement
- vfx
- generative-video
---

# Video-to-Video Multi-Element Replacement (Kỹ Thuật Bóc Tách & Thay Thế Đa Yếu Tố Video)

Tags: motion-mimic | video-to-video | inpainting | localization | lipsync | arcads | gobi

## Là gì
Kỹ thuật lấy một video review người thật (talking head hoặc product demo) đã chứng minh hiệu quả bán hàng (winning ad), sau đó dùng AI để bóc tách và thay thế có chọn lọc một hoặc nhiều lớp trong video:
1. **Thay thế Vật thể / Sản phẩm (Product Replacement)**: Thay sản phẩm trên tay bằng sản phẩm của thương hiệu mình qua SAM 2 tracking + Video Inpainting.
2. **Thay thế Diễn viên / Khuôn mặt (Actor / Face Replacement)**: Tráo mặt nhân vật AI KOC (Neau/LyLy hoặc Bi/Koala) vào cử động của diễn viên gốc qua LivePortrait / Motion Mimic.
3. **Thay thế Bối cảnh (Background Replacement)**: Tách phông xanh ảo (Green Screen Matting) để đổi không gian phòng.
4. **Thay thế Ngôn ngữ & Khẩu hình (Speech & Lip-sync Translation)**: Lồng tiếng bản địa hóa (Việt/Anh/Nhật) và chỉnh khớp khẩu hình môi 100%.

## Vì sao hiệu quả
- **Tận dụng công thức viral có sẵn**: Không cần thử nghiệm lại kịch bản hay góc quay; video gốc đã viral chứng minh kịch bản và cử chỉ đó thu hút người xem.
- **Tốc độ sản xuất vô hạn (Infinite Ad Iteration)**: Từ 1 video ban đầu có thể nhân bản thành 50 biến thể cho 50 sản phẩm khác nhau hoặc 10 thị trường quốc tế trong 1 buổi chiều.

## Ví dụ trong video
- Video `seq_008` (`1403971144535658` - By.Shlabu) @ `t=9.48s -> 29.67s`:
  - Biến đổi liên tục: Chai serum trên tay đổi thành hũ kem dưỡng, background đổi ra biển, áo thun đổi thành áo vest, khuôn mặt biến thành nữ châu Á, và tiếng Anh chuyển sang tiếng Nhật nhép môi trơn tru.

## Cách làm lại trong dự án này (Quy chuẩn `motion-mimic` của Gobi)
- **Quy trình 5 bước theo `.agent/skills/motion-mimic/SKILL.md`**:
  1. **Nạp Video Nguồn**: Đưa video tham chiếu vào `data/projects/<id>/raw/`.
  2. **Trích xuất Cử động (Motion Drive)**: Dùng LivePortrait trích xuất ma trận biểu cảm khuôn mặt và góc nghiêng đầu.
  3. **Áp dụng DNA KOC Gobi**: Nạp ảnh nhân vật chuẩn trong `characters/` (LyLy, Neau hoặc Bi 100cm).
  4. **Xử lý Âm thanh & Thoại**: Đọc kịch bản tiếng Việt bằng OmniVoice `soc-nho` (chuỗi mastering TikTok -14 LUFS, EQ presence +3.5dB @3.2kHz).
  5. **Biên tập xuất bản HyperFrames**: Dựng composition 9:16 có Safe Zone TikTok, tự động thêm phụ đề kinetic và BGM ducking.

## Mức độ tin cậy
Tuyệt đối · Cập nhật: 2026-11-04
