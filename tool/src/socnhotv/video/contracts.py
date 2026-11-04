from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from socnhotv.workspace import project_path, shared_path

Platform = Literal["tiktok", "reels", "shorts", "youtube", "facebook", "douyin"]


class VoiceSpec(BaseModel):
    voice_id: Optional[str] = None
    script: Optional[str] = None
    audio_path: Optional[str] = None


class TemplateMeta(BaseModel):
    id: str
    name: str
    description: str = ""
    platforms: List[Platform] = Field(default_factory=list)
    slots: List[Dict[str, Any]] = Field(default_factory=list)
    version: str = "1.0.0"


class RenderRequest(BaseModel):
    project_id: str
    template_id: str
    platforms: List[Platform]
    data: Dict[str, Any]
    voice: Optional[VoiceSpec] = None
    source_ref: Optional[str] = None
    output_name: str


class RenderJob(BaseModel):
    job_id: str
    project_id: str = ""
    status: Literal["queued", "rendering", "done", "failed"] = "queued"
    outputs: Dict[Platform, str] = Field(default_factory=dict)
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def submit_render(req: RenderRequest) -> RenderJob:
    """Submit render job to RenderQueue."""
    from socnhotv.video.queue import get_render_queue
    return get_render_queue().submit(req)


def get_render(project_id: str, job_id: str) -> RenderJob:
    """Read render job from RenderQueue."""
    from socnhotv.video.queue import get_render_queue
    return get_render_queue().get(project_id, job_id)


def list_templates() -> List[TemplateMeta]:
    """Scan data/shared/templates/*/template.json via template loader."""
    from socnhotv.video.templates.loader import list_templates as _loader_list_templates
    templates = _loader_list_templates()
    res: List[TemplateMeta] = []
    for t in templates:
        res.append(TemplateMeta(
            id=t.id,
            name=t.name,
            description=getattr(t, "description", "") or t.name,
            platforms=t.platforms,
            slots=[s.model_dump() for s in t.slots],
            version=str(t.version),
        ))
    return res
