from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Literal, Optional
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field

DEFAULT_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def now_iso() -> str:
    """Return current timestamp in ISO-8601 with Asia/Ho_Chi_Minh timezone."""
    return datetime.now(DEFAULT_TZ).isoformat()


def ensure_tz(dt: datetime) -> datetime:
    """Ensure datetime has timezone, default to Asia/Ho_Chi_Minh if naive."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=DEFAULT_TZ)
    return dt.astimezone(DEFAULT_TZ)


PlatformType = Literal["youtube", "tiktok", "facebook", "instagram", "douyin", "threads", "x"]

AccountAuthMode = Literal["oauth", "manual", "browser_assisted"]
AccountStatus = Literal["connected", "expired", "manual", "disabled"]

PostStatus = Literal[
    "draft",
    "pending_approval",
    "approved",
    "scheduled",
    "publishing",
    "published",
    "failed",
    "cancelled",
]

MediaKind = Literal["video", "image", "carousel"]
PrivacyType = Literal["public", "unlisted", "private"]


class PostingWindow(BaseModel):
    weekday: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start: str = Field(..., description="HH:MM format, e.g. '19:00'")
    end: str = Field(..., description="HH:MM format, e.g. '21:00'")


class AccountAuth(BaseModel):
    mode: AccountAuthMode = "manual"
    token_ref: Optional[str] = Field(None, description="Vault key reference, not raw token")
    scopes: List[str] = Field(default_factory=list)
    expires_at: Optional[str] = None


class SocialAccount(BaseModel):
    id: str = Field(default_factory=lambda: f"acc_{uuid.uuid4().hex[:10]}")
    platform: PlatformType
    handle: str
    display_name: str
    avatar: str = ""
    channel_url: str = ""
    auth: AccountAuth = Field(default_factory=AccountAuth)
    status: AccountStatus = "manual"
    default_hashtags: List[str] = Field(default_factory=list)
    default_caption_footer: str = ""
    posting_windows: List[PostingWindow] = Field(default_factory=list)
    daily_limit: int = 5
    tags: List[str] = Field(default_factory=list)


class PostMedia(BaseModel):
    path: str
    platform_variant: Optional[str] = None
    kind: MediaKind = "video"
    duration_s: float = 0.0
    thumb: str = ""


class PostApproval(BaseModel):
    required: bool = True
    by: Optional[str] = None
    at: Optional[str] = None
    note: Optional[str] = None


class PostTarget(BaseModel):
    id: str = Field(default_factory=lambda: f"tgt_{uuid.uuid4().hex[:10]}")
    account_id: str
    platform: PlatformType
    scheduled_at: Optional[str] = None
    caption: str = ""
    hashtags: List[str] = Field(default_factory=list)
    title: str = ""
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    privacy: PrivacyType = "public"
    made_for_kids: bool = False
    cover_time_s: float = 0.0
    first_comment: str = ""
    product_link: str = ""
    disclosure_ad: bool = False
    status: PostStatus = "draft"
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    attempts: int = 0
    last_error: Optional[str] = None
    published_at: Optional[str] = None


class Post(BaseModel):
    id: str = Field(default_factory=lambda: f"post_{uuid.uuid4().hex[:10]}")
    project_id: str
    title: str
    media: List[PostMedia] = Field(default_factory=list)
    source_ref: Optional[str] = None
    render_job_id: Optional[str] = None
    idea_id: Optional[str] = None
    status: PostStatus = "draft"
    approval: PostApproval = Field(default_factory=PostApproval)
    targets: List[PostTarget] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class RecurringSlot(BaseModel):
    id: str = Field(default_factory=lambda: f"slot_{uuid.uuid4().hex[:10]}")
    account_id: str
    rrule: str = Field(..., description="RFC5545 recurrence rule, e.g. FREQ=WEEKLY;BYDAY=MO,WE,FR;BYHOUR=19;BYMINUTE=0")
    label: str = ""
    template_hint: Optional[str] = None


class CampaignTag(BaseModel):
    id: str = Field(default_factory=lambda: f"tag_{uuid.uuid4().hex[:8]}")
    name: str
    color: str = "#6366f1"


class CalendarNote(BaseModel):
    id: str = Field(default_factory=lambda: f"note_{uuid.uuid4().hex[:8]}")
    date: str = Field(..., description="YYYY-MM-DD")
    text: str
    color: str = "#f59e0b"
