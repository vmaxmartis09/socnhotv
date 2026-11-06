# S1 — Biến tab "Lịch đăng" thành Trung tâm quản lý Social: tới 10 tài khoản đa nền tảng, chọn 1/nhiều video, lập kế hoạch caption & lịch đăng chuẩn

Bạn là SESSION S (Social Manager), session ĐỘC LẬP chạy song song với E2/E3 (không chờ họ). Làm đến cùng, tự debug, không hỏi lại điều có thể tự suy ra. Đọc: `CLAUDE.md`, `ai/plans/2026-11-roadmap/CONTRACTS.md` (mục 2.3, 3), `status/C.md`, `session-E-studio-consolidation/NODE_PARAMS_CONTRACT.md` (phân vùng file), memory UI dự án (gọn; nút thêm = thẻ nét đứt cạnh thẻ cuối; cùng thực thể = chung component và bấm được tới đúng mục), skill `ui-ux-pro-max`, `design-taste-frontend` (phần app screens).

## 0. Phạm vi & phân vùng (không đụng vùng khác)
Bạn sở hữu: `tool/src/socnhotv/social/**`, `core/api/routes/social.py`, `tool/tests/test_social_*.py`, `tool/dashboard/components/social/**`, `components/studio/tabs/PublishTab.tsx`, `lib/api/social.ts`, `store/modules/social.ts`, `messages/modules/social.{vi,en}.json`, `data/projects/*/publishing/**`.
KHÔNG sửa: `components/canvas/**`, `NodeTab.tsx`, `canvasSlice.ts`, `i18n/request.ts` (E3); `RightPanel.tsx`, `PageBar`, các trang `app/[locale]/**`, `components/{templates,renders,sources,products,intel}` (E2). Cần gì ở vùng họ → ghi `status/REQUESTS.md`. Không thêm tab phải mới, không thêm trang cấp cao: toàn bộ nằm trong **tab "Lịch đăng" (PublishTab)** + **1 panel nổi lớn "Trung tâm đăng"** mở từ tab đó. Git: `git add` theo đường dẫn, không `git add -A`/stash/reset. Không tắt cổng 3000; cổng 8000 chạy bản cũ → xem mục 7.

## 1. Thực trạng (từ ảnh chụp + code, 2026-11-04)
- Tab hiện: "Quản lý Xuất bản & Đăng bài", 2 kênh (YouTube + TikTok) đều "THỦ CÔNG", nút "Xem Lịch", danh sách 7 ngày.
- **Dữ liệu giả**: "38 bài đã lên lịch" (KOC Review: Bàn Chải Điện Trẻ Em…, Sóc Nhỏ và Hạt Dẻ Thần Kỳ…) là dữ liệu mẫu/di trú, không phải do người dùng tạo.
- **Lỗi logic**: mục "Lịch đăng sắp tới (7 ngày)" bắt đầu từ 30/10/2026 trong khi hôm nay 04/11 → hiện cả ngày đã qua như "sắp tới".
- **Lỗi hiển thị trong panel hẹp (~400px)**: huy hiệu "THỦ CÔNG" đè lên tên tài khoản, tiêu đề bài bị cắt cụt không tooltip, nhãn nút/khung giờ tràn; chip nền tảng chỉ 2 chữ cái.
- Chưa có: giới hạn & quản lý tới 10 tài khoản, nhóm tài khoản, chọn video nhiều–nhiều, kiểm tra tương thích video×nền tảng, lập kế hoạch hàng loạt tự xếp lịch, caption theo từng nền tảng/tài khoản có xem trước.
- Nhãn tab phải đang tiếng Anh (Project/Characters/Chat/Schedule/Jobs/Node/Shortcuts) — thuộc E2, ghi vào `status/REQUESTS.md` ("đổi nhãn vi: Dự án/Nhân vật/Chat/Lịch đăng/Công việc/Node/Phím tắt").

## 2. Mô hình & luật (backend `social/`, kèm test)
- **Giới hạn**: tối đa **10 tài khoản/dự án** (hằng `MAX_ACCOUNTS = 10`, trả 409 khi vượt, UI hiện `7/10`).
- **Nền tảng hỗ trợ**: `youtube, tiktok, facebook, instagram, threads, x`; nền tảng khác/không có API → `manual`. Mỗi tài khoản: `platform, handle, display_name, avatar, groups[] (nhãn nhóm như "Kênh chính", "Bán hàng"), auth{mode: oauth|manual, status: connected|expired|manual|disabled}, windows[] (khung giờ vàng), daily_limit, min_gap_minutes (mặc định 120), default_hashtags, caption_footer, affiliate_default (link + disclosure), color`.
- **`social/platform_rules.py`**: bảng luật mỗi nền tảng (tỉ lệ khuyến nghị, thời lượng tối đa, dung lượng, độ dài tiêu đề/caption, số hashtag tối đa, trường bắt buộc: YouTube title/description/tags/category/privacy/made_for_kids; TikTok privacy/comment/duet/stitch/nhãn nội dung AI; IG/FB cover & first comment…). Hàm `validate(video, target) -> list[Issue(level: error|warn, code, message_vi)]` dùng cho UI và scheduler.
- **Kho video đăng được** `GET /projects/{pid}/social/videos`: gom video hoàn tất từ `output/**` (mỗi video có các biến thể theo nền tảng từ render job: `outputs[platform]`) + video trong thư viện; trả `{id, title, thumb, duration_s, width, height, size_mb, variants{platform: path}, source (job/episode/library), posted_count, last_posted_at}` (đọc metadata bằng ffprobe, cache). Biến thể đúng tỉ lệ được chọn tự động theo nền tảng (9:16 cho tiktok/reels/shorts/threads, 16:9 cho youtube, 4:5 cho facebook); không có biến thể phù hợp → cảnh báo `ratio_mismatch` kèm đề xuất "dùng bản blur-pad" nếu có.
- **Kế hoạch hàng loạt (plan)**:
  - `POST /social/plans/preview` body `{video_ids[], account_ids[], strategy: now|fixed|auto, start_at, end_at?, per_day_limit?, caption_mode}` → trả danh sách `PlannedTarget{video, account, scheduled_at, issues[]}` (chưa lưu).
  - `POST /social/plans/commit` → tạo `Post` + `PostTarget` thật (mỗi video = 1 post, mỗi tài khoản = 1 target).
  - Thuật toán `auto`: duyệt từ `max(now, start_at)`; với mỗi tài khoản đặt bài vào các `windows` của nó, tôn trọng `daily_limit`, `min_gap_minutes`, không đặt vào quá khứ, rải đều nhiều video trên nhiều ngày, so le giữa các tài khoản cùng nền tảng (không đăng cùng 1 phút), múi giờ `Asia/Ho_Chi_Minh`. Có **quota planner**: cảnh báo khi kế hoạch vượt quota API (ví dụ YouTube `videos.insert` ≈1600/10.000 đơn vị/ngày → tối đa ~6 video/ngày/dự án; TikTok/Meta theo giới hạn adapter) và tự đẩy sang ngày sau.
- **Caption**: `POST /social/captions/generate` body `{video_id, platforms[], tone, goal(sales|story|education), include_affiliate}` → dùng kịch bản/transcript của video nếu có (`content/scripts`, episode, hoặc transcript job), sinh: hook 1 dòng, caption theo giới hạn từng nền tảng, hashtag (đúng số lượng cho nền tảng), CTA, YouTube title/description/tags. Có chế độ `vary_per_account=true`: mỗi tài khoản cùng nền tảng nhận bản viết khác nhau để không đăng trùng nguyên văn lên nhiều tài khoản. Disclosure affiliate tự chèn khi có link/công tắc. Provider LLM dùng `core/providers/router.py`; lỗi/thiếu khoá → fallback theo mẫu (không bịa số liệu/đánh giá).
- **Hàng đợi**: `GET /social/queue?bucket=upcoming|overdue|published|failed&account=&platform=&from=` — `upcoming` chỉ gồm `scheduled_at >= now` (sửa lỗi hiện thị ngày đã qua); `overdue` = chưa đăng & quá giờ.
- Giữ nguyên máy trạng thái/scheduler C1–C3 (duyệt tay mặc định, OAuth chính chủ, token trong key_vault, gói đăng tay + "Tôi đã đăng", retry/backoff, không đăng khi chưa duyệt, idempotent). Đăng thật lên tài khoản người dùng luôn cần người dùng bấm xác nhận trong UI.
- **Dữ liệu giả**: kiểm kê `publishing/posts/*.json`, `schedule.json`, `accounts.json` — bài/tài khoản không do người dùng tạo (seed/di trú, nhận biết bằng cờ `source` hoặc mẫu) → `git mv` sang `publishing/_demo/`, UI trống đúng nghĩa (empty state có nút "Thêm tài khoản" / "Lên lịch video"). Không xoá dữ liệu thật của người dùng; nếu không chắc bài nào là thật, hỏi người dùng 1 lần bằng danh sách ngắn trong báo cáo cuối, mặc định chuyển sang `_demo` chứ không xoá.

## 3. UI — Tab "Lịch đăng" (panel hẹp ~400px, gọn)
1. **Đầu tab**: dải trạng thái `7/10 tài khoản · 3 chờ duyệt · 2 quá hạn · bài kế tiếp 19:30` (bấm từng mục lọc danh sách) + nút chính **"+ Lên kế hoạch đăng"** (mở Trung tâm đăng).
2. **Tài khoản**: hàng chip cuộn ngang (avatar + biểu tượng nền tảng + trạng thái chấm màu), bấm → sheet sửa tài khoản; thẻ nét đứt "+ Thêm" cuối hàng (ẩn khi đủ 10, hiện "Đã đủ 10"). Lọc theo nhóm/nền tảng. Huy hiệu trạng thái không đè tên (dùng chấm màu + tooltip; chữ "Thủ công" chỉ ở sheet chi tiết).
3. **Hàng đợi**: nhóm theo ngày, mặc định **chỉ từ bây giờ trở đi**; tab con `Sắp tới · Quá hạn · Đã đăng · Lỗi`. Mỗi dòng 1 `PostRow` dùng chung component (thumb, tiêu đề xuống dòng 2 dòng + tooltip đầy đủ, chip nền tảng đủ chữ, tên tài khoản, giờ, trạng thái). Bấm → mở bài trong Trung tâm đăng; menu `…`: sửa, đổi giờ, nhân bản sang tài khoản khác, đăng ngay (xác nhận), huỷ, "Tôi đã đăng" (thủ công), tải gói đăng tay.
4. Mọi chữ qua i18n vi/en; Morphicons; không màu cứng; dark/light đúng; không cuộn ngang.

## 4. UI — "Trung tâm đăng" (panel nổi lớn, mở từ tab; có lại trong modal "Xem lịch")
Wizard 5 bước, lưu nháp tự động, quay lại được:
1. **Chọn video** (chọn 1 hoặc nhiều): lưới thumbnail từ `/social/videos` (thời lượng, tỉ lệ, dung lượng, chip biến thể có sẵn, "đã đăng n lần"), tìm kiếm, lọc "chưa đăng", chọn nhiều bằng ô tick/Shift-click, hiển thị số đã chọn.
2. **Chọn tài khoản** (chọn nhiều, tối đa 10): theo nhóm/nền tảng, "Chọn tất cả nhóm X". Ma trận **video × tài khoản** hiện ✓ / ⚠ / ✕ theo `validate` (thời lượng quá giới hạn, sai tỉ lệ, tài khoản hết hạn…) kèm lý do; tuỳ chọn bỏ qua cặp lỗi.
3. **Nội dung**: với mỗi video: caption chính + tab theo nền tảng (từng ô có đếm ký tự theo luật nền tảng, hashtag chips, YouTube title/description/tags/category/privacy/made-for-kids, TikTok privacy/comment/duet/stitch/nhãn AI, IG/FB cover + first comment, link affiliate + công tắc disclosure). Nút **"Viết caption tự động"** (từng video hoặc tất cả), công tắc "Mỗi tài khoản một biến thể", nút tạo lại từng ô, **xem trước dạng khung điện thoại** từng nền tảng (cắt "…xem thêm" đúng chỗ). Mẫu caption/hashtag lưu lại tái dùng (lưu ở `publishing/templates.json`).
4. **Lịch**: chọn `Đăng ngay` / `Chọn giờ` / `Tự xếp lịch` (khoảng ngày, số bài/ngày) → gọi `plans/preview` → hiện **lưới xem trước** (ngày × tài khoản) và danh sách; kéo/sửa từng giờ; cảnh báo xung đột, quota, quá khứ; nút "Xếp lại".
5. **Duyệt & xác nhận**: bảng tóm tắt (video, tài khoản, giờ, caption rút gọn, cảnh báo còn lại), công tắc "Duyệt trước khi đăng" (mặc định bật), nút **Xác nhận lên lịch** (gọi `plans/commit`). Hiện kết quả: n bài đã tạo / n bỏ qua + lý do.
Trong **"Xem lịch"** (tab phía trên cùng của cùng panel): lịch tháng/tuần với làn màu theo tài khoản, kéo-thả đổi giờ, chọn nhiều để dời/huỷ hàng loạt. **Không** làm Analytics, Automation, Thông báo, nhập số liệu (để im, không hiện UI).

## 5. Nghiệm thu (làm thật trong trình duyệt, panel ~400px, 375px, 1440px, dark + light)
1. Mở tab Lịch đăng: không còn 38 bài giả; empty state đúng; mục "sắp tới" không có ngày quá khứ.
2. Tạo đủ **10 tài khoản** (3 YouTube, 3 TikTok, 2 Facebook, 1 Instagram, 1 Threads; thủ công hoặc mock OAuth); tài khoản thứ 11 bị chặn cả UI lẫn API (409).
3. Chọn **3 video** + **10 tài khoản** → ma trận tương thích hiển thị ✓/⚠/✕ đúng luật (ví dụ video 16:9 + TikTok → cảnh báo tỉ lệ, dùng biến thể 9:16 nếu có).
4. "Viết caption tự động" ra caption đúng giới hạn từng nền tảng; bật "mỗi tài khoản một biến thể" → các tài khoản cùng nền tảng có bản khác nhau; xem trước điện thoại đúng.
5. "Tự xếp lịch" 7 ngày: không đặt vào quá khứ, đúng khung giờ từng tài khoản, ≥ `min_gap`, tôn `daily_limit`, quota YouTube được cảnh báo/đẩy ngày; kéo đổi giờ được; Xác nhận → đúng số target; tải lại trang vẫn còn.
6. Scheduler (adapter mock): tới giờ bài đã duyệt được đăng, bài chưa duyệt thì không; tài khoản thủ công sinh gói đăng tay + "Tôi đã đăng". Không đăng thật lên tài khoản người dùng khi chưa có xác nhận của họ.
7. Không còn chồng chữ/cắt cụt không tooltip ở panel 400px; console sạch, không Next "Issues" từ vùng của bạn.
8. `cd tool && .venv/bin/python -m pytest -q` pass; test mới: `test_social_limits.py` (10 tài khoản), `test_social_plan.py` (auto-schedule, gap, quota, múi giờ, không quá khứ), `test_social_rules.py` (platform rules/validate), `test_social_queue.py` (bucket upcoming không chứa quá khứ), `test_social_captions.py` (giới hạn ký tự, hashtag, disclosure, biến thể).
9. Chụp ảnh vào `data/projects/soc-nho-tv/shots/S_*.png`; ghi `status/S.md` (đã làm/chưa làm/chưa kiểm chứng) và tóm tắt tiếng Việt cuối cùng.

## 6. Không làm
Không thêm nền tảng/tính năng ngoài danh sách; không lưu mật khẩu; không viết code tự đăng bằng trình duyệt né phát hiện; không tự đăng thật khi chưa có xác nhận người dùng; không hiện số liệu/dữ liệu mẫu như thật.

## 7. Core API cổng 8000
Đang chạy bản cũ. Kiểm `ps aux | grep uvicorn` xem có `--reload`; nếu chưa: `mkdir ai/plans/2026-11-roadmap/status/.core-restart.lock` — thắng khoá thì tắt/chạy lại `cd tool && .venv/bin/python -m uvicorn socnhotv.core.api.app:app --app-dir src --host 127.0.0.1 --port 8000 --reload`, thua thì không đụng.
