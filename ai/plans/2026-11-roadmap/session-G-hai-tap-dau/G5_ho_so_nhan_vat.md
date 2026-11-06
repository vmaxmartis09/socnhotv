# G5: Hồ sơ nhân vật chi tiết + kiểm tra nhất quán

> Thuộc Session G. Đọc trước: `README.md` (mục 3, 4, 6), `status/THUC_TRANG_2026-11-06.md`, `data/projects/soc-nho-tv/characters/SCALE_LOCK.md`.
> Báo cáo tiến độ: `status/G5.md`.
> Mục tiêu dài hạn của người dùng: nhân vật càng chi tiết thì video (YouTube, TikTok KOC) càng thống nhất về nhân vật.

## Vấn đề
- Mỗi nhân vật có 16–55 ảnh nhưng **không có bộ ảnh chuẩn được chọn sẵn**: runner lấy ảnh tham chiếu gần như ngẫu nhiên (`_refs_for_scene`).
- Hồ sơ chỉ có `promptLock` dạng chữ, không có dữ liệu có cấu trúc (bảng màu, trang phục, đặc điểm không đổi, tỉ lệ cơ thể, cấm kỵ).
- **Không có bước kiểm tra** ảnh/clip sinh ra có đúng nhân vật không. Lệch thì không ai biết, không sinh lại.
- Khi clip AI qua nhiều shot, nhân vật dễ lệch hơn ảnh tĩnh.

## Tệp sở hữu
`tool/src/socnhotv/core/engine/character_consistency.py` (mới), `characters/<id>/consistency.json` (dữ liệu, mới), `components/characters/**`, `app/[locale]/characters/**`, `scripts/characters/**` (mới), `tool/tests/test_g5_*.py`, `status/G5.md`.
G5 **không** sửa `graph_runner.py`, `router.py`, provider. Cần gọi từ runner thì ghi "Yêu cầu gửi G3" (nhánh `image_gen` có thêm vài dòng gọi hàm của G5).

## Bước làm

### B1. Hồ sơ có cấu trúc `consistency.json` (pha 1, làm trước)
Mỗi nhân vật có tệp (schema ghi trong `status/G5.md`):
- `identity`: tên, loài, tuổi, `heightCm` (khớp `SCALE_LOCK.md`), tỉ lệ so với nhân vật khác.
- `locked`: bảng màu (mã HEX cho lông, mắt, áo, quần, giày), đặc điểm không đổi (đuôi, tai, họa tiết), trang phục mặc định.
- `forbidden`: những lỗi hay gặp cần chặn trong prompt phủ định (ví dụ: "đuôi quá ngắn", "mập").
- `references`: danh sách ảnh tham chiếu **đã chọn** theo vai trò: `front`, `three_quarter`, `profile`, `full_body`, `expressions` (vui, buồn, ngạc nhiên, giận), mỗi cái trỏ về một tệp có sẵn trong `characters/<id>/`. Tối thiểu `front` + `full_body`; mục tiêu 5–8 ảnh.
- `voiceId`, ghi chú giọng.
Viết `scripts/characters/build_consistency.py <id>`: gợi ý sẵn ảnh tham chiếu từ thư mục ảnh (ưu tiên nền đơn giản, chính diện rõ), **người dùng duyệt** trước khi khoá. Làm cho 5 nhân vật của Tập 1–2: `soc_nho`, `de_mun`, `me_soc`, `de_bong`, `ong_de_rau_bac`.

### B2. Chọn ảnh tham chiếu theo shot (pha 1)
`character_consistency.refs_for_shot(shot, characters)` trả danh sách ảnh tham chiếu ngắn gọn cho 1 shot, dựa trên `shotSize`, góc máy (`camera`), biểu cảm (`expression`):
- shot toàn cảnh → `full_body`; cận mặt → `front` hoặc `expressions[...]`; ngang → `profile`.
- Tôn trọng giới hạn số ảnh tham chiếu của model (`max_references` trong `models.yaml`, G1 thêm).
- Thêm `locked` + `forbidden` vào prompt/negativePrompt (`build_prompt_block(characters)`).
Test: cùng một shot luôn ra cùng danh sách (tất định).

### B3. Chấm điểm nhất quán (pha 2)
`character_consistency.score_image(image_path, character_id)` → `{score 0–1, issues[]}`.
- Dùng model nhìn (Gemini vision qua `ProviderRouter.analyze_vision`, có JSON schema) so ảnh sinh ra với ảnh `front` + `locked` (màu áo, đuôi, tỉ lệ).
- Cấu hình ngưỡng (mặc định 0.7). **Chạy dưới `SpendGuard`**; chế độ mock chỉ trả kết quả giả và ghi rõ.
- Dự phòng không tốn model: so sánh bảng màu chủ đạo (histogram) với `locked.palette`, ghi `method: "palette"`.
- Với clip: lấy 3 khung (đầu, giữa, cuối) rồi chấm từng khung.

### B4. Vòng sinh lại shot lệch (pha 2, phối hợp G3)
- Hàm `regenerate_policy(shot_result)`: dưới ngưỡng thì đề xuất sinh lại tối đa N lần (mặc định 2) với prompt nhấn mạnh phần `issues`, có trần chi phí.
- Phần gọi lại provider do runner (G3) thực hiện; G5 chỉ cung cấp hàm chấm và quyết định. Ghi "Yêu cầu gửi G3" cùng ví dụ gọi.
- Ghi kết quả từng shot vào `output/<ep>/consistency_report.json` (điểm, số lần sinh lại, shot vẫn lệch).

### B5. Giao diện Nhân vật (pha 2)
Trong trang `/characters`: tab "Nhất quán" hiện bộ ảnh chuẩn theo vai trò, bảng màu khoá, nút "Chọn lại ảnh", xem báo cáo `consistency_report.json` của tập (shot nào lệch, bấm vào xem ảnh). Dùng Morphicons, i18n vi/en, component dùng chung với thẻ nhân vật hiện có.

## Done khi
- 5 nhân vật có `consistency.json` đã duyệt, mỗi người ≥5 ảnh tham chiếu đủ vai trò.
- `refs_for_shot` chạy cho 60 shot của Tập 1–2 không lỗi, tất định, đúng giới hạn số ảnh.
- Chấm điểm thử trên 10 ảnh thật (5 đúng, 5 cố tình lệch) cho kết quả phân biệt được; ghi độ chính xác thật trong `status/G5.md` (không khoe số chưa đo).
- Test `test_g5_*` pass, dùng thư mục tạm.
