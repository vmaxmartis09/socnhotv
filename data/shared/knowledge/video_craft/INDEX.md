# Mục Lục Tri Thức Sản Xuất Video Craft (Video Craft Knowledge Index)

> **Cập nhật:** 2026-11-04 23:30  
> **Phiên phụ trách:** Session D (Messenger Stored) & Session D2 (Research Analyst - Mode T)  
> **Nguyên tắc:** 100% tài liệu được kiểm chứng qua video thực tế, có nguồn độc lập, không suy đoán.

---

## 1. Cấu Trúc Kho Tri Thức (Knowledge Architecture)

```
data/shared/knowledge/video_craft/
├── INDEX.md                     # Mục lục trung tâm toàn bộ kho tri thức (file này)
├── tools_landscape.md           # Bản đồ đối chiếu công cụ AI Video toàn cầu vs Stack nội bộ
├── requests_for_A.md            # Đề xuất template/engine gửi Session A
├── requests_for_B.md            # Đề xuất sản phẩm/dữ liệu gửi Session B
├── requests_for_C.md            # Đề xuất phân phối/lịch đăng gửi Session C
├── techniques/                  # 32 thẻ kỹ thuật độc lập (Technique Cards)
│   ├── STATUS.md                # Bảng trạng thái triển khai (in-studio / knowledge)
│   ├── registry.json            # Machine-readable schema registry
│   └── *.md                     # Chi tiết từng kỹ thuật
├── playbooks/                   # 10 kịch bản chiến lược sản xuất (Playbooks)
├── workflows/                   # 3 quy trình tái lập từng bước (Workflows)
├── tiktok/                      # Dữ liệu thu thập & sàng lọc diện rộng TikTok (Mode T)
│   ├── channels.jsonl           # 7 kênh AI Video mục tiêu
│   ├── channels_triage.csv      # Bảng thẩm định kênh
│   ├── queue.jsonl              # 282 video thu hoạch
│   ├── triage.csv               # Bảng phân loại 282 video (113 LEARN / 169 SKIP)
│   ├── skipped.md               # Nhật ký loại bỏ video lùa gà / lỗi thời
│   ├── state.json               # Checkpoint trạng thái quét
│   ├── CHANNEL_MAP.md           # Bản đồ kênh theo chuyên môn & độ tin cậy
│   └── SUMMARY.md               # Báo cáo tổng hợp điều hành đợt quét Mode T
└── videos/                      # Báo cáo phân tích chuyên sâu (G1→G6 + H5)
    ├── <video_id>/              # Gói 7 file (meta, transcript, scenes, shotlist, metrics, sources, REPORT)
```

---

## 2. Danh Mục Kỹ Thuật Đã Kiểm Chứng (32 Technique Cards)

### 2.1. Nhóm Đã Tích Hợp Vào Studio (`in-studio` - 15 thẻ)
1. [`3-layer-knowledge-retention`](techniques/3-layer-knowledge-retention.md): Lưu trữ tri thức 3 lớp và truy nguyên nguồn gốc
2. [`camera-motion-choreography`](techniques/camera-motion-choreography.md): Vũ đạo chuyển động camera 5 cú máy kinh điển
3. [`cinematography-camera-mechanics-cheatsheet`](techniques/cinematography-camera-mechanics-cheatsheet.md): Sổ tay thông số kỹ thuật điện ảnh và ống kính
4. [`confession-hook`](techniques/confession-hook.md): Hook thú nhận bí mật hậu trường phá vỡ phòng thủ người xem
5. [`deterministic-web-to-video-rendering`](techniques/deterministic-web-to-video-rendering.md): Kiến trúc render video tất định bằng HTML5/CSS/GSAP
6. [`evergreen-shortform-foundations`](techniques/evergreen-shortform-foundations.md): Cấu trúc video ngắn thường xanh giữ chân lâu dài
7. [`first-comment-link-routing`](techniques/first-comment-link-routing.md): Phễu gắn link affiliate qua bình luận đầu tiên không bóp reach
8. [`foreground-occlusion-spatial-depth-layering`](techniques/foreground-occlusion-spatial-depth-layering.md): Phân tầng không gian 3 lớp tiền cảnh - trung cảnh - hậu cảnh
9. [`high-status-color-contrast`](techniques/high-status-color-contrast.md): Bảng màu tương phản chuẩn sang trọng tăng giá trị cảm nhận
10. [`in-situ-koc-placement`](techniques/in-situ-koc-placement.md): Đặt nhân vật KOC AI vào bối cảnh đời thực
11. [`llm-script-to-timeline-automation`](techniques/llm-script-to-timeline-automation.md): Biên dịch tự động kịch bản JSON sang dòng thời gian HyperFrames
12. [`pre-publish-hook-retention-prediction`](techniques/pre-publish-hook-retention-prediction.md): Dự đoán và chấm điểm khả năng giữ chân của hook trước khi render
13. [`rapid-montage-proof`](techniques/rapid-montage-proof.md): Cắt ghép bằng chứng dồn dập trong 2 giây đầu
14. [`transition-foresight-continuity`](techniques/transition-foresight-continuity.md): Chuyển cảnh tiên liệu hướng chuyển động quang học
15. [`virtual-influencer-paradox-storytelling`](techniques/virtual-influencer-paradox-storytelling.md): Nghệ thuật kể chuyện phá vỡ bức tường thứ 4 của KOC ảo

### 2.2. Nhóm Tri Thức Nổi Bật Sẵn Sàng Triển Khai (`knowledge` - 17 thẻ tiêu biểu)
- [`commercial-spec-ai-animation`](techniques/commercial-spec-ai-animation.md): Làm phim quảng cáo 3D thương mại cao cấp với Kling 1.5 hai đầu
- [`motion-brush-trajectory-steering`](techniques/motion-brush-trajectory-steering.md): Điều khiển đa quỹ đạo chuyển động camera và hiệu ứng hạt
- [`virtual-try-on-pipeline`](techniques/virtual-try-on-pipeline.md): Thử đồ ảo KOC thời trang giữ nguyên 100% hoa văn và chất vải
- [`tiered-channel-automation-engine`](techniques/tiered-channel-automation-engine.md): Mô hình vận hành kênh tự động 4 tầng phân tách độc lập
- [`ai-video-realism-anti-artifact`](techniques/ai-video-realism-anti-artifact.md): Triệt tiêu lỗi méo hình và da sáp nhựa bằng hạt phim 35mm
- [`walking-outfit-transition`](techniques/walking-outfit-transition.md): Chuyển đổi trang phục theo nhịp bước chân người mẫu
- [`split-canvas-lookbook`](techniques/split-canvas-lookbook.md): Bố cục khung hình chia đôi / chia ba lookbook
- [`sticker-cutout-doodle`](techniques/sticker-cutout-doodle.md): Viền sticker trắng cắt rời và nét vẽ doodle hoạt hình
- [`360-turntable-catalog`](techniques/360-turntable-catalog.md): Bàn xoay sản phẩm 360 độ góc nhìn toàn diện
- [`channel-style-cloning-template-pipeline`](techniques/channel-style-cloning-template-pipeline.md): Nhân bản phong cách kênh thành template HyperFrames
- [`frictionless-remix-workflow`](techniques/frictionless-remix-workflow.md): Quy trình tái chế B-Roll và Hook không ma sát
- [`multi-agent-broll-orchestration`](techniques/multi-agent-broll-orchestration.md): Điều phối Agent sinh B-roll song song đa luồng

---

## 3. Danh Mục Chiến Lược Sản Xuất (10 Playbooks)

1. [`hook-and-retention`](playbooks/hook-and-retention.md): Nghệ thuật Hook 3 giây và duy trì tỷ lệ giữ chân
2. [`camera-and-transitions`](playbooks/camera-and-transitions.md): Vũ đạo chuyển động máy quay và kỹ thuật chuyển cảnh
3. [`depth-and-composition`](playbooks/depth-and-composition.md): Bố cục không gian 3 lớp và màu sắc điện ảnh
4. [`koc-review-and-sales`](playbooks/koc-review-and-sales.md): Video KOC AI review sản phẩm chuyển đổi cao
5. [`affiliate-links-and-first-comment`](playbooks/affiliate-links-and-first-comment.md): Chiến lược gắn link tiếp thị liên kết an toàn
6. [`ai-workflow-comfyui-and-tools`](playbooks/ai-workflow-comfyui-and-tools.md): Thiết lập pipeline ComfyUI tạo tài sản hình ảnh
7. [`yt-animation-episode`](playbooks/yt-animation-episode.md): Sản xuất tập phim hoạt hình 3D Sóc Nhỏ (Bi) & Koala
8. [`tiktok-ai-vton`](playbooks/tiktok-ai-vton.md): Video KOC thời trang ảo & Virtual Try-On chuyển đổi giỏ hàng
9. [`ai-spec-commercial`](playbooks/ai-spec-commercial.md): Phim quảng cáo thương hiệu cao cấp chuẩn điện ảnh 4K
10. [`faceless-channel-scaling`](playbooks/faceless-channel-scaling.md): Vận hành mạng lưới kênh tự động hoá quy mô lớn

---

## 4. Danh Mục Quy Trình Tái Lập Từng Bước (3 Workflows)

1. [`vton-flux-catvton`](workflows/vton-flux-catvton.md): Quy trình ghép trang phục ảo lên người mẫu KOC AI
2. [`spec-commercial-kling-comfyui`](workflows/spec-commercial-kling-comfyui.md): Quy trình làm phim quảng cáo 3D với Blender + Kling 1.5
3. [`faceless-tts-hyperframes`](workflows/faceless-tts-hyperframes.md): Quy trình sản xuất video Faceless hoàn chỉnh qua OmniVoice + HyperFrames

---

## 5. Báo Cáo Phân Tích Chuyên Sâu Các Video Điểm Ngọt (Deep Dive Reports)

| ID Video | Tác Giả | Chỉ Số Thực Tế | Kỹ Thuật Đúc Kết | Báo Cáo Chi Tiết |
| :--- | :--- | :--- | :--- | :---: |
| `7681660841434926354` | @ddoquynhtram.magentx | 99.1K views · 4575 likes | Virtual Try-On, CatVTON, Split Lookbook | [Xem REPORT](videos/7681660841434926354/REPORT.md) |
| `7695663938083507464` | @70.ai.studio | 88s TVC · Cinematic | Spec Commercial 3D, Two-Frame Conditioning | [Xem REPORT](videos/7695663938083507464/REPORT.md) |
| `7694697264454962440` | @magentx.ai | 22.5K views · 687 likes | Multi-Angle Virtual KOC, Consistent Face | [Xem REPORT](videos/7694697264454962440/REPORT.md) |
| `7702553918156328213` | @anongvn | 21.0K views · 850 likes | 4-Tier Channel Automation Engine | [Xem REPORT](videos/7702553918156328213/REPORT.md) |
| `7693503813071703297` | @ngoc.agi | 7.0K views · 209 likes | Kling 1.5 Motion Brush, Parallax Dynamic | [Xem REPORT](videos/7693503813071703297/REPORT.md) |
| `7697472862633921812` | @bahuy.henry | 101 views · Timeline | Claude Script to Timeline Assembly | [Xem REPORT](videos/7697472862633921812/REPORT.md) |

---

## 6. Giao Thức Phối Hợp Đa Session
- **Khóa cố vấn (Advisory Lock):** Mọi thao tác sửa đổi file chung trong `video_craft/` đều phải kiểm tra và tạo khóa `mkdir data/shared/knowledge/video_craft/.lock`, đọc lại nội dung trước khi ghi, và giải phóng khóa `rmdir` ngay sau khi hoàn thành.
- **Tiêu chuẩn chất lượng:** Mọi tài liệu kỹ thuật đều có dẫn chứng video ID thực tế, cấu hình thông số có thể thực thi được ngay bằng mã nguồn dự án, và được liên kết chéo hai chiều (bi-directional links).
