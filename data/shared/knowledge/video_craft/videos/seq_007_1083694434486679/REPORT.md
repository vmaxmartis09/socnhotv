# Báo cáo Phân tích Video — Seq 007

- **ID Video**: `1083694434486679`
- **Tiêu đề gốc**: "LÀM VIDEO AI BÁN QUẦN ÁO HÀNG LOẠT – KHÔNG CẦN MẪU THẬT, KHÔNG CẦN TỰ QUAY!"
- **Giảng viên**: Thân Ca (kênh Jolie Mê Xem Phim)
- **Quyết định**: `LEARN` (Quy trình sản xuất hàng loạt video thời trang affiliate qua Canvas node-graph và kỹ thuật ghép nối 2-node Kling 1.5).

---

## 1. Tóm tắt phân tích
Video dài gần 4 phút (233.01s), hướng dẫn thực hành từng bước (step-by-step tutorial) trên nền tảng **Infinite Canvas** để tạo video người mẫu AI review quần áo cho kênh bán hàng affiliate:
- **Bước 1**: Nạp ảnh khuôn mặt và ảnh dáng người mẫu đã định sẵn.
- **Bước 2**: Nạp ảnh bộ trang phục (quần áo chụp phẳng hoặc trên ma-nơ-canh).
- **Bước 3**: Chạy node Thử đồ ảo (Virtual Try-on) ở chuẩn 2K, tỷ lệ dọc 9:16. So sánh kỹ hoa văn vải, đường may để bảo đảm tính chân thực.
- **Bước 4 & 5 (Kỹ thuật mấu chốt)**: Chia video 30 giây thành **2 Node Video Kling 1.5** (mỗi node 15 giây):
  - Node 1: Góc quay toàn cảnh 1-12 (mẫu dạo phố).
  - Node 2: Lấy frame cuối của Node 1 làm frame đầu -> chạy góc quay cận cảnh 16-24 (xoay người, chi tiết phom áo).
- **Bước 6**: Ghép nối 2 video thành clip 30 giây mượt mà hoàn chỉnh.

---

## 2. Công thức Blueprint
Thời lượng: **30s video thành phẩm** (tổng video hướng dẫn 233s) | Công nghệ: **Infinite Canvas + Kling 1.5**

```
GIAI ĐOẠN 1: CHUẨN BỊ ASSET (Canvas Ingestion)
  ├─ Node Input 1: Master Headshot (Ảnh chân dung mẫu)
  ├─ Node Input 2: Master Body Pose (Dáng đứng chuẩn)
  └─ Node Input 3: Flat-lay Garment (Ảnh áo/váy phẳng)

GIAI ĐOẠN 2: THỬ ĐỒ ẢO 2K (Virtual Try-on Node)
  └─ Output: Ảnh tĩnh 2K người mẫu mặc hoàn chỉnh trang phục, tỉ lệ 9:16

GIAI ĐOẠN 3: SINH VIDEO ĐA PHÂN ĐOẠN (Dual-Node Kling 1.5)
  ├─ Node Video 1 (15s): Kling 1.5 Catwalk (Camera dạo phố góc 1-12)
  │    └─ Extract Last-Frame (t=14.9s)
  └─ Node Video 2 (15s): Kling 1.5 Detail Turn (Frame đầu = Last-Frame, góc 16-24)

GIAI ĐOẠN 4: GHÉP NỐI & DỰNG HOÀN CHỈNH (Assembly)
  └─ Nối Clip 1 + Clip 2 trên Timeline HyperFrames -> Xuất MP4 30s
```

---

## 3. Những gì nên học
1. **[Dual-Node Video Stitching (Kỹ thuật Nối Video 2 Phân Đoạn)](file:///Volumes/Data/socnhotv/data/shared/knowledge/video_craft/techniques/dual-node-video-stitching.md)**: Không bao giờ ép AI sinh 1 clip dài >20s (sẽ bị lỗi biến dạng cơ thể). Luôn chia thành 2 clip 15s nối nhau qua cơ chế *Last-Frame to First-Frame Continuity*.
2. **[Visual Quality Inspection Checklist](file:///Volumes/Data/socnhotv/data/shared/knowledge/video_craft/techniques/visual-quality-checklist.md)**: Thao tác phóng to 200% kiểm tra chi tiết hoa văn, phom dáng và khớp cổ trước khi bấm render video để tránh lãng phí credit GPU.
3. **[Infinite Canvas Mental Model](file:///Volumes/Data/socnhotv/data/shared/knowledge/video_craft/techniques/infinite-canvas-workflow.md)**: Trực quan hóa quy trình dưới dạng sơ đồ hộp và dây nối (nodes & wires) giúp nhân sự dễ dàng kiểm soát luồng dữ liệu sản phẩm.

---

## 4. Những gì nên làm TỐT HƠN (5 Cải tiến kiểm thử A/B)
1. **Tự động hóa hoàn toàn bước ghép nối bằng HyperFrames**:
   - *Hiện trạng trong video*: Giảng viên phải tải thủ công 2 video 15s về máy tính, rồi mở phần mềm CapCut/Premiere lên kéo ghép thủ công.
   - *Cải tiến của SocNhoTV*: HyperFrames tự động bắt output URL của 2 node, tự xếp vào timeline GSAP và render ra video 30s chỉ bằng 1 dòng lệnh CLI hoặc API `submit_render`.
2. **Thêm Audio Mastering & BGM Auto-Ducking**:
   - *Cải tiến*: HyperFrames tự động chèn voiceover `soc-nho` hoặc `neau` đọc review, đồng thời tự động giảm âm lượng nhạc nền (Ducking -6dB) khi có tiếng nói.
3. **Thêm Kinetic Subtitles & Safe-Zone Overlay**:
   - *Cải tiến*: Bổ sung phụ đề karaoke và nhãn giá sản phẩm theo vùng an toàn TikTok.
4. **Tối ưu thời gian chờ Render**:
   - *Cải tiến*: Sử dụng background queue (`RenderJob` của Session A) để người dùng có thể submit hàng loạt 20 sản phẩm cùng lúc mà không phải ngồi đợi từng video.
5. **Thêm thẻ chuyển động Callout sản phẩm ở đoạn 15s-30s**:
   - *Cải tiến*: Ở đoạn cận cảnh, thêm đường vẽ doodle hoặc icon Morphicon chỉ vào cúc áo, túi áo hoặc chất liệu vải.

---

## 5. Cách tái tạo cho Dự án SocNhoTV & Gobi Social
- Đã tạo Technique Card:
  - `techniques/dual-node-video-stitching.md`
- Đã cập nhật vào `harvest/accepted.md`.
- Đã gửi đề xuất quy trình tự động ghép 2-clip cho Session A (`requests_for_A.md`).
