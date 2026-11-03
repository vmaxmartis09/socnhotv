# Quy tắc UI của AI Video Studio (bắt buộc cho mọi thay đổi giao diện)

1. **Hộp hành động mở sát icon**: hộp xác nhận (và mọi hộp hành động nhỏ) mở ngay cạnh icon đã gọi nó, với animation icon "mọc"
   thành hộp (scale từ vị trí icon, bo tròn → bo góc); không mở giữa màn hình trừ khi gọi bằng bàn phím. `confirm()` tự lấy vị trí nút bấm gần nhất.
1b. **Xác nhận dùng chung**: mọi xóa/tạo/đổi quan trọng gọi `await confirm({ tone, title, message })` từ `lib/confirm.ts`
   (tone: danger | warning | info | success, mỗi mức có icon và màu riêng). Không dùng `window.confirm`.
2. **Mở rộng thay vì modal**: nơi nào panel mở rộng được thì mở rộng sang trái để xem trước
   (`lib/preview.ts` → `usePreview.open(...)`). Chỉ dùng modal cho xác nhận và form ngắn.
2b. **Chuyển tab thì tab mở rộng đi kèm phải tắt**: đổi panel, đổi tab con, đổi mục đang chọn đều gọi
   `usePreview.getState().close()`. Vùng xem trước chỉ thuộc về ngữ cảnh đã mở nó.
3. **Click vs nhấn đúp**: click = chọn + xem trước; nhấn đúp = mở/vào (dự án → vào Studio, kịch bản → đọc đầy đủ,
   job → focus node trong Studio).
4. **Icon thay chữ**: chỗ nào dùng được icon thì dùng icon kèm tooltip. `components/ui/TooltipHost.tsx` (gắn ở layout) hiện tooltip
   tức thì cho mọi phần tử có `title`, `data-tip`, hoặc nút chỉ-icon có `aria-label`; nút icon mới BẮT BUỘC có một trong các thuộc tính đó.
5. **Căn trái** mọi thứ có tab; không căn giữa/phải.
6. **Thanh cuộn**: không hiện bừa bãi. Vùng cuộn dùng `scroll-quiet`, hàng ngang dùng `no-scrollbar`; mọi danh sách
   dài đều cuộn được (hàng ngang hỗ trợ lăn chuột).
7. **Thanh điều hướng là "sticky" nổi** (viên thuốc bo tròn, không phải rail dính cạnh): thanh công cụ Studio (trái, giữa),
   thanh Sảnh/Studio/Công việc + hồ sơ (trái, dưới), dock panel (phải, giữa). Dock và panel là một khối nổi tự to ra khi mở,
   hiện nhãn khi mở. KHÔNG làm rail full-height dính cạnh màn hình.
8. **Studio là toàn màn hình**: breadcrumb, công cụ, hồ sơ nổi trên canvas. Breadcrumb bắt đầu bằng icon Sảnh.
9. **Phím tắt** khai báo ở một chỗ: `lib/shortcuts.ts` (hiển thị ở panel Phím tắt, phím `?`). `Esc` đóng xem trước rồi thu gọn panel.
10. **Trạng thái AI** luôn dùng `components/ui/AiLoading.tsx` (tia sáng + chữ chạy ánh sáng + khung xương).
11. **Animation** cho mọi chuyển đổi (framer-motion): mở/đóng, đổi tab, danh sách xuất hiện, bấm nút (`active:scale`).
12. **Chọn dự án thì Studio theo**: dùng `switchProject(id)`; không gọi `setActiveProjectId` trực tiếp.
13. **Thông tin trống phải có dấu hiệu, không chiếm chỗ**: mục/tab/nút không có dữ liệu thì mờ + vô hiệu hóa (tooltip "— trống"),
    một cụm mục trống gom thành MỘT dòng mờ nét đứt (bấm để bổ sung), không dựng khối rỗng. Số đếm gắn vào chính tab/nút (không đặt số trôi nổi).
14. **Neo vị trí**: vùng chứa UI nổi dùng `overflow-clip` (không `overflow-hidden`) để focus/scrollIntoView không đẩy thanh nav lệch khỏi màn hình.
15. **Chi tiết trong tab**: ở tab đã chọn/focus được mục (ví dụ Dự án), bấm vào chỉ hiện chi tiết ngay trong tab kèm nút quay lại; không mở thêm vùng mở rộng.
16. **Công việc** là một tab riêng ở dock phải (icon Activity, nhãn "Công việc"), có chấm số job đang chạy.
17. **Chuyển động nhẹ, dễ chịu**: không dùng spring nảy, không scale mạnh; mở/đóng/co giãn dùng tween 0.15–0.25s ease-out
    (`[0.22, 1, 0.36, 1]`), chỉ đổi kích thước một lần mượt; nội dung đổi bằng mờ dần, không trượt xa.
18. **Không lặp animation**: cái đã hiện rồi thì khi mở cái khác/quay lại không chạy lại hiệu ứng xuất hiện (khung, dock, danh sách, ảnh, thẻ).
    Dùng `initial={enterOnce(key, {...})}` từ `lib/motion.ts`; đổi nội dung trong khối đã mở thì đổi ngay, chỉ khối mới mở mới có animation.
19. **Không có hai nút cùng chức năng trên cùng một mặt giao diện**: trước khi thêm nút, kiểm tra màn hình đã có nút làm việc đó chưa
    (ví dụ: "Vào Studio" chỉ ở chi tiết dự án, không có ở thanh trên; Jobs chỉ ở dock; sửa nhân vật chỉ ở icon bút; chạy node chỉ ở icon Play của node).
    Nút chỉ hiện khi nó làm việc khác với các nút đã có.
20. **Trống thì gợi ý việc cần làm**: ô viền nét đứt kèm icon, tiêu đề + gợi ý ngắn + dấu `+`; mỗi ô một việc riêng (không lặp chức năng với
    nút khác trên màn hình). Ví dụ dự án trống: "Tạo nhân vật" (mở tab Nhân vật), "Dựng tập và kịch bản đầu tiên" (vào Studio + tạo đồ thị mẫu).
21. **Khoảng cách gọn**: trong panel nổi dùng `space-y-3`/`gap-3`, padding thẻ `p-3`; không chừa khoảng trống thừa quanh thành phần.
22. **Nút thêm nằm cạnh các thẻ**: nút "thêm" của một danh sách thẻ là một thẻ trống viền nét đứt đặt ngay sau thẻ cuối (cùng kích thước thẻ),
    bấm vào mở lựa chọn ngay trong thẻ đó; không đặt nút `+` trôi nổi ở góc hàng riêng.
22. **Một thành phần, một giao diện; bấm là tới đúng việc**: cùng một thực thể (nhân vật, tập, flow, job…) hiển thị ở nhiều tab phải dùng CHUNG một component
    (ví dụ thẻ poster nhân vật `components/characters/CharacterPoster.tsx`), không dựng chip/thẻ riêng. Mọi mục hiển thị đều bấm được và đưa tới đúng
    tab + đúng mục đó (`useHubScope.openTab(tab, action, focusId)`; tab đích đọc `pendingFocus` rồi `clearFocus()`).

