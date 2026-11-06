# Hợp đồng giữa 2 session độc lập E3 (Node nhập liệu) và E2 (Vỏ ứng dụng gọn)

Hai session chạy SONG SONG, không chờ nhau. Chúng gặp nhau ở đúng 1 chỗ: **tham số node trong đồ thị**. File này cố định tên tham số để E2 sinh preset đồ thị mà không cần đọc code E3.

## 1. Tham số node (E3 hiện thực trong UI + runner; E2 chỉ ghi các giá trị này vào đồ thị)
| node | params |
|---|---|
| `text` | `{ content: string }` |
| `image`, `character_image`, `scene` | `{ uri: string, name?: string }` — `uri` là đường dẫn tương đối project do `POST /projects/{pid}/library/upload` trả về (ví dụ `assets/<sha256>.png`); rỗng = chưa có ảnh |
| `script` | `{ mode: "ai" \| "paste" \| "episode", rawScript: string, targetSceneCount: number, targetDurationSec: number, episodeId?: string, granularity?: "shot" \| "scene" }` — `mode:"paste"` dùng `rawScript` (không gọi LLM); `mode:"episode"` (E4, 2026-11-06) đọc `content/episodes/<episodeId>/KICH*.md`, `granularity` mặc định `"shot"` (mỗi shot 1 cảnh) hoặc `"scene"` (gộp shot theo cảnh); mỗi cảnh có `characters`, `speaker`, `dialogue`, `imagePrompt` |
| `voice_tts` | `{ text?: string, voiceId: string }` — `text` chỉ dùng khi cổng `text` chưa nối dây |
| `image_gen`, `image_edit`, `video_gen` | `{ prompt: string, referenceImages?: string[], model, aspectRatio }` — `image_gen` (E4): nối cổng vào `scenes` = **lặp theo cảnh** (mỗi cảnh 1 ảnh, prompt lấy `imagePrompt` của cảnh, `params.prompt` thành hậu tố chung; ảnh tham chiếu lọc theo nhân vật có mặt), cổng ra `scenes` = danh sách cảnh đã gắn `image`/`imageUri` để nối thẳng vào `hyperframes_render.scenes` |
| `captions` | `{ language: "vi", style: string }` |
| `hyperframes_render` | giữ nguyên params hiện có; thêm `{ templateId?: string, platform?: string }` |
| `export` | `{ platforms: string[], outputFileName: string }` |
Tên cổng (port) lấy từ `GET /node-types`, KHÔNG hardcode ở E2.
Cổng kiểu `image[]` và `scenes` nhận **nhiều dây** (gộp theo thứ tự dây); các cổng khác vẫn "dây sau thắng".

## 2. Cách E2 áp preset vào Studio
Chỉ dùng action có sẵn `setNodesAndEdges(nodes, edges)` và `createEpisode(title)` của `store/slices/canvasSlice.ts` (file do E3 sở hữu — E2 không sửa). Code preset ở file mới `lib/graph-presets.ts` và store mới `store/modules/create.ts` (E2 sở hữu).

## 3. Phân vùng file (không được đụng vùng của session kia)
| | **E3 — Node nhập liệu** | **E2 — Vỏ ứng dụng gọn** |
|---|---|---|
| Frontend | `components/canvas/**` (StudioCanvas, StudioNode, NodeBody, …), `components/studio/tabs/NodeTab.tsx`, `store/slices/canvasSlice.ts`, `lib/core-api.ts`, `lib/api/nodes.ts` (mới), `messages/modules/nodes.{vi,en}.json` (mới), `i18n/request.ts` (chỉ E3 được sửa) | `components/navigation/**` (PageBar, nav-modules), `app/[locale]/**` (xoá/redirect trang), `components/{templates,renders,sources,products,intel}/**`, `components/studio/RightPanel.tsx`, `components/studio/PreviewPane.tsx`, `components/studio/tabs/JobsCostTab.tsx` (⚠ `components/social/**` và `PublishTab.tsx` thuộc **session S**, xem `../session-S-social-manager/S1_social_manager.md`), `components/create/**` (mới: panel Tạo video), `lib/graph-presets.ts`, `store/modules/create.ts`, `messages/modules/studio.{vi,en}.json` (mới) |
| `components/canvas/StudioStickToolbar.tsx` | E2 được thêm DUY NHẤT nút "Tạo video" (1 import + 1 nút), E3 không đụng file này | |
| Backend | `core/engine/{graph_runner,validator,script_parser}.py`, `core/nodes/registry.py`, providers (chỉ phần ảnh tham chiếu), `tool/tests/test_script_parser.py`, `test_graph_inputs.py` | không sửa backend (chỉ đọc API) |
| Dữ liệu | — | `git mv` dữ liệu analytics mẫu → `_demo/` |
| Status | `status/E3.md` | `status/E2.md` |

`i18n/request.ts`: **E3 làm việc đầu tiên (trong 10 phút đầu, commit riêng)**: viết lại loader tổng quát nạp thêm `nodes.*` và `studio.*` (try/catch, rỗng nếu chưa có file). E2 chỉ tạo `studio.{vi,en}.json`, không sửa `request.ts`; trong lúc chờ E3 đổi loader, E2 cứ viết nhãn, test i18n sau.

## 4. Điểm gặp nhau & cách không phải chờ
- E2 xây Tạo video, Jobs, Đăng, cắt trang mà không cần E3 xong. Preset đồ thị chỉ ghi params theo bảng mục 1.
- Việc cuối của E2 (nghiệm thu "tạo video ra mp4 thật" bằng `mode:"paste"`) cần runner của E3: E2 kiểm `status/E3.md` có dòng `RUNNER_PASTE_DONE`; chưa có thì chạy thử bằng `mode:"ai"` với provider mock, ghi rõ "chưa kiểm paste" vào `status/E2.md`, rồi quay lại kiểm khi có dòng đó — không đứng chờ.
- Core API cổng 8000 đang chạy bản cũ (`/video/templates` 404). Kiểm `ps aux | grep uvicorn` xem có `--reload` chưa; nếu chưa: `mkdir ai/plans/2026-11-roadmap/status/.core-restart.lock` — ai thắng mkdir thì tắt và chạy lại `cd tool && .venv/bin/python -m uvicorn socnhotv.core.api.app:app --app-dir src --host 127.0.0.1 --port 8000 --reload`, người còn lại không đụng. Không ai được tắt cổng 3000.
- Git: chỉ `git add <đường dẫn vùng mình>`, không `git add -A`/stash/reset/checkout/rebase (còn session D ghi `data/shared/knowledge/video_craft`). Gặp `index.lock` đợi 5 giây thử lại.
