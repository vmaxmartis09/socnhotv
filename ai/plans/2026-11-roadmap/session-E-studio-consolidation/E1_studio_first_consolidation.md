# E1 — (ĐÃ BỊ THAY THẾ BỞI E2_lean_studio.md — KHÔNG DÙNG FILE NÀY; chỉ giữ để tham khảo phần "Vấn đề thật")

# E1 — Gom lại về Studio: bỏ trang thừa, nhét Social/Nguồn/Sản phẩm/Render vào panel phải

Bạn là SESSION E, session DUY NHẤT được sửa frontend ở giai đoạn này. Làm đến cùng, tự debug, không hỏi lại điều có thể tự suy ra. Đọc trước: `CLAUDE.md`, `ai/AGENTS.md`, `ai/plans/2026-11-roadmap/CONTRACTS.md`, `status/{A,B,C}.md`, memory UI của dự án (spacing gọn; nút thêm = thẻ nét đứt cạnh thẻ cuối; cùng thực thể = chung component và bấm được tới đúng mục), skill `ui-ux-pro-max`, `design-taste-frontend`.

## 0. Vấn đề thật (đã khảo sát 2026-11-04)
Mục tiêu của người dùng: **Studio là trung tâm để làm video**; mọi thứ liên quan Social/đăng bài nằm **trong tab bên phải** của Studio. Ba session A/B/C đã làm backend tốt (giữ nguyên) nhưng UI đi ngược mục tiêu:
1. `PageBar.tsx` hiển thị menu 6 trang cấp cao: Templates · Renders · Sources · Products · Intel · Social (từ `components/navigation/nav-modules/*`). Mỗi mục là 1 trang riêng, bản sao rời khỏi Studio.
2. Đảo ngược tỉ trọng: Social có ~4.250 dòng UI toàn trang (`components/social/*`: CalendarView 528, AnalyticsTab 628, AccountsTab 555, PostComposer 642, PostsTab 429, ApprovalsTab 325…) trong khi tab phải thật `components/studio/tabs/PublishTab.tsx` chỉ 83 dòng. Tương tự `components/{templates,renders,sources,products,intel}` ~4.900 dòng + ~1.400 dòng trang.
3. Trang **Templates trống** ("Không tìm thấy mẫu phù hợp") dù `data/shared/templates/` có 8 template: uvicorn cổng 8000 đang chạy bản cũ, `GET /video/templates` trả 404. Overlay lỗi Next "4–8 Issues" hiện ở hầu hết trang.
4. Giao diện không nhất quán: Templates tối, Sources/Products/Intel nền sáng kèm các khối xám đè (kanban Intel mờ, ô "Thêm sản phẩm mới" xám), tên dự án trên PageBar mờ trong dark mode, nhãn menu còn tiếng Anh ("Templates", "Renders"…).
5. **Số liệu giả trình bày như thật**: `social/seed_sample_analytics.py` + các file `data/projects/soc-nho-tv/analytics/{metrics,insights,recommendations.json,learnings.md}` là dữ liệu mẫu; `status/REQUESTS.md` còn ghi "median views 12.4K, giữ chân 78.5%, khung giờ vàng Thứ 2/Thứ 6" như kết luận thật. Composer có giá trị mặc định giả ("Video mới", đường dẫn `content/episodes/soc-nho/video.mp4`).

## 1. Kiến trúc đích — "Studio-first"
- **Trang cấp cao còn lại**: `/` (Sảnh), `/studio`, `/characters`, `/projects`, `/settings`, `/jobs`. Các trang `/templates`, `/templates/[id]`, `/renders`, `/renders/episode/[eid]`, `/sources`, `/products`, `/intel`, `/social`, `/publish` → **xoá** (route cũ chỉ còn redirect về `/studio`, mở đúng tab/panel tương ứng, theo mẫu `app/[locale]/publish/page.tsx` hiện có).
- **PageBar** trở lại đúng bản gốc: Sảnh › dự án đang mở. Xoá `nav-modules` khỏi PageBar (giữ file nếu còn dùng ở nơi khác, nếu không thì xoá hẳn cùng `sources-icons.ts`).
- **Panel phải vẫn 5 tab** (chat · node · project · publish · jobs), KHÔNG thêm tab mới:
  | Tab | Nhận thêm |
  |---|---|
  | **Project** (chia nhỏ thành section gập được, tách file: `ProjectTab.tsx` hiện 1.221 dòng không được to thêm) | **Nguồn** (danh sách gọn + ô dán link + thẻ nét đứt "Nạp nguồn"; bấm nguồn → panel nổi chi tiết/`LocalizeStudio`), **Sản phẩm** (lưới gọn + thẻ nét đứt "Thêm sản phẩm"; bấm → modal chi tiết), **Ý tưởng & Phân tích** (danh sách ý tưởng gọn có trạng thái, nút "Tạo kịch bản"; Blueprint/Học kênh/Chiến lược nằm trong 1 modal "Phân tích" mở từ đây, không phải trang) |
  | **Node** | Giữ nguyên; node mới (`template_render`, `platform_export`, `source_video`, `localize`, `blueprint_analyze`, `script_from_blueprint`, `channel_insight`) xuất hiện trong bảng thêm node hiện có, nhóm theo category |
  | **Publish (đổi nhãn "Đăng")** | **Trung tâm Social thu gọn**: dải trạng thái (số tài khoản kết nối, bài chờ duyệt, bài kế tiếp), `AgendaList` 7 ngày tới, danh sách duyệt nhanh (Duyệt/Từ chối/Sửa), nút "+ Lên lịch" mở `PostComposer` dạng **panel nổi trong Studio** (không phải trang), nút "Lịch đầy đủ" mở 1 **modal lớn** chứa 3 tab con (Lịch tháng/tuần · Tài khoản · Phân tích). Tự động hoá/Thông báo/Nhập tay số liệu để trong modal đó, ẩn dưới "Nâng cao". |
  | **Jobs** | Hợp nhất hàng đợi Render (`RenderJobCard`, SSE %, huỷ/render lại/tải) với chi phí hiện có; chip lọc Chạy/Xong/Lỗi; nút **"Gửi sang Đăng"** trên job xong → tạo bài nháp (`POST /projects/{pid}/social/posts/draft`) và nhảy sang tab Đăng đúng bài đó |
- **Canvas Studio**: thêm nút **"Bắt đầu từ mẫu"** trên thanh công cụ (`StudioStickToolbar`) → panel nổi thư viện mẫu (lưới gọn, chip loại + nền tảng, hover xem preview). Chọn mẫu → form slot (`SlotField`) → tạo **preset đồ thị** trên canvas (script → voice_tts → captions → template_render → export…, đã nối dây, có số bước chạy) thay vì một đường render riêng. Chạy bằng nút Chạy sẵn có của Studio. `EpisodeBuildPanel` mở thành panel nổi từ tập phim trong Sidebar.
- **PreviewPane** của Studio: tab nền tảng (TikTok/Reels/Shorts/YouTube/Facebook/Douyin) + bật/tắt overlay safe-zone (đưa logic từ trang template cũ vào đây).
- Thực thể dùng chung 1 component ở mọi nơi (RenderJobCard, PostChip, AccountChip, SourceCard, ProductCard) và bấm vào đều tới đúng mục (job → node/đầu ra, bài đăng → composer, nguồn → chi tiết, sản phẩm → chi tiết).

## 2. Thứ tự làm (mỗi bước xong: tsc sạch phần mình sửa, kiểm trình duyệt, commit riêng)
**Bước 0 — Chạy lại core đúng bản.** Tắt uvicorn cổng 8000 đang chạy cũ, chạy lại `cd tool && .venv/bin/python -m uvicorn socnhotv.core.api.app:app --app-dir src --host 127.0.0.1 --port 8000 --reload`. Kiểm: `GET /video/templates` trả 8 mẫu, `/sources/_ping`, `/intel/_ping`, `/social/_ping` 200. Không tắt cổng 3000. Thêm vào Studio một dải cảnh báo nhỏ "Core cũ/không phản hồi: chạy lệnh …" khi `/health` hoặc `/video/templates` lỗi (thay cho trang rỗng im lặng).
**Bước 1 — Kiểm kê.** Viết `status/E_audit.md`: mỗi file UI mới → KEEP-CORE / MOVE (vào đâu) / DELETE, kèm lý do 1 dòng. Quy tắc mặc định: thứ gì không đạt được trong ≤2 cú bấm từ Studio thì bỏ UI (giữ backend và API). Không xoá backend, API, test, dữ liệu.
**Bước 2 — Dọn nav & route.** Theo mục 1. Xoá trang + component mồ côi; không để import chết.
**Bước 3 — Tab Đăng + Jobs + Project mới** theo bảng trên; tái dùng component của C/A/B (di chuyển/chia nhỏ, không viết lại logic). Giới hạn: mỗi file ≤ 400 dòng; tab chính ≤ 250 dòng (tách section).
**Bước 4 — Bắt đầu từ mẫu + PreviewPane.** Preset đồ thị phải dùng đúng node trong `GET /node-types`; kiểm bằng validator đồ thị (`POST /projects/{pid}/graph/validate`).
**Bước 5 — Dữ liệu giả.** (a) `seed_sample_analytics` không được tự chạy; (b) chuyển dữ liệu mẫu ở `data/projects/soc-nho-tv/analytics/` (metrics/insights/recommendations/learnings) sang `analytics/_demo/` bằng `git mv`, UI Phân tích hiển thị trạng thái rỗng "Chưa có số liệu thật — nhập tay hoặc kết nối tài khoản" và chỉ hiện dữ liệu mẫu khi người dùng bật công tắc "Xem dữ liệu mẫu" kèm nhãn rõ; (c) sửa `status/REQUESTS.md`: thêm ghi chú đầu mục "các con số 12.4K/78.5%/khung giờ vàng là DỮ LIỆU MẪU, không dùng để ra quyết định"; (d) bỏ mặc định giả trong composer: tiêu đề trống, media bắt buộc chọn thật từ Jobs/Library, không có đường dẫn giả.
**Bước 6 — Đồng nhất giao diện.** Mọi màn dùng token theme (không màu cứng), dark/light đúng, xoá khối xám đè; mọi nhãn qua i18n vi/en (không còn chữ Anh sót); Morphicons duy nhất (`grep -rn "lucide-react" tool/dashboard/{app,components,lib}` = 0); UI gọn.
**Bước 7 — Sạch lỗi.** Mở `http://localhost:3000/vi/studio` và từng tab phải: đọc console, sửa **mọi** lỗi/overlay "Issues" của Next (hydration, key trùng, fetch 404, import chết). Cuối cùng: `npx tsc --noEmit` và `npm run build` sạch.

## 3. Nghiệm thu (làm thật trong trình duyệt ở 1440px và 375px, dark + light)
1. `/vi/studio` chỉ còn PageBar Sảnh › dự án; không còn menu 6 mục; mọi route cũ redirect đúng.
2. Studio → "Bắt đầu từ mẫu" → chọn `tiktok-sales-v1` → điền slot → canvas có đồ thị nối dây hợp lệ → Chạy (provider mock được) → job xuất hiện ở tab Jobs → "Gửi sang Đăng" → bài nháp hiện ở tab Đăng → Duyệt → có trong Agenda → mở "Lịch đầy đủ" thấy đúng bài, kéo đổi ngày được, đóng modal về lại Studio.
3. Tab Project: dán 1 link nguồn, thêm 1 sản phẩm bằng thẻ nét đứt; bấm vào mở đúng chi tiết.
4. Không còn Next "Issues"; console sạch; không request 404.
5. Số dòng UI mới (components/{social,templates,renders,sources,products,intel} + trang) giảm ≥ 35% so với hiện tại; liệt kê trước/sau trong `status/E.md`.
6. Chụp ảnh trước/sau vào `data/projects/soc-nho-tv/shots/E_*.png` (Studio tổng, tab Đăng, tab Jobs, tab Project, Lịch đầy đủ, mẫu).
7. `cd tool && .venv/bin/python -m pytest -q` vẫn pass (không phá backend).

## 4. Luật
- Không sửa core engine, adapters, providers, API route logic, test backend (trừ khi lỗi chặn UI, ghi rõ). Không xoá dữ liệu người dùng (chỉ `git mv` dữ liệu mẫu).
- Session D vẫn có thể đang ghi `data/shared/knowledge/video_craft/**`: `git add` theo đường dẫn của bạn, không `git add -A`, không stash/reset.
- Không tắt server 3000. Không thêm tab phải thứ 6, không thêm trang cấp cao mới, không thêm thư viện UI mới.
- Báo cáo thật: cái gì đã làm/chưa làm/chưa kiểm chứng ghi vào `status/E.md`; cuối cùng tóm tắt tiếng Việt: đã xoá gì, gộp gì vào đâu, còn nợ gì.
