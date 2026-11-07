# PROMPT SETUP ĐẦY ĐỦ — SocNhoTV (máy mới)

Dán nguyên khối prompt dưới đây cho Claude Code (hoặc agent AI) chạy ở thư mục gốc repo trên máy mới. Agent sẽ tự cài đặt, kiểm tra và báo cáo.

---

```text
Bạn đang setup project SocNhoTV trên máy mới. Thư mục làm việc là root repo (có ai/, tool/, data/, integrations/). Làm tuần tự, sau mỗi bước kiểm tra kết quả; lỗi thì thử cách khác (tối thiểu 3 cách) trước khi báo lại. Không bỏ qua bước nào, không xoá dữ liệu có sẵn.

BƯỚC 0 — Chuẩn bị công cụ hệ thống
- Cần: git, git-lfs, uv (Python), Python 3.12 (pyproject yêu cầu >=3.10,<3.13), Node.js >=20 + npm, ffmpeg (tuỳ chọn, có imageio-ffmpeg).
- macOS: brew install git git-lfs uv node ffmpeg. Windows: winget install Git.Git GitHub.GitHub-LFS astral-sh.uv OpenJS.NodeJS.LTS (hoặc dùng setup.ps1 có sẵn).
- Chạy: git lfs install

BƯỚC 1 — Lấy code và data
- git clone https://github.com/vmaxmartis09/socnhotv.git (hoặc git pull nếu đã có), rồi: git lfs pull
  -> Phải tải đủ các file .mp4 và thư viện .dylib/.node/.so (LFS). Kiểm tra: git lfs ls-files | wc -l khớp số file LFS.
- Repo KHÔNG chứa integrations/OmniVoice (nó là repo upstream riêng). Clone lại:
  git clone https://github.com/k2-fsa/OmniVoice integrations/OmniVoice
  Sau đó cài theo README của OmniVoice (uv sync trong thư mục đó).

BƯỚC 2 — Python backend
- Tạo môi trường tại root: uv venv .venv --python 3.12 && uv sync (dùng uv.lock). Nếu uv.lock lệch, dùng uv pip install -e . trong .venv.
- Kiểm tra: .venv/bin/python -c "import fastapi, torch, faster_whisper; print('ok')" (Windows: .venv\Scripts\python).
- tool/ có .venv riêng: cd tool && uv sync (dùng tool/uv.lock). Các toolbox con (tool/toolbox/tools/*/) có .venv riêng: với mỗi thư mục có pyproject.toml hoặc uv.lock, chạy uv sync trong thư mục đó.
- Lưu ý: .venv được commit trong repo nhưng chứa đường dẫn tuyệt đối của máy cũ; nếu python không chạy được thì xoá .venv và tạo lại như trên.

BƯỚC 3 — Dashboard (Next.js)
- cd tool/dashboard && npm ci (dùng package-lock.json). Nếu node_modules đã có mà lỗi binary (@next/swc), xoá node_modules rồi npm ci lại.
- Kiểm tra build: NEXT_DIST_DIR=.next-build npx next build  (KHÔNG build vào .next khi dev server cổng 3000 đang chạy).

BƯỚC 4 — Khoá bí mật (.env)
- Tạo/đối chiếu file .env ở root với các khoá: GEMINI_API_KEY, SOCNHOTV_SPEND_CAP_USD. Nếu chưa có, hỏi người dùng nhập giá trị THẬT; KHÔNG tự điền khoá giả, KHÔNG in khoá ra chat.
- Khoá đã lộ trong lịch sử git công khai nếu repo public: khuyến nghị người dùng rotate khoá cũ.

BƯỚC 5 — Kiểm tra dữ liệu đã đủ
- data/workspace.json tồn tại; project active mặc định: soc-nho-tv.
- data/shared/: voice_vault/, models/, knowledge/, templates/, music_sfx/, brand_kits/ có dữ liệu.
- data/projects/<id>/ có đủ: characters/, content/, products/, publishing/, analytics/, output/, shots/, raw/, accounts/, runs/, assets/ (kể cả các file .mp4 sau git lfs pull).
- Chạy: git status — phải sạch (hoặc chỉ có thay đổi của người dùng). Không có file nào bị ignore: .gitignore đã được bỏ hết quy tắc loại trừ.

BƯỚC 6 — Chạy và kiểm tra
- Backend: python -m socnhotv --project soc-nho-tv --help (kiểm tra CLI hoạt động).
- Dashboard dev: cd tool/dashboard && npm run dev:web, mở http://localhost:3000.
- Báo cáo: danh sách bước đã pass, bước fail kèm lỗi nguyên văn, và việc người dùng còn phải làm (nhập .env, rotate khoá, clone OmniVoice nếu chưa).

Quy tắc: không đẩy .env hay khoá lên git. Không sửa file dữ liệu khi chỉ setup.
```

---

## Ghi chú cho người dùng
- Anti-gate đã bị xoá khỏi `data/projects/`.
- `.gitignore` đã được làm trống (không loại trừ file nào).
- File >90MB được đưa qua Git LFS (`.gitattributes`).
