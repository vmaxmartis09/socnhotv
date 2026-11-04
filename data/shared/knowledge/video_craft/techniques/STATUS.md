# Trạng Thái Kho Kỹ Thuật Video Craft (Techniques Status)

- **Cập nhật tự động**: 2026-11-04 23:18
- **Tổng số kỹ thuật**: 26
- **Đã tích hợp vào Studio (`in-studio`)**: **14** thẻ
- **Đang thử nghiệm (`prototyped`)**: 0 thẻ
- **Kho kiến thức tham chiếu (`knowledge`)**: 12 thẻ
- **Hết hạn / Cần đánh giá lại (`needs-review`)**: 0 thẻ

---

## 1. Kỹ Thuật Đã Vào Studio (`in-studio` - Sẵn Sàng Sản Xuất)

| ID | Tên Kỹ Thuật | Tái Lập Được? | Nơi Triển Khai | Bằng Chứng (Video ID) |
| :--- | :--- | :---: | :--- | :---: |
| `3-layer-knowledge-retention` | **3-Layer Knowledge Retention & Origin Traceability** | ✅ yes | `tool/src/socnhotv/video/craft/lint.py`, `data/shared/knowledge/video_craft/playbooks/depth-and-composition.md` | seq_016 |
| `camera-motion-choreography` | **Camera Motion Choreography (Vũ Đạo Chuyển Động Camera 5 Cú Máy Kinh Điển)** | ✅ yes | `tool/src/socnhotv/video/craft/camera.py`, `data/shared/knowledge/video_craft/playbooks/camera-and-transitions.md` | seq_006 |
| `cinematography-camera-mechanics-cheatsheet` | **Cinematography & Camera Mechanics Cheatsheet** | ✅ yes | `tool/src/socnhotv/video/craft/camera.py`, `data/shared/knowledge/video_craft/playbooks/camera-and-transitions.md` | seq_014 |
| `confession-hook` | **Confession Hook / Secret Reveal (Hook Thú Nhận Bí Mật Hậu Trường)** | ✅ yes | `tool/src/socnhotv/video/craft/hooks.py`, `data/shared/knowledge/video_craft/playbooks/hook-and-retention.md` | seq_001 |
| `deterministic-web-to-video-rendering` | **Deterministic Web-to-Video Rendering Architecture** | ✅ yes | `tool/src/socnhotv/video/hyperframes_engine.py` | seq_N03 |
| `evergreen-shortform-foundations` | **Evergreen Shortform Foundations (Cấu Trúc Video Ngắn Thường Xanh)** | ✅ yes | `tool/src/socnhotv/video/craft/lint.py`, `data/shared/knowledge/video_craft/playbooks/hook-and-retention.md` | seq_011 |
| `first-comment-link-routing` | **First-Comment Link Routing & Zero-Penalty Affiliate Funnel** | ✅ yes | `tool/src/socnhotv/social/publishing_templates.py`, `data/shared/knowledge/video_craft/playbooks/affiliate-links-and-first-comment.md` | seq_013 |
| `foreground-occlusion-spatial-depth-layering` | **Foreground Occlusion & 3-Layer Spatial Depth Partitioning** | ✅ yes | `tool/src/socnhotv/video/craft/depth.py`, `data/shared/knowledge/video_craft/playbooks/depth-and-composition.md` | seq_N08 |
| `high-status-color-contrast` | **High-Status Color Contrast (Bảng Màu Tương Phản Chuẩn Sang Trọng)** | ✅ yes | `tool/src/socnhotv/video/craft/lint.py`, `data/shared/knowledge/video_craft/playbooks/depth-and-composition.md` | seq_016 |
| `in-situ-koc-placement` | **In-Situ KOC Placement (Đặt Nhân Vật KOC Vào Bối Cảnh Đời Thực)** | ✅ yes | `tool/src/socnhotv/video/craft/depth.py`, `data/shared/knowledge/video_craft/playbooks/koc-review-and-sales.md` | seq_002 |
| `pre-publish-hook-retention-prediction` | **Pre-Publish Hook Retention Prediction & Heuristic Scoring** | ✅ yes | `tool/src/socnhotv/video/craft/hooks.py`, `tool/src/socnhotv/video/craft/lint.py`, `data/shared/knowledge/video_craft/playbooks/hook-and-retention.md` | seq_N04 |
| `rapid-montage-proof` | **Rapid Montage Proof (Cắt Ghép Bằng Chứng Dồn Dập)** | ✅ yes | `tool/src/socnhotv/video/craft/transitions.py`, `data/shared/knowledge/video_craft/playbooks/camera-and-transitions.md` | seq_003 |
| `transition-foresight-continuity` | **Transition Foresight & Motion Continuity (Chuyển Cảnh Tiên Liệu Hướng Chuyển Động)** | ✅ yes | `tool/src/socnhotv/video/craft/transitions.py`, `data/shared/knowledge/video_craft/playbooks/camera-and-transitions.md` | seq_N01 |
| `virtual-influencer-paradox-storytelling` | **Virtual Influencer Paradox Storytelling & 4th Wall Break** | ✅ yes | `tool/src/socnhotv/video/craft/hooks.py`, `data/shared/knowledge/video_craft/playbooks/hook-and-retention.md` | seq_N07 |

---

## 2. Hàng Chờ Triển Khai (`prototyped` hoặc `knowledge` ưu tiên cao)

| ID | Tên Kỹ Thuật | Khả Năng Tái Lập | Công Cụ Cần | Đánh Giá Ưu Tiên |
| :--- | :--- | :--- | :--- | :---: |
| `360-turntable-catalog` | 360 Turntable Catalog (Bàn Xoay Sản Phẩm 360 Độ) | partial (Cần quay sẵn video bàn xoay sản phẩm hoặc 3D model render loop) | Blender / 3D Model / Video quay sản phẩm thực tế | MEDIUM |
| `channel-style-cloning-template-pipeline` | Channel Style Cloning & Template Pipeline | yes (Định hình style thông qua template HyperFrames JSON + CSS) | HyperFrames, Template Engine | HIGH |
| `frictionless-remix-workflow` | Frictionless Remix Workflow (Quy Trình Tái Chế B-Roll & Hook Không Ma Sát) | yes | Asset Library, HyperFrames | HIGH |
| `multi-agent-broll-orchestration` | Multi-Agent B-Roll Orchestration & Parallel Asset Generation | yes | Python asyncio, AI Providers | HIGH |
| `split-canvas-lookbook` | Split Canvas Lookbook (Khung Hình Chia Đôi / Chia Ba Lookbook) | yes | HyperFrames Layout | HIGH |
| `sticker-cutout-doodle` | Sticker Cutout & Motion Doodle (Viền Sticker Trắng Cắt Rời & Nét Vẽ Hoạt Hình) | yes | HyperFrames SVG, CSS drop-shadow | HIGH |
| `walking-outfit-transition` | Walking Outfit Transition (Chuyển Đổi Trang Phục Theo Bước Chân) | yes | HyperFrames, GSAP beat sync | HIGH |

---

## 3. Kiến Thức Tham Chiếu / Ngoài Phạm Vi (`knowledge` / `build: no`)

| ID | Tên Kỹ Thuật | Lý Do Giữ Mức Kiến Thức | Hết Hạn |
| :--- | :--- | :--- | :---: |
| `7-platform-automated-syndication-and-scope-locked-crm` | 7-Platform Automated Syndication & Scope-Locked CRM | partial (Social scheduler hỗ trợ queue đa kênh; CRM webhook ngoài phạm vi video engine) | 2027-11-04 |
| `dual-node-video-stitching` | Dual-Node Video Stitching (Nối Đoạn Video 2 Đầu Bằng AI) | partial (Cần mô hình video generation ngoài có API image-to-video/extend như Kling/Runway) | 2027-11-04 |
| `local-comfyui-pipeline` | Local ComfyUI Pipeline For Generative B-Roll | partial (Đòi hỏi GPU cục bộ chuyên dụng và cài ComfyUI riêng; hiện dự án ưu tiên Tier 0 local DNA + cloud fallback) | 2027-11-04 |
| `niche-opportunity-index` | Niche Opportunity Index & Market Gap Discovery | partial (Mô hình tính điểm thị trường bằng tay/kịch bản; ngoài core video engine) | 2027-11-04 |
| `video-element-replacement` | Video Element Replacement & AI Inpainting (Thay Thế Vật Thể Trong Video) | partial (Cần video inpainting model chuyên biệt) | 2027-11-04 |
