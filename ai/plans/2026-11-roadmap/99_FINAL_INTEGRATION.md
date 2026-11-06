# 99 — Tích hợp cuối (chạy khi A4, B4, C4 đều xong — 1 session)

Bạn là kỹ sư tích hợp. Đọc: `README.md`, `CONTRACTS.md`, `status/A.md`, `status/B.md`, `status/C.md`, `status/REQUESTS.md`. Giờ bạn được phép sửa file chung.

1. **Xử lý REQUESTS.md**: từng dòng → làm hoặc ghi lý do bỏ. Ví dụ dự kiến: gắn `video.cli` vào `python -m socnhotv`; link "Dựng tập" từ `EpisodeDetail.tsx` sang `/renders/episode/[eid]`; UI param riêng cho node `template_render` trong `StudioNode.tsx`; deps còn thiếu.
2. **Kiểm hợp đồng thật** (không mock): 
   - B: link nguồn (video owned/licensed) → localize Mode L → A render `tiktok`+`youtube` → C nhận draft (auto_draft) → duyệt → gói đăng tay.
   - B: video review mẫu → blueprint → script KOC cho 1 sản phẩm → A render `koc-review-v1` → C lịch.
   - B4 ideas → C kéo vào lịch → promote → A episode → 3 shorts → C draft.
   Ghi log từng bước vào `status/E2E.md`, lỗi nào sửa ngay.
3. **Chất lượng**: `cd tool && .venv/bin/python -m pytest -q` pass hết; `cd tool/dashboard && npx tsc --noEmit && npm run build` sạch; quét `grep -rn "lucide-react" tool/dashboard/{app,components,lib}` = 0; kiểm mọi trang mới ở 375px và dark mode.
4. **Dọn nợ**: gỡ `lucide-react` khỏi `package.json` nếu không còn import; ghi chú `studio/` gốc là legacy trong `LEGACY_LINKS.md`; cập nhật `ai/map/TOOLS.md` + `ai/map/DATA.md` với module/API/thư mục mới.
5. **Bộ nhớ**: gộp tóm tắt + `analytics/learnings.md` vào `ai/memory/CONTINUITY.md` (trạng thái 3 mảng, lệnh chạy chuẩn, giới hạn), cập nhật `CLAUDE.md` mục 5 đường dẫn engine đúng thực tế (`tool/src/socnhotv/video/hyperframes_engine.py`).
6. Bảng % hoàn thiện mới (so với bảng trong README) ghi vào `README.md` mục "Sau tích hợp".
7. Commit `chore(integration): wire A/B/C, e2e verified, docs + memory`.
