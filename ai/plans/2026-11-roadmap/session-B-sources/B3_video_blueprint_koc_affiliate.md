# B3 — Phân tích video mẫu → Blueprint · Sản phẩm · Kịch bản KOC review & Affiliate

Bạn là Session B. Đọc: `CONTRACTS.md` (2.1, 2.2, 3), `status/B.md`, `status/A.md` (danh sách template + slots), `socnhotv/intelligence/contracts.py`, `core/providers/google_provider.py` (vision), node `vision_analyze` trong `core/nodes/registry.py` (chỉ đọc), skill `motion-mimic` (KOC LyLy/Neau), thư mục `data/projects/soc-nho-tv/products/` và `characters/`.

## Mục tiêu
"Học" 1 video bán hàng/review/affiliate đang viral → tách cấu trúc thành `VideoBlueprint` → áp cấu trúc đó cho **sản phẩm của mình** với **nhân vật KOC của mình** → ra kịch bản + RenderRequest. Không copy hình/lời nguồn, chỉ copy *khung*.

## Việc cần làm
1. **Danh mục sản phẩm `intelligence/products.py`** + API `routes/intel.py`: `Product {id, name, brand, category, price, sale_price, currency, affiliate_links{tiktok_shop, shopee, lazada, other}, usp[], pain_points[], specs{}, images[], videos[], target_audience, compliance_notes (cấm nói gì: y tế, cam kết…)}` lưu `products/<id>/product.json` + media. CRUD `GET/POST/PUT/DELETE /projects/{pid}/products`, upload ảnh. Import nhanh từ URL sản phẩm: chỉ đọc metadata công khai (title/og:image/giá) bằng httpx; không đăng nhập.
2. **`intelligence/analyzer.py`** — `analyze_video(source_id) -> VideoBlueprint`:
   - Dùng `scenes.json` (B1) + transcript (B2 asr) + keyframes → gọi vision LLM theo lô (≤12 khung/1 lần) mô tả visual + on-screen text.
   - Gán `role` cho mỗi beat: `hook, problem, agitate, reveal, demo, proof(social/số liệu), compare, offer, urgency, cta`.
   - Đo nhịp: số cut/10s, thời lượng hook, vị trí CTA, tỉ lệ có mặt người/nhân vật, có text overlay không, loại nhạc.
   - Gợi ý `suggested_template_id` bằng so khớp scenes của template (A) với chuỗi role (rapidfuzz).
   - Lưu `content/blueprints/<id>.json` qua contract.
3. **`intelligence/patterns.py`**: gộp nhiều blueprint cùng niche → "công thức" (role sequence phổ biến, độ dài hook trung vị, CTA phổ biến, câu hook mẫu đã trừu tượng hoá dạng khuôn `"[Nỗi đau] ? Đây là cách …"`). API `GET /projects/{pid}/intel/patterns?niche=`.
4. **`intelligence/script_gen.py`** — 3 generator, input (product, blueprint|pattern, character_id, platform, duration):
   - `koc_review`: KOC/nhân vật nói ngôi thứ nhất, có ưu + 1 nhược thật (tăng tin cậy), chấm điểm, CTA giỏ hàng. Ánh xạ slot template `koc-review-v1`.
   - `tiktok_sales`: hook 3s theo pattern, demo, giá/ưu đãi, urgency hợp lệ (không bịa "chỉ còn 2 suất" nếu không có dữ liệu), CTA. Slot `tiktok-sales-v1`.
   - `affiliate_compare`: 2–3 sản phẩm, bảng tiêu chí, kết luận theo nhu cầu. Slot `affiliate-compare-v1`.
   - Mọi script qua **bộ lọc tuân thủ** `intelligence/compliance.py`: chặn tuyên bố y tế/chữa bệnh, cam kết tuyệt đối, so sánh hạ thấp thương hiệu khác, thiếu disclosure affiliate (tự chèn "#affiliate"/"link tiếp thị" vào caption). Trả cảnh báo + bản sửa.
   - Output: `content/scripts/<id>.json` + `RenderRequest` sẵn sàng (gọi `submit_render` khi người dùng bấm, không tự gọi).
   - Tuỳ chọn KOC chuyển động: nếu người dùng chọn "bắt chước động tác từ video mẫu" → tạo task theo skill `motion-mimic` (chỉ khi rights nguồn ≠ reference_only hoặc video do người dùng tự quay).
5. **Tạo ContentIdea**: mỗi script sinh 1 `ContentIdea` (status `scripted`) để C đưa lên lịch.
6. **UI**:
   - `app/[locale]/products/**` + `components/products/*`: lưới sản phẩm (thẻ thêm nét đứt cạnh thẻ cuối), chi tiết sản phẩm, link affiliate, USP.
   - `app/[locale]/intel/**` + `components/intel/BlueprintView.tsx`: timeline beat màu theo role trên thanh thời gian, thumbnail mỗi beat, số liệu nhịp, nút "Áp cho sản phẩm…" → wizard 3 bước (chọn sản phẩm → chọn nhân vật/KOC + giọng → chọn kiểu script & nền tảng) → xem/sửa script → "Gửi render".
   - Nút "Phân tích cấu trúc" trong chi tiết nguồn (component của B1).
   - Nav `nav-modules/sources.ts` thêm: Sản phẩm, Phân tích.
7. **Node plugin**: `blueprint_analyze` (video → blueprint), `script_from_blueprint` (blueprint + product + character → script text + RenderRequest json).

## Nghiệm thu
- `test_intel_analyzer.py` (mock vision/LLM: role gán đúng, pacing tính đúng), `test_intel_script_gen.py` (slot khớp template, compliance chặn "chữa khỏi 100%", tự chèn disclosure), `test_intel_products_api.py`.
- Chạy thật: 1 video review sản phẩm (nguồn B1) → blueprint hiển thị trên UI → áp cho 1 sản phẩm mẫu tạo trong `products/` → script KOC + RenderRequest gửi được.
- Commit `feat(B3): video blueprint analyzer, products, KOC/sales/affiliate script generators`. Cập nhật `status/B.md`.
