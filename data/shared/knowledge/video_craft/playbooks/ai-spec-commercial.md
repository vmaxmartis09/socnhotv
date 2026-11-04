# Playbook 09: Sản Xuất Phim Quảng Cáo Thương Hiệu Chuẩn Điện Ảnh (AI Spec Commercial Mastery)

> Áp dụng cho: TVC quảng cáo sản phẩm cao cấp, video giới thiệu thương hiệu, chiến dịch ra mắt sản phẩm mới  
> Mục tiêu cốt lõi: Đạt đẳng cấp hình ảnh điện ảnh 4K, vượt qua định kiến "rác AI", thuyết phục khách hàng doanh nghiệp trả giá cao ($1,000 - $5,000/video).

---

## 1. Danh Sách Kỹ Thuật Sử Dụng
- [`commercial-spec-ai-animation`](../techniques/commercial-spec-ai-animation.md): Điều phối mô hình 3D kết hợp Kling 1.5 Start/End Frame hai đầu.
- [`motion-brush-trajectory-steering`](../techniques/motion-brush-trajectory-steering.md): Điều khiển chính xác quỹ đạo chuyển động camera và các thành phần hạt/khói/nước.
- [`ai-video-realism-anti-artifact`](../techniques/ai-video-realism-anti-artifact.md): Phủ lớp hạt quang học 35mm, triệt tiêu viền nhựa và hòa sắc LUT điện ảnh.
- [`cinematography-camera-mechanics-cheatsheet`](../techniques/cinematography-camera-mechanics-cheatsheet.md): 5 cú máy kinh điển (Dolly Zoom, Orbit, Crane Shot, Whip Pan, Tracking).
- [`high-status-color-contrast`](../techniques/high-status-color-contrast.md): Bảng màu tương phản sang trọng (Teal/Amber, Obsidian/Gold).

---

## 2. Quy Trình Sản Xuất 4 Giai Đoạn (4-Phase Production Pipeline)

### Giai đoạn 1: Tiền kỳ & Concept Định Hướng (Pre-Production & Moodboard)
- Xác định DNA thương hiệu: Giá trị cốt lõi, bảng màu chủ đạo (Brand Kit), phong cách âm nhạc.
- Xây dựng Storyboard phân cảnh 6–8 shot:
  - Shot 1: Khởi đầu bí ẩn (Macro chi tiết kim loại/ánh sáng phản chiếu).
  - Shot 2: Cú máy Orbit hé lộ đường nét sản phẩm.
  - Shot 3: Tương tác vật lý (nước bắn, khói bay, hạt bụi vàng chuyển động).
  - Shot 4: Nhân vật hoặc bối cảnh thế giới tương lai.
  - Shot 5: Chuyển cảnh tăng tốc (Whip Pan) đến cao trào.
  - Shot 6: Khóa lại bằng Logo Sting thương hiệu sang trọng.

### Giai đoạn 2: Pre-vis Camera & Khóa Khung Hình Hai Đầu (Blocking & Keyframing)
- Sử dụng Blender tạo chuyển động camera chuẩn xác: độ dài tiêu cự (Focal Length 50mm hoặc 85mm), tốc độ di chuyển đều (Linear hoặc Ease In/Out).
- Render Keyframe Start và End qua Flux.1 Dev với độ sắc nét tuyệt đối.

### Giai đoạn 3: Sinh Chuyển Động AI (Motion Interpolation)
- Nạp 2 khung hình vào Kling 1.5 Professional Mode.
- Thiết lập Motion Index ở mức 3–4 để giữ cho kim loại và đá quý luôn rắn rỏi, không bị dẻo như thạch.
- Sử dụng Motion Brush tô riêng vùng khói/ánh sáng chuyển động nhanh, giữ cố định vùng thân sản phẩm.

### Giai đoạn 4: Hậu kỳ Âm Thanh Đa Lớp & Master Phim (Post & Sound Design)
- Lắp ráp composition trên HeyGen HyperFrames:
  - Phủ lớp hạt nhiễu quang học `35mm Film Grain` 7% độ mờ.
  - Đồng bộ âm thanh Foley: Tiếng lách cách kim loại, tiếng rít gió, tiếng nổ sub-bass tại các điểm chuyển cảnh.
  - Xuất bản chuẩn ProRes 422HQ hoặc MP4 H.264 4K 60Mbps.

---

## 3. Khuôn Mẫu Kịch Bản TVC 30s (Luxury Brand Commercial Template)

```
[00:00 - 00:05] (Shot 1 - The Spark):
Cận cảnh macro bề mặt kim loại vàng chải xước. Một tia sáng lướt qua để lại vệt phản quang lấp lánh.
SFX: Âm thanh ngân vang pha lê (Crystal chime) + tiếng bass sâu dần.

[00:05 - 00:12] (Shot 2 - The Silhouette):
Cú máy Orbit 90 độ hé lộ toàn bộ dáng vẻ tinh xảo của sản phẩm giữa không gian đen tuyền obsidian.
VO trầm ấm: "Đẳng cấp không đến từ sự phô trương, mà ẩn giấu trong từng đường nét hoàn mỹ."

[00:12 - 00:20] (Shot 3 - Dynamic Elements):
Những giọt nước hoặc hạt bụi vàng bay lơ lửng xung quanh sản phẩm theo chuyển động slow-motion 120fps.
SFX: Tiếng nước rơi tí tách siêu thực, nhạc nền đẩy lên cao trào.

[00:20 - 00:26] (Shot 4 - Climax Transition):
Camera lùi nhanh (Punch-out) ra bối cảnh cung điện hoặc sảnh triển lãm kiến trúc hiện đại.
VO: "Nơi công nghệ hòa quyện cùng nghệ thuật chế tác vượt thời gian."

[00:26 - 00:30] (Shot 5 - Brand Lockup):
Sản phẩm đứng tĩnh ở trung tâm, logo thương hiệu màu vàng kim hiện ra sắc nét cùng slogan.
SFX: Tiếng gong trầm ấm ngân dài kết thúc.
```

---

## 4. Tiêu Chuẩn Nghiệm Thu Khắt Khe (Quality Benchmark)
- [ ] 0% hiện tượng biến dạng cấu trúc (Geometric morphing) trên bề mặt sản phẩm.
- [ ] Phản chiếu ánh sáng trên mặt kính/kim loại tuân thủ đúng định luật quang học.
- [ ] Âm thanh Foley và BGM phối khí chuẩn Dolby/Stereo -14 LUFS.
- [ ] Logo thương hiệu hiển thị rõ ràng, không bị mờ hay biến dạng viền.
