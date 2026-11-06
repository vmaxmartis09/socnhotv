# C4 — Analytics đa nền tảng · Giờ vàng · Vòng tự học · Tự động hoá luồng Render → Lịch

Bạn là Session C. Đọc: `CONTRACTS.md`, `status/C.md`, `status/A.md` + `status/B.md` (biết A/B đã có gì), `social/*`, skill `dataviz` (bắt buộc trước khi vẽ biểu đồ), `CLAUDE.md` mục 6 (giao thức tự học).

## Việc cần làm
1. **Thu số liệu `social/analytics/collectors/`**:
   - `youtube.py`: YouTube Data API `videos.list(statistics)` + YouTube Analytics API (views, averageViewDuration, averageViewPercentage, subscribersGained, impressions/CTR nếu có quyền) theo ngày.
   - `tiktok.py`: Display API/Research không có → dùng `video/query` của Content Posting/Display nếu scope cho phép; không thì nhập tay.
   - `meta.py`: insights Page video / IG Reels (plays, reach, avg watch time, saves, shares).
   - `manual.py`: form nhập tay + import CSV (export từ TikTok Studio/YouTube Studio) — map cột linh hoạt.
   - Lưu `analytics/metrics/<post_target_id>.jsonl` (snapshot theo thời điểm: 1h, 6h, 24h, 72h, 7d, 28d) + job thu định kỳ trong scheduler C3.
2. **`social/analytics/insights.py`**:
   - KPI theo tài khoản/nền tảng/khoảng thời gian: views, watch time, retention trung bình, ER = (like+comment+share+save)/views, follower gain, CTR, doanh thu affiliate nhập tay.
   - **Giờ vàng**: heatmap weekday×giờ theo median views 24h → cập nhật đề xuất `posting_windows` (người dùng bấm "Áp dụng").
   - **Hiệu quả theo template / blueprint / pillar / nhân vật / giọng**: join `Post.render_job_id → RenderRequest.template_id` (đọc `runs/render_queue/*.json` của A, chỉ đọc), `idea_id → ContentIdea.blueprint_ref` (B), → bảng xếp hạng.
   - Phát hiện outlier (≥ 2× median 7 ngày) và bài kém (≤ 0.5×) kèm giả thuyết LLM (hook? độ dài? giờ đăng?).
   - Xuất `analytics/insights/<yyyy-mm-dd>.json` + `analytics/learnings.md` (tóm tắt dễ đọc).
3. **Vòng tự học**: mỗi tuần (job scheduler) → cập nhật `analytics/learnings.md`; file `analytics/recommendations.json` mà B (ideas priority) và A (template ưu tiên) có thể đọc. Không sửa `ai/memory/CONTINUITY.md` (file chung) — ghi đề xuất cập nhật vào `status/REQUESTS.md` để 99_FINAL gộp.
4. **Tự động hoá luồng (Automation rules)** `social/automation.py` + UI:
   - Rule dạng `{trigger: render_done | idea_scripted | schedule_gap, conditions, actions}`; ví dụ mặc định (tắt sẵn): "Khi render xong template `tiktok-sales-*` → tạo bài nháp cho tài khoản TikTok + Reels, caption auto, giờ gợi ý, gửi duyệt".
   - Đọc sự kiện `runs/events/render.jsonl` (A) và `content/ideas/` (B) — chỉ đọc.
   - "Lấp lịch trống": nếu tuần tới thiếu bài so với mục tiêu (trong `content/strategy.json` của B nếu có, hoặc cấu hình account) → cảnh báo + gợi ý ideas phù hợp.
   - Mọi rule vẫn dừng ở `pending_approval` trừ khi người dùng bật "tự duyệt" cho rule đó (cảnh báo rõ trong UI).
5. **UI tab Phân tích** (`/social/analytics`) + widget trong tab Lịch:
   - Hàng KPI (stat tile), biểu đồ views theo ngày từng nền tảng (SVG thuần theo skill dataviz, đúng light/dark), heatmap giờ vàng, bảng top/bottom bài (bấm → mở bài trong composer), bảng hiệu quả template/pillar/nhân vật, khung "Bài học tuần này" render `learnings.md`.
   - Trang `/social/automation`: danh sách rule, bật/tắt, sửa điều kiện, log lần chạy.
   - Ô lịch hiển thị chỉ số nhỏ (views 24h) cho bài đã đăng.
6. **Thông báo**: trung tâm thông báo nhỏ trong Social (đăng thành công/thất bại, token hết hạn, gói đăng tay đến giờ, lịch trống).

## Nghiệm thu Session C
- `test_social_analytics.py` (fixture metrics: KPI, ER, heatmap, join template đúng), `test_social_automation.py` (render_done → draft pending_approval; tự duyệt chỉ khi bật).
- E2E C (`test_social_e2e.py`, mock adapter): inbox → draft → approve → scheduler đăng → collector lấy metrics → insights có bài đó.
- UI: `/social/analytics` có dữ liệu (nhập tay CSV mẫu nếu chưa có API), chụp `shots/C4_*.png`.
- `status/C.md`: % từng mảng, hướng dẫn tạo OAuth app từng nền tảng (từng bước, link chính thức), giới hạn quota.
- Commit `feat(C4): analytics, best-time heatmap, automation rules, learning loop`.
