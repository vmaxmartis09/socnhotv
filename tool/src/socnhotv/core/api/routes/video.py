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
from sse_starlette.sse import EventSourceResponse

from socnhotv.video.contracts import RenderJob, RenderRequest
from socnhotv.video.platforms import PlatformPreset, list_platforms
from socnhotv.video.queue import get_render_queue
from socnhotv.video.templates.loader import get_template, get_template_dir, list_templates
from socnhotv.video.templates.preview import generate_template_preview
from socnhotv.video.templates.schema import TemplateMeta, validate_template_data

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
