"""Video API routes plugin.

Cung cấp các endpoint:
- GET /video/_ping
- GET /video/platforms
- GET /video/templates?category=&platform=
- GET /video/templates/{tid}
- POST /video/templates/{tid}/validate
- POST /video/templates/{tid}/preview
- GET /video/templates/{tid}/preview.mp4
- GET /video/templates/{tid}/preview.jpg
- POST /projects/{pid}/video/render
- GET /projects/{pid}/video/render/{job_id}
- GET /projects/{pid}/video/renders?status=
- POST /projects/{pid}/video/render/{job_id}/cancel
- GET /projects/{pid}/video/render/{job_id}/events (SSE)
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from socnhotv.video.contracts import RenderJob, RenderRequest
from socnhotv.video.episode.assets import estimate_episode_cost, generate_scene_assets
from socnhotv.video.episode.assemble import assemble_episode
from socnhotv.video.episode.planner import EpisodePlan, ScenePlan, plan_episode
from socnhotv.video.episode.shorts import extract_and_assemble_shorts
from socnhotv.video.episode.voice import synthesize_episode_voice
from socnhotv.video.platforms import PlatformPreset, list_platforms
from socnhotv.video.queue import get_render_queue
from socnhotv.video.templates.loader import get_template, get_template_dir, list_templates
from socnhotv.video.templates.preview import generate_template_preview
from socnhotv.video.templates.schema import TemplateMeta, validate_template_data
from socnhotv.workspace.paths import project_path

logger = logging.getLogger("socnhotv.routes.video")

router = APIRouter(tags=["video"])


@router.get("/video/_ping")
async def ping_video():
    return {"status": "ok", "module": "video"}


@router.get("/video/platforms", response_model=List[PlatformPreset])
async def get_platforms():
    """Trả về danh sách tất cả các preset nền tảng video hỗ trợ."""
    return list_platforms()


# --- TEMPLATES API ---


@router.get("/video/templates", response_model=List[TemplateMeta])
async def get_templates(
    category: Optional[str] = Query(None, description="Lọc theo category: sales, review, reup, animation..."),
    platform: Optional[str] = Query(None, description="Lọc theo nền tảng: tiktok, reels, youtube..."),
):
    """Danh sách các video templates trong hệ thống."""
    return list_templates(category=category, platform=platform)


@router.get("/video/templates/{tid}", response_model=TemplateMeta)
async def get_template_detail(tid: str):
    """Chi tiết metadata và các slots của template."""
    try:
        return get_template(tid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Template '{tid}' không tồn tại")


@router.post("/video/templates/{tid}/validate")
async def validate_template_input(tid: str, data: Dict[str, Any]):
    """Kiểm tra dữ liệu slot người dùng cung cấp cho template."""
    try:
        template = get_template(tid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Template '{tid}' không tồn tại")

    errors = validate_template_data(template, data)
    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


@router.post("/video/templates/{tid}/preview")
async def render_template_preview(tid: str):
    """Render preview nhanh 540p cho template từ sample.data.json."""
    try:
        get_template(tid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Template '{tid}' không tồn tại")

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: generate_template_preview(tid))
        return {
            "status": "ok",
            "preview_mp4": f"/video/templates/{tid}/preview.mp4",
            "preview_jpg": f"/video/templates/{tid}/preview.jpg",
        }
    except Exception as e:
        logger.error(f"Render preview template {tid} thất bại: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/video/templates/{tid}/preview.mp4")
async def get_template_preview_mp4(tid: str):
    """Tải hoặc xem preview video MP4 của template."""
    try:
        t_dir = get_template_dir(tid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Template '{tid}' không tồn tại")

    video_file = t_dir / "preview.mp4"
    if not video_file.exists():
        # Tự sinh nếu chưa có
        try:
            generate_template_preview(tid)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Chưa có preview.mp4: {e}")

    return FileResponse(video_file, media_type="video/mp4")


@router.get("/video/templates/{tid}/preview.jpg")
async def get_template_preview_jpg(tid: str):
    """Xem thumbnail JPEG preview của template."""
    try:
        t_dir = get_template_dir(tid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Template '{tid}' không tồn tại")

    jpg_file = t_dir / "preview.jpg"
    if not jpg_file.exists():
        # Tự sinh nếu chưa có
        try:
            generate_template_preview(tid)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Chưa có preview.jpg: {e}")

    return FileResponse(jpg_file, media_type="image/jpeg")


# --- RENDERS QUEUE API ---


@router.post("/projects/{pid}/video/render", response_model=RenderJob)
async def submit_video_render(pid: str, req: RenderRequest):
    """Đưa yêu cầu render video vào hàng đợi."""
    req.project_id = pid
    queue = get_render_queue()
    job = queue.submit(req)
    return job


@router.get("/projects/{pid}/video/render/{job_id}", response_model=RenderJob)
async def get_video_render(pid: str, job_id: str):
    """Lấy thông tin và trạng thái của render job."""
    queue = get_render_queue()
    try:
        return queue.get(pid, job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Job {job_id} không tồn tại")


@router.get("/projects/{pid}/video/renders", response_model=List[RenderJob])
async def list_video_renders(
    pid: str,
    status: Optional[str] = Query(None, description="Lọc theo trạng thái: queued, rendering, done, failed"),
):
    """Danh sách các render job trong project."""
    queue = get_render_queue()
    return queue.list_jobs(pid, status=status)


@router.post("/projects/{pid}/video/render/{job_id}/cancel", response_model=RenderJob)
async def cancel_video_render(pid: str, job_id: str):
    """Huỷ tiến trình render job đang xếp hàng hoặc đang xử lý."""
    queue = get_render_queue()
    try:
        return queue.cancel(pid, job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Job {job_id} không tồn tại")


@router.get("/projects/{pid}/video/render/{job_id}/events")
async def stream_render_events(request: Request, pid: str, job_id: str):
    """SSE endpoint phát trực tiếp sự kiện và tiến độ render job."""
    queue = get_render_queue()

    async def event_generator() -> AsyncGenerator[Dict[str, str], None]:
        last_status = None
        while True:
            if await request.is_disconnected():
                break

            try:
                job = queue.get(pid, job_id)
                current_data = job.model_dump_json()

                if job.status != last_status or True:
                    last_status = job.status
                    yield {
                        "event": "progress",
                        "data": current_data,
                    }

                if job.status in ("done", "failed"):
                    yield {
                        "event": "completed",
                        "data": current_data,
                    }
                    break
            except FileNotFoundError:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": f"Job {job_id} not found"}),
                }
                break

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


# --- EPISODE PIPELINE API ---


class EpisodePlanRequest(BaseModel):
    script: str
    title: Optional[str] = "Hoạt hình Sóc Nhỏ Bi & Bạn Koala"


class EpisodeBuildRequest(BaseModel):
    use_mock: bool = False


@router.post("/projects/{pid}/video/episodes/{eid}/plan", response_model=EpisodePlan)
async def plan_video_episode(pid: str, eid: str, req: EpisodePlanRequest):
    """Lập kế hoạch phân cảnh (ScenePlan) và ước tính chi phí cho tập phim."""
    plan = plan_episode(req.script, episode_id=eid, title=req.title or "Hoạt hình Sóc Nhỏ Bi & Bạn Koala")
    cost_info = estimate_episode_cost(plan.scenes)
    plan.estimated_cost_usd = cost_info["total_estimated_usd"]

    plan_file = project_path(pid, "output", eid, "plan.json")
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    plan_file.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    return plan


@router.post("/projects/{pid}/video/episodes/{eid}/build")
async def build_video_episode(pid: str, eid: str, req: Optional[EpisodeBuildRequest] = None):
    """Thực thi pipeline sản xuất tập phim YouTube 16:9 và 3 video Shorts 9:16."""
    use_mock = req.use_mock if req is not None else False

    plan_file = project_path(pid, "output", eid, "plan.json")
    if not plan_file.exists():
        default_script = (
            "Cảnh 1: Phòng khám Bác sĩ Koala\n"
            "Bi: Bác sĩ Koala ơi, răng của em bị sâu đau quá!\n"
            "Koala: Để bác xem nào, em ăn nhiều kẹo ngọt mà quên đánh răng đúng không?\n"
            "Cảnh 2: Hướng dẫn chăm sóc răng miệng\n"
            "Koala: Mỗi ngày em phải đánh răng 2 lần, sáng và tối nhé!\n"
            "Bi: Dạ, em nhớ rồi ạ, em sẽ chăm chỉ đánh răng!\n"
            "Cảnh 3: Kết thúc vui vẻ\n"
            "Bi: Răng em hết đau rồi, cảm ơn Bác sĩ Koala!\n"
            "Koala: Chúc Bi luôn vui khỏe và có nụ cười thật tươi!"
        )
        plan = plan_episode(default_script, episode_id=eid, title="Sóc Nhỏ và Chiếc Răng Sâu")
        cost_info = estimate_episode_cost(plan.scenes)
        plan.estimated_cost_usd = cost_info["total_estimated_usd"]
        plan_file.parent.mkdir(parents=True, exist_ok=True)
        plan_file.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    else:
        with open(plan_file, "r", encoding="utf-8") as f:
            plan = EpisodePlan.model_validate_json(f.read())

    # 1. Sinh assets keyframe
    scene_assets = generate_scene_assets(pid, eid, plan.scenes, use_mock=use_mock)

    # 2. Tổng hợp voiceover đa nhân vật & mastering
    voice_path, _ = await synthesize_episode_voice(pid, eid, plan.scenes, use_mock=use_mock)

    # 3. Dựng RenderRequest cho tập YouTube 16:9
    main_req = assemble_episode(pid, eid, plan.title, plan.scenes, scene_assets, voice_path)

    # 4. Trích xuất 3 Shorts 9:16
    shorts_reqs = extract_and_assemble_shorts(pid, eid, plan.scenes, scene_assets, voice_path)

    # 5. Gửi vào hàng đợi RenderQueue
    queue = get_render_queue()
    main_job = queue.submit(main_req)
    shorts_jobs = [queue.submit(sr) for sr in shorts_reqs]

    build_status = {
        "episode_id": eid,
        "title": plan.title,
        "main_job_id": main_job.job_id,
        "shorts_job_ids": [j.job_id for j in shorts_jobs],
        "status": "queued",
        "scenes_count": len(plan.scenes),
        "estimated_cost_usd": plan.estimated_cost_usd,
    }
    status_file = project_path(pid, "output", eid, "build_status.json")
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text(json.dumps(build_status, indent=2, ensure_ascii=False), encoding="utf-8")

    return build_status


@router.get("/projects/{pid}/video/episodes/{eid}/status")
async def get_video_episode_status(pid: str, eid: str):
    """Tra cứu trạng thái sản xuất tập phim và các video shorts phái sinh."""
    status_file = project_path(pid, "output", eid, "build_status.json")
    plan_file = project_path(pid, "output", eid, "plan.json")

    if not status_file.exists():
        if plan_file.exists():
            with open(plan_file, "r", encoding="utf-8") as f:
                plan_data = json.load(f)
            return {
                "episode_id": eid,
                "status": "planned",
                "plan": plan_data,
            }
        raise HTTPException(status_code=404, detail=f"Tập phim {eid} chưa được lập kế hoạch hoặc sản xuất")

    with open(status_file, "r", encoding="utf-8") as f:
        build_status = json.load(f)

    queue = get_render_queue()
    main_job = None
    try:
        main_job = queue.get(pid, build_status["main_job_id"])
    except FileNotFoundError:
        pass

    shorts_jobs = []
    for s_id in build_status.get("shorts_job_ids", []):
        try:
            shorts_jobs.append(queue.get(pid, s_id))
        except FileNotFoundError:
            pass

    all_jobs = ([main_job] if main_job else []) + shorts_jobs
    all_statuses = [j.status for j in all_jobs if j]
    if not all_statuses:
        aggregate_status = build_status.get("status", "unknown")
    elif all(s == "done" for s in all_statuses):
        aggregate_status = "done"
    elif any(s == "failed" for s in all_statuses):
        aggregate_status = "failed"
    elif any(s == "rendering" for s in all_statuses):
        aggregate_status = "rendering"
    else:
        aggregate_status = "queued"

    build_status["status"] = aggregate_status
    build_status["main_job"] = main_job.model_dump() if main_job else None
    build_status["shorts_jobs"] = [j.model_dump() for j in shorts_jobs]

    ep_dir = project_path(pid, "output", eid)
    chapters_file = ep_dir / "chapters.txt"
    meta_file = ep_dir / "youtube_meta.json"
    if chapters_file.exists():
        build_status["chapters"] = chapters_file.read_text(encoding="utf-8")
    if meta_file.exists():
        try:
            build_status["youtube_meta"] = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    return build_status


# --- CRAFT TOOLKIT API (SESSION K) ---

class CraftHooksRequest(BaseModel):
    topic: str
    character: str = "soc-nho"


class CraftLintRequest(BaseModel):
    script: str
    duration_sec: Optional[float] = None
    platform: str = "tiktok"


@router.post("/video/craft/hooks")
async def generate_craft_hooks(req: CraftHooksRequest):
    """Sinh 3 biến thể Hook A/B/C và chấm điểm theo heuristic rules (Session K)."""
    from socnhotv.video.craft.hooks import generate_hook_variants
    res = generate_hook_variants(topic=req.topic, character=req.character)
    return {
        "topic": res.topic,
        "best_variant_id": res.best_variant_id,
        "selected_hook": res.selected_hook,
        "variants": [
            {
                "variant_id": v.variant_id,
                "archetype": v.archetype,
                "text": v.text,
                "reasoning": v.reasoning,
                "score": {
                    "total_score": v.score.total_score,
                    "word_count": v.score.word_count,
                    "estimated_duration_sec": v.score.estimated_duration_sec,
                    "has_greeting_penalty": v.score.has_greeting_penalty,
                    "penalties": v.score.penalties,
                    "bonuses": v.score.bonuses,
                }
            }
            for v in res.variants
        ]
    }


@router.post("/video/craft/lint")
async def lint_craft_script(req: CraftLintRequest):
    """Creative QA / Lint kịch bản video trước khi render (Session K)."""
    from socnhotv.video.craft.lint import lint_script
    report = lint_script(script_text=req.script, duration_sec=req.duration_sec, platform=req.platform)
    return {
        "passed": report.passed,
        "total_checks": report.total_checks,
        "error_count": report.error_count,
        "warning_count": report.warning_count,
        "info_count": report.info_count,
        "issues": [
            {
                "level": i.level,
                "rule_id": i.rule_id,
                "message_vi": i.message_vi,
                "technique_ref": i.technique_ref,
                "suggestion_vi": i.suggestion_vi,
            }
            for i in report.issues
        ]
    }


