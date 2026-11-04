"""Intelligence API routes plugin.

Prefix: /intel (hoặc lồng sau /projects/{project_id}/intel khi mở rộng).
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/intel", tags=["intel"])


@router.get("/_ping")
async def ping_intel():
    return {"status": "ok", "module": "intel"}
