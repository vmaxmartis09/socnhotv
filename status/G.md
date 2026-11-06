# SESSION G — BÁO CÁO TỔNG (G4 gom từ các luồng)

> Cập nhật: 2026-11-06 18:10 (+07). Nguồn: `status/G1.md`, `status/G3.md`, `status/G4.md`, git log `main`, đo trực tiếp.
> G2 và G5 **chưa có** `status/G2.md` / `status/G5.md` trên main lúc viết.
> Quy tắc: chỉ ghi điều đã đo được. Mục nào chưa đạt ghi **CHƯA** kèm lý do.

## 1. Trả lời thẳng

| Câu hỏi | Trả lời |
|---|---|
| Tập 1 / Tập 2 đã xong chưa? | **CHƯA.** Chưa có `output/ep01-nui-lua-trong-bung-bi/ep01-nui-lua-trong-bung-bi.mp4` hay tệp tương ứng của Tập 2. |
| Đã có video thật nào từ flow Studio chưa? | **CHƯA.** Các mốc M1–M4 chưa chạy được (mục 3). |
| Chặn ở đâu? | Luồng **G2** chưa đưa gì vào main: router chưa có `runPolicy` (giọng thật khi ảnh mock) và chưa gọi provider ảnh free của G1. Hiện ở chế độ thật mà chọn `pollinations-flux`, router **âm thầm trả mock**. |
| Phần nào đã sẵn sàng? | Engine dựng theo shot (G3), provider ảnh free (G1, chạy thật ngoài Studio: 3 ảnh S01–S03), giọng thật 60/60 câu trong cache, kịch bản 2 tập khoá, công cụ nghiệm thu, xem/tua trong Studio, test không đụng dữ liệu thật (G4). |

## 2. Theo luồng

| Luồng | Đã vào main | Đo được | Chưa |
|---|---|---|---|
| G1 nguồn AI | `6b624c3`, `a709daa`: Pollinations (chính, $0, ảnh tham chiếu), Cloudflare Workers AI, mflux local; `factories.py` (C1), `models.yaml` C2 | 3 ảnh thật Tập 1 S01–S03 (Pollinations, 5,9–10,3 s/ảnh, giới hạn IP ~1 ảnh/45 s); test G1 10/10 | Chưa nối vào router (việc của G2). Nguồn video free khả thi duy nhất: làm tay trên web có credit (C5). Plan mới thêm nguồn trả phí Google có kiểm soát — chưa có báo cáo. |
| G2 chế độ lai + chọn model | **chưa có commit** | — | `runPolicy`, router tra `PROVIDER_FACTORIES`, ModelPicker, key mới ở Cài đặt |
| G3 engine dựng | `ad356de`, `fff3c0c`: bỏ fallback `generate_video` 45 s, ghim HyperFrames 0.9.12, camera theo kịch bản, `video_gen` lặp shot (C4), clip tay (C5), BGM ducking, xuất `<ep>.mp4` (C6) | render 10 s mất 7,2 s (1,38× realtime) → ước 600 s ≈ 7,2 phút; test G3 10/10 | Chưa có BGM thật (`data/shared/music_sfx/` trống). Yêu cầu từ G4: mục 5. |
| G4 dữ liệu + nghiệm thu | `0a070f4` (+ commit cuối) | xem `status/G4.md` | M1–M4 |
| G5 hồ sơ nhân vật | đang làm, chưa commit | `consistency.json` 5 nhân vật đã xuất hiện trong dữ liệu | — |

## 3. Các mốc

| Mốc | Trạng thái | Lý do / bằng chứng |
|---|---|---|
| M1 — Tập 1 lai (ảnh mock + giọng thật), xem được trong Studio | **CHƯA** | Cần `runPolicy` (G2). Giọng thật đã sẵn trong cache (60/60), engine G3 sẵn. |
| M2 — Tập 1 Mức A, ảnh free thật qua ModelPicker | **CHƯA** | Router chưa gọi provider G1; chưa có ModelPicker. |
| M3 — Tập 2 Mức A | **CHƯA** | như M2 |
| M4 — Mức B (≥5 clip/tập) | **CHƯA** | `clips/` trống. Đã có gói shot ZIP (6 shot priority 1/tập) để làm tay. |

"Định nghĩa Done" (README mục 5) cho từng tập — chưa chạy được vì chưa có video tập:

| Mục | Tập 1 | Tập 2 |
|---|---|---|
| 1 ffprobe | CHƯA (chưa có video) | CHƯA |
| 2 âm lượng | CHƯA | CHƯA |
| 3 ≥30 ảnh khác, không mock | CHƯA (chưa chạy node ảnh thật) | CHƯA |
| 4 giọng đúng | **Sẵn sàng**: 30/30 câu OmniVoice đúng voiceId trong cache, nghe lại không còn câu chèn | **Sẵn sàng**: 30/30 |
| 5 `mock:false` | CHƯA | CHƯA |
| 6 người dùng duyệt contact sheet | CHƯA | CHƯA |
| 7 tua trong Studio | Backend 206 ĐẠT trên tệp 260 MB; UI có nút "Xem & tua" — CHƯA thử trên video tập | như Tập 1 |

## 4. Phát hiện quan trọng trong phiên

1. **Giọng 2 nhân vật hỏng mà không chỉ số nào cũ bắt được:** `vn-be-04` (Dê Mun, 25 câu) và `vn-be-01` (Dê Bông, 6 câu) đạt âm lượng và provenance nhưng **30/31 câu bị chèn câu mẫu** ở đầu, do `reference_transcript.txt` không khớp lát âm mẫu. G4 đã sửa (sao lưu bản cũ), đọc lại 31 câu, nghe lại bằng Whisper: còn 0 câu chèn. `verify_episode.py` nay nghe lại từng câu.
2. **Ảnh tham chiếu sai:** runner lấy 4 ảnh PNG đầu theo tên → dính ảnh quay lưng. G4 viết `dna_reference_files()` + `dnaReferences`; cần G3 gọi.
3. **Test làm bẩn dữ liệu thật:** 643/716 thư mục `run_*` trong `runs/` chỉ chứa 1 `state.json` (rác test cũ), thêm 2 dự án rác `test-scene-batch`, `test-step5`. Đã chặn bằng sandbox; **chưa xoá** (chờ người dùng quyết).
4. **Kịch bản:** `videoPrompt` ghi "8-second" cho shot 20 s; Tập 2 S13 lời thoại dính câu mô tả ("dê mun (85cm)…"). Đã sửa, khoá `locked`.
5. **Báo cáo cũ nói quá** (Session V "video đầu tiên xuất sắc"): đã đính chính trong `ai/memory/CONTINUITY.md`.

## 5. Việc cần làm tiếp (theo luồng)

- **G2 (chặn chính):** `runPolicy` (C3); `router.get_provider` tra `PROVIDER_FACTORIES` và báo lỗi thay vì `return self._mock` ở chế độ thật; ModelPicker; gắn preview video thật cho node; nút preset "Tập hoạt hình (tái dùng)"; tab "Công việc" hiện danh sách thành phẩm.
- **G3:** `_character_dna` dùng `dna_reference_files()`; export không tạo `output/<ep>-2/` khi chạy lại; `video.json` ghi đúng giọng + `episodeId`/`engine`; chọn shot theo `priority`; BGM.
- **G4 (khi G2 vào main):** M1 → verify `--allow-mock-images` → M2 → M3 → contact sheet cho người dùng duyệt → M4.
- **Người dùng:** (a) quyết có xoá 643 thư mục `runs/` rác + 2 dự án rác không; (b) nghe thử giọng Dê Mun / Dê Bông mới (`data/shared/voice_vault/vn-be-04|vn-be-01/`), bản cũ ở `_backup_2026-11-06_G4/`; (c) thả 1 tệp nhạc nền vào `data/shared/music_sfx/` (hoặc giao G1 tìm nhạc free có giấy phép).

## 6. Test

`.venv/bin/pytest` toàn bộ (sandbox): **289 passed, 5 failed, 1 skipped**. 5 lỗi có sẵn từ trước Session G (`test_custom_ports` ×2 lỗi thời, `test_craft_index` ×2 do 6 thẻ thiếu front-matter, `test_content_policy` ×1), lỗi y hệt khi chạy trên dữ liệu thật. `runs/` thật 725 → 725.
