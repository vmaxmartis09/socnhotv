"""Video API routes plugin.

Cung cấp các endpoint:
- GET /video/_ping
- GET /video/platforms
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
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from sse_starlette.sse import EventSourceResponse

from socnhotv.video.contracts import RenderJob, RenderRequest
from socnhotv.video.platforms import PlatformPreset, list_platforms
from socnhotv.video.queue import get_render_queue

logger = logging.getLogger("socnhotv.routes.video")

router = APIRouter(tags=["video"])


@router.get("/video/_ping")
async def ping_video():
    return {"status": "ok", "module": "video"}


@router.get("/video/platforms", response_model=List[PlatformPreset])
async def get_platforms():
    """Trả về danh sách tất cả các preset nền tảng video hỗ trợ."""
    return list_platforms()


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
