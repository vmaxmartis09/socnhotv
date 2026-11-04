# BẢN ĐỒ DỮ LIỆU (DATA DIRECTORY)

Tài liệu định vị các kho dữ liệu, tri thức và assets trong dự án SocNhoTV.

---

## 1. Kho Tri Thức Video Thực Chiến (`data/shared/knowledge/video_craft/`)
- **26 Thẻ Kỹ Thuật (Techniques):** `data/shared/knowledge/video_craft/techniques/*.md`
- **Catalog Máy Đọc (Registry):** `data/shared/knowledge/video_craft/techniques/registry.json`
- **Bảng Trạng Thái Triển Khai (Status):** `data/shared/knowledge/video_craft/techniques/STATUS.md`
- **7 Playbooks Thực Chiến:** `data/shared/knowledge/video_craft/playbooks/*.md` (được đồng bộ vào `ai/skills/video-craft/references/`)
  - `hook-and-retention.md`
  - `camera-and-transitions.md`
  - `depth-and-composition.md`
  - `koc-review-and-sales.md`
  - `affiliate-links-and-first-comment.md`
  - `yt-animation-episode.md`
  - `ai-workflow-comfyui-and-tools.md`

## 2. Tài Sản Dùng Chung (`data/shared/`)
- **Kho giọng đọc (Voice Vault):** `data/shared/voice_vault/soc-nho/`
- **Templates mẫu:** `data/shared/templates/`
- **Kỹ thuật demo mp4:** `data/shared/templates/_techniques/`

## 3. Dữ Liệu Từng Project (`data/projects/<project-id>/`)
- **Nhân vật Master DNA (Sóc Nhỏ Bi):** `data/projects/soc-nho-tv/characters/soc_nho/`
- **Kho tư liệu & Shots:** `data/projects/<project-id>/raw/`, `shots/`
- **Thành phẩm Master:** `data/projects/<project-id>/output/`
