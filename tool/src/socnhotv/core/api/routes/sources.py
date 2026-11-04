"""Sources API routes plugin.

Prefix: /sources (hoặc lồng sau /projects/{project_id}/sources khi mở rộng).
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/_ping")
async def ping_sources():
    return {"status": "ok", "module": "sources"}
