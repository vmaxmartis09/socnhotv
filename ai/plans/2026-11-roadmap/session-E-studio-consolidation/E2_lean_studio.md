# E2 — Studio tối giản: TẠO VIDEO tự động + MỘT chỗ quản lý & hẹn giờ đăng. Cắt hết phần thừa.

Bạn là SESSION E2 (Vỏ ứng dụng gọn), session ĐỘC LẬP chạy SONG SONG với session E3 (`E3_node_inputs_first.md` — làm node nhập liệu), không chờ nhau. Đọc `NODE_PARAMS_CONTRACT.md` cùng thư mục TRƯỚC: nó chốt tên tham số node và phân vùng file. **Bạn KHÔNG sửa** `components/canvas/**` (trừ thêm đúng 1 nút "Tạo video" vào `StudioStickToolbar.tsx`), `NodeTab.tsx`, `canvasSlice.ts`, `i18n/request.ts`, backend. Nhãn mới đặt trong `messages/modules/studio.{vi,en}.json`. Preset đồ thị viết ở `lib/graph-presets.ts` và áp bằng action có sẵn `setNodesAndEdges`. Mục nghiệm thu "ra mp4 thật bằng kịch bản dán sẵn" cần dòng `RUNNER_PASTE_DONE` trong `status/E3.md`: chưa có thì chạy thử bằng `mode:"ai"` + provider mock, ghi rõ vào `status/E2.md`, làm nốt việc khác rồi quay lại kiểm. Làm đến cùng, tự debug, không hỏi lại điều có thể tự suy ra. Đọc: `CLAUDE.md`, `ai/AGENTS.md`, memory UI dự án (spacing gọn; nút thêm = thẻ nét đứt cạnh thẻ cuối; cùng thực thể = chung component, bấm được tới đúng mục), skill `ui-ux-pro-max`, `design-taste-frontend`. File này THAY E1.

## 0. Mục tiêu duy nhất của sản phẩm (người dùng đã chốt)
1. **Làm ra 1 hoặc nhiều video, có kịch bản tự động hoá**, ngay trong Studio.
2. **Template có sẵn tự sinh ra đồ thị trong Studio** với đúng kích thước/chất lượng/nền tảng — người dùng không phải tự chỉnh thông số kỹ thuật.
3. **Một chỗ quản lý social**: tài khoản, lịch, và người dùng tự bấm đăng/hẹn giờ.
Hết. Mọi thứ không phục vụ 3 việc này → bỏ khỏi UI (giữ backend nằm im, không bảo trì).

## 1. Thực trạng cần sửa (đã khảo sát)
- 3 session đã dựng 6 trang cấp cao (Templates · Renders · Sources · Products · Intel · Social) hiện trên `PageBar` + ~11.000 dòng UI (`components/{social,templates,renders,sources,products,intel}` + `app/[locale]/{templates,renders,sources,products,intel,social}`), trong khi tab phải thật `components/studio/tabs/PublishTab.tsx` chỉ 83 dòng.
- Trang Templates trống: uvicorn cổng 8000 chạy bản cũ, `GET /video/templates` trả 404 dù `data/shared/templates/` có 8 mẫu → phải chạy lại core. Overlay lỗi Next "4–8 Issues", nền sáng/tối lệch, nhãn tiếng Anh sót.
- Số liệu phân tích MẪU (`social/seed_sample_analytics.py`, `data/projects/soc-nho-tv/analytics/*`, và đoạn "12.4K views/78.5%" trong `status/REQUESTS.md`) đang bị coi như thật.

## 2. Kiến trúc đích

### 2.1 Chỉ còn các trang: `/` (Sảnh), `/studio`, `/characters`, `/projects`, `/settings`, `/jobs`
Xoá các trang `/templates`, `/templates/[id]`, `/renders`, `/renders/episode/[eid]`, `/sources`, `/products`, `/intel`, `/social`, `/publish` (route cũ redirect về `/studio`, mẫu `publish/page.tsx` hiện có). `PageBar` trở lại chỉ: Sảnh › dự án đang mở. Xoá `nav-modules/*` nếu không còn ai dùng.

### 2.2 Panel phải vẫn 5 tab, KHÔNG thêm tab/mục: chat · node · project · **Đăng** · jobs
Không nhét Nguồn/Sản phẩm/Ý tưởng/Phân tích/Blueprint vào Project. Xoá UI của chúng:
`components/intel/*`, `components/products/*`, `components/sources/*`, `components/renders/EpisodeBuildPanel.tsx`, `components/templates/*` (trừ phần dùng lại ở 2.3), **KHÔNG đụng `components/social/**` và `PublishTab.tsx`: do session S (`session-S-social-manager/S1_social_manager.md`) sở hữu và làm lại toàn bộ tab Đăng/Lịch.** Bạn chỉ xoá trang `/social`, `/publish` (redirect) và các thứ ngoài social.
Ẩn khỏi bảng thêm node các node phụ: `source_video`, `localize`, `blueprint_analyze`, `script_from_blueprint`, `channel_insight` (giữ code backend; chỉ lọc ở frontend bằng 1 danh sách ẩn). Giữ hiển thị `template_render`, `platform_export`.

### 2.3 Luồng "TẠO VIDEO" — nút chính trên thanh công cụ Studio (`StudioStickToolbar`)
Mở **panel nổi 3 bước** (tái dùng `SlotField`, `SlotValidate`, `VoiceSelectorWithClone`, API `lib/api/video.ts`):
1. **Chọn mẫu**: lưới gọn 8 mẫu từ `GET /video/templates` (ảnh preview, tên, nền tảng, thời lượng; hover xem preview). Không bộ lọc rườm rà (tối đa 1 hàng chip loại).
2. **Nội dung**: 
   - Ô "Chủ đề/ý tưởng" + nút **Tự viết kịch bản** (dùng API sẵn có `POST /projects/{pid}/ai/script`, hoặc `intelligence.script_gen` qua API nếu phù hợp mẫu: bán hàng/KOC/affiliate); hoặc dán kịch bản có sẵn. Kịch bản tự điền các slot của mẫu (hook, thân, CTA); sửa được từng slot.
   - Slot sản phẩm nhập thẳng trong form (tên, giá, USP, ảnh) — **không có kho sản phẩm riêng**.
   - Chọn nhân vật + giọng (mặc định Sóc Nhỏ + `soc-nho`).
   - **Nhiều video**: chuyển công tắc "Hàng loạt" → mỗi dòng 1 chủ đề (hoặc 1 kịch bản ngăn bằng `---`), N dòng = N video dùng cùng mẫu/giọng.
3. **Xuất**: nền tảng (tick; mặc định theo mẫu), chất lượng 2 mức (Chuẩn / Cao). **Kích thước, fps, safe-zone, -14 LUFS, codec tự lấy từ preset `video/platforms.py`, không có ô nhập thông số.** Hiện ước tính chi phí tổng (từ `/estimate` + `spend_guard`) và 1 nút **Tạo**.
Khi bấm Tạo, với mỗi video: tạo 1 tập/đồ thị (đặt tên theo chủ đề) trong Studio với **preset đồ thị đã nối dây** (ví dụ: script → voice_tts → captions → template_render → platform_export), đúng node trong `GET /node-types`, kiểm bằng `POST /projects/{pid}/graph/validate`; xếp bước chạy theo trục trái→phải sẵn có; rồi đưa vào hàng đợi chạy (tuần tự, không song song nhiều hơn `SOCNHOTV_RENDER_PARALLEL`). Bấm vào tập ở Sidebar để xem/sửa đồ thị như bình thường.
`PreviewPane` có tab nền tảng + bật/tắt safe-zone (chuyển logic từ trang template cũ).

### 2.4 Tab **Jobs**: hàng đợi render duy nhất
Hợp nhất `RenderJobCard` (% qua SSE, huỷ, chạy lại, xem/tải từng nền tảng) + chi phí hiện có; chip lọc Chạy/Xong/Lỗi. Job xong có nút **"Đăng/Lên lịch"** → mở composer với video đã chọn sẵn.

### 2.5 Tab **Đăng** — ĐÃ GIAO CHO SESSION S (bỏ qua mục này; chỉ đảm bảo nhãn tab tiếng Việt "Lịch đăng" và nút "Đăng/Lên lịch" ở Jobs gọi composer của S qua `store/modules/social.ts` action `openPlanner({videoIds})` nếu S đã có, chưa có thì mở tab Lịch đăng). Mô tả dưới đây chỉ để tham khảo ý đồ:
- **Tài khoản** (thẻ gọn + thẻ nét đứt "Thêm tài khoản"): trạng thái kết nối (OAuth chính chủ hoặc "thủ công"), bấm vào sửa khung giờ.
- **Sắp tới**: danh sách bài theo ngày (tái dùng `AgendaList`/`PostChip`): trạng thái nháp/đã hẹn/đã đăng/lỗi; bấm → sửa.
- **+ Lên lịch** → composer (tái dùng `PostComposer` rút gọn ≤ 300 dòng): chọn video từ Jobs, chọn tài khoản, caption/hashtag tự sinh cho từng nền tảng (nút sinh có sẵn), giờ đăng (chọn tay hoặc "giờ gợi ý" theo khung giờ tài khoản), **Hẹn giờ** hoặc **Đăng ngay**. Công tắc "Duyệt trước khi đăng" mặc định bật (không có tab Duyệt riêng — chỉ là trạng thái trong danh sách, duyệt bằng 1 nút).
- **Lịch** (nút mở modal lớn): chỉ `CalendarView` tháng/tuần kéo-thả đổi giờ. Không Analytics, không Automation, không Thông báo, không nhập số liệu.
- Nền tảng không có API → vẫn hẹn giờ; đến giờ tạo "gói đăng tay" + nhắc, nút "Tôi đã đăng" (backend C3 có sẵn). Đăng thật lên tài khoản luôn cần người dùng bấm xác nhận trong UI.
- Mọi dữ liệu thật từ `/projects/{pid}/social/*`; không dữ liệu mẫu, không mặc định giả (tiêu đề trống, media phải chọn thật).

### 2.6 Dữ liệu giả
`seed_sample_analytics` không tự chạy; `git mv` `data/projects/soc-nho-tv/analytics/{metrics,insights,recommendations.json,learnings.md}` → `analytics/_demo/`; thêm ghi chú đầu `status/REQUESTS.md`: các con số 12.4K/78.5%/giờ vàng là DỮ LIỆU MẪU, không dùng để quyết định.

## 3. Thứ tự làm (mỗi bước: kiểm trình duyệt, tsc sạch phần mình sửa, commit riêng bằng đường dẫn)
0. **Chạy lại core đúng bản**: tắt uvicorn 8000 cũ, chạy `cd tool && .venv/bin/python -m uvicorn socnhotv.core.api.app:app --app-dir src --host 127.0.0.1 --port 8000 --reload`; kiểm `/video/templates` trả 8 mẫu, `/social/accounts` hoạt động. Không tắt cổng 3000. Thêm dải cảnh báo nhỏ trong Studio khi core không phản hồi/cũ.
1. **Cắt**: xoá trang/route/component theo 2.1–2.2 và dữ liệu mẫu 2.6; sửa import chết. Viết `status/E_cut.md`: danh sách đã xoá + số dòng trước/sau.
2. **Tạo video** (2.3) — làm trước phần nền tảng tự động hoá: preset đồ thị cho từng mẫu (8 mẫu), validate được; thử chạy với provider mock cho cả 1 video và 3 video hàng loạt.
3. **Jobs** (2.4) và **Đăng** (2.5).
4. **Đồng nhất giao diện**: token theme (không màu cứng), dark/light đúng, hết khối xám đè, i18n vi/en đầy đủ, chỉ Morphicons (`grep -rn "lucide-react" tool/dashboard/{app,components,lib}` = 0), UI gọn.
5. **Sạch lỗi**: duyệt `http://localhost:3000/vi/studio` và từng tab, sửa mọi lỗi console/overlay "Issues" của Next (hydration, key trùng, 404, import chết); `npx tsc --noEmit` và `npm run build` sạch.

## 4. Nghiệm thu (làm thật trong trình duyệt, 1440px và 375px, dark + light)
1. Studio → **Tạo video** → chọn `tiktok-sales-v1` → nhập chủ đề → Tự viết kịch bản → slot tự điền → Tạo → thấy đồ thị nối dây hợp lệ → chạy (mock OK) → job ở tab Jobs → xem được video đúng kích thước 1080×1920.
2. Làm lại với công tắc **Hàng loạt** 3 chủ đề → ra 3 tập/3 job; mẫu `yt-animation-episode-v1` ra 16:9 1920×1080.
3. Job xong → "Đăng/Lên lịch" → composer có video đúng → Hẹn giờ cho 2 tài khoản → thấy ở tab Đăng → mở Lịch kéo sang ngày khác → reload vẫn còn. Tài khoản thủ công tạo được gói đăng tay.
4. Không còn menu 6 mục, không còn trang cũ (redirect đúng); không Next "Issues"; console sạch; không request 404.
5. Số dòng UI giảm ≥ 60% so với hiện tại (trước/sau ghi ở `status/E.md`). `cd tool && .venv/bin/python -m pytest -q` vẫn pass.
6. Chụp ảnh trước/sau vào `data/projects/soc-nho-tv/shots/E_*.png` (Studio, panel Tạo video 3 bước, tab Jobs, tab Đăng, Lịch).

## 5. Luật
- Bước 0 (chạy lại core) theo mục 4 của `NODE_PARAMS_CONTRACT.md` (khoá `.core-restart.lock`, kiểm `--reload`), không giẫm chân E3.
- Không xoá backend/API/test/dữ liệu người dùng; chỉ xoá UI và `git mv` dữ liệu mẫu. Không sửa core engine/providers/adapters (trừ lỗi chặn UI, ghi rõ).
- Không thêm trang, tab, thư viện UI, hay tính năng ngoài 3 mục tiêu ở mục 0. Nếu muốn thêm → ghi đề xuất vào `status/E.md`, không tự làm.
- Session D có thể đang ghi `data/shared/knowledge/video_craft/**`: `git add` theo đường dẫn của bạn, không `git add -A`/stash/reset.
- Báo cáo thật: cái gì chưa làm/chưa kiểm chứng ghi vào `status/E.md`; cuối cùng tóm tắt tiếng Việt: đã xoá gì, còn gì, còn nợ gì.
