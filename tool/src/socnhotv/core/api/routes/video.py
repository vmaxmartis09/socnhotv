"""Video API routes plugin.

Prefix: /video (hoặc lồng sau /projects/{project_id}/video khi mở rộng).
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/video", tags=["video"])


@router.get("/_ping")
async def ping_video():
    return {"status": "ok", "module": "video"}
