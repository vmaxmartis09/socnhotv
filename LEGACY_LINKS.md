# SỔ TAY QUẢN LÝ SYMLINK TƯƠNG THÍCH (LEGACY LINKS)

Tài liệu này theo dõi toàn bộ các symbolic link (symlink) được tạo trong quá trình tái cấu trúc repository SocNhoTV để đảm bảo tính tương thích ngược với các IDE, Agent AI và công cụ hiện hữu.

> [!NOTE]
> Quy tắc kiểm tra: Trước Bước 8, bắt buộc chạy `grep` toàn bộ codebase để đảm bảo không còn code nào phụ thuộc cứng vào các đường dẫn cũ trước khi xem xét gỡ bỏ hoặc giữ lại các link tương thích.

---

## 1. Danh sách Symlink phần AI & Agent Configurations

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

## 2. Danh sách Symlink dữ liệu & công cụ (sẽ cập nhật ở Bước 4 & Bước 5)

*(Sẽ bổ sung khi di chuyển data và tool ở Bước 4 & 5)*
