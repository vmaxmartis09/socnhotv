# In-situ KOC Placement (Ghép Nhân Vật KOC Vào Bối Cảnh Sản Phẩm Thật)

Tags: ai-workflow | virtual-koc | product-placement | ecommerce | hyperframes

## Là gì
Kỹ thuật lấy trực tiếp hình ảnh chụp sản phẩm thực tế (nội thất, thời trang trên ma-nơ-canh, đồ gia dụng đặt tại phòng khách/bếp) làm background, sau đó đưa nhân vật ảo (Virtual KOC hoặc nhân vật 3D hoạt hình) vào đúng vị trí tương tác (ngồi, đứng tựa, cầm nắm) với tỷ lệ chuẩn xác và bóng đổ chân thực.

## Vì sao hiệu quả
- **Tận dụng 100% kho ảnh sản phẩm có sẵn**: Doanh nghiệp hoặc shop bán hàng không cần chi tiền dựng studio hay thuê thợ quay đắt đỏ; chỉ cần gửi ảnh sản phẩm chụp điện thoại.
- **Tăng tính tin cậy (Social Proof)**: Sản phẩm trông giống hệt hàng thật khách sẽ nhận được, loại bỏ cảm giác "video hoạt hình vẽ viển vông".
- **Sản xuất hàng loạt (Scalability)**: Một nhân vật KOC có thể xuất hiện trong 100 bối cảnh phòng khác nhau trong vòng vài phút.

## Ví dụ trong video
- Video `seq_001` (`1342818958924942`) @ `t=8.92s -> 21.08s`:
  - Ảnh bộ sofa xám đặt trong phòng khách được chèn nhân vật nữ AI ngồi tự nhiên, tay ấn xuống đệm ghế chứng minh độ đàn hồi.

## Cách làm lại trong dự án này (HyperFrames + Gobi Ecosystem)
- **Chuẩn bị Asset**:
  - `background_image`: Ảnh sản phẩm (tỉ lệ 9:16 hoặc 4:5).
  - `character_clip`: Nhân vật AI KOC (LyLy/Neau hoặc Sóc Nhỏ Bi/Koala) xuất dưới dạng video WebM alpha trong suốt hoặc MP4 kèm track green-screen / matte.
- **Tỉ lệ nhân vật khóa cứng theo luật dự án**:
  - Khi dùng Bi & Koala: Sóc Nhỏ (Bi) 100cm, Koala 150cm (tuân thủ `SCALE_LOCK.md`). Đặt Bi ngồi vừa vặn trên ghế sofa, chân buông lơ lửng đáng yêu.
- **Hiệu ứng đổ bóng trong HyperFrames**:
  - Thêm một `<div>` bóng đổ mờ (`box-shadow` hoặc gradient ellipse đen mờ `rgba(0,0,0,0.35) blur(12px)`) dưới chân/đáy nhân vật để gắn nhân vật vào mặt sàn bối cảnh.
- **Animation tương tác**:
  - Sử dụng GSAP scale/translate đồng bộ với lời thoại khi chỉ tay vào chi tiết sản phẩm.

## Công cụ, Chi phí & Thời gian
- **Công cụ**:
  - Sinh nhân vật: Flux Inpainting / LivePortrait / Kling Video-to-Video.
  - Biên tập composition: HyperFrames HTML5/GSAP.
- **Chi phí**: Dưới 0.05$ cho 1 video hoàn chỉnh (chủ yếu là token sinh video clip ngắn 3-5s của nhân vật).
- **Thời gian render**: ~15-30 giây trên HyperFrames CLI (`python -m socnhotv video render`).

## Lỗi thường gặp & Cách tránh
- *Lỗi*: Tỷ lệ nhân vật không tương xứng với đồ vật (nhân vật quá to hoặc quá bé so với ghế/bàn). Khắc phục: Khóa cứng scale ratio và căn chỉnh theo điểm neo (anchor points).
- *Lỗi*: Ánh sáng trên nhân vật ngược hướng với ánh sáng trong ảnh phòng. Khắc phục: Dùng CSS filter điều chỉnh brightness/contrast hoặc prompt khớp hướng nắng (Lighting alignment).

## Cách đo hiệu quả
- Chỉ số **Product Click-Through Rate (CTR)** và **Conversion Rate (CR)** trên TikTok Shop / Facebook Shop.

## Nguồn tham khảo
- Video `1342818958924942` (Seq 001)
- Flux.1-Fill inpainting documentation
- HeyGen HyperFrames composition blueprints (`ai/skills/hyperframes*`)

**Mức độ tin cậy**: Cao · Cập nhật: 2026-11-04
