# B2 — Bản địa hoá video Douyin/TikTok TQ → Việt: ASR · Dịch · Viết lại · Lồng tiếng · Dựng lại

Bạn là Session B. Đọc: `CONTRACTS.md` (mục 2.1 RenderRequest, mục 3 Bản quyền), `status/B.md`, `status/A.md` (template `localized-reup-v1` đã có chưa), `core/adapters/caption_adapter.py`, `core/adapters/voice_adapter.py`, `core/adapters/audio_mastering.py`, `core/providers/router.py` (chỉ đọc, dùng lại), skill `vietnamese-voice-clone`, `embedded-captions`.

## Mục tiêu
Từ 1 `SourceItem` → bản tiếng Việt hoàn chỉnh mang dấu ấn kênh mình: phụ đề VI, lời mới viết lại theo giọng thương hiệu, lồng giọng (soc-nho hoặc KOC), dựng trong khung template của mình. Hai chế độ:
- **Mode R (Remake – mặc định, an toàn):** chỉ lấy *cấu trúc + nội dung ý* từ nguồn (`reference_only` đủ), dựng lại bằng hình của mình (thư viện project, ảnh/clip AI, nhân vật) → không dùng clip gốc.
- **Mode L (Localize – cần rights ≠ reference_only):** giữ clip gốc, thay audio/phụ đề, bọc khung brand + nhân vật bình luận. API phải từ chối Mode L nếu rights = `reference_only`.

## Việc cần làm
1. **`sources/asr.py`**: `faster-whisper` (đã có trong deps) model `medium`/`large-v3` theo env, `language="zh"` tự dò; word timestamps; ưu tiên phụ đề gốc nếu có. Output `raw/<id>/transcript.orig.json` [{start,end,text,words[]}]. Tách vocal/nhạc nền nếu có công cụ trong `integrations/` (kiểm tra; nếu không, bỏ qua và ghi chú).
2. **`sources/translate.py`**: dịch câu-theo-câu ZH→VI qua LLM của `providers/router.py`, giữ timestamp; glossary dự án (`knowledge/glossary.json`, tạo nếu chưa có) cho tên sản phẩm/thuật ngữ; kiểm độ dài câu VI ≤ 1.25× thời lượng gốc (tốc độ đọc ~15 ký tự/s), quá thì rút gọn. Output `transcript.vi.json`.
3. **`sources/rewrite.py`**: viết lại kịch bản theo "brand voice" (đọc `data/shared/brand_kits/*` + `knowledge/`), 3 kiểu: `faithful` (sát ý), `hook_boost` (hook 3s mạnh hơn, CTA rõ), `character` (lời Sóc Nhỏ/KOC xưng hô thân thiện). Output `content/scripts/<source_id>.<style>.json` gồm lines có thời lượng mục tiêu.
4. **`sources/revoice.py`**: TTS từng câu bằng `voice_adapter` (voice mặc định `soc-nho`, chọn được KOC voice-id), time-stretch nhẹ (0.9–1.1×) cho khớp khung câu, mastering -14 LUFS, ghép `raw/<id>/voice.vi.mp3`. Mode L: duck/bỏ giọng gốc, giữ nhạc nếu đã tách.
5. **`sources/localize_pipeline.py`**: `run(project_id, source_id, mode, style, voice_id, platforms, template_id="localized-reup-v1" (L) | do người dùng chọn (R))` → chuỗi asr→translate→rewrite→revoice → tạo `RenderRequest` và gọi `socnhotv.video.contracts.submit_render` (KHÔNG import nội bộ của A). Mode R: chọn media từ thư viện project theo từ khoá từng câu (khớp tên/tag file trong `library/`) + cho phép cờ `generate_missing=true` (đẩy yêu cầu ảnh AI vào node image_gen — chỉ tạo danh sách prompt, không tự tiêu tiền nếu spend guard chặn). Lưu từng bước để chạy lại được. Truyền `source_ref` vào RenderRequest.
6. **API** (`routes/sources.py`): `POST /projects/{pid}/sources/{sid}/localize` (body: mode, style, voice_id, platforms, template_id, auto_draft) → job; `GET …/localize/{job}`; `GET/PUT …/transcript?lang=orig|vi` (sửa tay phụ đề); `GET/PUT …/script?style=`.
7. **UI** `components/sources/LocalizeStudio.tsx` (mở từ chi tiết nguồn): 3 cột — video gốc | bảng câu (gốc / dịch / viết lại, sửa inline, nghe thử từng câu TTS) | thiết lập (mode R/L với khoá L khi reference_only kèm giải thích, style, giọng qua `VoiceSelectorWithClone`, nền tảng, template, tự tạo nháp). Nút "Bản địa hoá" → theo dõi tiến độ, link sang `/renders` của A.
8. **Node plugin** thêm `localize` (input video+audio; output script, audio vi, subtitle).

## Nghiệm thu
- `test_sources_localize.py` (mock ASR/LLM/TTS): Mode L bị chặn khi reference_only; Mode R tạo RenderRequest có `source_ref`, đúng platforms; độ dài câu VI bị rút gọn khi vượt.
- Chạy thật 1 video ngắn (≤30s) tiếng Trung → transcript.vi + voice.vi.mp3 nghe được, -14 LUFS ±1, gửi render thành công (nếu A chưa xong template thì job nằm `queued` là đạt).
- Commit `feat(B2): douyin localization pipeline (asr, translate, rewrite, revoice)`. Cập nhật `status/B.md`.
