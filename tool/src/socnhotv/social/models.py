from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Literal, Optional
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field

DEFAULT_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
MAX_ACCOUNTS = 10


class AccountLimitExceededError(ValueError):
    """Raised when trying to add more accounts than MAX_ACCOUNTS."""
    pass


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
    groups: List[str] = Field(default_factory=list)
    default_hashtags: List[str] = Field(default_factory=list)
    default_caption_footer: str = ""
    posting_windows: List[PostingWindow] = Field(default_factory=list)
    daily_limit: int = 5
    min_gap_minutes: int = 120
    color: str = "#6366f1"
    affiliate_default: dict = Field(default_factory=lambda: {"link": "", "disclosure": False})
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
    cover_url: Optional[str] = None
    first_comment: str = ""
    product_link: str = ""
    disclosure_ad: bool = False
    ai_generated_label: bool = False
    comment_enabled: bool = True
    duet_enabled: bool = True
    stitch_enabled: bool = True
    category: str = "22"
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


class PostMetricsSnapshot(BaseModel):
    timestamp: str = Field(default_factory=now_iso)
    post_id: str
    target_id: str
    platform: PlatformType
    checkpoint: Literal["1h", "6h", "24h", "72h", "7d", "28d", "manual", "custom"] = "custom"
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    watch_time_s: float = 0.0
    avg_retention_pct: float = 0.0
    subscribers_gained: int = 0
    ctr: float = 0.0
    revenue: float = 0.0
    raw: dict = Field(default_factory=dict)


class KPISummary(BaseModel):
    total_views: int = 0
    total_watch_time_s: float = 0.0
    avg_retention_pct: float = 0.0
    engagement_rate: float = 0.0  # ER = (likes + comments + shares + saves) / max(views, 1) * 100
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_saves: int = 0
    follower_gain: int = 0
    avg_ctr: float = 0.0
    affiliate_revenue: float = 0.0
    post_count: int = 0


class GoldenSlotRecommendation(BaseModel):
    weekday: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    hour: int = Field(..., ge=0, le=23)
    median_views: float = 0.0
    sample_count: int = 0
    score: float = 0.0
    is_recommended: bool = False


class OutlierItem(BaseModel):
    post_id: str
    target_id: str
    title: str
    platform: PlatformType
    views: int
    benchmark_views: float
    ratio: float
    kind: Literal["top_outlier", "underperforming"]
    hypothesis: str


class AutomationRule(BaseModel):
    id: str = Field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:8]}")
    name: str
    enabled: bool = False
    trigger: Literal["render_done", "idea_scripted", "schedule_gap"]
    conditions: dict = Field(default_factory=dict)  # e.g. {"template_id_prefix": "tiktok-sales-"}
    actions: dict = Field(default_factory=dict)  # e.g. {"create_draft": True, "platforms": ["tiktok", "reels"], "auto_approve": False}
    last_run_at: Optional[str] = None
    run_count: int = 0
    last_log: Optional[str] = None


class SocialNotification(BaseModel):
    id: str = Field(default_factory=lambda: f"notif_{uuid.uuid4().hex[:8]}")
    type: Literal["publish_success", "publish_failed", "token_expired", "manual_package_due", "schedule_gap", "system"]
    title: str
    message: str
    created_at: str = Field(default_factory=now_iso)
    read: bool = False
    action_url: Optional[str] = None
    data: dict = Field(default_factory=dict)


class ContentTemplate(BaseModel):
    id: str = Field(default_factory=lambda: f"tpl_{uuid.uuid4().hex[:8]}")
    name: str
    purpose: str = "general"  # "sales", "koc", "education", "story"
    platforms: List[PlatformType] = Field(default_factory=list)
    caption_hook: str = ""
    caption_body: str = ""
    caption_cta: str = ""
    hashtags: List[str] = Field(default_factory=list)
    first_comment: str = ""
    footer: str = ""
    disclosure: str = ""
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class BulkActionRequest(BaseModel):
    ids: List[str]  # target_ids
    action: Literal["approve", "reschedule", "duplicate_to", "cancel", "delete_draft", "retry"]
    params: dict = Field(default_factory=dict)


