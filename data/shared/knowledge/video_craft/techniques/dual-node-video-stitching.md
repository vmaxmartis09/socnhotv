# Dual-Node Video Stitching (Kỹ Thuật Nối Video Đa Phân Đoạn Bằng Khung Hình Khóa)

Tags: ai-workflow | video-generation | continuity | kling | hyperframes | editing

## Là gì
Kỹ thuật sản xuất video AI dài (30 giây – 60 giây) mạch lạc mà không bị biến dạng cơ thể (morphing drift) bằng cách chia nhỏ thành các phân đoạn ngắn 10s–15s. Khung hình cuối cùng (Last-Frame) của phân đoạn trước được trích xuất để làm khung hình bắt đầu (Start-Frame) cho phân đoạn kế tiếp, sau đó ghép nối trên timeline HyperFrames.

## Vì sao hiệu quả
- **Khắc phục giới hạn của mô hình Diffusion thời gian**: Các mô hình như Kling 1.5, Runway Gen-3, Wan 2.1 hoạt động ổn định nhất trong khoảng 5s–15s đầu. Nếu ép mô hình sinh liên tục 30s trong 1 prompt, nhân vật sẽ dần bị biến dạng mặt, tay chân thừa hoặc màu áo bị đổi.
- **Tạo sự đa dạng về góc máy (Multi-shot variety)**: Phân đoạn 1 dùng góc toàn cảnh dạo phố (Wide Shot), phân đoạn 2 dùng góc cận cảnh xoay người (Close-up Turn). Việc đổi góc máy giữa 2 phân đoạn giúp video giữ chân người xem tốt hơn một góc máy tĩnh buồn ngủ kéo dài suốt 30 giây.

## Ví dụ trong video
- Video `seq_007` (`1083694434486679` - Thân Ca) @ `t=114.7s -> 174.7s`:
  - Node 1: Kling 1.5 tạo clip 15s dạo phố góc 1–12.
  - Node 2: Dùng frame cuối của Node 1 làm input, Kling 1.5 tạo clip 15s xoay người góc 16–24.
  - Ghép 2 clip lại thành video 30 giây hoàn chỉnh.

## Cách làm lại trong HyperFrames
- **Timeline Composition HTML5**:
  ```html
  <div class="video-stitch-container">
    <video class="clip" data-start="0" data-duration="15" src="kling_part1_15s.mp4" style="width: 100%; height: 100%; object-fit: cover;"></video>
    <video class="clip" data-start="15" data-duration="15" src="kling_part2_15s.mp4" style="width: 100%; height: 100%; object-fit: cover;"></video>
  </div>
  ```
- **Chuyển cảnh mượt mà**:
  - Dùng hiệu ứng Flash cut hoặc Whip pan nhẹ 0.15s ngay tại mốc `t=15.0s` bằng GSAP để che đi bất kỳ sai lệch nhỏ nào về ánh sáng giữa 2 lần render.

## Mức độ tin cậy
Tuyệt đối · Cập nhật: 2026-11-04
