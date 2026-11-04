# Playbook 08: Chiến Lược Video KOC Thời Trang Ảo & Virtual Try-On (TikTok AI VTON Mastery)

> Áp dụng cho: Kênh TikTok Shop, Affiliate thời trang, Lookbook ảo, Showroom thương hiệu số  
> Mục tiêu cốt lõi: Tối ưu tỷ lệ nhấp vào giỏ hàng (Cart CTR >= 4.5%), giữ chân người xem bằng trải nghiệm thời trang sống động và form dáng chuẩn xác.

---

## 1. Danh Sách Kỹ Thuật Sử Dụng
- [`virtual-try-on-pipeline`](../techniques/virtual-try-on-pipeline.md): Ghép trang phục thật lên mẫu KOC AI với độ chuẩn xác nếp gấp và hoa văn.
- [`ai-video-realism-anti-artifact`](../techniques/ai-video-realism-anti-artifact.md): Triệt tiêu biến dạng bề mặt vải, hiện tượng da sáp giả và ánh sáng vô trọng lực.
- [`walking-outfit-transition`](../techniques/walking-outfit-transition.md): Chuyển đổi 3-4 outfit liên tục theo từng bước chân dậm nhịp.
- [`split-canvas-lookbook`](../techniques/split-canvas-lookbook.md): Chia màn hình đôi để đồng thời chiếu form dáng toàn cảnh và cận cảnh chất liệu vải.
- [`first-comment-link-routing`](../techniques/first-comment-link-routing.md): Dẫn hướng người mua vào link giỏ hàng hoặc comment ghim an toàn không bị bóp tương tác.

---

## 2. Quy Trình Từng Bước (Step-by-Step Workflow)

### Bước 1: Hook Bắt Mắt Trong 3 Giây Đầu (0s - 3s)
- Mở màn bằng kỹ thuật **Split Canvas** hoặc **Walking Outfit Transition**:
  - Trình diễn ngay 1 outfit hoàn hảo trong chuyển động xoay 45 độ.
  - Phụ đề động giật tít: *"3 cách phối đồ hack dáng cho nàng công sở dưới 50kg!"* hoặc *"Chiếc váy biến hình đang sốt rần rần trên TikTok..."*.

### Bước 2: Trình Diễn Bằng Chứng Vải Vóc & Form Dáng (3s - 10s)
- Chuyển sang góc quay cận cảnh (Macro Shot) chất liệu vải dệt qua Flux.1 + CatVTON.
- Nổi bật đường may, độ rủ và tính co giãn.
- KOC AI thực hiện động tác xoay nhẹ để thấy độ bay của tà áo.

### Bước 3: Đặt Vào Bối Cảnh Thực Tế (In-Situ Placement) (10s - 18s)
- Thay đổi phông nền phía sau KOC từ studio sang quán cà phê ngoài trời hoặc sảnh văn phòng hiện đại.
- Giọng đọc OmniVoice truyền cảm nhấn mạnh tính ứng dụng thực tế (đi làm, đi chơi, không lo nhăn).

### Bước 4: Chuyển Hướng Giỏ Hàng An Toàn (18s - 25s)
- Hiển thị bảng tag kích cỡ (Size S/M/L) trong vùng an toàn (TikTok Safe Zone: cách đáy 320px).
- Nút CTA động với icon MorphIcon nhấp nháy hướng xuống góc trái dưới màn hình: *"Nhấp vào góc trái bên dưới để rinh ngay em nó với voucher giảm 50k nha!"*.

---

## 3. Khuôn Mẫu Kịch Bản 25s (VTON Conversion Blueprint)

```
[00:00 - 00:03] (Hook Visual):
KOC bước đi dậm nhịp, trang phục biến hình mượt mà từ bộ đồ mặc nhà sang set đầm công sở sang trọng.
VO: "Đừng vội mua đồ thu đông nếu nàng chưa biết set đồ hack dáng đỉnh cao này!"

[00:03 - 00:10] (Texture Proof):
Khung hình chia đôi: Bên trái KOC xoay 360 độ, bên phải macro cận cảnh đường may và cúc ngọc trai.
VO: "Chất vải dệt kim tăm cao cấp, co giãn 4 chiều mềm mịn như mây mà giặt máy không lo bai dão nha."

[00:10 - 00:18] (Lifestyle Context):
KOC ngồi uống trà trong quán cafe ngập nắng.
VO: "Mặc đi làm thanh lịch, chiều đi hẹn hò với người thương thì bao xinh luôn. Tôn eo cực đỉnh cho các nàng từ 45 đến 58kg."

[00:18 - 00:25] (Safe-Zone CTA):
Icon giỏ hàng nhấp nháy ở vùng an toàn đáy màn hình.
VO: "Số lượng deal hời trong giỏ hàng góc trái có hạn thôi, các nàng nhanh tay bấm vào giỏ để nhận ưu đãi hôm nay nhé!"
```

---

## 4. Checklist Kiểm Định Trước Khi Đăng (Pre-Publish Checklist)
- [ ] Ảnh gốc trang phục chuẩn màu 98% so với sản phẩm thực tế giao cho khách.
- [ ] Không có chi tiết bàn tay 6 ngón hoặc biến dạng khuôn mặt khi xoay góc.
- [ ] Vùng giỏ hàng và thanh tiêu đề không che mất mặt KOC hoặc phụ đề chính.
- [ ] Âm lượng đạt chuẩn -14 LUFS, không có tiếng rè hoặc méo tiếng.
