# SESSION T — TOOLBOX: nơi chứa tool độc lập + kho dùng chung
# Prompt giao cho Antigravity (Ag). Mã nhiệm vụ: T-00 … T-12. Làm tuần tự theo mã, mỗi mã xong phải có bằng chứng file thật.

## 0. Bối cảnh đã kiểm (2026-11-05)
- Repo theo kiến trúc 3 phần: `ai/` (luật, kế hoạch) · `tool/` (phần mềm duy nhất) · `data/` (dữ liệu). Xem `ai/AGENTS.md` mục 3.
- **Chưa có nơi chứa tool độc lập.** Hiện có: `tool/integrations/` (rỗng), `tools/` ở gốc repo (`flow_tool`, `video/policy_compliance_checker.py`: lạc chỗ, vi phạm "zero root pollution"), `tool/scripts/` (script lẻ, không có hợp đồng).
- Kho dùng chung hiện có: `data/shared/voice_vault/` (soc-nho, koala-voice, be-an-voice). `data/shared/library/` và `data/shared/models/` **rỗng**.
- Máy: Python 3.11.3, **không có `ffmpeg` trên PATH, không có `nvidia-smi` (không GPU NVIDIA)** → mọi tool phải chạy được CPU, hoặc khai báo rõ `requires_gpu: true`.

## 1. Ràng buộc cách ly (BẮT BUỘC, để không ảnh hưởng session khác)
1. **Chỉ được ghi vào**: `tool/toolbox/**`, `data/shared/assets/**`, `data/shared/models/**`, `data/shared/voice_vault/**` (chỉ THÊM thư mục mới + `index.jsonl`, không sửa/xóa voice cũ), `data/shared/toolbox/**`, `ai/plans/2026-11-roadmap/session-T-toolbox/**`, `ai/plans/2026-11-roadmap/status/T.md`, `ai/map/TOOLS.md` (chỉ thêm 1 mục "Toolbox" ở cuối).
2. **Cấm đụng**: `tool/src/socnhotv/**`, `tool/dashboard/**`, `ai/plans/.../session-F-*`, `session-K-*`, `data/projects/**`, `data/shared/knowledge/**`, `data/shared/music_sfx/**`, `data/workspace.json`, thư mục `tools/` ở gốc (chỉ báo cáo, không di chuyển). Cần gì ở đó → ghi vào `status/REQUESTS.md`, không tự sửa.
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
| **T-09** | **Tool tăng nét** `upscale`: Real-ESRGAN ncnn-vulkan hoặc bản CPU nếu không có Vulkan; ghi tốc độ CPU thực đo | Ảnh 512→1024 có kết quả + thời gian đo |
| **T-10** | **Tool độ sâu cho parallax** `depth-layers`: Depth Anything V2 Small (kiểm giấy phép từng size) → tách 3 lớp tiền/trung/hậu cảnh PNG alpha cho `craft/depth` (Session F dùng sau) | 3 lớp xuất ra, ghép lại ≈ ảnh gốc (SSIM ≥ 0.95, đo bằng code) |
| **T-11** | **Tool tách cảnh/cắt** `scene-cut`: PySceneDetect + `auto-editor`, phục vụ Shorts cắt từ tập dài | Cắt thử 1 video mẫu ra đúng số đoạn |
| **T-12** | Cập nhật `ai/map/TOOLS.md` (mục Toolbox), chạy `toolbox doctor` + smoke test toàn bộ, ghi kết quả thật vào `status/T.md`, liệt kê tool `broken/planned` trung thực | Báo cáo có số liệu; không tool nào đánh `verified` nếu chưa có file đầu ra |

Thứ tự phụ thuộc: T-00 → T-01 → T-02 → T-03 → (T-04, T-08) → T-05/T-06/T-07/T-09/T-10/T-11 (song song được) → T-12.

## 4. Gợi ý tool làm video có thể clone về máy (chưa kiểm — Ag phải kiểm giấy phép & yêu cầu máy)
| Nhóm | Tool | Giấy phép (cần kiểm) | Ghi chú |
|---|---|---|---|
| Tách nền | rembg; BiRefNet | MIT; MIT | CPU được. Tránh RMBG-1.4/2.0 cho thương mại (non-commercial) |
| Clone/TTS | OmniVoice (đang dùng); F5-TTS; GPT-SoVITS; XTTS-v2 | ?; code MIT, weights CC-BY-NC; MIT; CPML (non-commercial) | Tiếng Việt cần thử thật; weights NC không dùng mặc định |
| Phiên âm/canh | faster-whisper; whisper.cpp; WhisperX | MIT; MIT; BSD | Dùng model ≥ small cho tiếng Việt |
| Tách giọng/nhạc | Demucs | MIT | Làm sạch mẫu giọng, tách BGM |
| Tăng nét | Real-ESRGAN (ncnn-vulkan) | BSD-3 | CPU rất chậm |
| Nội suy khung | RIFE (ncnn) | MIT (kiểm) | Làm mượt shot ảnh động |
| Độ sâu | Depth Anything V2 Small | Apache-2.0 (Small; size lớn khác) | Parallax 3 lớp |
| Cắt/ghép | FFmpeg; PySceneDetect; auto-editor; MoviePy | LGPL/GPL tuỳ build; BSD; Unlicense; MIT | FFmpeg đang **thiếu** trên máy |
| Dựng | HyperFrames (đang dùng) | đã có | Remotion cần giấy phép trả phí khi thương mại |
| Sinh video cục bộ | Wan 2.x; LTX-Video; ComfyUI | Apache-2.0 / weights OpenRAIL | **Cần GPU NVIDIA**, máy hiện không có; để P2 |
| Nhạc/SFX | AudioCraft (MusicGen/AudioGen) | code MIT, weights CC-BY-NC | Không dùng thương mại; `music_sfx` đang trống, nên dùng nhạc CC0 |
| Tải tham khảo | yt-dlp | Unlicense | Chỉ cho nghiên cứu nội bộ; không dùng lại nội dung có bản quyền |

## 5. Báo cáo cuối của Ag
Ghi vào `ai/plans/2026-11-roadmap/status/T.md`: mỗi mã (done/partial/blocked) + đường dẫn bằng chứng + điều chưa làm. Cấm báo "xuất sắc/pass" không kèm file đo được (bài học từ F0 audit mục 1).
