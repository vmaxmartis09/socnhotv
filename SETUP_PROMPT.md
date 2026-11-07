# SETUP_PROMPT — dựng lại toàn bộ SocNhoTV trên máy mới

> Dán **nguyên văn phần "PROMPT" bên dưới** cho một AI Agent (Claude Code, Codex, Cursor…) mở sẵn trong thư mục repo vừa clone.
> Repo chứa **cả code lẫn toàn bộ dữ liệu** (không bỏ qua phần nào), kể cả `.venv` của máy gốc, trừ `.env` (khoá API) (macOS Apple Silicon).
> Trọng số mô hình tải từ Hugging Face lần đầu dùng. `integrations/OmniVoice` là repo upstream lồng nhau (mục 5).

---

## PROMPT

Bạn đang ở thư mục gốc của repo `socnhotv` (đã clone). Hãy dựng toàn bộ dự án chạy được trên máy này và **tự kiểm chứng bằng lệnh thật**, không suy đoán. Báo cáo từng bước đạt/không đạt kèm lệnh đã chạy.

### 0. Quy tắc bắt buộc
- Đọc `CLAUDE.md` và `ai/AGENTS.md` trước. Kiến trúc 3 phần: `ai/` (luật + trí nhớ cho AI), `tool/` (code), `data/` (toàn bộ dữ liệu). Không để dữ liệu vào `tool/`.
- Không gọi API trả phí, không bật billing. Mặc định chạy chế độ $0: ảnh mock hoặc local, giọng OmniVoice trên máy.
- Không xoá, không ghi đè `data/`. Muốn thử thì dùng bản sao.
- Commit chỉ kèm đường dẫn tệp của mình (`git commit -- <tệp>`), không `git add -A`.

### 1. Lấy dữ liệu
```bash
git lfs install && git lfs pull   # chỉ còn 1 tệp mô hình ≈99 MB (depth-anything) qua LFS
```
Nếu báo hết hạn mức LFS: báo người dùng, **không** tự mua thêm. Video demo/thành phẩm cũ đã bị xoá; flow sẽ tạo video mới khi chạy.

### 2. Công cụ hệ thống (macOS)
Cần: Python 3.12, Node.js ≥ 20, ffmpeg (có `ffprobe`), git-lfs, Chrome/Chromium (HyperFrames dùng Chrome headless).
```bash
brew install python@3.12 node ffmpeg git-lfs
python3.12 --version && node -v && ffmpeg -version | head -1
```

### 3. Backend Python
Repo không có `.venv`. Tạo mới:
```bash
rm -rf .venv && python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .                 # cài gói socnhotv từ pyproject.toml (src ở tool/src)
.venv/bin/pip install uvicorn fastapi pydantic python-multipart jinja2 requests faster-whisper
.venv/bin/python -c "import socnhotv; print('socnhotv OK')"
```
Nếu thiếu thư viện khi chạy, đọc `pyproject.toml` và `tool/pyproject.toml` rồi cài bổ sung.

### 4. Dashboard (Next.js)
```bash
npm --prefix tool/dashboard install
npx --prefix tool/dashboard tsc --noEmit -p tool/dashboard      # kiểm kiểu, kỳ vọng 0 lỗi
```
Production build chỉ khi dev server chưa chạy: `NEXT_DIST_DIR=.next-build npx next build` (đừng build vào `.next` khi cổng 3000 đang chạy).

### 5. OmniVoice (giọng nói, $0, chạy trên máy)
`integrations/OmniVoice` là một repo git lồng nhau (upstream) nên KHÔNG nằm trong repo này. Clone lại đúng phiên bản máy gốc rồi tạo venv riêng:
```bash
mkdir -p integrations && git clone https://github.com/k2-fsa/OmniVoice integrations/OmniVoice
git -C integrations/OmniVoice checkout 08be0b4ccbac3e13e374e86fbfead4b4cac343e2
cd integrations/OmniVoice
python3.11 -m venv .venv 2>/dev/null || python3.12 -m venv .venv
.venv/bin/pip install -e .          # xem integrations/OmniVoice/README.md nếu cần PyTorch bản Apple Silicon (MPS)
cd ../..
```
Trọng số `k2-fsa/OmniVoice` và `Systran/faster-whisper-*` tự tải vào `~/.cache/huggingface` lần đầu dùng (cần mạng). Kho giọng nằm sẵn ở `data/shared/voice_vault/<voice-id>/` (mỗi giọng có `omnivoice_prompt.pt`, `reference_clean_slice.wav`, `reference_transcript.txt`).
**Kiểm giọng thật:**
```bash
.venv/bin/python scripts/voice/voice_studio.py speak --voice soc-nho --script "Chào các bạn nhỏ" --output /tmp/t.mp3
ffmpeg -hide_banner -nostats -i /tmp/t.mp3 -af ebur128 -f null - 2>&1 | grep "I:"     # kỳ vọng ≈ -14 LUFS
```

### 6. HyperFrames (dựng video)
Đã ghim trong `tool/dashboard/node_modules` (≈ v0.9.12). Kiểm:
```bash
tool/dashboard/node_modules/.bin/hyperframes doctor      # kỳ vọng Chrome headless + FFmpeg OK
```

### 7. Biến môi trường
`.env` **không** nằm trong repo (khoá API không được đẩy lên). Chạy `cp .env.example .env` rồi điền `GEMINI_API_KEY` nếu cần (để trống vẫn chạy được chế độ $0). `SOCNHOTV_SPEND_CAP_USD` là trần chi tiêu. Sinh ảnh bằng Gemini **không có hạn mức miễn phí**; mặc định giữ ảnh mock/local.

### 8. Chạy hệ thống
```bash
.venv/bin/uvicorn socnhotv.core.api.app:app --host 127.0.0.1 --port 8000 --reload &
npm --prefix tool/dashboard run dev -- -p 3000 &
curl -s localhost:8000/health        # kỳ vọng {"status":"healthy",...}
```
Mở `http://localhost:3000/vi/studio`.

### 9. Kiểm toàn bộ (bắt buộc làm thật)
```bash
.venv/bin/pytest tool/tests -q       # nền tảng cũ: ~399 passed, 5 failed có sẵn, 3 skipped
```
5 lỗi có sẵn (không do bạn): `test_content_policy::test_import_text_and_merge_rules`, `test_craft_index` ×2, `test_custom_ports` ×2.
Rồi:
1. `curl localhost:8000/projects/soc-nho-tv/graph` và `/projects/gobi/graph` đều trả đồ thị (gobi = 7 node, KOC thử đồ).
2. Trên Studio: đổi sang project **Gobi KOC**, bấm chip giọng `koc-lyly` để nghe mẫu; gõ một câu ngắn vào ô lời của node Gobi rồi bấm "Nghe thử câu này".
3. Chạy flow Tập 1 ở chế độ **Tuỳ chỉnh**: Ảnh = Mock, Video = Tắt, Giọng = Trên máy, Kịch bản = Mock. Kỳ vọng: 6/6 node xong, video 1920×1080, 600 s, **có tiếng** (≈ -14 LUFS).

### 10. Dữ liệu cần biết
- `data/projects/soc-nho-tv`: hoạt hình thiếu nhi (50 kịch bản tập, nhân vật Sóc Nhỏ/Koala… ảnh DNA ở `characters/`).
- `data/projects/gobi`: KOC thời trang Gobi (37 ảnh góc, phòng khách, giọng `koc-lyly`), flow thử đồ đã lưu.
- `data/shared/`: `voice_vault/` (giọng), `templates/` (10 template video), `music_sfx/` (54 SFX, chưa có nhạc nền), `models/`, `knowledge/`.
- Báo cáo tình trạng thật: `status/AUDIT_2026-11-07.md`. Mọi báo cáo "xong 100%" cũ phải coi là lời khai, chưa phải bằng chứng.

### 11. Việc còn dở (không phải lỗi cài đặt)
- Nguồn ảnh AI thật cho bước "Gobi mặc đồ" (đang mock). Gemini ảnh trả phí; Pollinations tải ảnh nhân vật lên host công khai; mflux chưa cài.
- Chưa có nhạc nền (BGM) trong `data/shared/music_sfx/`.
- Giọng `koc-1-mb` lỗi lát mẫu (`needs_fix`).
- Nạp ảnh sản phẩm vào node "Ảnh sản phẩm" của flow Gobi.

Khi xong, in bảng: bước · lệnh đã chạy · kết quả · ghi chú.
