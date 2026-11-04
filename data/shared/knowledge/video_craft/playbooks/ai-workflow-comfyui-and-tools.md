# Playbook 07: AI Workflow ComfyUI & Tích Hợp Công Cụ Ngoài (AI Workflow & External Tools)

> Áp dụng cho: Mở rộng pipeline tạo sinh (Generative Pipeline), tích hợp b-roll nâng cao và xử lý công cụ ngoài  
> Mục tiêu cốt lõi: Phân định ranh giới giữa render nội bộ tất định (HyperFrames) và sinh tư liệu ngoài (ComfyUI / Kling / Flux), tối ưu chi phí và tránh vendor lock-in.

---

## 1. Danh Sách Kỹ Thuật Sử Dụng
- [`local-comfyui-pipeline`](../techniques/local-comfyui-pipeline.md): Xây dựng pipeline sinh ảnh/b-roll cục bộ không tốn phí token.
- [`multi-agent-broll-orchestration`](../techniques/multi-agent-broll-orchestration.md): Điều phối song song nhiều agent tạo sinh tài nguyên.
- [`dual-node-video-stitching`](../techniques/dual-node-video-stitching.md): Kỹ thuật nối cảnh video bằng outpainting AI.
- [`video-element-replacement`](../techniques/video-element-replacement.md): Thay thế vật thể hoặc phông nền qua inpainting.

---

## 2. Quy Trình Từng Bước (Step-by-Step Workflow)

### Bước 1: Phân Loại Tác Vụ Theo Tiers (Kiến Trúc Đa Tầng)
Hệ thống SocNhoTV phân tầng xử lý nghiêm ngặt:
1. **Tier 0 (Local Deterministic - Mặc định, 0đ API):**
   - Dựng trực tiếp từ ảnh DNA sẵn có + OmniVoice local + HyperFrames HTML5/GSAP.
   - Luôn hoạt động ngay cả khi ngắt kết nối mạng hoặc hết quota API.
2. **Tier 1 (Cloud Fallback / AI Enhancer):**
   - Sử dụng khi cần sinh b-roll phong cảnh mới hoặc minh họa phức tạp.
   - Gọi qua các adapter thống nhất tại `tool/src/socnhotv/adapters/` (Google Gemini, OpenAI, Claude, Replicate).
3. **Tier 2 (Heavy Generative / Local GPU ComfyUI):**
   - Dành cho các tác vụ sinh video diffusion nặng (Kling, Runway, AnimateDiff).
   - Chỉ kích hoạt khi máy host có card đồ họa chuyên dụng và người dùng bật cờ `--use-comfyui`.

### Bước 2: Chuẩn Hóa Dữ Liệu Đầu Vào & Đầu Ra
- Mọi tài nguyên sinh từ công cụ ngoài phải được lưu vào thư mục `data/projects/<project-id>/raw/` hoặc `library/`.
- Định dạng xuất chuẩn:
  - Video B-roll: MP4 H.264, 1080x1920 (9:16) hoặc 1920x1080 (16:9), 30fps.
  - Hình ảnh: PNG 24-bit hoặc WebP chất lượng 90%.

### Bước 3: Đưa Tài Nguyên Vào Engine HyperFrames
- Thay vì ghép nối trực tiếp bằng ffmpeg dòng lệnh dễ lỗi codec, tài nguyên sau khi sinh được nạp làm thẻ `<video>` hoặc `<img>` trong composition HTML5 của HyperFrames.
- HyperFrames chịu trách nhiệm cắt cúp, áp dụng chuyển cảnh và master âm thanh cuối cùng.

---

## 3. Khuôn Mẫu Cấu Hình Prompt ComfyUI / API Call

```json
{
  "workflow_id": "broll-nature-generator",
  "model": "flux-1-schnell",
  "prompt": "Cinematic shot of raindrops falling into a tranquil forest puddle, macro lens, water ripples reflecting sunlight, 4k ultra-detailed",
  "aspect_ratio": "9:16",
  "steps": 4,
  "output_dir": "data/projects/soc-nho-tv/raw/broll/"
}
```

---

## 4. Sai Lầm Thường Gặp (Pitfalls to Avoid)
1. **Phụ thuộc cứng vào 1 nhà cung cấp cloud:** Khi nhà cung cấp tăng giá hoặc đổi API, hệ thống bị tê liệt. Luôn giữ Tier 0 hoạt động độc lập.
2. **Chờ đợi render video diffusion quá lâu trong luồng chính:** Tác vụ sinh video AI ngoài mất 1-3 phút, phải chạy dạng bất đồng bộ (Queue / Background Job).
3. **Méo hình dạng hoặc mất nhận diện nhân vật (Character Hallucination):** Mô hình video ngoài dễ làm biến dạng tai hoặc mắt của Sóc Nhỏ. Không đưa nhân vật chính vào video diffusion nếu chưa huấn luyện LoRA đặc thù.

---

## 5. Checklist Trước Khi Xuất Bản (Pre-Publish Checklist)
- [ ] Tier 0 local luôn sẵn sàng chạy dự phòng nếu mạng gặp sự cố.
- [ ] Mọi asset sinh từ AI ngoài đã được kiểm tra tính toàn vẹn (không lỗi glitch, méo chữ).
- [ ] Video B-roll tuân thủ đúng khung hình 9:16 và tốc độ khung hình 30fps.
- [ ] Nhân vật chính Bi và Koala không bị lệch nhận diện master DNA.
