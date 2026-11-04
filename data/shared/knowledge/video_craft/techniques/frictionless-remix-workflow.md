# Frictionless 3-Step Remix (Quy Trình Remix Video 3 Bước Không Rào Cản)

Tags: ux | template | workflow | hyperframes | automation | ecommerce

## Là gì
Mô hình trải nghiệm người dùng đóng gói toàn bộ quy trình phức tạp của AI (Prompt engineering, negative prompt, checkpoint models, LoRA weighting, sampler steps, composite layers) vào đúng 3 thao tác cơ bản:
1. **Chọn Template có sẵn**: Duyệt thư viện video mẫu đã kiểm chứng hiệu quả.
2. **Nạp Asset Sản Phẩm**: Tải lên 1 ảnh sản phẩm phẳng (quần áo, nội thất, mỹ phẩm).
3. **Bấm Remix & Render**: Hệ thống tự động gán sản phẩm vào slot, đồng bộ voiceover và xuất video.

## Vì sao hiệu quả
- **Xóa bỏ rào cản kỹ thuật (Eliminates Cognitive Friction)**: 95% người làm kinh doanh online không muốn và không có thời gian học ComfyUI, mã nguồn hay prompt. Họ chỉ muốn một "nút bấm ra kết quả".
- **Tính nhất quán công nghiệp (Industrial Determinism)**: Template cố định bố cục, safe zone, hiệu ứng chữ và âm thanh giúp video xuất xưởng luôn đạt chuẩn chất lượng 100%, không bị lỗi biến dạng ngẫu nhiên.

## Ví dụ trong video
- Video `seq_003` (`2272929803457749`) @ `t=25.4s -> 35.96s`:
  - Người dùng bấm nút "Remix" trên web Co-Maker, chọn ảnh chiếc áo thun và nhận về video người mẫu KOC ảo mặc áo thun xoay người trong 15 phút.

## Cách làm lại trong dự án này (HyperFrames + Dashboard Session A)
- **Kiến trúc Template HyperFrames**:
  - Mỗi template là một thư mục HTML5 chuẩn:
    - `index.html`: chứa khung bố cục GSAP với các biến CSS hoặc data attribute (`data-slot="product-image"`, `data-slot="koc-model"`, `data-slot="headline"`).
    - `meta.json`: khai báo các slot đầu vào mà người dùng cần điền.
- **Tích hợp Backend Python**:
  - Khi người dùng bấm Remix trên Web Dashboard, API gọi `submit_render(RenderRequest(...))` truyền data slot vào. Engine HyperFrames thay thế các asset slot và chạy headless Chromium render ra MP4 chuẩn 1080x1920.

## Lỗi thường gặp & Cách tránh
- *Lỗi*: Slot sản phẩm bị méo tỉ lệ (aspect ratio distortion) khi ảnh của người dùng không chuẩn kích thước. Khắc phục: Dùng CSS `object-fit: contain` hoặc auto-crop padding thông minh.
- *Lỗi*: Text tiêu đề quá dài làm tràn màn hình. Khắc phục: Giới hạn ký tự (character count limit) trong schema Pydantic hoặc tự động co kích thước font (`clamp()`).

## Mức độ tin cậy
Cao · Cập nhật: 2026-11-04
