# CONTRACTS — Luật chung cho 3 session song song (ĐỌC TRƯỚC MỌI PROMPT)

## 0. Luật vàng
1. **Chỉ sửa file trong vùng sở hữu của session mình.** Cần thay đổi file vùng khác → ghi yêu cầu vào `ai/plans/2026-11-roadmap/status/REQUESTS.md` (append 1 dòng, có tên session + ngày), KHÔNG tự sửa.
2. **Không sửa các file chung** sau khi 00_BOOTSTRAP đã xong: `tool/pyproject.toml`, `tool/dashboard/package.json`, `tool/src/socnhotv/core/api/app.py`, `tool/src/socnhotv/core/nodes/registry.py`, `tool/dashboard/messages/{vi,en}.json`, `tool/dashboard/i18n/request.ts`, `tool/dashboard/store/index.ts`, file nav chính, `ai/memory/CONTINUITY.md`, `CLAUDE.md`, `AGENTS.md`.
   Thiếu dependency → ghi vào `REQUESTS.md`, tạm dùng thư viện có sẵn hoặc `try: import … except ImportError` có fallback.
3. **Không tắt/khởi động lại** server cổng 3000 (Next dev) và 8000 (uvicorn). Test backend bằng `pytest` + `fastapi.testclient`. Nếu cần server riêng: A dùng 8101, B dùng 8102, C dùng 8103.
4. **Commit theo đường dẫn:** `git add <đường dẫn vùng mình>` → `git commit -m "feat(<A|B|C>): …"`. Không `git add -A`, không `git stash`, không `git reset`, không `git checkout -- .`, không rebase. Gặp `index.lock` → đợi 3–5s thử lại.
5. **Kiểm tra TypeScript chỉ theo file của mình:** `cd tool/dashboard && npx tsc --noEmit 2>&1 | grep -E "<thư mục của mình>"` — lỗi ở vùng khác không phải việc của mình.
6. Mỗi prompt kết thúc bằng việc cập nhật `ai/plans/2026-11-roadmap/status/<A|B|C>.md` (chỉ file của mình): đã làm gì, file nào, test nào pass, còn nợ gì.
7. Luật dự án vẫn áp dụng: Morphicons (`@/components/ui/icons`, `MorphIcon`), không `lucide-react`; HyperFrames là công cụ dựng mặc định; voice `soc-nho`; Bi 100cm / Koala 150cm; UI gọn, nút thêm = thẻ nét đứt cạnh thẻ cuối; cùng thực thể = chung component, bấm vào phải tới đúng mục.
8. Code mới bằng Python 3.12 typed (pydantic v2) + TypeScript strict. Mọi đường dẫn dữ liệu qua `socnhotv.workspace` (`project_path(project_id, ...)`, `shared_path(...)`), không hardcode `data/projects/...`.

## 1. Vùng sở hữu

| Session | Backend | Frontend | Data |
|---|---|---|---|
| **A — Video** | `tool/src/socnhotv/video/**`, `core/adapters/hyperframes_adapter.py`, `core/api/routes/video.py`, `core/nodes/plugins/video.py`, `tool/tests/test_video_*.py` | `app/[locale]/templates/**`, `app/[locale]/renders/**`, `components/templates/**`, `components/renders/**`, `components/navigation/nav-modules/video.ts`, `messages/modules/video.{vi,en}.json`, `store/modules/video.ts` | `data/shared/templates/**`, `data/projects/*/output/**`, `data/projects/*/runs/render_queue/**` |
| **B — Sources & Intel** | `tool/src/socnhotv/sources/**`, `tool/src/socnhotv/intelligence/**`, `core/api/routes/sources.py`, `core/api/routes/intel.py`, `core/nodes/plugins/sources.py`, `tool/tests/test_sources_*.py`, `tool/tests/test_intel_*.py` | `app/[locale]/sources/**`, `app/[locale]/intel/**`, `app/[locale]/products/**`, `components/sources/**`, `components/intel/**`, `components/products/**`, `nav-modules/sources.ts`, `messages/modules/sources.{vi,en}.json`, `store/modules/sources.ts` | `data/projects/*/raw/**`, `products/**`, `knowledge/**`, `content/ideas/**`, `content/blueprints/**`, `content/scripts/**`, `content/strategy.json` |
| **C — Social** | `tool/src/socnhotv/social/**`, `core/api/routes/social.py`, `core/nodes/plugins/social.py`, `tool/tests/test_social_*.py` | `app/[locale]/social/**`, `app/[locale]/publish/page.tsx`, `components/social/**`, `components/studio/tabs/PublishTab.tsx`, `nav-modules/social.ts`, `messages/modules/social.{vi,en}.json`, `store/modules/social.ts` | `data/projects/*/publishing/**`, `accounts/**`, `analytics/**` |

| **D — Research (độc lập, chỉ đọc code)** | không sửa code | không sửa UI | `data/shared/knowledge/video_craft/**`, `status/D.md` (xem `session-D-research/D0_video_research_analyst.md`). A/B/C được ĐỌC kho này (playbooks, technique cards, requests_for_X.md). |

`core/api/routes/`, `core/nodes/plugins/`, `nav-modules/`, `messages/modules/`, `store/modules/` là các thư mục plugin do 00_BOOTSTRAP tạo, tự nạp mọi file bên trong.

## 2. Hợp đồng giữa các session (tạo sẵn ở 00_BOOTSTRAP)

### 2.1 `socnhotv.video.contracts` (A sở hữu, B & C gọi)
```python
Platform = Literal["tiktok","reels","shorts","youtube","facebook","douyin"]
class RenderRequest(BaseModel):
    project_id: str
    template_id: str               # vd "tiktok-sales-v1"
    platforms: list[Platform]      # render 1 nội dung ra nhiều nền tảng
    data: dict                     # slot của template (text, ảnh, clip, sản phẩm…)
    voice: VoiceSpec | None        # {voice_id:"soc-nho", script:str} hoặc {audio_path:str}
    source_ref: str | None = None  # id nguồn (B) để truy vết bản quyền
    output_name: str
class RenderJob(BaseModel):
    job_id: str; status: Literal["queued","rendering","done","failed"]
    outputs: dict[Platform, str]   # đường dẫn mp4 tương đối project
    error: str | None = None
def submit_render(req: RenderRequest) -> RenderJob      # stub: ghi JSON vào runs/render_queue/
def get_render(project_id: str, job_id: str) -> RenderJob
def list_templates() -> list[TemplateMeta]
```

### 2.2 `socnhotv.intelligence.contracts` (B sở hữu, A & C đọc)
```python
class VideoBlueprint(BaseModel):   # cấu trúc 1 video mẫu
    id: str; source_ref: str; duration_s: float; platform: str
    hook: str; beats: list[Beat]    # Beat{t_start,t_end,role:"hook|problem|demo|proof|cta|…",summary,visual,on_screen_text}
    cta: str; pacing_cuts_per_10s: float; suggested_template_id: str | None
class ChannelBlueprint(BaseModel): # cấu trúc 1 kênh
    id: str; channel_url: str; niche: str; pillars: list[str]
    title_patterns: list[str]; avg_duration_s: float; upload_cadence: str
    top_videos: list[dict]; best_hooks: list[str]
class ContentIdea(BaseModel):      # ý tưởng → C đưa lên lịch
    id: str; project_id: str; title: str; platform_targets: list[str]
    template_id: str | None; blueprint_ref: str | None; priority: int
    status: Literal["new","scripted","rendered","scheduled","dropped"]
```
Lưu tại `content/blueprints/*.json`, `content/ideas/*.json`.

### 2.3 `socnhotv.social.contracts` (C sở hữu, A & B gọi)
```python
def create_draft_post(project_id: str, media_path: str, title: str, caption: str,
                      platforms: list[str], source_ref: str | None = None,
                      render_job_id: str | None = None) -> str   # trả post_id
```
Stub: ghi `publishing/inbox/<id>.json`. C1 thay bằng implement thật nhưng **giữ nguyên chữ ký**.

### 2.4 Sự kiện (không bắt buộc)
File-based: `data/projects/<id>/runs/events/*.jsonl` với `{ts, source:"A|B|C", type, payload}`.

## 3. Bản quyền & an toàn (bắt buộc cho B và C)
- Mọi nguồn tải về có trường `rights: "owned" | "licensed" | "permission" | "reference_only"` và `source_url`, `author`. Mặc định `reference_only`.
- `reference_only` chỉ được dùng để **học cấu trúc** (blueprint, transcript, nhịp) — **không** đưa clip gốc vào render. Muốn dùng clip gốc trong video → phải đổi rights khác `reference_only` (người dùng tự xác nhận trên UI).
- Không viết code né Content-ID/nhận diện trùng lặp (lật hình, tăng tốc, đổi màu nhằm qua mặt hệ thống). Biến đổi được phép là biến đổi sáng tạo: dịch, lồng tiếng, dựng lại bằng template, thêm bình luận/nhân vật.
- Đăng bài ưu tiên **API chính thức** (YouTube Data API, TikTok Content Posting API, Meta Graph). Không lưu mật khẩu; chỉ OAuth token trong `key_vault`. Mặc định `manualApprovalRequired = true`.
