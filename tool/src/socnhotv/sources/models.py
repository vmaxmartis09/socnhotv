from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

PlatformType = Literal["douyin", "tiktok", "youtube", "bilibili", "facebook", "instagram", "local"]
RightsType = Literal["owned", "licensed", "permission", "reference_only"]
SourceStatus = Literal["queued", "downloading", "ready", "failed"]


class SourceFiles(BaseModel):
    video: Optional[str] = None
    audio: Optional[str] = None
    thumb: Optional[str] = None
    subtitle_orig: Optional[str] = None


class SourceStats(BaseModel):
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0


class SceneCut(BaseModel):
    scene_idx: int
    start_s: float
    end_s: float
    thumb: str = ""


class SourceItem(BaseModel):
    id: str
    project_id: str
    platform: PlatformType
    url: str
    author: str = ""
    author_url: str = ""
    title: str = ""
    description: str = ""
    duration_s: float = 0.0
    published_at: str = ""
    stats: SourceStats = Field(default_factory=SourceStats)
    hashtags: List[str] = Field(default_factory=list)
    music: str = ""
    rights: RightsType = "reference_only"  # Default reference_only per manifesto
    rights_note: str = ""
    files: SourceFiles = Field(default_factory=SourceFiles)
    status: SourceStatus = "queued"
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IngestRequest(BaseModel):
    urls: List[str] = Field(default_factory=list)
    rights: RightsType = "reference_only"
    rights_note: str = ""


class UpdateRightsRequest(BaseModel):
    rights: RightsType
    rights_note: Optional[str] = None
    confirm_rights: bool = False
