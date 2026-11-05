from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from socnhotv.social.models import (
    DEFAULT_TZ,
    MAX_ACCOUNTS,
    PlatformType,
    Post,
    PostTarget,
    SocialAccount,
    ensure_tz,
)
from socnhotv.social.platform_rules import Issue, validate
from socnhotv.social.store import SocialStore
from socnhotv.workspace.paths import project_path


class QueueItem(BaseModel):
    post_id: str
    target_id: str
    title: str
    platform: PlatformType
    account_id: str
    account_name: str
    account_avatar: str = ""
    scheduled_at: Optional[str] = None
    status: str
    caption: str = ""
    thumb: str = ""
    bucket: Literal["draft", "pending_approval", "upcoming", "overdue", "published", "failed"]
    approval_required: bool = True
    approval_status: str = "pending"  # "approved", "pending", "rejected"
    is_manual: bool = False
    has_package: bool = False
    issues: List[Issue] = Field(default_factory=list)


class QueueSummary(BaseModel):
    accounts_count: int
    max_accounts: int = MAX_ACCOUNTS
    draft_count: int = 0
    pending_approval_count: int = 0
    overdue_count: int = 0
    upcoming_count: int = 0
    published_count: int = 0
    failed_count: int = 0
    next_post_time: Optional[str] = None


class QueueResponse(BaseModel):
    items: List[QueueItem]
    summary: QueueSummary
    total: int = 0
    page: int = 1
    page_size: int = 100
    groups: Optional[Dict[str, List[QueueItem]]] = None


def get_social_queue(
    project_id: str,
    bucket: Optional[str] = "upcoming",
    account_id: Optional[str] = None,
    platform: Optional[str] = None,
    from_date: Optional[str] = None,
    group_by: Optional[str] = None,
    sort: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> QueueResponse:
    store = SocialStore(project_id)
    all_accounts = {a.id: a for a in store.list_accounts()}
    posts = store.list_posts()
    now_dt = datetime.now(DEFAULT_TZ)

    all_items: List[QueueItem] = []
    summary = QueueSummary(
        accounts_count=len(all_accounts),
        max_accounts=MAX_ACCOUNTS,
    )

    next_dt: Optional[datetime] = None

    for p in posts:
        thumb = p.media[0].thumb if p.media and p.media[0].thumb else ""
        video_info = {
            "title": p.title,
            "duration_s": p.media[0].duration_s if p.media else 30.0,
        }

        for t in p.targets:
            acc = all_accounts.get(t.account_id)
            acc_name = acc.display_name if acc else t.account_id
            acc_avatar = acc.avatar if acc else ""
            is_manual = acc.auth.mode == "manual" if acc else False

            # Check if package exists for manual target
            has_pkg = False
            pkg_path = project_path(
                project_id,
                "publishing",
                "packages",
                p.id,
                t.platform,
                ensure=False,
            )
            if pkg_path.exists():
                has_pkg = True

            # Determine scheduled datetime
            t_dt: Optional[datetime] = None
            if t.scheduled_at:
                try:
                    t_dt = ensure_tz(datetime.fromisoformat(t.scheduled_at.replace("Z", "+00:00")))
                except Exception:
                    t_dt = None

            # Accurate bucket partitioning:
            # 1. published
            # 2. failed
            # 3. pending_approval
            # 4. draft (no scheduled_at OR status is draft)
            # 5. upcoming (scheduled_at >= now_dt AND not draft)
            # 6. overdue (scheduled_at < now_dt AND not published)
            if t.status == "published":
                item_bucket = "published"
                summary.published_count += 1
            elif t.status == "failed":
                item_bucket = "failed"
                summary.failed_count += 1
            elif p.approval.required and (p.status == "pending_approval" or t.status == "pending_approval"):
                item_bucket = "pending_approval"
                summary.pending_approval_count += 1
            elif not t.scheduled_at or t.status == "draft":
                item_bucket = "draft"
                summary.draft_count += 1
            elif t_dt is not None:
                if t_dt >= now_dt:
                    item_bucket = "upcoming"
                    summary.upcoming_count += 1
                    if next_dt is None or t_dt < next_dt:
                        next_dt = t_dt
                else:
                    item_bucket = "overdue"
                    summary.overdue_count += 1
            else:
                item_bucket = "draft"
                summary.draft_count += 1

            appr_status = "approved" if not p.approval.required or p.status == "approved" else "pending"
            issues = validate(video_info, t, acc)

            item = QueueItem(
                post_id=p.id,
                target_id=t.id,
                title=p.title,
                platform=t.platform,
                account_id=t.account_id,
                account_name=acc_name,
                account_avatar=acc_avatar,
                scheduled_at=t.scheduled_at,
                status=t.status,
                caption=t.caption,
                thumb=thumb,
                bucket=item_bucket,
                approval_required=p.approval.required,
                approval_status=appr_status,
                is_manual=is_manual,
                has_package=has_pkg,
                issues=issues,
            )
            all_items.append(item)

    if next_dt:
        summary.next_post_time = next_dt.strftime("%H:%M")

    # Filter items
    filtered = all_items
    if bucket and bucket != "all":
        filtered = [item for item in filtered if item.bucket == bucket]

    if account_id:
        filtered = [item for item in filtered if item.account_id == account_id]

    if platform:
        filtered = [item for item in filtered if item.platform == platform]

    if from_date:
        filtered = [item for item in filtered if item.scheduled_at and item.scheduled_at >= from_date]

    # Sorting
    if sort == "title":
        filtered.sort(key=lambda x: x.title.lower())
    elif sort == "-title":
        filtered.sort(key=lambda x: x.title.lower(), reverse=True)
    elif sort == "-scheduled_at" or bucket in ("overdue", "published"):
        filtered.sort(key=lambda x: x.scheduled_at or "", reverse=True)
    elif sort == "scheduled_at" or bucket == "upcoming":
        filtered.sort(key=lambda x: x.scheduled_at or "")
    else:
        filtered.sort(key=lambda x: x.scheduled_at or "")

    total_count = len(filtered)

    # Grouping if requested
    groups_dict = None
    if group_by:
        groups_dict = {}
        for it in filtered:
            if group_by == "date":
                key = it.scheduled_at[:10] if it.scheduled_at else "Chưa hẹn giờ"
            elif group_by == "account":
                key = it.account_name or it.account_id
            elif group_by == "platform":
                key = it.platform
            elif group_by == "status":
                key = it.status
            else:
                key = "Tất cả"
            groups_dict.setdefault(key, []).append(it)

    # Pagination slice
    start_idx = max(0, (page - 1) * page_size)
    paged_items = filtered[start_idx : start_idx + page_size]

    return QueueResponse(
        items=paged_items,
        summary=summary,
        total=total_count,
        page=page,
        page_size=page_size,
        groups=groups_dict,
    )
