# 00 — BOOTSTRAP (chạy đúng 1 lần, bởi session thắng khoá `status/.bootstrap.lock`)

> Cả 3 session A/B/C khởi động cùng lúc. Session nào `mkdir ai/plans/2026-11-roadmap/status/.bootstrap.lock` thành công thì làm file này; 2 session còn lại làm phần logic thuần Python trong thư mục riêng và KHÔNG chờ. Làm bootstrap thật gọn, ưu tiên Bước 1–5 (backend + khung frontend) trước và tạo `status/BOOTSTRAP_DONE` ngay khi Bước 1–5 xong (Bước 6 cài deps làm sau, rồi ghi thêm `status/DEPS_DONE`).

Bạn là kỹ sư trưởng của repo `/Volumes/Data/socnhotv`. Nhiệm vụ: dựng "khung cắm" để 3 session A/B/C làm song song mà không đụng file nhau. Đọc trước: `CLAUDE.md`, `ai/AGENTS.md`, `ai/plans/2026-11-roadmap/README.md`, `ai/plans/2026-11-roadmap/CONTRACTS.md`. Làm hết các bước, không hỏi lại.

Bối cảnh thật: backend FastAPI ở `tool/src/socnhotv/core/api/app.py` (`app.include_router(data_router)`, `voice_router`), node đăng ký cứng trong `core/nodes/registry.py::initialize_defaults()`, i18n Next-intl nạp `messages/${locale}.json` trong `tool/dashboard/i18n/request.ts`, store Zustand ở `tool/dashboard/store/`. Các thư mục `tool/src/socnhotv/{video,social,intelligence,workspace,adapters}` đang TRỐNG.

## Bước 1 — Workspace module
Tạo `tool/src/socnhotv/workspace/__init__.py` + `paths.py`:
- `repo_root()` (dò ngược tới thư mục có `data/workspace.json`), `data_root()`, `project_path(project_id, *parts) -> Path` (tự `mkdir parents` cho thư mục cha khi `ensure=True`), `shared_path(*parts)`, `active_project_id()` đọc `data/workspace.json`, `list_projects()`.
- Không đổi `ProjectStore`; chỉ thêm helper. Test `tool/tests/test_workspace_paths.py`.

## Bước 2 — Router plugin tự nạp
- Tạo package `tool/src/socnhotv/core/api/routes/__init__.py` có `def include_all(app)`: duyệt `pkgutil.iter_modules` trong package, import từng module, nếu có biến `router` (APIRouter) thì `app.include_router(router)`. Bắt lỗi import từng module và `logging.warning` (1 module hỏng không làm sập server).
- Tạo sẵn 4 file rỗng có `router = APIRouter(prefix=..., tags=[...])` + 1 endpoint `GET /_ping`: `video.py` (`/video`), `sources.py` (`/sources`), `intel.py` (`/intel`), `social.py` (`/social`). Prefix tính sau `/projects/{project_id}` khi cần — ghi rõ trong docstring.
- Sửa `app.py` duy nhất 1 lần: sau 2 dòng `include_router` hiện có thêm `from socnhotv.core.api.routes import include_all; include_all(app)`.

## Bước 3 — Node plugin tự nạp
- Tạo `tool/src/socnhotv/core/nodes/plugins/__init__.py` với `def load_all(registry_cls)`: import mọi module con, gọi `module.register(registry_cls)` nếu có.
- Sửa `registry.py` 1 lần: cuối `initialize_defaults()` gọi `load_all(cls)`.
- Tạo sẵn `plugins/video.py`, `plugins/sources.py`, `plugins/social.py` với `def register(registry): pass`.

## Bước 4 — Hợp đồng liên session (stub chạy được)
Tạo đúng chữ ký trong `CONTRACTS.md` mục 2:
- `tool/src/socnhotv/video/__init__.py`, `video/contracts.py`: models + `submit_render` (ghi `runs/render_queue/<job_id>.json` status `queued`), `get_render`, `list_templates` (đọc `data/shared/templates/*/template.json`, trả `[]` nếu chưa có).
- `tool/src/socnhotv/intelligence/__init__.py`, `intelligence/contracts.py`: `VideoBlueprint`, `Beat`, `ChannelBlueprint`, `ContentIdea` + `save_*/load_*/list_*` lưu JSON ở `content/blueprints/`, `content/ideas/`.
- `tool/src/socnhotv/social/__init__.py`, `social/contracts.py`: `create_draft_post(...)` ghi `publishing/inbox/<post_id>.json`.
- `tool/src/socnhotv/sources/__init__.py` (rỗng).
- Test `tool/tests/test_contracts_stubs.py` cho cả 3.

## Bước 5 — Frontend plugin
1. **i18n:** tạo `tool/dashboard/messages/modules/` với 6 file `video.vi.json, video.en.json, sources.vi.json, sources.en.json, social.vi.json, social.en.json` (mỗi file `{"video": {"title": "Video"}}` v.v. — key gốc = tên module). Sửa `i18n/request.ts` để deep-merge `messages/${locale}.json` với mọi `messages/modules/*.${locale}.json` (import tĩnh 3 module cụ thể là đủ, không cần glob).
2. **Nav:** tìm nơi định nghĩa menu điều hướng chính (Sidebar/UserBubble/layout `app/[locale]/layout.tsx` — tìm `href=` tới `/characters`, `/jobs`, `/settings`). Tạo `tool/dashboard/components/navigation/nav-modules/{index.ts,video.ts,sources.ts,social.ts}`: mỗi file export `NavItem[]` (`{id, href, labelKey, icon}` icon lấy từ `@/components/ui/icons`); `index.ts` gộp lại. Render các item này trong menu chính đúng style hiện tại. Ban đầu mỗi module 1 item: `/templates` (A), `/sources` (B), `/social` (C).
3. **Store:** tạo `tool/dashboard/store/modules/{video,sources,social}.ts`, mỗi file 1 Zustand store độc lập rỗng (`create<…>()(() => ({}))`). Session tự mở rộng file của mình, không đụng `store/index.ts`.
4. Tạo 3 page placeholder `app/[locale]/templates/page.tsx`, `app/[locale]/sources/page.tsx`, `app/[locale]/social/page.tsx` dùng layout/Card có sẵn, hiển thị tiêu đề module.
5. Thêm vào `lib/core-api.ts` KHÔNG làm. Mỗi session tự tạo `lib/api/<module>.ts` của mình (ghi chú điều này vào CONTRACTS nếu thiếu).

## Bước 6 — Dependencies (gom 1 lần, sau này không ai sửa)
- `tool/pyproject.toml` thêm: `yt-dlp`, `scenedetect[opencv]`, `imagehash`, `apscheduler>=3.10`, `google-api-python-client`, `google-auth-oauthlib`, `jinja2`, `python-dateutil`, `rapidfuzz`. Chạy `cd tool && uv sync` (hoặc `.venv/bin/pip install -e .`). Nếu gói nào cài lỗi → bỏ khỏi pyproject và ghi vào `status/REQUESTS.md`.
- Dashboard: thêm devDependency `hyperframes` (CLI HeyGen HyperFrames; nếu tên gói npm khác, xem `ai/skills/hyperframes-cli/SKILL.md` để lấy đúng tên) và `@dnd-kit/core`, `@dnd-kit/sortable`, `date-fns`. `npm install`. Xác nhận `npx hyperframes --version` chạy được; nếu không, ghi lại cách chạy đúng vào `status/REQUESTS.md`.

## Bước 7 — Sửa bug có sẵn nhỏ
- Frontend `components/studio/tabs/PublishTab.tsx` gọi `POST /projects/{id}/publishing/schedule` không tồn tại → KHÔNG sửa ở đây (session C xử lý), chỉ ghi vào `status/C.md` mục "Nợ đầu vào".

## Bước 8 — Nghiệm thu
- `cd tool && .venv/bin/python -m pytest -q` pass toàn bộ (test cũ + mới).
- `cd tool/dashboard && npx tsc --noEmit` không phát sinh lỗi mới.
- `curl localhost:8000/video/_ping`, `/sources/_ping`, `/intel/_ping`, `/social/_ping` trả 200 (server 8000 có thể cần người dùng restart — nếu không chạy `--reload`, hãy khởi động lại uvicorn 8000 MỘT lần duy nhất ở bước này: `cd tool && .venv/bin/python -m uvicorn socnhotv.core.api.app:app --app-dir src --host 127.0.0.1 --port 8000 --reload`).
- Mở `http://localhost:3000` thấy 3 mục menu mới, bấm vào ra đúng trang.
- Tạo `ai/plans/2026-11-roadmap/status/{A,B,C,REQUESTS}.md` (tiêu đề + "Chưa bắt đầu").
- Commit: `chore(bootstrap): plugin routers/nodes/nav/i18n + cross-session contracts`.
- **Cuối cùng, sau khi commit thành công**, tạo file `ai/plans/2026-11-roadmap/status/BOOTSTRAP_DONE` (nội dung: ngày giờ + hash commit). Session B và C đang chờ file này mới được bắt đầu.

Báo cáo cuối: danh sách file tạo/sửa, kết quả test, các gói không cài được.
