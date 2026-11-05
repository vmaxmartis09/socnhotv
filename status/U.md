# SESSION U — TAB TEMPLATE ĐẦY ĐỦ

**Trạng thái phiên:** `READY_FOR_USER_TEST` (Nhiệm vụ U-01 hoàn tất)  
**Nhánh:** `main` (làm việc trực tiếp trên `main` theo chỉ đạo người dùng)  
**Ngày cập nhật:** 2026-11-05  
**Phụ trách:** Antigravity (Ag) — Pair programming  

---

## 1. TỔNG QUAN TIẾN ĐỘ NHIỆM VỤ SESSION U

| Mã | Nhiệm vụ | Trạng thái | Cổng nghiệm thu (File thật) | Ghi chú |
|---|---|---|---|---|
| **U-00** | Đọc quy chuẩn & kiểm toán thực tế 8 template cũ (chạy thật) | **HOÀN THÀNH** | `status/U.md`, `data/shared/toolbox/ready/U-00.md` | Phát hiện 100% template đang ra ảnh/video mock đen |
| **U-01** | Hợp đồng template v2 (`template.json`) + JSON Schema + Validator | **HOÀN THÀNH** | `data/shared/templates/_schema/template.v2.schema.json`, `data/shared/toolbox/ready/U-01.md` | Đã kiểm định tự động: 8/8 template hợp lệ v2, 7/7 unit tests pass |
| **U-02** | API danh mục templates + kiểm điều kiện (tools, providers, GPU) | **HOÀN THÀNH** | `tool/dashboard/app/api/templates/route.ts`, `data/shared/toolbox/ready/U-02.md` | `curl` endpoint JSON thật; phát hiện chính xác tool/key/gpu |
| **U-03** | UI tab Template theo chuẩn dự án (Morphicons, theme sáng/tối) | **HOÀN THÀNH** | `components/templates/**`, `data/shared/toolbox/ready/U-03.md` | Build Next.js pass, check:icons pass, ảnh chụp sáng/tối thật |
| **U-04** | U-D Review sản phẩm: nối `bg-remove` tách nền thật → MP4 9:16 | **HOÀN THÀNH** | `affiliate-compare-v1`, `unboxing-v1`, `data/shared/toolbox/ready/U-04.md` | MP4 thật 540x960 84 frames, contact sheet, status verified |
| **U-05** | U-C TikTok KOC review: MP4 thật có giọng OmniVoice + subtitle | **HOÀN THÀNH** | `koc-review-v1`, `data/shared/toolbox/ready/U-05.md` | MP4 thật 540x960 108 frames, WER 6.25%, status verified |
| **U-06** | U-G Video vẽ tay: tool Toolbox `handdraw` + template | **HOÀN THÀNH** | `tool/toolbox/tools/handdraw/`, `handdraw-whiteboard-v1`, `data/shared/toolbox/ready/U-06.md` | Tool handdraw + template verified, MP4 72 frames, MIT license |
| **U-07** | U-F Motion graphics / kinetic text bằng HyperFrames | **HOÀN THÀNH** | `shorts-fact-v1`, `data/shared/toolbox/ready/U-07.md` | MP4 9:16 + 16:9 thật, kinetic text, status verified |
| **U-08** | U-E Thay nhân vật: Tier A overlay-replace + giới hạn trung thực | **HOÀN THÀNH** | `character-overlay-replace-v1`, `data/shared/toolbox/ready/U-08.md` | MP4 thật 540x960 72 frames, UI minh bạch Tier A, status verified |
| **U-09** | U-A/U-B Nối Session F (hoạt hình series Bi / phim ngắn) | ĐANG THỰC HIỆN | `blocked_by: F` nếu F chưa có render | Kiểm tra Session F & animatic tier A |
| **U-10** | Nâng cấp kiểm tra các template phụ (U-I, J, K, L, M, H) | CHỜ CHẠY | Bảng runnable/draft | Chờ U-09 |
| **U-11** | Vòng tự học: Thẻ kỹ thuật + `repo_watch.md` (≥10 repo) | CHỜ CHẠY | File Markdown có số liệu GitHub API thật | Chờ U-10 |
| **U-12** | Tổng kết Session U, cập nhật `TOOLS.md` & nghiệm thu | CHỜ CHẠY | Báo cáo hoàn chỉnh + catalog template | Chờ U-11 |

---

## 2. KẾT QUẢ KIỂM TOÁN THỰC TẾ 8 TEMPLATE CŨ (U-00)

Tất cả 8 template trong `data/shared/templates/` đã được kiểm tra trực tiếp qua 3 tầng:
1. **Tầng dữ liệu & template engine** (`template.json`, `sample.data.json`, `compose_template` Jinja2).
2. **Tầng dựng preview** (`generate_template_preview` / `fallback_ffmpeg` / `HyperFramesEngine`).
3. **Tầng thực thi đồ thị Studio** (`GraphRunner` với `node_template_render` và `node_platform_export`).

### Bảng kết quả kiểm toán 8 template

| # | ID Template | Tên mẫu | Category & Platform | Tình trạng preview hiện tại | Kết quả chạy Studio Graph | Đánh giá trung thực |
|---|---|---|---|---|---|---|
| 1 | `tiktok-sales-v1` | Bán hàng TikTok – Hook 3s | sales · tiktok (9:16) | `preview.mp4`: 5876B, 3.0s, **100% màu đơn sắc #121524**. `preview.jpg`: ảnh đen 3KB | Node rơi vào nhánh `else:` của `graph_runner.py` sinh ảnh mock JPG | **MOCK** (chưa có handler, asset `product.png` thiếu) |
| 2 | `koc-review-v1` | KOC Review Sản Phẩm – 5 Sao | review · tiktok (9:16) | Trước test: thiếu MP4; Render thử: 5876B, 3.0s, **100% màu đơn sắc #121524** | Rơi vào `else:` sinh ảnh mock JPG | **MOCK** (không có frame thật) |
| 3 | `affiliate-compare-v1` | So Sánh Sản Phẩm Affiliate | affiliate · tiktok (9:16) | `preview.mp4`: 5876B, 3.0s, **100% màu đơn sắc #121524** | Rơi vào `else:` sinh ảnh mock JPG | **MOCK** (video nền đen) |
| 4 | `unboxing-v1` | Mở Hộp Đập Hộp – Punch-in | review · tiktok (9:16) | Trước test: thiếu MP4; Render thử: 5876B, 3.0s, **100% màu đơn sắc #121524** | Rơi vào `else:` sinh ảnh mock JPG | **MOCK** (không có video mở hộp) |
| 5 | `localized-reup-v1` | Bản Địa Hoá Video | reup · tiktok (9:16) | Trước test: thiếu MP4; Render thử: 5876B, 3.0s, **100% màu đơn sắc #121524** | Rơi vào `else:` sinh ảnh mock JPG | **MOCK** (video rỗng) |
| 6 | `yt-animation-episode-v1` | Hoạt Hình Dài Tập YouTube | animation · youtube (16:9) | Trước test: thiếu MP4; Render thử: 5882B, 3.0s, **100% màu đơn sắc #121524** | Rơi vào `else:` sinh ảnh mock JPG | **MOCK** (phụ thuộc Session F) |
| 7 | `shorts-fact-v1` | Kiến Thức Thú Vị – Kinetic | education · shorts (9:16) | `preview.mp4`: 5876B, 3.0s, **100% màu đơn sắc #121524** | Rơi vào `else:` sinh ảnh mock JPG | **MOCK** (chưa có kinetic text thật) |
| 8 | `story-cartoon-v1` | Truyện Kể Thiếu Nhi Dọc | story · tiktok (9:16) | Trước test: thiếu MP4; Render thử: 5876B, 3.0s, **100% màu đơn sắc #121524** | Rơi vào `else:` sinh ảnh mock JPG | **MOCK** (không có lật trang/karaoke) |

**Tỉ lệ template đạt chuẩn verified:** **0/8 (0%)**  
**Tỉ lệ template chạy ra video thật:** **0/8 (0%)**

---

## 3. CÁC NGUYÊN NHÂN KỸ THUẬT & LỖI THẬT ĐÃ PHÁT HIỆN

### Lỗi 1: `template_render` và `platform_export` hoàn toàn thiếu handler trong `graph_runner.py`
- Khi người dùng bấm tạo video từ template trên Studio (đồ thị sinh từ `tool/dashboard/lib/template-graphs.ts`), 2 node `template_render` và `platform_export` được gửi sang backend.
- Trong `tool/src/socnhotv/core/engine/graph_runner.py` hàm `_execute_node_handler()`, chuỗi `elif node_type == ...` **không hề có** nhánh nào cho `template_render` hay `platform_export`.
- Hậu quả: Luồng thực thi rơi vào khối `else:` (dòng 1424):
  ```python
  else:
      gen_fn = self.provider.generate_images
      arts = await gen_fn(prompt=f"Generic execution for {node.type}", ...)
  ```
  Backend gọi `MockProvider` sinh 1 file ảnh JPEG giả lập (`assets/<hash>.jpg`), gán cờ `completed` và `is_success = True`! Hệ thống báo hoàn tất thành công nhưng người dùng chỉ nhận được ảnh giả thay vì video MP4.

### Lỗi 2: Bộ sinh preview `generate_template_preview` chỉ render hình chữ nhật đơn sắc
- Trong `tool/src/socnhotv/video/templates/preview.py`, logic render cố tình gọi thẳng `render_fallback_ffmpeg` thay vì HyperFrames.
- `render_fallback_ffmpeg` (dòng 87–96 của `fallback_ffmpeg.py`) kiểm tra nếu `media_files` trong thư mục `assets` rỗng, nó sẽ chạy lệnh ffmpeg sinh video màu đơn sắc:
  ```bash
  ffmpeg -y -f lavfi -i color=c=0x111625:s=540x960:d=3.0 ...
  ```
- Kết quả: `preview.mp4` đo được đúng 5876 bytes (bitrate cực thấp 15 kb/s do chỉ nén 1 màu đồng nhất), và `preview.jpg` chứa 100% pixel màu RGB `(18, 21, 36)`. Không hề có chữ, không có animation, không có nhân vật hay sản phẩm.

### Lỗi 3: Rào cản phiên bản Node.js với `hyperframes` CLI
- Khi gọi `HyperFramesEngine.render()`, engine thực thi lệnh `npx -y hyperframes render ...`.
- Package `hyperframes@0.9.15` (cũng như 0.9.12) có đoạn kiểm tra phiên bản cứng trong `dist/runtimeVersion.js`:
  ```javascript
  const major = Number.parseInt(version.split(".", 1)[0] ?? "", 10);
  if (Number.isFinite(major) && major >= 22) return null;
  return `HyperFrames requires Node.js >= 22 (current: ${version}). Switch Node versions and retry.`;
  ```
- Môi trường Windows hiện hành đang cài **Node.js v20.14.0**. Do đó lệnh CLI `hyperframes` lập tức thoát với mã lỗi 1 và thông báo lỗi trên.
- Đã kiểm chứng: Khi loại trừ rào cản kiểm tra chuỗi phiên bản này, toàn bộ engine `hyperframes` (v0.9.15) chạy bình thường trên Node 20.14.0 với đầy đủ các lệnh render, lint, check, snapshot.

### Lỗi 4: Phụ thuộc mạng ngoại tuyến (GSAP CDN)
- Cả 8 file `composition.html.j2` đều chứa thẻ `<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>`.
- Khi máy offline hoặc môi trường headless Chrome bị chặn/chậm mạng, composition bị treo hoặc không chạy timeline GSAP. Cần được vendor nội bộ.

### Lỗi 5: Schema `template.json` cũ (v1) thiếu các trường quản trị v2
- Các template hiện tại dùng hợp đồng v1 (`category`, `slots` dạng thô với key `key`, không có `kind`, `status`, `tier`, `requires`, `recipe`, `sample_output`, `verified_on`, `sources`, `learned_from`).

---

## 4. KẾT LUẬN & ĐỀ XUẤT CHO BƯỚC TIẾP THEO

- Cổng nghiệm thu **U-00 đã hoàn tất**: Toàn bộ hiện trạng 8 template được kiểm chứng bằng số đo ffprobe và log mã nguồn thật. Không có template nào hiện tại là "video thật".
- Chuyển sang **U-01**: Thiết lập Hợp đồng Template v2 (`template.json`), tạo JSON Schema chuẩn tại `data/shared/templates/_schema/template.v2.schema.json`, viết script validator, và migrate 8 template cũ sang v2.
