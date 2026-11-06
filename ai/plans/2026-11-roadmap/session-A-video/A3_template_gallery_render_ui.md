# A3 — UI: Thư viện Template + Trình đổ dữ liệu + Hàng đợi Render

Bạn là Session A. Đọc: `CONTRACTS.md`, `status/A.md`, memory UI của dự án (spacing gọn; nút thêm = thẻ nét đứt cạnh thẻ cuối; cùng thực thể = chung component; bấm vào phải tới đúng mục), `tool/dashboard/components/ui/*` (Card, icons, MorphIcon, ConfirmHost, TooltipHost), cách `components/characters/CharactersManager.tsx` dựng lưới thẻ (tái dùng pattern). Skill `ui-ux-pro-max` để kiểm tra UX.

Chỉ sửa trong: `app/[locale]/templates/**`, `app/[locale]/renders/**`, `components/templates/**`, `components/renders/**`, `nav-modules/video.ts`, `messages/modules/video.*.json`, `store/modules/video.ts`, `lib/api/video.ts`.

## Việc cần làm
1. **`lib/api/video.ts`**: client typed cho mọi endpoint A1/A2 (dùng `CORE_URL` từ `lib/repositories/core.ts` — chỉ import, không sửa).
2. **Trang `/templates`** (Thư viện):
   - Lọc theo category (chip), nền tảng (icon), tìm kiếm. Lưới thẻ `TemplateCard` (preview.jpg, hover phát preview.mp4 muted, badge nền tảng, thời lượng).
   - Bấm thẻ → `/templates/[id]`.
3. **Trang `/templates/[id]`** (Đổ dữ liệu & render):
   - Trái: form sinh tự động từ `slots` (`SlotField` theo type: text có đếm ký tự, media[] kéo-thả + chọn từ thư viện project `GET /projects/{pid}/library`, product chọn từ `products/` (đọc qua API B nếu có `GET /projects/{pid}/products`; nếu 404 thì cho nhập tay), voice chọn bằng component có sẵn `components/voice/VoiceSelectorWithClone.tsx` (import, không sửa), script textarea).
   - Phải: khung preview đổi được nền tảng (tab TikTok/Reels/Shorts/YouTube/Facebook/Douyin) có **overlay safe-zone** bật/tắt; nút "Xem nhanh" (preview 540p).
   - Dưới: chọn nhiều nền tảng (checkbox) + "Tự tạo bài nháp sau khi render" (→ `data.auto_draft=true`) + nút Render.
   - Validate realtime qua `POST /validate`, lỗi hiển thị ngay dưới slot.
4. **Trang `/renders`** (Hàng đợi): danh sách job (trạng thái, % qua SSE, nền tảng, thời gian), mở chi tiết: player từng nền tảng, tải mp4, thumbnail, log, nút Huỷ / Render lại / "Gửi sang Lịch đăng" (gọi API C `POST /projects/{pid}/social/posts/draft` nếu tồn tại, không thì hiện hướng dẫn). Thẻ job dùng chung 1 component `RenderJobCard` ở mọi nơi.
5. **Studio canvas**: node `template_render` (A2) hiển thị trong canvas qua cơ chế node-types sẵn có. KHÔNG sửa `StudioCanvas.tsx`/`StudioNode.tsx`; nếu cần UI riêng cho param node, ghi vào `REQUESTS.md`.
6. Nav: `nav-modules/video.ts` có 2 mục: Template (`/templates`), Render (`/renders`) với icon Morphicons; trạng thái active dùng `MorphIcon`.
7. i18n vi/en đầy đủ trong `messages/modules/video.*.json`.

## Nghiệm thu
- `npx tsc --noEmit | grep -E "templates|renders|lib/api/video|store/modules/video"` sạch.
- Trên `http://localhost:3000`: mở Template → chọn `tiktok-sales-v1` → đổ sample → Render tiktok+youtube → thấy job chạy % → xem 2 video. Chụp màn hình lưu `data/projects/soc-nho-tv/shots/A3_*.png`.
- Kiểm tra mobile 375px không tràn ngang.
- Commit `feat(A3): template gallery, slot editor, render queue UI`. Cập nhật `status/A.md`.
