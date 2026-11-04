# Session K — Craft to Capability (Knowledge → Capability)

**Trạng thái:** ĐANG THỰC HIỆN  
**Bắt đầu:** 2026-11-04 22:58  
**Mục tiêu:** Biến 26 thẻ kỹ thuật trong `data/shared/knowledge/video_craft/` thành kỹ năng thường trực của dự án qua 4 lớp:
1. Lớp 1: Agent luôn biết & luôn tra (skill `ai/skills/video-craft`, 7 playbooks thật, front-matter chuẩn cho 26 thẻ, `registry.json` + `STATUS.md`, tích hợp `AGENTS.md` / `CLAUDE.md` / `ai/map/`).
2. Lớp 2: Studio tự áp dụng các kỹ thuật tái lập được bằng stack hiện có qua gói `tool/src/socnhotv/video/craft/` (Hook Lab A/B/C, Chiều sâu 3 lớp, Chuyển cảnh liền mạch, Camera presets, Creative QA/lint, Mẫu liên kết & first-comment).
3. Lớp 3: Demo MP4 thật + test tự động cho từng kỹ thuật, A/B so sánh thực tế.
4. Lớp 4: Vòng nâng cấp liên tục (`video_craft_promote.py`, kiểm tra hết hạn, cập nhật prompt D/D2).

---

## 1. Nhật ký tiến độ từng bước

| Bước | Hạng mục | Trạng thái | Chi tiết / Bằng chứng |
| :--- | :--- | :---: | :--- |
| **K0** | Khởi động & Khảo sát | [x] Hoàn thành | Kiểm tra 26 thẻ, kiểm tra status V (V1 đang chạy), xác lập ranh giới |
| **K1** | Lớp 1: Skill `video-craft` & Playbooks | [x] Hoàn thành | Tạo `ai/skills/video-craft/SKILL.md` (68 dòng) & 7 playbooks thực chiến tại `data/shared/knowledge/video_craft/playbooks/` & sync `references/` |
| **K2** | Lớp 1: Chuẩn hóa 26 thẻ & Indexer | [x] Hoàn thành | 26/26 thẻ có YAML front-matter chuẩn; `video_craft_index.py` sinh `registry.json` & `STATUS.md`; test `test_craft_index.py` 2/2 pass |
| **K3** | Lớp 1: Móc vào luật dự án & Bản đồ | [x] Hoàn thành | Cập nhật Mục 8 vào `AGENTS.md` & `CLAUDE.md`; tạo `ai/map/TOOLS.md`, `DATA.md`; cập nhật `CONTINUITY.md` |
| **K4** | Lớp 2: Module `socnhotv.video.craft` | [ ] Đang thực hiện | Thiết kế và viết `hooks.py`, `depth.py`, `transitions.py`, `camera.py`, `lint.py` |
| **K5** | Lớp 3: Demo thật & Unit tests | [ ] Chờ | Dựng demo MP4 cho từng craft module, test pytest cho từng module, so sánh A/B |
| **K6** | Lớp 2: UI Studio (Panel Tạo video) | [ ] Chờ | Công tắc gọn trong Create Video (Hook A/B/C, 3 lớp, Chuyển cảnh auto, Lint) |
| **K7** | Lớp 4: Cổng thăng hạng & Hết hạn | [ ] Chờ | `video_craft_promote.py`, cập nhật prompt D/D2 (G5) |
| **K8** | Tích hợp runner (nếu V xong) / Tổng kết | [ ] Chờ | Kiểm tra lại V.md; nghiệm thu toàn diện |

---

## 2. Ghi chú tích hợp song song
- Session V đang chạy làm video 45s (`status/V.md`: ĐANG THỰC HIỆN).
- Tuân thủ ranh giới: KHÔNG can thiệp vào `graph_runner.py`, runner events, Jobs/export khi V chưa hoàn tất. Các module craft giữ thiết kế standalone sạch và cắm qua hook/adapter an toàn.
