# Tài liệu & Nguồn truy vết (Sources & Verification) — Seq 008

Video ID: `1403971144535658` | Tiêu đề: "Arcads video element replacement" | Tác giả: By.Shlabu

## Chuỗi truy vết 3 tầng (3-Tier Investigation)

### Tầng 1: Nền tảng Arcads AI
1. **Arcads.ai**:
   - Nền tảng AI UGC hàng đầu cho thương mại điện tử quốc tế (eCommerce & DTC Brands).
   - Khả năng: Nhận 1 video review có sẵn -> Tự động sinh ra hàng trăm biến thể quảng cáo (Infinite variations) bằng cách tráo đổi diễn viên AI, giọng đọc, ngôn ngữ và vật thể cầm trên tay.
   - Chi phí thương mại: ~100$ – 300$/tháng cho các gói doanh nghiệp.
   - Độ tin cậy: Tuyệt đối.

### Tầng 2: Công nghệ cốt lõi đằng sau Video-to-Video Replacement
2. **Video Inpainting & Handheld Object Tracking**:
   - Sử dụng mô hình SAM 2 (Segment Anything Model 2) để tracking chính xác vật thể trên tay người nói theo từng frame.
   - Inpaint vật thể mới (lọ serum, chai nước) vào vùng bounding box chuyển động mà không làm biến dạng ngón tay người cầm.
   - Bằng chứng tài liệu:
     - Meta AI: *SAM 2: Segment Anything in Images and Videos* (2024).
     - Repo: `https://github.com/facebookresearch/sam2`
   - Độ tin cậy: Rất cao.

3. **Motion Mimic & Expressive Lip-sync**:
   - AniPortrait / LivePortrait: Nhận video gốc làm motion driver, áp dụng lên khuôn mặt nhân vật mới.
   - HeyGen Video Translation API: Dịch ngôn ngữ tự động (tiếng Anh sang tiếng Nhật, tiếng Việt) và tái tạo lại cử động môi khớp từng âm vị (Phoneme-level lip movement).
   - Độ tin cậy: Rất cao.

### Tầng 3: Đối chiếu với Kỹ năng `motion-mimic` của SocNhoTV
4. **Sự tương đồng tuyệt đối**:
   - Trong workspace SocNhoTV, kỹ năng `.agent/skills/motion-mimic/SKILL.md` được xây dựng để thực hiện chính xác quy trình này cho nhân vật KOC LyLy và Neau.
   - Thay vì trả hàng trăm đô la cho Arcads.ai, hệ thống Gobi Social tận dụng:
     1. SAM 2 + ComfyUI để tracking và thay thế sản phẩm.
     2. OmniVoice SOTA đọc kịch bản tiếng Việt.
     3. HyperFrames Engine để dựng composition 9:16 có Safe Zone TikTok.

## Bảng tổng hợp nguồn

| URL / Định danh | Loại | Điều học được | Độ tin cậy |
|---|---|---|---|
| `https://www.facebook.com/share/r/19f81rzRTd/` | Video gốc | Minh họa trực quan 4 lớp thay thế: Sản phẩm, Bối cảnh, Nhân vật, Ngôn ngữ | Tuyệt đối |
| `https://www.arcads.ai/` | Nền tảng thương mại | Mô hình kinh doanh "1 video ra vô hạn quảng cáo" cho DTC | Rất cao |
| `https://github.com/facebookresearch/sam2` | Open-source SOTA | Cơ chế tracking và segment vật thể trong video của SAM 2 | Rất cao |
| `.agent/skills/motion-mimic/SKILL.md` | Skill nội bộ dự án | Quy trình motion-mimic cho KOC Gobi dựng qua HyperFrames | Tuyệt đối |
