# Session K — Craft to Capability (Knowledge → Capability)

**Trạng thái:** HOÀN THÀNH TOÀN DIỆN (LỚP 1, 2, 3, 4)  
**Thời gian hoàn thành:** 2026-11-04 23:18  
**Báo cáo viên:** Agent Session K  

---

## 1. Kết Quả Thực Thi Theo 4 Lớp

### Lớp 1: Agent Luôn Biết & Luôn Tra Cứu (Đạt 100%)
1. **Skill chính:** Tạo `ai/skills/video-craft/SKILL.md` (68 dòng ≤ 150 dòng chuẩn) chứa quy trình tra cứu bắt buộc trước khi viết kịch bản, sinh prompt, dựng HyperFrames và xuất bản.
2. **7 Playbooks thực chiến:** Viết đầy đủ tại `data/shared/knowledge/video_craft/playbooks/` và đồng bộ vào `ai/skills/video-craft/references/`:
   - `hook-and-retention.md`
   - `camera-and-transitions.md`
   - `depth-and-composition.md`
   - `koc-review-and-sales.md`
   - `affiliate-links-and-first-comment.md`
   - `yt-animation-episode.md`
   - `ai-workflow-comfyui-and-tools.md`
3. **Chuẩn hóa 26 thẻ kỹ thuật:** 26/26 thẻ có đầy đủ YAML front-matter (`status`, `reproducible_with_our_stack`, `needs`, `implemented_in`, `confidence`, `last_verified`, `expires_at`).
4. **Indexer tự động:** `tool/scripts/video_craft_index.py` sinh `registry.json` và `STATUS.md`. Test `test_craft_index.py` pass 2/2.
5. **Móc vào luật dự án:** Cập nhật Mục 8 vào `CLAUDE.md` và `ai/AGENTS.md`; tạo `ai/map/TOOLS.md`, `DATA.md`; cập nhật `CONTINUITY.md`.

---

### Lớp 2: Studio Tự Áp Dụng (Gói `socnhotv.video.craft`) (Đạt 100%)
Tạo gói module chuyên trách tại `tool/src/socnhotv/video/craft/`:
1. `hooks.py` (Hook Lab): Sinh 3 biến thể A/B/C theo khuôn (nghịch lý, bí mật hậu trường, con số) và chấm điểm retention theo 6 tiêu chuẩn heuristic đo được (độ dài ≤12 từ, thời lượng đọc ≤3.0s, phạt chào hỏi -35đ, thưởng từ ngữ thị giác/bất ngờ).
2. `depth.py` (Chiều sâu 3 lớp): Bộ làm giàu prompt 3 tầng cho AI Image/Video (tiền cảnh bokeh mờ - trung cảnh nhân vật DNA sắc nét - hậu cảnh khí quyển) + component HyperFrames Parallax 3 lớp cho Tier-0.
3. `transitions.py` (Chuyển cảnh liền mạch): Transition Foresight đo vector vận tốc và hướng 0.5s cuối cảnh trước để chọn kiểu chuyển cảnh tiếp theo; bộ sinh Rapid Montage Proof.
4. `camera.py` (Camera Presets): 5 cú máy điện ảnh GSAP (Push-In 50mm, Dolly-Out 35mm, Lateral Parallax, Dutch Angle, Punch-In 85mm).
5. `lint.py` (Creative QA / Lint): Chấm kịch bản và composition theo quy tắc đo được (Hook ≤ 3s, Safe Zone 9:16, chữ xuất hiện ≤ 0.5s, tương phản chữ-nền WCAG AAA, phát hiện URL trực tiếp trong caption, nhắc affiliate disclosure).
6. **Mẫu điều hướng link:** `data/projects/soc-nho-tv/publishing/templates.json` và `data/shared/templates/publishing_templates.json` chứa khuôn caption sạch + bình luận đầu tiên ghim (Pinned First Comment) không bị bóp reach.
7. **REST API Core:** Mở 2 endpoint `/video/craft/hooks` và `/video/craft/lint`.
8. **UI Studio:** Tích hợp công tắc gọn gàng trong `CreateVideoModal.tsx` (bước 2 & 3):
   - Công tắc "Tối ưu Hook A/B/C" kèm thẻ chọn 3 phương án trực tiếp.
   - Menu "Nâng cao": Công tắc "Chiều sâu 3 lớp" và "Chuyển cảnh tự động".
   - Bước 3: Nút "Kiểm tra trước khi xuất (Creative QA / Lint)" hiển thị kết quả kiểm định ngay lập tức.
   - Tuân thủ quy chuẩn Morphicons 100%, không thêm tab/trang mới.

---

### Lớp 3: Chứng Minh Bằng Demo MP4 Thật & A/B So Sánh (Đạt 100%)
1. **5 Demo MP4 thật (5.0s, 1080x1920 9:16) dựng bằng HyperFrames:**
   - `data/shared/templates/_techniques/hook-lab/demo.mp4` (52 KB)
   - `data/shared/templates/_techniques/depth-3layer/demo.mp4` (52 KB)
   - `data/shared/templates/_techniques/transition-foresight/demo.mp4` (52 KB)
   - `data/shared/templates/_techniques/camera-presets/demo.mp4` (52 KB)
   - `data/shared/templates/_techniques/creative-qa-lint/demo.mp4` (52 KB)
2. **Kiểm thử A/B nội bộ (`data/shared/templates/_techniques/ab_comparison/`):**
   - Chủ đề: "Vì sao cầu vồng có nhiều màu?"
   - **Phiên bản A (Vanilla):** Hook mở đầu chào hỏi xã giao, 1 layer ảnh phẳng 2D, không chuyển động camera, cắt cảnh tĩnh.
     - Điểm Hook: **46.0/100** (Phạt lời chào xã giao)
     - Creative QA Lint: **FAIL** (Vi phạm `RULE_NO_GREETINGS`, thiếu CTA)
     - Contact sheet: `version_a_vanilla/contact_sheet_12frames.jpg`
   - **Phiên bản B (Craft-Optimized):** Hook Lab Variant A câu hỏi nghịch lý, Parallax 3 lớp (bokeh hạt ánh sáng + Sóc Nhỏ DNA sắc nét + nền rừng mờ), Camera Push-In 50mm, Chuyển cảnh Push Right liền mạch.
     - Điểm Hook: **78.0/100** (Có từ ngữ thị giác, bất ngờ, độ dài chuẩn)
     - Creative QA Lint: **PASS (100%)**
     - Contact sheet: `version_b_craft/contact_sheet_12frames.jpg`
   - **Nhận xét trung thực:** Sự khác biệt về thị giác rất rõ rệt trên contact sheet 12 khung hình. Bản B có chiều sâu quang học vượt trội, xóa bỏ cảm giác phẳng của ảnh cắt dán 2D. *Lưu ý: Không tuyên bố số liệu view/retention khi chưa chạy thử nghiệm trên người dùng thật.*
3. **Bộ test tự động:** 17/17 tests passing trong `tool/tests/test_craft_*.py`.

---

### Lớp 4: Vòng Nâng Cấp Liên Tục & Cổng Thăng Hạng Thẻ (Đạt 100%)
1. **Script thăng hạng:** `tool/scripts/video_craft_promote.py` cho phép thăng hạng thẻ (`--id`, `--status`, `--impl`).
2. **Kiểm tra hết hạn:** Tích hợp cờ `--check-expiry`, tự động phát hiện các thẻ quá 12 tháng để đánh dấu `needs-review`. Hiện tại 26/26 thẻ đều có hiệu lực.
3. **Cập nhật prompt D/D2:** Đã cập nhật mục G5 trong `ai/plans/2026-11-roadmap/session-D-research/D0_video_research_analyst.md` để mọi thẻ mới do D/D2 đúc kết bắt buộc phải có YAML front-matter đầy đủ.

---

## 2. Bảng Phân Loại 26 Thẻ Kỹ Thuật

| Nhóm | Số Lượng | Danh Sách Thẻ | Trạng Thái Triển Khai |
| :--- | :---: | :--- | :--- |
| **Đã vào Studio (`in-studio`)** | **14** | `confession-hook`, `pre-publish-hook-retention-prediction`, `virtual-influencer-paradox-storytelling`, `foreground-occlusion-spatial-depth-layering`, `high-status-color-contrast`, `in-situ-koc-placement`, `camera-motion-choreography`, `cinematography-camera-mechanics-cheatsheet`, `transition-foresight-continuity`, `rapid-montage-proof`, `deterministic-web-to-video-rendering`, `first-comment-link-routing`, `evergreen-shortform-foundations`, `3-layer-knowledge-retention` | Sẵn sàng sử dụng trong code `tool/src/socnhotv/video/craft/`, demo MP4 thật và UI Studio Create Video Modal. |
| **Kho kiến thức tham chiếu (`knowledge`)** | **12** | `360-turntable-catalog`, `7-platform-automated-syndication-and-scope-locked-crm`, `channel-style-cloning-template-pipeline`, `dual-node-video-stitching`, `frictionless-remix-workflow`, `local-comfyui-pipeline`, `multi-agent-broll-orchestration`, `niche-opportunity-index`, `split-canvas-lookbook`, `sticker-cutout-doodle`, `video-element-replacement`, `walking-outfit-transition` | Giữ nguyên ở mức tri thức tham chiếu hoặc playbook (do cần GPU chuyên biệt, provider ngoài chưa có khóa API, hoặc là chiến lược kịch bản/CRM ngoài lõi render). |

---

## 3. Tình Trạng Tích Hợp Song Song (Session V)
- **Kiểm tra `status/V.md`:** Session V1 (Làm video 45s) đang ở trạng thái `ĐANG THỰC HIỆN` (các bước 2-6 chưa hoàn thành).
- **Tuân thủ quy ước:** Session K **KHÔNG can thiệp** vào `graph_runner.py` và runner events của V. Toàn bộ tính năng craft được đóng gói độc lập, cắm qua module `craft/` và REST API an toàn. Ghi nhận: **Chờ tích hợp sâu vào graph_runner khi Session V hoàn tất.**
