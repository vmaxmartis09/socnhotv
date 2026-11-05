# SESSION T — TOOLBOX: nơi chứa tool độc lập + kho dùng chung
# Prompt giao cho Antigravity (Ag). Mã nhiệm vụ: T-00 … T-12. Làm tuần tự theo mã, mỗi mã xong phải có bằng chứng file thật.

## 0. Bối cảnh đã kiểm (2026-11-05)
- Repo theo kiến trúc 3 phần: `ai/` (luật, kế hoạch) · `tool/` (phần mềm duy nhất) · `data/` (dữ liệu). Xem `ai/AGENTS.md` mục 3.
- **Chưa có nơi chứa tool độc lập.** Hiện có: `tool/integrations/` (rỗng), `tools/` ở gốc repo (`flow_tool`, `video/policy_compliance_checker.py`: lạc chỗ, vi phạm "zero root pollution"), `tool/scripts/` (script lẻ, không có hợp đồng).
- Kho dùng chung hiện có: `data/shared/voice_vault/` (soc-nho, koala-voice, be-an-voice). `data/shared/library/` và `data/shared/models/` **rỗng**.
- Máy: Python 3.11.3, **không có `ffmpeg` trên PATH, không có `nvidia-smi` (không GPU NVIDIA)** → mọi tool phải chạy được CPU, hoặc khai báo rõ `requires_gpu: true`.

## 1. Ràng buộc cách ly (BẮT BUỘC, để không ảnh hưởng session khác)
1. **Chỉ được ghi vào**: `tool/toolbox/**`, `data/shared/assets/**`, `data/shared/models/**`, `data/shared/voice_vault/**` (chỉ THÊM thư mục mới + `index.jsonl`, không sửa/xóa voice cũ), `data/shared/toolbox/**`, và (chỉ T-13, chỉ TẠO file mới) `tool/dashboard/components/toolbox/**`, `tool/dashboard/app/[locale]/toolbox/**`, `ai/plans/2026-11-roadmap/session-T-toolbox/**`, `ai/plans/2026-11-roadmap/status/T.md`, `ai/map/TOOLS.md` (chỉ thêm 1 mục "Toolbox" ở cuối).
2. **Cấm đụng**: `tool/src/socnhotv/**`, `tool/dashboard/**` (trừ hai thư mục toolbox ở trên, và không sửa file có sẵn), `ai/plans/.../session-F-*`, `session-K-*`, `data/projects/**`, `data/shared/knowledge/**`, `data/shared/music_sfx/**`, `data/workspace.json`, thư mục `tools/` ở gốc (chỉ báo cáo, không di chuyển). Cần gì ở đó → ghi vào `status/REQUESTS.md`, không tự sửa.
3. **Mỗi tool tự đóng gói**: venv riêng (`uv venv` trong thư mục tool), `pyproject.toml`/`package.json` riêng, KHÔNG import `socnhotv`, KHÔNG sửa Python/Node toàn cục. Cài dependency vào venv của tool, không `pip install` toàn cục.
4. **Git**: làm trên nhánh riêng `session-t/toolbox`. Commit nhỏ theo mã (`feat(toolbox): T-03 ...`). Không rebase/force-push. Không commit weights, venv, `node_modules`, mẫu giọng thật (thêm `.gitignore`).
5. **Không đọc/ghi khóa API** ngoài `key_vault` hiện có; tool mặc định offline.
6. **Giấy phép**: trước khi clone phải đọc LICENSE của **code và weights riêng**, ghi vào `tool.json.license`. Weights/kho non-commercial (CC-BY-NC, CPML…) → đánh `commercial_ok: false`, KHÔNG đặt làm mặc định. Không chép mã AGPL vào repo (chỉ chạy như tiến trình ngoài).
7. Mọi số liệu/giá/giấy phép trong prompt này là **từ trí nhớ, chưa kiểm** — phải kiểm lại ở nguồn rồi ghi nguồn + ngày vào `tool.json`.

## 2. Thiết kế

### 2.1 Cây thư mục
```
tool/toolbox/
  README.md                 # cách thêm tool, hợp đồng, quy ước
  toolbox_cli/              # CLI mỏng, chỉ dùng stdlib: list | doctor | run | add
  contracts/                # tool.schema.json, run_io.schema.json, store_record.schema.json
  _template/                # khung tool mẫu (copy để tạo tool mới)
  tools/<tool-id>/
    tool.json               # manifest (xem 2.2)
    run.py (hoặc run.mjs)   # điểm vào duy nhất theo hợp đồng 2.3
    .venv/                  # gitignore
    vendor/                 # mã clone về (pin commit), gitignore nếu lớn
    tests/                  # smoke test trên mẫu nhỏ
data/shared/
  voice_vault/<voice-id>/   # đã có; thêm voice.json + index.jsonl (T-04)
  assets/cutouts/<sha8>/    # ảnh tách nền: cutout.png, mask.png, source.json
  assets/audio/, assets/frames/ …   # kho theo loại, tạo khi cần
  models/<tool-id>/…        # weights tải về, gitignore, có SHA256 + nguồn
  toolbox/runs.jsonl        # nhật ký chạy (append-only)
```

### 2.2 `tool.json` (manifest)
`id, name, version, category, entry, runtime (python3.11|node), install, requires_gpu, requires_ffmpeg, license{code,weights,commercial_ok,source_url,checked_on}, inputs/outputs (kiểu), writes_to (kho nào), models[{path,sha256,url}], smoke_test, status (planned|installed|verified|broken)`.

### 2.3 Hợp đồng chạy (độc lập hoàn toàn)
`toolbox run <tool-id> --in in.json --out out.json` ⇒ chạy `tools/<id>/run.py` bằng venv của chính tool, như **tiến trình con**.
- `in.json`: `{ "params": {...}, "inputs": [đường dẫn tuyệt đối], "project": "<id|null>", "dry_run": false }`
- `out.json`: `{ "ok": bool, "outputs": [{"path","kind","sha256"}], "store_records": [...], "warnings": [], "error": null|{"code","message"}, "elapsed_s": n }`
- Exit code: 0 ok · 2 thiếu dependency/model (kèm cách cài) · 3 input sai · 1 lỗi khác. Không hỏi tương tác, không in rác ra stdout ngoài đường dẫn out.json. Lỗi phải **lỗi thật**, cấm trả file giả/mock.
- Session khác (Studio/graph runner) chỉ cần gọi CLI này → không import code của toolbox.

### 2.4 Quy tắc kho dùng chung (an toàn khi nhiều session ghi)
- Thư mục theo **hash nội dung** (`sha8`) hoặc id slug duy nhất → không ghi đè.
- Ghi file: ghi vào `.tmp` rồi `os.replace` (atomic). Cập nhật `index.jsonl`: chỉ **append** một dòng JSON, có file lock (`msvcrt`).
- Mỗi bản ghi có `created_by_tool, tool_version, source, license, created_at`.
- Kho voice: mỗi voice một thư mục `voice.json {id, display_name, aliases[], engine, lang, sample_paths, loudness, status: ready|todo_clone|fallback, consent_note}`. **Alias** giải quyết lệch tên `voice-koala` ↔ `koala-voice` (chỉ thêm `aliases`, không đổi tên thư mục).

## 3. Danh sách nhiệm vụ

| Mã | Nhiệm vụ | Cổng nghiệm thu (file thật) |
|---|---|---|
| **T-00** | Đọc `ai/AGENTS.md`, `ai/map/TOOLS.md`, `tools/`, `tool/integrations/`; xác nhận bản kiểm ở mục 0 còn đúng; tạo nhánh; tạo `status/T.md` | `status/T.md` có danh sách đã kiểm |
| **T-01** | Dựng khung `tool/toolbox/` + `contracts/*.schema.json` + `_template/` + `README.md` | JSON schema hợp lệ; `_template` chạy được "echo tool" |
| **T-02** | CLI `toolbox_cli` (stdlib): `list`, `doctor` (kiểm python, ffmpeg, GPU, dung lượng, venv từng tool), `run`, `add` | `toolbox doctor` in báo cáo thật, nêu rõ ffmpeg đang thiếu |
| **T-03** | Kho dùng chung: module ghi atomic + append `index.jsonl` + lock (stdlib); test 2 tiến trình ghi song song 200 bản ghi | Test: 0 dòng hỏng, 0 trùng id |
| **T-04** | Kho `voice_vault`: sinh `voice.json` cho 3 voice hiện có, alias `voice-koala`→`koala-voice`; tạo bản ghi `todo_clone` cho bông, mun, lu, mimi + người lớn (KHÔNG tạo giọng giả) | `index.jsonl` liệt kê đủ; alias resolve đúng; không file cũ bị sửa |
| **T-05** | **Tool tách nền** `bg-remove`: bọc `rembg` (MIT, CPU) làm mặc định; tuỳ chọn BiRefNet. Ảnh vào → `cutout.png` RGBA + `mask.png` → `data/shared/assets/cutouts/<sha8>/`. Chạy thử trên ảnh DNA Bi trong `data/projects/soc-nho-tv/characters/soc_nho/` (CHỈ ĐỌC) | Mở ảnh kết quả xem viền; kiểm bằng code có pixel alpha 0 và 255 |
| **T-06** | **Tool clone giọng** `voice-clone`: bọc OmniVoice sẵn có (chỉ gọi, không sửa) + mastering -14 LUFS theo AGENTS mục 4. Mẫu giọng + `voice-id` → `voice_vault/<id>/` + `voice.json`. Bắt buộc `consent_note` (mẫu của ai, được phép chưa). Không có mẫu giọng → lỗi 3, KHÔNG tạo | Clone thử bằng mẫu có sẵn; whisper nghe lại, báo WER; vault index cập nhật |
| **T-07** | **Tool phiên âm + canh thời gian** `stt-align`: faster-whisper hoặc whisper.cpp; xuất word-level timings JSON (cho karaoke). whisper-tiny kém với tiếng Việt → mặc định `small` trở lên | Timings khớp ±150ms trên 1 file thoại mẫu |
| **T-08** | **Tool ffmpeg bundle** `ffmpeg-bin`: tải bản static vào `data/shared/models/ffmpeg-bin/`, kiểm SHA256; `toolbox doctor` tự tìm; **không sửa PATH hệ thống** | `ffmpeg -version` chạy qua đường dẫn của tool |
| **T-09** | *(Tuỳ chọn, làm cuối)* **Tool tăng nét** `upscale`: repo Real-ESRGAN ít bảo trì (xem mục 4); chỉ làm nếu cần, ghi tốc độ CPU thực đo | Ảnh 512→1024 có kết quả + thời gian đo |
| **T-10** | **Tool độ sâu cho parallax** `depth-layers`: Depth Anything V2 Small (kiểm giấy phép từng size) → tách 3 lớp tiền/trung/hậu cảnh PNG alpha cho `craft/depth` (Session F dùng sau) | 3 lớp xuất ra, ghép lại ≈ ảnh gốc (SSIM ≥ 0.95, đo bằng code) |
| **T-11** | **Tool tách cảnh/cắt** `scene-cut`: PySceneDetect + `auto-editor`, phục vụ Shorts cắt từ tập dài | Cắt thử 1 video mẫu ra đúng số đoạn |
| **T-13** | Giao diện Toolbox trong dashboard theo mục 4B (chỉ làm sau khi có ≥ 2 tool verified) | Build pass, `check:icons` sạch, ảnh chụp sáng/tối đã mở xem |
| **T-12** | Cập nhật `ai/map/TOOLS.md` (mục Toolbox), chạy `toolbox doctor` + smoke test toàn bộ, ghi kết quả thật vào `status/T.md`, liệt kê tool `broken/planned` trung thực | Báo cáo có số liệu; không tool nào đánh `verified` nếu chưa có file đầu ra |

Thứ tự: T-00 → T-01 → T-02 → T-03 → (T-04, T-08) → tool theo thứ tự test ở mục 4, **từng tool một theo giao thức 4C** → T-13 → T-12.

## 4. Tool miễn phí nên clone (ĐÃ kiểm bằng GitHub API ngày 2026-11-05: sao / giấy phép của repo / lần push gần nhất)
Giấy phép dưới đây là của **mã nguồn repo**; **weights model có thể khác** → Ag vẫn phải đọc model card trước khi tải.

| Ưu tiên | Tool | Repo | Sao | Giấy phép | Push | Dùng cho | Nhẹ/CPU? |
|---|---|---|---|---|---|---|---|
| A | rembg | danielgatis/rembg | 25k | MIT | 11-02 | Tách nền (T-05) | CPU được, model u2net ~170MB |
| A | faster-whisper | SYSTRAN/faster-whisper | 26k | MIT | 11-02 | Phiên âm (T-07) | CPU int8 được |
| A | whisper.cpp | ggml-org/whisper.cpp | 55k | MIT | 11-05 | Phiên âm nhẹ, không cần Python | Rất nhẹ |
| A | OmniVoice | k2-fsa/OmniVoice | 16k | Apache-2.0 | 11-02 | Clone giọng (đang dùng, T-06) | đã chạy trên máy |
| A | auto-editor | WyattBlue/auto-editor | 5.8k | Unlicense | 11-05 | Cắt khoảng lặng, cắt Shorts (T-11) | Nhẹ |
| A | PySceneDetect | Breakthrough/PySceneDetect | 5.4k | BSD-3 | 11-02 | Tách cảnh (T-11) | Nhẹ, CPU |
| A | silero-vad | snakers4/silero-vad | 10.6k | MIT | 10-22 | Phát hiện lời nói, cắt mẫu giọng sạch | Rất nhẹ |
| B | BiRefNet | ZhengPeng7/BiRefNet | 4.4k | MIT | 10-25 | Tách nền chất lượng cao hơn rembg | Nặng hơn, CPU chậm |
| B | Demucs | adefossez/demucs | 3.5k | MIT | 10-26 | Tách giọng/nhạc nền | CPU chậm nhưng chạy được |
| B | Depth-Anything-V2 | DepthAnything/Depth-Anything-V2 | 9.1k | Apache-2.0 | 2026-03 | Tách 3 lớp parallax (T-10) | Bản Small chạy CPU; **chỉ Small là Apache**, size lớn khác giấy phép (kiểm) |
| B | WhisperX | m-bain/whisperX | 25k | BSD-2 | 10-22 | Canh từng từ cho karaoke | Cần model align tiếng Việt, kiểm |
| B | F5-TTS | SWivid/F5-TTS | 15.5k | MIT (code) | 11-03 | TTS dự phòng | **Weights thường CC-BY-NC** → không dùng thương mại |
| B | GPT-SoVITS | RVC-Boss/GPT-SoVITS | 65k | MIT | 10-31 | Clone giọng ít mẫu | Cần GPU để tốt; thử tiếng Việt |
| B | MoviePy | Zulko/moviepy | 15k | MIT | 08-26 | Ghép/cắt bằng Python | Nhẹ; cần ffmpeg |
| C | CosyVoice | QwenAudio/CosyVoice | 24k | Apache-2.0 | 05-26 | TTS/clone đa ngôn ngữ | Nặng, cần GPU để mượt |
| C | yt-dlp | yt-dlp/yt-dlp | 205k | Unlicense | 11-04 | Chỉ để nghiên cứu nội bộ | Nhẹ |

**Bỏ qua / thận trọng (đã kiểm):**
- `xinntao/Real-ESRGAN` (BSD-3) lần push cuối 2024-08, `rife-ncnn-vulkan` (MIT) 2024-01, `Real-ESRGAN-ncnn-vulkan` giấy phép `NOASSERTION` 2024-05 → ít bảo trì. T-09 đổi thành **tuỳ chọn**, Ag chỉ làm nếu thật sự cần tăng nét, và phải đọc LICENSE từng file.
- `Wav2Lip` (không có giấy phép), `SadTalker` (NOASSERTION), `ComfyUI-RMBG` (GPL-3.0), `rhubarb-lip-sync` (NOASSERTION) → **không đưa vào mặc định**; nếu cần lip-sync phải hỏi người dùng.
- Sinh video cục bộ (Wan/LTX/ComfyUI) cần GPU NVIDIA, máy hiện không có → để sau.
- RMBG-1.4/2.0, XTTS-v2, AudioCraft: weights non-commercial → không mặc định.
- FFmpeg: giấy phép LGPL/GPL tuỳ bản build → T-08 ghi rõ bản nào được tải.

**Thứ tự đề xuất để người dùng test sớm:** T-05 tách nền → T-07 phiên âm → T-06 clone giọng → T-11 cắt cảnh → T-10 độ sâu → còn lại.

## 4B. T-13 — Giao diện Toolbox trong dashboard (sau khi có ≥ 2 tool verified)
Giao diện **bắt buộc** tuân thủ chuẩn chung của dự án; đọc trước: `ai/rules/ui-rules.md` (22 điều), `ai/rules/morphicons.md`, `ai/skills/design-taste-frontend`, `tool/dashboard/app/globals.css`.
- **Theme**: chỉ dùng token CSS có sẵn (`--background`, `--card`, `--border`, `--brand`, `--success/--warning/--danger/--info`, `--radius-*`, `--shadow-float`); hỗ trợ cả sáng và tối (`.dark`). Cấm hard-code màu, cấm thêm thư viện UI mới.
- **Icon**: chỉ `@/components/ui/icons` và `MorphIcon` (Morphicons); **cấm `lucide-react`**. Nút chỉ-icon phải có `aria-label`/`data-tip` (tooltip tức thì qua `TooltipHost`). Icon đổi trạng thái (chạy/dừng, ok/lỗi) dùng `<MorphIcon … spring="snappy" />`.
- **Thành phần dùng chung**: `Button`, `Card`, `AiLoading` (mọi trạng thái đang chạy), `StatusIsland`, `ConfirmHost` qua `confirm()` từ `lib/confirm.ts` (cấm `window.confirm`).
- **Animation**: framer-motion, tween 0.15–0.25s ease-out `[0.22, 1, 0.36, 1]`, không spring nảy, không scale mạnh; không lặp animation: dùng `initial={enterOnce(key, …)}` từ `lib/motion.ts`; bấm nút `active:scale`.
- **Bố cục**: căn trái; thẻ `p-3`, khoảng cách `gap-3`; vùng cuộn dùng `scroll-quiet`; trạng thái trống dùng ô viền nét đứt có gợi ý việc cần làm (quy tắc 13, 20); nút "thêm" là thẻ trống nét đứt cạnh thẻ cuối (quy tắc 22); không hai nút cùng chức năng (quy tắc 19); click = chọn + xem trước, nhấn đúp = mở (quy tắc 3).
- **Nội dung**: danh sách tool (trạng thái `planned/installed/verified/broken`, giấy phép, yêu cầu GPU/ffmpeg), nút chạy thử với mẫu nhỏ, xem kho (voice, cutouts) bằng thẻ có xem trước. Tiếng Việt qua `messages/` (i18n sẵn có).
- **Cách ly**: chỉ TẠO file mới trong `tool/dashboard/components/toolbox/**` và `tool/dashboard/app/[locale]/toolbox/**`. KHÔNG sửa file hiện có của dashboard; việc đăng ký menu/phím tắt/i18n ghi vào `status/REQUESTS.md` để người dùng duyệt. Gọi backend chỉ qua `toolbox` CLI/một API mỏng trong `tool/toolbox/`, không sửa `tool/src/socnhotv`.
- **Nghiệm thu**: `npm run check:icons` (script có sẵn) sạch; `NEXT_DIST_DIR=.next-build npx next build` pass (KHÔNG build vào `.next` khi dev server cổng 3000 đang chạy); chụp ảnh màn hình sáng + tối và mở xem.

## 4C. Giao thức báo người dùng test
Xong **từng tool** (không đợi cả đợt), Ag làm đúng 3 việc rồi DỪNG chờ người dùng test tool đó, không tự chuyển sang tool kế nếu tool này chưa được xác nhận:
1. Ghi `data/shared/toolbox/ready/T-XX.md`: tên tool, lệnh chạy thử 1 dòng (có ví dụ đường dẫn mẫu thật), file đầu ra nằm ở đâu, kết quả đã đo (thời gian, kích thước, chỉ số), giới hạn đã biết.
2. Cập nhật dòng tương ứng trong `status/T.md`: `READY_FOR_USER_TEST`.
3. Nhắn người dùng 1 câu: "T-XX <tên> sẵn sàng test: chạy <lệnh>, xem <đường dẫn>".
Người dùng trả "OK T-XX" thì mới đánh `verified`; trả lỗi thì sửa tiếp trong cùng mã. (Riêng T-00…T-04 là hạ tầng, không cần chờ.)

## 5. Báo cáo cuối của Ag
Ghi vào `ai/plans/2026-11-roadmap/status/T.md`: mỗi mã (done/partial/blocked) + đường dẫn bằng chứng + điều chưa làm. Cấm báo "xuất sắc/pass" không kèm file đo được (bài học từ F0 audit mục 1).
