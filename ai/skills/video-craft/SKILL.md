---
name: video-craft
description: Kích hoạt khi viết, sửa, đánh giá video, kịch bản, prompt ảnh/video, hook, caption, chuyển cảnh, camera, quảng cáo, affiliate, KOC và hoạt hình. Hướng dẫn tra cứu kho 26 thẻ kỹ thuật video craft và 7 playbooks thực chiến của SocNhoTV.
metadata:
  version: "1.0.0"
  date: "2026-11-04"
  author: "SocNhoTV Craft Architecture"
---

# 🎬 Video Craft Skill: Kỹ Năng Biên Tập & Tối Ưu Giữ Chân Thực Chiến

Kho tri thức video thực chiến gồm **26 thẻ kỹ thuật** (`data/shared/knowledge/video_craft/techniques/`) và **7 playbooks** (`data/shared/knowledge/video_craft/playbooks/`).

---

## 1. Quy Trình Tra Cứu Bắt Buộc (Look-Up Workflow)

Khi thực hiện bất kỳ tác vụ nào liên quan đến video, Agent bắt buộc tra cứu theo thứ tự:

1. **Trước khi viết kịch bản (Scripting):**
   - Đọc playbook `references/hook-and-retention.md`.
   - Tra cứu thẻ `confession-hook` hoặc `virtual-influencer-paradox-storytelling`.
   - Sinh tối thiểu 3 biến thể hook A/B/C, chấm điểm bằng `tool/src/socnhotv/video/craft/hooks.py`.

2. **Trước khi sinh Prompt Hình ảnh / B-Roll (Visual Generation):**
   - Đọc playbook `references/depth-and-composition.md`.
   - Áp dụng cấu trúc 3 tầng: Tiền cảnh mờ (bokeh) - Trung cảnh nét (nhân vật DNA) - Hậu cảnh khí quyển (`foreground-occlusion-spatial-depth-layering`).

3. **Trước khi dựng Composition HyperFrames (Animation & Editing):**
   - Đọc playbook `references/camera-and-transitions.md`.
   - Chọn chuyển động camera từ `tool/src/socnhotv/video/craft/camera.py`.
   - Áp dụng quy tắc `transition-foresight-continuity` qua `tool/src/socnhotv/video/craft/transitions.py`.

4. **Trước khi xuất bản & Viết Caption (Publishing & QA):**
   - Chạy Creative QA Lint: `tool/src/socnhotv/video/craft/lint.py`.
   - Đọc playbook `references/affiliate-links-and-first-comment.md` để điều hướng link vào bình luận đầu tiên.

---

## 2. Bảng Chọn Kỹ Thuật Theo Mục Đích (Use-Case Matrix)

| Mục Đích | Playbook Tham Chiếu | Thẻ Kỹ Thuật Chính | Trạng Thái Studio |
| :--- | :--- | :--- | :---: |
| **Giữ chân 3 giây đầu** | [`hook-and-retention`](references/hook-and-retention.md) | `confession-hook`, `pre-publish-hook-retention-prediction` | **in-studio** (`hooks.py`) |
| **Xóa phẳng AI / Chiều sâu** | [`depth-and-composition`](references/depth-and-composition.md) | `foreground-occlusion-spatial-depth-layering`, `high-status-color-contrast` | **in-studio** (`depth.py`) |
| **Chuyển cảnh mượt mà** | [`camera-and-transitions`](references/camera-and-transitions.md) | `transition-foresight-continuity`, `camera-motion-choreography` | **in-studio** (`transitions.py`) |
| **Camera điện ảnh GSAP** | [`camera-and-transitions`](references/camera-and-transitions.md) | `cinematography-camera-mechanics-cheatsheet` | **in-studio** (`camera.py`) |
| **Kiểm tra chất lượng trước xuất** | Mọi playbooks | `evergreen-shortform-foundations`, `3-layer-knowledge-retention` | **in-studio** (`lint.py`) |
| **Bán hàng / KOC Review** | [`koc-review-and-sales`](references/koc-review-and-sales.md) | `in-situ-koc-placement`, `rapid-montage-proof`, `360-turntable-catalog` | **in-studio** / knowledge |
| **Điều hướng link Affiliate** | [`affiliate-links-and-first-comment`](references/affiliate-links-and-first-comment.md) | `first-comment-link-routing` | **in-studio** (social) |
| **Hoạt hình tập Sóc Nhỏ** | [`yt-animation-episode`](references/yt-animation-episode.md) | `deterministic-web-to-video-rendering`, `channel-style-cloning-template-pipeline` | **in-studio** (templates) |
| **Tích hợp ComfyUI / AI ngoài** | [`ai-workflow-comfyui-and-tools`](references/ai-workflow-comfyui-and-tools.md) | `multi-agent-broll-orchestration`, `local-comfyui-pipeline` | knowledge (Tier 1/2) |

---

## 3. Lệnh Quản Trị & Kiểm Tra Kho Tri Thức

- **Sinh lại bảng tra cứu và kiểm tra lỗi thẻ:**
  ```bash
  python tool/scripts/video_craft_index.py
  python tool/scripts/video_craft_index.py --check
  ```
- **Thăng hạng thẻ kỹ thuật mới:**
  ```bash
  python tool/scripts/video_craft_promote.py --id <technique-id>
  ```
- **Xem trạng thái chi tiết mọi kỹ thuật:**
  Đọc file `data/shared/knowledge/video_craft/techniques/STATUS.md` hoặc `registry.json`.
