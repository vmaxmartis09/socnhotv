# SENIOR BACKEND ARCHITECTURE & REPOSITORY GOVERNANCE STANDARDS

> [!CRITICAL]
> **QUY TẮC BẮT BUỘC ĐỐI VỚI MỌI TÁC VỤ SINH FILE & THÊM REPO MỚI**
> Dự án tuân thủ nghiêm ngặt tiêu chuẩn kiến trúc tại [`ARCHITECTURE.md`](../../ARCHITECTURE.md). Tuyệt đối không sinh file tự do ở thư mục gốc hoặc tạo thư mục rác.

---

## 1. CHÍNH SÁCH KHÔNG XẢ RÁC THƯ MỤC GỐC (ZERO-ROOT-POLLUTION)
- **CẤM TUYỆT ĐỐI:** Không tạo bất kỳ file `.py`, `.mjs`, `.txt`, `.json`, `.bat`, `.sh` hay file media (.jpg, .mp4, .mp3) ở thư mục gốc (`/Volumes/Data/gobi-social/`).
- Thư mục gốc chỉ được phép chứa: các file meta dự án (`README.md`, `pyproject.toml`, `requirements.txt`, tài liệu chỉ dẫn Agent `AGENTS.md`, `ARCHITECTURE.md`, `CONTINUITY.md`).

---

## 2. BẢN ĐỒ VỊ TRÍ ĐẶT FILE MỚI BẮT BUỘC
Khi tạo file mới, Agent **BẮT BUỘC** đặt vào đúng phân tầng:

| Loại công việc | Thư mục bắt buộc |
| :--- | :--- |
| **Nghiệp vụ Render video, cắt ghép, subtitle** | `src/gobi/services/media/` |
| **Xử lý âm thanh, Voice Clone, Edge-TTS** | `src/gobi/services/voice/` |
| **Kịch bản, Prompt 36 góc camera** | `src/gobi/services/prompt/` |
| **Tự học, tối ưu prompt, phân tích Big Data** | `src/gobi/services/intelligence/` |
| **Tự động hóa trình duyệt (Ego, Playwright)** | `src/gobi/adapters/browser/` |
| **Adapter nền tảng (TikTok, FB, Flow/Veo)** | `src/gobi/adapters/platforms/<platform>/` |
| **Scraper cào dữ liệu xu hướng** | `src/gobi/adapters/scrapers/` |
| **Lệnh dòng lệnh mới (CLI)** | `src/gobi/cli/` |
| **Data model, Pydantic schema, luật Safe Zone** | `src/gobi/domain/` |
| **File cấu hình JSON/YAML** | `configs/` (hoặc `configs/products/`) |
| **Ảnh Master DNA, 36 panels, Voice Vault** | `assets/<subfolder>/` |
| **Dữ liệu thô cào về (TXT, JSON dumps)** | `data/raw/<source>/` |
| **Kiểm thử tự động chính thức** | `tests/unit/`, `tests/integration/`, `tests/e2e/` |
| **File nháp, inspect DOM, debug tạm thời** | `scratch/` (CẤM TẠO Ở ROOT) |
| **Nhúng / Clone repo bên thứ 3 từ bên ngoài** | `integrations/<repo_name>/` (Kèm Adapter tại `src/gobi/adapters/integrations/`) |

---

## 3. NGUYÊN TẮC TÍCH HỢP REPO NGOẠI VI (INTEGRATIONS PROTOCOL)
- Mọi repository bên thứ 3 (như crawlers, frameworks ngoài) **BẮT BUỘC** nằm trong `integrations/<repo_name>/`.
- Tuyệt đối không clone thẳng vào root hay vào `tools/`.
- Phải có file `integrations/<repo_name>/INTEGRATION_NOTE.md` và một class Adapter tại `src/gobi/adapters/integrations/` để cách ly logic.
