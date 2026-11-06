# G1: Nguồn AI miễn phí (lùng sục, kiểm thật, tích hợp)

> Thuộc Session G. Đọc trước: `status/THUC_TRANG_2026-11-06.md`, `README.md` (mục 3, 4, 6).
> Giải quyết **N1**: hiện không có nguồn sinh ảnh/video nào dùng được (key Gemini hỏng, không có fal/replicate).
> Báo cáo tiến độ: `status/G1.md`.

## Mục tiêu đo được
1. `ai/knowledge/free_ai_sources.md`: bảng các nguồn **đã gọi thử thật** trong phiên làm, ghi ngày kiểm. Nguồn nào chưa gọi thử thì để ở mục "chưa kiểm".
2. **≥ 1 nguồn ảnh miễn phí có nhận ảnh tham chiếu nhân vật** (để giữ đúng DNA Sóc Bi, Dê Mun…) chạy được qua `ProviderRouter`. Cần sinh được 60 ảnh 16:9 cho 2 tập trong hạn mức free, hoặc chạy trên máy.
3. **≥ 1 nguồn ảnh dự phòng** (không cần tham chiếu cũng được).
4. **≥ 1 đường làm clip video miễn phí**, có ghi số clip/ngày thực tế. Nếu chỉ có đường làm tay qua web (credit miễn phí hằng ngày) thì ghi rõ là "làm tay" để G3/G4 dùng đường nhập clip (C5).

## Tệp sở hữu
`core/providers/<mới>_provider.py`, `core/providers/factories.py` (mới), `core/providers/key_vault.py`, `core/models_registry/models.yaml`, `core/models_registry/registry.py`, `scripts/local_ai/**`, `ai/knowledge/free_ai_sources.md`, `tool/tests/test_g1_*.py`, `status/G1.md`.
**Không sửa** `router.py` (của G2) hay `graph_runner.py`.

## Bước làm

### B1. Lùng sục và kiểm thật (pha 1, làm trước)
Danh sách **ứng viên**, cần kiểm từng cái. Thông tin trong danh sách có thể đã cũ: phải tự vào trang chính thức đọc hạn mức và điều khoản hiện hành, rồi gọi thử 1 lần.

| Nhóm | Ứng viên | Cần kiểm |
|---|---|---|
| Ảnh, API free | Google Gemini API (người dùng tạo **key mới** trên AI Studio, key cũ hỏng) | Model ảnh (`gemini-*-image`) có hạn mức free không, nhận được mấy ảnh tham chiếu |
| | Pollinations.ai | Có cần token không, giới hạn tốc độ, model nào nhận ảnh đầu vào (kiểu kontext), điều khoản dùng thương mại |
| | Cloudflare Workers AI | Hạn mức neuron free/ngày quy ra số ảnh FLUX schnell. Không có tham chiếu, chỉ làm dự phòng |
| | Hugging Face Inference Providers / ZeroGPU Spaces | Credit free hằng tháng, Space FLUX Kontext / Qwen-Image-Edit, hạn mức/ngày |
| | Together AI và các endpoint "free" khác | Còn endpoint FLUX free không |
| Ảnh, chạy trên máy ($0, không giới hạn) | `mflux` (FLUX trên MLX, lượng tử 4-bit), Draw Things, ComfyUI chạy MPS | Đo **giây/ảnh** 1344×768 trên M4 16 GB; Kontext/edit có ảnh tham chiếu chạy được không; dung lượng model (ổ chỉ còn ~24 GB trống) |
| Video, chạy trên máy | LTX-Video (bản nhỏ/distilled), Wan 2.x (1.3B / 5B TI2V) qua MLX hoặc ComfyUI | Đo **phút/clip 5 giây**; RAM có đủ không |
| Video, API/Space free | HF ZeroGPU Spaces (Wan, LTX) | Số clip/ngày |
| Video, web có credit hằng ngày (**người dùng làm tay**) | Kling, Hailuo/MiniMax, Vidu, PixVerse, Google Flow/Veo (nếu gói của người dùng có) | Credit/ngày, watermark, độ dài clip, có nhận ảnh khung đầu (image-to-video) không |
| Text/vision (kiểm định, viết lại prompt) | Gemini free tier (text), Groq, OpenRouter (model free), Cerebras | Hạn mức/ngày, có JSON schema không |
| Nhạc nền/SFX free bản quyền | Pixabay Music, YouTube Audio Library, Openverse (skill `media-use` có tìm SFX qua Openverse không cần tài khoản) | Giấy phép cho video YouTube trẻ em |

Mỗi nguồn ghi đủ: **link chính thức, ngày kiểm, cần key không, hạn mức đo được, có tham chiếu không, giấy phép đầu ra, lệnh gọi thử, kết quả (ảnh/clip lưu ở `data/projects/soc-nho-tv/shots/G1_*`)**.

**Cấm:** tạo hàng loạt tài khoản hay email ảo để cày credit, xoay vòng key, vượt CAPTCHA, dùng API không chính thức lách điều khoản. Cần key thì dừng lại, hướng dẫn người dùng tự tạo trên trang chính chủ, rồi cho vào `.env`.

### B2. Chọn chiến lược ảnh cho 2 tập (pha 1)
Ghi quyết định ở đầu `free_ai_sources.md`. Ví dụ dạng: "Chính: <nguồn có tham chiếu>, dự phòng: <nguồn 2>, cuối cùng: chạy trên máy". Kèm phép tính: 60 ảnh (+20% làm lại) so với hạn mức hoặc thời gian thực tế.

### B3. Provider đầu tiên + nhà máy provider (pha 1)
- `core/providers/factories.py` đúng hợp đồng **C1** (README mục 4).
- `core/providers/<nguon>_provider.py` kế thừa `BaseProvider`. Phải cài **đủ các hàm abstract** (`provider_name`, `generate_images`, `generate_video`, `speak_voice`, `analyze_vision`). Hàm nào không hỗ trợ thì `raise ProviderError(kind=INVALID_PARAMS, ...)` kèm thông báo rõ.
- `generate_images(prompt, references, aspect_ratio, resolution, n, seed, node_id, run_id, model)`:
  - Gửi kèm ảnh tham chiếu (đường dẫn tương đối trong dự án → đọc tệp → base64 hoặc upload, tùy API).
  - Lưu bằng `store.store_bytes(...)`. Ghi `provenance.provider/model` đúng sự thật, `cost_usd = 0.0`.
  - Gặp 429 hoặc 5xx: retry có backoff (`ProviderErrorKind.TRANSIENT`). Hết hạn mức ngày/tháng: `raise ProviderError(..., kind=ProviderErrorKind.QUOTA)` (xem `errors.py`) để router của G2 chuyển sang nguồn dự phòng.
- `key_vault.PROVIDER_SPECS`: thêm nguồn mới có cần key (tên biến env, độ dài tối thiểu). Nguồn không cần key: `needs_key: False` trong `PROVIDER_META`.
- `models.yaml`: thêm model mới với trường **C2** (`tier`, `supports_reference`, `max_references`, `quota_note`, `speed_note`). `registry.py` đọc được các trường này (giữ tương thích ngược).
- Test `tool/tests/test_g1_<nguon>.py`: dùng mock HTTP (không gọi mạng trong CI), dùng `tmp_path`. Thêm 1 script gọi thật `scripts/local_ai/smoke_<nguon>.py` để chạy tay.
- **Thử thật:** sinh 3 ảnh cho shot S01, S02, S03 của Tập 1, dùng `imagePrompt` trong `script.json` và ảnh DNA của nhân vật trong shot. Lưu `shots/G1_ep01_S0x.png`. Ghi nhận xét nhân vật có giống DNA không.

### B4. Nguồn dự phòng + model chạy trên máy (pha 2)
- Provider thứ hai cùng chuẩn C1.
- `scripts/local_ai/`: script cài và chạy model ảnh trên máy (ví dụ `mflux`) **trong venv riêng**, không đụng `.venv` chính. Provider `local_image_provider.py` gọi qua subprocess (giống cách OmniVoice đang chạy). Đo thời gian thật.
- Video: nếu có nguồn API/Space free thì làm `generate_video(prompt, first_frame_uri, duration_sec, aspect_ratio, …)` trả clip MP4. Nếu chỉ có web làm tay thì viết hướng dẫn từng bước trong `free_ai_sources.md`: lấy ảnh khung đầu + `videoPrompt` của shot → tạo clip trên web → tải về đặt tên `clips/<shotId>.mp4` (hợp đồng C5).

### B5. Bàn giao
- `status/G1.md`: nguồn nào chạy, model id trong sổ, biến env cần đặt, lệnh smoke, hạn mức, các rủi ro.
- Ghi "Yêu cầu gửi G2": các model mới cần hiện ở ModelPicker, key mới cần ô nhập trong Cài đặt.

## Done khi
- `free_ai_sources.md` có ≥ 5 nguồn đã kiểm thật, có ngày kiểm.
- Smoke script sinh được ảnh thật cho 3 shot Tập 1, có ảnh tham chiếu nhân vật. Ảnh lưu trong `shots/`, provenance không phải mock.
- `pytest tool/tests/test_g1_*` pass. `GET /models` (sau khi G2 merge C2) liệt kê model mới với `tier` đúng.
