# C2 — UI Social Manager: Lịch tháng/tuần kéo-thả · Soạn bài đa nền tảng · Hàng chờ duyệt · Tài khoản

Bạn là Session C. Đọc: `CONTRACTS.md`, `status/C.md`, API C1, memory UI dự án (spacing gọn, nút thêm = thẻ nét đứt cạnh thẻ cuối, cùng thực thể = chung component, bấm vào tới đúng mục), `components/ui/*`, `components/ui/icons.ts` + `MorphIcon.tsx`, skill `ui-ux-pro-max`, `design-taste-frontend` (phần app screens). Thư viện kéo-thả `@dnd-kit/*` và `date-fns` đã được bootstrap cài (kiểm `status/REQUESTS.md`).

Chỉ sửa trong: `app/[locale]/social/**`, `app/[locale]/publish/page.tsx`, `components/social/**`, `components/studio/tabs/PublishTab.tsx`, `nav-modules/social.ts`, `messages/modules/social.*.json`, `store/modules/social.ts`, `lib/api/social.ts`.

## Kiến trúc màn hình `/social`
Thanh trên: chọn project (dùng project active hiện có), bộ lọc nền tảng (icon toggle), tài khoản, trạng thái, tìm kiếm, nút "+ Bài mới". Tab con (URL `/social/[tab]`):
1. **Lịch** (`calendar`) — mặc định.
   - View Tháng / Tuần / Danh sách (agenda) chuyển bằng segmented control, nút Hôm nay, ‹ ›.
   - Ô ngày hiển thị `PostChip` (màu theo nền tảng, chấm trạng thái, giờ, thumbnail nhỏ); quá 3 → "+n".
   - View Tuần: trục giờ 00–24, slot `RecurringSlot` hiển thị nền sọc nhạt = "khung giờ vàng trống", bấm slot trống → soạn bài với giờ đó.
   - **Kéo-thả** chip đổi ngày/giờ (`PUT …/targets/{tid}/time`), optimistic update + hoàn tác (toast "Hoàn tác"). Không cho kéo bài `published`.
   - Ghi chú ngày (11.11, Tết…) hiện dải màu đầu ô.
   - Múi giờ hiển thị rõ góc phải (Asia/Ho_Chi_Minh).
2. **Hàng chờ duyệt** (`approvals`): danh sách `pending_approval` dạng thẻ lớn: player video, caption từng nền tảng (tab), checklist tự động (đủ caption, có disclosure nếu affiliate, độ dài video ≤ giới hạn nền tảng, tỉ lệ đúng, account còn kết nối, `source_ref` rights ≠ reference_only nếu dùng clip gốc — đọc `raw/<id>/meta.json` qua API B `GET /projects/{pid}/sources/{sid}` nếu có). Nút Duyệt / Từ chối (bắt nhập lý do) / Sửa. Duyệt hàng loạt có xác nhận (`lib/confirm.ts`).
3. **Bài viết** (`posts`): bảng tất cả post, lọc/sắp xếp, chọn nhiều → đổi trạng thái, nhân bản, huỷ.
4. **Tài khoản** (`accounts`): lưới `AccountCard` (avatar, handle, nền tảng, trạng thái kết nối, số bài đã lên lịch tuần này, khung giờ đăng) + thẻ "Thêm tài khoản" nét đứt cạnh thẻ cuối. Dialog thêm: chọn nền tảng → chọn chế độ (OAuth chính chủ — nút "Kết nối" sẽ hoạt động ở C3; Thủ công — nhập handle/URL). Sửa posting windows bằng lưới 7 ngày × khung giờ.
5. **Phân tích** (`analytics`): placeholder, C4 làm.

## Trình soạn bài `PostComposer` (drawer phải, dùng chung cho mọi nơi tạo/sửa bài)
- Media: chọn từ `/renders` của A (`GET /projects/{pid}/video/renders?status=done` nếu có) hoặc thư viện project, hoặc từ inbox; tự chọn biến thể đúng nền tảng (`outputs[platform]`).
- Chọn nhiều tài khoản → mỗi tài khoản 1 tab `TargetEditor`: caption (đếm ký tự theo giới hạn), hashtag chips, YT title/description/tags/privacy/made_for_kids, cover time, first comment, product link + tick "Nội dung quảng cáo/affiliate", giờ đăng (date-time picker + nút "Giờ gợi ý" gọi `/suggest-time`).
- Nút "Sinh caption cho tất cả nền tảng" → `/caption-variants`.
- Lưu nháp / Gửi duyệt / (nếu đã duyệt) Lên lịch.
- Xem trước dạng khung điện thoại từng nền tảng (caption cắt "…xem thêm" đúng chỗ).

## Gộp khu lịch cũ
- `PublishTab.tsx` (tab phải trong Studio): thay bằng bản rút gọn dùng **chung component** `PostChip`/`AgendaList` của C — hiển thị 7 ngày tới cho project active, nút "Mở Social Manager" → `/social/calendar`, nút "+ Lên lịch" mở `PostComposer`. Bỏ gọi endpoint 404. Không đụng store chính: dùng `store/modules/social.ts` (state: posts, accounts, filters, view, selectedDate; actions gọi `lib/api/social.ts`).
- `app/[locale]/publish/page.tsx` → redirect sang `/social/calendar`.
- Nav: 1 mục "Social" icon Morphicons (`MorphIcon` khi active).
- Bảng ý tưởng từ B: trong view Tuần có cột trái "Ý tưởng chờ lên lịch" (đọc ideas qua `GET /projects/{pid}/intel/ideas?status=scripted,rendered` nếu có), kéo ý tưởng vào ô lịch → `POST /social/ideas/{iid}/schedule`.

## Nghiệm thu
- `npx tsc --noEmit | grep -E "social|PublishTab|publish/page"` sạch.
- Trên `http://localhost:3000/vi/social`: thấy dữ liệu đã di trú; tạo bài 2 tài khoản (TikTok + YouTube thủ công) → gửi duyệt → duyệt → thấy trên lịch → kéo sang ngày khác → reload vẫn còn. Mobile 375px: lịch tháng chuyển thành agenda, không tràn ngang. Dark mode đúng.
- Chụp `data/projects/soc-nho-tv/shots/C2_*.png` (tháng, tuần, duyệt, composer).
- Commit `feat(C2): social manager UI (calendar dnd, composer, approvals, accounts)`. Cập nhật `status/C.md`.
