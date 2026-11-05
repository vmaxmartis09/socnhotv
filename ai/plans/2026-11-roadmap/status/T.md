# Báo Cáo Tiến Độ Session T — Toolbox & Shared Vaults

**Trạng thái:** ĐANG THỰC HIỆN  
**Nhánh:** `session-t/toolbox`  
**Ngày bắt đầu:** 2026-11-05  
**Phạm vi sở hữu:** `tool/toolbox/**`, `data/shared/assets/**`, `data/shared/models/**`, `data/shared/voice_vault/**`, `data/shared/toolbox/**`, `tool/dashboard/components/toolbox/**`, `tool/dashboard/app/[locale]/toolbox/**`, `ai/plans/2026-11-roadmap/session-T-toolbox/**`, `ai/plans/2026-11-roadmap/status/T.md`.

---

## 1. BẢNG THEO DÕI NHIỆM VỤ

| Mã | Nhiệm vụ | Trạng thái | Bằng chứng / Đường dẫn | Ghi chú |
|---|---|---|---|---|
| **T-00** | Khởi tạo Session T, kiểm tra môi trường, tạo nhánh & status/T.md | DONE | `status/T.md` | Xác nhận môi trường đúng như mục 0 |
| **T-01** | Dựng khung `tool/toolbox/` + contracts + _template + README | DONE | `tool/toolbox/contracts/`, `tool/toolbox/_template/`, `tool/toolbox/README.md` | JSON schema hợp lệ, echo tool test pass |
| **T-02** | CLI `toolbox_cli` (list, doctor, run, add) | PLANNED | `tool/toolbox/toolbox_cli/` | |
| **T-03** | Kho dùng chung: atomic write + append lock + stress test | PLANNED | `tool/toolbox/contracts/` & tests | |
| **T-04** | Chuẩn hóa `voice_vault`: voice.json, aliases, todo_clone | PLANNED | `data/shared/voice_vault/` | |
| **T-08** | Tool bundle ffmpeg static (CPU) | PLANNED | `data/shared/models/ffmpeg-bin/` | |
| **T-05** | Tool tách nền `bg-remove` (rembg CPU) | PLANNED | `tool/toolbox/tools/bg-remove/` | Chờ test user |
| **T-07** | Tool phiên âm `stt-align` (faster-whisper CPU) | PLANNED | `tool/toolbox/tools/stt-align/` | Chờ test user |
| **T-06** | Tool clone giọng `voice-clone` (OmniVoice wrapper) | PLANNED | `tool/toolbox/tools/voice-clone/` | Chờ test user |
| **T-11** | Tool tách cảnh `scene-cut` (PySceneDetect + auto-editor) | PLANNED | `tool/toolbox/tools/scene-cut/` | Chờ test user |
| **T-10** | Tool độ sâu `depth-layers` (Depth Anything V2 Small) | PLANNED | `tool/toolbox/tools/depth-layers/` | Chờ test user |
| **T-09** | *(Tuỳ chọn)* Tool tăng nét `upscale` | PLANNED | `tool/toolbox/tools/upscale/` | Tuỳ chọn |
| **T-13** | Giao diện Dashboard Toolbox (Morphicons, theme token) | PLANNED | `tool/dashboard/.../toolbox/` | Sau khi có >=2 tool verified |
| **T-12** | Tổng kết, doctor full, map/TOOLS.md | PLANNED | `ai/map/TOOLS.md`, `status/T.md` | |

---

## 2. KẾT QUẢ KIỂM TRA MÔI TRƯỜNG MỤC 0 (T-00)

1. **Kiến trúc 3 phần (`ai/`, `tool/`, `data/`)**:
   - `ai/`: chứa luật `ai/AGENTS.md`, các plan, map/TOOLS.md.
   - `tool/`: chứa `src/socnhotv/`, `dashboard/`, `integrations/` (rỗng, chỉ có .gitkeep), `scripts/`.
   - `tools/` ở gốc repo hiện có `flow_tool/` và `video/policy_compliance_checker.py` (ghi nhận vi phạm zero root pollution, không đụng vào theo luật cách ly).
   - `data/`: `data/shared/voice_vault/` có 3 thư mục `soc-nho`, `koala-voice`, `be-an-voice` và `.uploads`.
   - `data/shared/library/` và `data/shared/models/` hiện rỗng (chỉ có `.gitkeep`).

2. **Môi trường Runtime**:
   - Python: Có Python 3.11 (`C:\Users\dtthoai\AppData\Local\Programs\Python\Python311\python.exe`) và Python 3.12 (`C:\Python312\python.exe`), gọi được qua `py -3.11` hoặc đường dẫn tuyệt đối.
   - `ffmpeg`: **KHÔNG có** trên PATH. Sẽ giải quyết độc lập tại T-08 (`ffmpeg-bin`).
   - `nvidia-smi` / GPU: **KHÔNG có** GPU NVIDIA. Mọi tool mặc định chạy CPU (`requires_gpu: false`).
   - Node / NPM: Có sẵn cho Dashboard (T-13).

3. **Nhánh Git**:
   - Nhánh làm việc riêng: `session-t/toolbox` (được tạo từ nhánh có `T0_TOOLBOX_PROMPT.md`).
