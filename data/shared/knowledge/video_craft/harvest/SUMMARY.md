# Báo Cáo Tổng Hợp Nghiên Cứu Video Craft (Lũy Kế: 31 Mục Đã Duyệt)

- **Thời gian cập nhật**: 04/11/2026
- **Phạm vi**: 31 mục video từ tin nhắn Messenger "Stored" (Gồm Batch 1, Batch 2 và Lô 11 video mới nhất vừa chia sẻ: N01 - N11).
- **Trạng thái thực thi**: 100% hoàn tất phân tích và sàng lọc 31/31 mục.

---

## 1. Thống Kê Tổng Quan Lũy Kế (31 Mục)

| Phân Loại | Số Lượng | Tỷ Lệ | Danh Sách Mục |
|---|---|---|---|
| **Học chuyên sâu (LEARN)** | **18** | 58.1% | Seq 003, 005, 006, 007, 008, 011, 012, 014, 015, 020, N01, N02, N03, N04, N05, N07, N08, N10, N11 |
| **Học một phần & bóc tách phễu (LEARN-PARTIAL)** | **5** | 16.1% | Seq 001, 002, 009, 013, 016 |
| **Ghi nhận Sản phẩm / Thị trường (NOTE-PRODUCT)** | **2** | 6.5% | Seq 004 (Đầm NuNu), Seq 019 (Khung tranh đèn LED Luviare) |
| **Bỏ qua không phù hợp (SKIP-irrelevant)** | **3** | 9.7% | Seq 010 (An ninh mạng), Seq 017 (Game dev 2D), Seq 018 (Game sprite) |
| **Bỏ qua lùa gà / Khóa học Zoom (SKIP-scam)** | **2** | 6.5% | Seq N06 (Zoom 2 ngày YouTube US 100tr), Seq N09 (Zoom 1 buổi video AI Agent) |
| **Chờ kiểm tra / Lỗi truy cập** | **0** | 0.0% | Tỷ lệ xử lý thành công 100% |
| **Tổng cộng đã duyệt** | **31** | 100% | Đã ghi nhận đầy đủ vào `triage.csv`, `accepted.md`, `skipped.md`, `notes.md` |

---

## 2. Top 5 Bài Học Đắt Giá Áp Dụng Ngay Cho Hệ Thống Sóc Nhỏ TV / HyperFrames

### 1. Kiến Trúc Render Video Tất Định Từ Web Code (Duy Luân Dễ Thương - Seq N03)
- **Vấn đề cốt lõi**: Các mô hình video diffusion (Runway, Kling) luôn có tính bất định, méo chữ và khó sửa đổi từng frame.
- **Giải pháp**: Tạo animation bằng web code (HTML5/CSS/GSAP), kiểm soát Virtual Clock của trình duyệt Headless Chrome, xuất frame qua đường ống `FFmpeg image2pipe` và chạy song song đa luồng (multi-worker chunking).
- **Ứng dụng**: Xác nhận tính đúng đắn 100% của kiến trúc **HeyGen HyperFrames Engine** tại `tool/src/socnhotv/video/hyperframes_engine.py`.

### 2. Kỹ Thuật Che Khuất Tiền Cảnh Xóa Bỏ Cảm Giác 'Phẳng AI' (Jolie Mê Xem Phim - Seq N08)
- **Vấn đề**: Video AI thường bị người xem nhận ra ngay vì mọi chi tiết đều nét đều, thiếu chiều sâu quang học.
- **Giải pháp**: Bắt buộc cấu trúc prompt 3 tầng:
  1. *Tiền cảnh (Foreground - Out of focus bokeh)*: Lá cây, ngọn cỏ lướt sát ống kính, vai người.
  2. *Trung cảnh (Midground - In-focus sharp)*: Nhân vật thực hiện hành động chính.
  3. *Hậu cảnh (Background - Atmospheric haze)*: Mờ dần ở phía xa.
- **Ứng dụng**: Tích hợp template 3-layer depth vào bộ sinh prompt của Sóc Nhỏ và AI KOC thời trang.

### 3. Quy Trình Tiền Kiểm Thử Hook Giữ Chân Người Xem Bằng AI (Hong Phuong - Seq N04)
- **Vấn đề**: 80% người xem lướt qua trong 3 giây đầu; nhà sáng tạo chỉ biết video flop sau khi đã xuất bản.
- **Giải pháp**: Sản xuất 3-5 biến thể hook cho cùng 1 video, nạp vào mô hình dự đoán đường cong chú ý theo từng giây (Second-by-Second Attention Curve), dùng LLM gọt giũa từ ngữ thừa trước khi render bản master.
- **Ứng dụng**: Session A (Script) tự động sinh 3 hook A/B/C; Session B chọn hook có điểm dự đoán cao nhất.

### 4. Kịch Bản Tự Sự Nhân Vật Ảo Đời Thường & Phá Bức Tường Thứ 4 (Seq N07)
- **Công thức**: 
  1. *Hook nghịch lý*: "Sáng nay họ khen em tự nhiên nhất nhóm, đâu biết em mới có mặt trên đời 11 phút".
  2. *Vi hành động đời thường*: Dưỡng da, tập gym, uống nước, tương tác với quán cà phê quen.
  3. *Cú lật nhận thức*: Nhìn thẳng ống kính: "Em không có thật đâu, nhưng anh chị vẫn xem tới đây đúng không?".
- **Ứng dụng**: Kịch bản shorts viral cho Sóc Nhỏ (Bi) và KOC LyLy/Neau.

### 5. Infinite Canvas Storyboard & Chống Giật Hình Bằng Transition Foresight (Seq N01)
- **Giải pháp**: Neo nhân vật bằng 3 góc chuẩn (Chính diện 0°, Nghiêng 45°, Góc nghiêng 90°).
- **Transition Foresight**: Lấy 0.5s cuối cảnh trước làm gốc tính toán vector chuyển động cho cảnh kế tiếp, loại bỏ triệt để hiện tượng nhảy khung (jump cut).

---

## 3. Các Mô Hình Phễu "Lùa Gà" Thường Gặp Cần Cảnh Giác

1. **Phễu "Zoom 2 ngày kiếm 100tr/tháng YouTube Mỹ" (Seq N06)**: Dụ dỗ người xem vào phòng Zoom 2 ngày miễn phí với lời hứa x2 x3 thu nhập năm 2026, hoàn toàn không có kỹ thuật thực tế.
2. **Phễu "Giao việc 1 lần cho Agent làm video từ A-Z" (Seq N09)**: Nói chung chung về AI Agent làm video để kéo học viên vào 1 buổi Zoom hướng dẫn trực tiếp.
3. **Phễu "Agent 1 câu lệnh bán triệu đơn" (Seq 001)**: Gán mác AI Agent cho các thao tác ghép ảnh đơn giản để bán khóa học Netlify 899k.
4. **Phễu "50K/tháng có KOC vô tận" (Seq 003)**: Web app bọc ngoài IDM-VTON mã nguồn mở nhưng giật tít đánh lừa người dùng.
5. **Phễu "Comment 333 nhận phần mềm video AI vô hạn" (Seq 009)**: Lấy bản ComfyUI Desktop portable miễn phí để kéo leads vào nhóm kín.

---

## 4. Danh Mục 26 Thẻ Kỹ Thuật Đã Xây Dựng (Techniques Library)

1. `techniques/confession-hook.md`
2. `techniques/in-situ-koc-placement.md`
3. `techniques/rapid-montage-proof.md`
4. `techniques/frictionless-remix-workflow.md`
5. `techniques/split-canvas-lookbook.md`
6. `techniques/sticker-cutout-doodle.md`
7. `techniques/camera-motion-choreography.md`
8. `techniques/dual-node-video-stitching.md`
9. `techniques/video-element-replacement.md`
10. `techniques/local-comfyui-pipeline.md`
11. `techniques/niche-opportunity-index.md`
12. `techniques/walking-outfit-transition.md`
13. `techniques/first-comment-link-routing.md`
14. `techniques/evergreen-shortform-foundations.md`
15. `techniques/360-turntable-catalog.md`
16. `techniques/3-layer-knowledge-retention.md`
17. `techniques/high-status-color-contrast.md`
18. `techniques/transition-foresight-continuity.md`
19. `techniques/multi-agent-broll-orchestration.md`
20. `techniques/deterministic-web-to-video-rendering.md`
21. `techniques/pre-publish-hook-retention-prediction.md`
22. `techniques/7-platform-automated-syndication-and-scope-locked-crm.md`
23. `techniques/virtual-influencer-paradox-storytelling.md`
24. `techniques/foreground-occlusion-spatial-depth-layering.md`
25. `techniques/cinematography-camera-mechanics-cheatsheet.md`
26. `techniques/channel-style-cloning-template-pipeline.md`
