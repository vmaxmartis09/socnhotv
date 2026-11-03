# SỔ TAY QUẢN LÝ SYMLINK TƯƠNG THÍCH (LEGACY LINKS)

Tài liệu này theo dõi toàn bộ các symbolic link (symlink) được tạo trong quá trình tái cấu trúc repository SocNhoTV để đảm bảo tính tương thích ngược với các IDE, Agent AI và công cụ hiện hữu.

> [!NOTE]
> Quy tắc kiểm tra: Trước Bước 8, bắt buộc chạy `grep` toàn bộ codebase để đảm bảo không còn code nào phụ thuộc cứng vào các đường dẫn cũ trước khi xem xét gỡ bỏ hoặc giữ lại các link tương thích.

---

## 1. Danh sách Symlink phần AI & Agent Configurations (Tạo ở Bước 3)

| Symlink (Nơi đặt) | Đích trỏ đến (Target) | Mục đích / Công cụ sử dụng | Trạng thái dự kiến sau Bước 8 |
| :--- | :--- | :--- | :--- |
| `AGENTS.md` | `ai/AGENTS.md` | Agent AI đọc luật từ root | **Giữ vĩnh viễn** làm entrypoint |
| `CLAUDE.md` | `ai/AGENTS.md` | Claude Code & Claude Desktop | **Giữ vĩnh viễn** |
| `GEMINI.md` | `ai/AGENTS.md` | Gemini CLI & Antigravity | **Giữ vĩnh viễn** |
| `.cursorrules` | `ai/AGENTS.md` | Cursor AI IDE | **Giữ vĩnh viễn** |
| `.claude/skills` | `../ai/skills` | Claude Code skill discovery | **Giữ vĩnh viễn** |
| `.agents` | `ai` | Tương thích ngược với config cũ | Tạm thời (review ở Bước 8) |
| `.agent` | `ai` | Antigravity IDE built-in discovery | Tạm thời (review ở Bước 8) |

---

## 2. Danh sách Symlink dữ liệu & tài liệu (Tạo ở Bước 4)

| Symlink (Nơi đặt) | Đích trỏ đến (Target) | Mục đích sử dụng | Trạng thái dự kiến sau Bước 8 |
| :--- | :--- | :--- | :--- |
| `assets/soc_nho` | `../data/projects/soc-nho-tv/characters/soc_nho` | Script cũ đọc DNA ảnh & profile Sóc Nhỏ | Tạm thời (gỡ ở Bước 8) |
| `assets/koala` | `../data/projects/soc-nho-tv/characters/koala` | Script cũ đọc DNA ảnh & profile Koala | Tạm thời (gỡ ở Bước 8) |
| `assets/character_scale/SCALE_LOCK.md` | `../../data/projects/soc-nho-tv/characters/SCALE_LOCK.md` | Quy chuẩn tỉ lệ nhân vật | Tạm thời (gỡ ở Bước 8) |
| `assets/voice_vault` | `../data/shared/voice_vault` | Voice studio & clone script cũ | Tạm thời (gỡ ở Bước 8) |
| `projects/soc-nho-sau-rang` | `../data/projects/soc-nho-tv/content/episodes/soc-nho-sau-rang` | HyperFrames video project cũ | Tạm thời (gỡ ở Bước 8) |
| `work/flow_package_demo` | `../data/projects/soc-nho-tv/raw/flow_package_demo` | Demo packages cũ | Tạm thời (gỡ ở Bước 8) |
| `output` | `data/projects/soc-nho-tv/output` | Script xuất file cũ ra output/ | Tạm thời (gỡ ở Bước 8) |
| `docs` | `ai/knowledge` | IDE / Dev tra cứu tài liệu cũ | Tạm thời (gỡ ở Bước 8) |
| `studio` | `tool/dashboard` | Lối tắt nhanh vào ứng dụng AI Video Studio Next.js | **Giữ vĩnh viễn** |
