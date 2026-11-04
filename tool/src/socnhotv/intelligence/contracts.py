from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from socnhotv.workspace import project_path


class Beat(BaseModel):
    t_start: float
    t_end: float
    role: str  # "hook|problem|demo|proof|cta|..."
    summary: str
    visual: str = ""
    on_screen_text: str = ""


class VideoBlueprint(BaseModel):
    id: str
    source_ref: str
    duration_s: float
    platform: str
    hook: str
    beats: List[Beat] = Field(default_factory=list)
    cta: str
    pacing_cuts_per_10s: float = 0.0
    suggested_template_id: Optional[str] = None


class ChannelBlueprint(BaseModel):
    id: str
    channel_url: str
    niche: str
    pillars: List[str] = Field(default_factory=list)
    title_patterns: List[str] = Field(default_factory=list)
    avg_duration_s: float = 0.0
    upload_cadence: str = ""
    top_videos: List[Dict[str, Any]] = Field(default_factory=list)
    best_hooks: List[str] = Field(default_factory=list)


class ContentIdea(BaseModel):
    id: str
    project_id: str
    title: str
    platform_targets: List[str] = Field(default_factory=list)
    template_id: Optional[str] = None
    blueprint_ref: Optional[str] = None
    priority: int = 0
    status: Literal["new", "scripted", "rendered", "scheduled", "dropped"] = "new"


# --- Persistence helpers ---

def save_video_blueprint(project_id: str, bp: VideoBlueprint) -> Path:
    target = project_path(project_id, "content", "blueprints", f"video_{bp.id}.json", ensure=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(bp.model_dump_json(indent=2))
    return target


def load_video_blueprint(project_id: str, bp_id: str) -> Optional[VideoBlueprint]:
    target = project_path(project_id, "content", "blueprints", f"video_{bp_id}.json")
    if not target.exists():
        return None
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)
    return VideoBlueprint(**data)


def list_video_blueprints(project_id: str) -> List[VideoBlueprint]:
    folder = project_path(project_id, "content", "blueprints")
    if not folder.exists():
        return []
    results: List[VideoBlueprint] = []
    for p in folder.glob("video_*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            results.append(VideoBlueprint(**data))
        except Exception:
            continue
    return results


def save_channel_blueprint(project_id: str, bp: ChannelBlueprint) -> Path:
    target = project_path(project_id, "content", "blueprints", f"channel_{bp.id}.json", ensure=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(bp.model_dump_json(indent=2))
    return target


def load_channel_blueprint(project_id: str, bp_id: str) -> Optional[ChannelBlueprint]:
    target = project_path(project_id, "content", "blueprints", f"channel_{bp_id}.json")
    if not target.exists():
        return None
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ChannelBlueprint(**data)


def list_channel_blueprints(project_id: str) -> List[ChannelBlueprint]:
    folder = project_path(project_id, "content", "blueprints")
    if not folder.exists():
        return []
    results: List[ChannelBlueprint] = []
    for p in folder.glob("channel_*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            results.append(ChannelBlueprint(**data))
        except Exception:
            continue
    return results


def save_content_idea(project_id: str, idea: ContentIdea) -> Path:
    target = project_path(project_id, "content", "ideas", f"{idea.id}.json", ensure=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(idea.model_dump_json(indent=2))
    return target


def load_content_idea(project_id: str, idea_id: str) -> Optional[ContentIdea]:
    target = project_path(project_id, "content", "ideas", f"{idea_id}.json")
    if not target.exists():
        return None
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ContentIdea(**data)


def list_content_ideas(project_id: str) -> List[ContentIdea]:
    folder = project_path(project_id, "content", "ideas")
    if not folder.exists():
        return []
    results: List[ContentIdea] = []
    for p in folder.glob("*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            results.append(ContentIdea(**data))
        except Exception:
            continue
    return results
