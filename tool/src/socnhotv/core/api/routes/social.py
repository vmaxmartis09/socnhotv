"""Social API routes plugin.

Prefix: /social (hoặc lồng sau /projects/{project_id}/social khi mở rộng).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException, Query, Request, status
from fastapi.responses import FileResponse

from socnhotv.social.vault import get_social_vault as get_key_vault
from socnhotv.social.adapters import export_package_zip, get_adapter
from socnhotv.social.analytics.collectors.manual import ManualCollector
from socnhotv.social.analytics.insights import AnalyticsEngine
from socnhotv.social.automation import SocialAutomationEngine
from socnhotv.social.contracts import create_draft_post, ingest_inbox
from socnhotv.social.migrate import migrate_legacy_publishing
from socnhotv.social.models import (
    MAX_ACCOUNTS,
    AccountLimitExceededError,
    AutomationRule,
    BulkActionRequest,
    CalendarNote,
    ContentTemplate,
    DEFAULT_TZ,
    Post,
    PostingWindow,
    PostMetricsSnapshot,
    PostTarget,
    RecurringSlot,
    SocialAccount,
    SocialNotification,
    ensure_tz,
    now_iso,
)
from socnhotv.social.captions import CaptionGenerateRequest, CaptionGenerator
from socnhotv.social.planner import PlanCommitRequest, PlanPreviewRequest, SocialPlanner
from socnhotv.social.platform_rules import validate
from socnhotv.social.queue import QueueResponse, get_social_queue
from socnhotv.social.scheduler import SocialScheduler
from socnhotv.social.service import InvalidStateTransitionError, SocialService
from socnhotv.social.store import SocialStore
from socnhotv.social.video_library import VideoLibrary

router = APIRouter(tags=["social"])


@router.get("/social/_ping")
async def ping_social():
    return {"status": "ok", "module": "social"}


# ==========================================
# Video Library, Bulk Plans, Captions & Queue
# ==========================================

@router.get("/projects/{project_id}/social/videos")
async def get_publishable_videos(project_id: str):
    lib = VideoLibrary(project_id)
    return lib.list_videos()


@router.get("/social/videos")
async def get_publishable_videos_alias(project_id: str = Query("soc-nho-tv")):
    lib = VideoLibrary(project_id)
    return lib.list_videos()


@router.get("/projects/{project_id}/social/library")
async def get_social_library(
    project_id: str,
    filter: Optional[str] = Query(None),
    account: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
):
    lib = VideoLibrary(project_id)
    return lib.list_library(filter_type=filter, account_id=account, platform=platform, q=q)


@router.get("/social/library")
async def get_social_library_alias(
    project_id: str = Query("soc-nho-tv"),
    filter: Optional[str] = Query(None),
    account: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
):
    lib = VideoLibrary(project_id)
    return lib.list_library(filter_type=filter, account_id=account, platform=platform, q=q)


@router.post("/projects/{project_id}/social/plans/preview")
async def preview_plan(project_id: str, payload: PlanPreviewRequest):
    planner = SocialPlanner(project_id)
    return planner.preview_plan(payload)


@router.post("/social/plans/preview")
async def preview_plan_alias(payload: PlanPreviewRequest, project_id: str = Query("soc-nho-tv")):
    planner = SocialPlanner(project_id)
    return planner.preview_plan(payload)


@router.post("/projects/{project_id}/social/plans/commit")
async def commit_plan(project_id: str, payload: PlanCommitRequest):
    planner = SocialPlanner(project_id)
    return planner.commit_plan(payload)


@router.post("/social/plans/commit")
async def commit_plan_alias(payload: PlanCommitRequest, project_id: str = Query("soc-nho-tv")):
    planner = SocialPlanner(project_id)
    return planner.commit_plan(payload)


@router.post("/projects/{project_id}/social/captions/generate")
async def generate_captions(project_id: str, payload: CaptionGenerateRequest):
    gen = CaptionGenerator(project_id)
    return gen.generate(payload)


@router.post("/social/captions/generate")
async def generate_captions_alias(payload: CaptionGenerateRequest, project_id: str = Query("soc-nho-tv")):
    gen = CaptionGenerator(project_id)
    return gen.generate(payload)


@router.get("/projects/{project_id}/social/queue", response_model=QueueResponse)
async def get_queue_route(
    project_id: str,
    bucket: Optional[str] = Query("upcoming"),
    account: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    group_by: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    return get_social_queue(
        project_id=project_id,
        bucket=bucket,
        account_id=account,
        platform=platform,
        from_date=from_date,
        group_by=group_by,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/social/queue", response_model=QueueResponse)
async def get_queue_alias(
    project_id: str = Query("soc-nho-tv"),
    bucket: Optional[str] = Query("upcoming"),
    account: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    group_by: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    return get_social_queue(
        project_id=project_id,
        bucket=bucket,
        account_id=account,
        platform=platform,
        from_date=from_date,
        group_by=group_by,
        sort=sort,
        page=page,
        page_size=page_size,
    )


# ==========================================
# Overview & Bulk Operations
# ==========================================

@router.get("/projects/{project_id}/social/overview")
async def get_social_overview(project_id: str):
    store = SocialStore(project_id)
    posts = store.list_posts()
    accounts = store.list_accounts()
    acc_map = {a.id: a for a in accounts}
    now_dt = datetime.now(DEFAULT_TZ)
    plus_24h = now_dt + timedelta(hours=24)
    plus_7d = now_dt + timedelta(days=7)

    upcoming_24h = []
    overdue = []
    failed = []
    pending_approval = []

    scheduled_dates_per_account: Dict[str, set] = {a.id: set() for a in accounts}

    for p in posts:
        for t in p.targets:
            acc = acc_map.get(t.account_id)
            target_info = {
                "post_id": p.id,
                "target_id": t.id,
                "title": p.title,
                "platform": t.platform,
                "account_id": t.account_id,
                "account_name": acc.display_name if acc else t.account_id,
                "account_avatar": acc.avatar if acc else "",
                "status": t.status,
                "scheduled_at": t.scheduled_at,
                "thumb": p.media[0].thumb if p.media and p.media[0].thumb else "",
                "caption": t.caption,
            }

            if t.status == "failed":
                failed.append(target_info)
            elif t.status == "published":
                pass
            elif p.approval.required and (p.status == "pending_approval" or t.status == "pending_approval"):
                pending_approval.append(target_info)
            elif t.scheduled_at:
                try:
                    t_dt = ensure_tz(datetime.fromisoformat(t.scheduled_at.replace("Z", "+00:00")))
                except Exception:
                    t_dt = None

                if t_dt:
                    date_str = t_dt.strftime("%Y-%m-%d")
                    scheduled_dates_per_account.setdefault(t.account_id, set()).add(date_str)

                    if t_dt < now_dt:
                        overdue.append(target_info)
                    elif now_dt <= t_dt <= plus_24h:
                        upcoming_24h.append(target_info)

    token_expiring = []
    for a in accounts:
        if a.auth and a.auth.expires_at:
            try:
                exp_dt = ensure_tz(datetime.fromisoformat(a.auth.expires_at.replace("Z", "+00:00")))
                if now_dt <= exp_dt <= plus_7d:
                    token_expiring.append({
                        "id": a.id,
                        "display_name": a.display_name,
                        "platform": a.platform,
                        "expires_at": a.auth.expires_at,
                        "days_left": max(0, (exp_dt - now_dt).days),
                    })
            except Exception:
                pass

    empty_slots = []
    for day_offset in range(7):
        target_day = now_dt + timedelta(days=day_offset)
        weekday = target_day.weekday()
        date_str = target_day.strftime("%Y-%m-%d")

        for a in accounts:
            if date_str not in scheduled_dates_per_account.get(a.id, set()):
                matching_windows = [w for w in a.posting_windows if w.weekday == weekday]
                if matching_windows:
                    for w in matching_windows:
                        empty_slots.append({
                            "date": date_str,
                            "weekday": weekday,
                            "account_id": a.id,
                            "account_name": a.display_name,
                            "platform": a.platform,
                            "start": w.start,
                            "end": w.end,
                        })

    return {
        "summary": {
            "upcoming_24h_count": len(upcoming_24h),
            "overdue_count": len(overdue),
            "failed_count": len(failed),
            "pending_approval_count": len(pending_approval),
            "token_expiring_count": len(token_expiring),
            "empty_slots_7d_count": len(empty_slots),
        },
        "upcoming_24h": upcoming_24h,
        "overdue": overdue,
        "failed": failed,
        "pending_approval": pending_approval,
        "token_expiring_accounts": token_expiring,
        "empty_slots_7d": empty_slots[:15],
    }


@router.get("/social/overview")
async def get_social_overview_alias(project_id: str = Query("soc-nho-tv")):
    return await get_social_overview(project_id)


@router.post("/projects/{project_id}/social/targets/bulk")
async def bulk_targets_action(project_id: str, payload: BulkActionRequest):
    store = SocialStore(project_id)
    posts = store.list_posts()
    results = []

    target_map = {}
    for p in posts:
        for t in p.targets:
            target_map[t.id] = (p, t)

    now_dt = datetime.now(DEFAULT_TZ)

    for tid in payload.ids:
        if tid not in target_map:
            results.append({"id": tid, "success": False, "error": "Target not found"})
            continue

        p, t = target_map[tid]
        try:
            if payload.action == "approve":
                t.status = "scheduled" if t.scheduled_at else "approved"
                if all(other_t.status in ("scheduled", "approved", "published") for other_t in p.targets):
                    p.status = "scheduled" if any(other_t.scheduled_at for other_t in p.targets) else "approved"
                store.save_post(p)
                store.append_audit("user", "bulk_approve", p.id, target_id=t.id, note="Bulk approved")
                results.append({"id": tid, "success": True, "error": None})

            elif payload.action == "reschedule":
                new_time = payload.params.get("new_time")
                shift_hours = payload.params.get("shift_hours")
                shift_days = payload.params.get("shift_days")

                if new_time:
                    t.scheduled_at = new_time
                elif shift_hours is not None or shift_days is not None:
                    base_dt = now_dt
                    if t.scheduled_at:
                        try:
                            base_dt = ensure_tz(datetime.fromisoformat(t.scheduled_at.replace("Z", "+00:00")))
                        except Exception:
                            base_dt = now_dt
                    if base_dt < now_dt:
                        base_dt = now_dt
                    shift = timedelta(hours=int(shift_hours or 0), days=int(shift_days or 0))
                    t.scheduled_at = (base_dt + shift).isoformat()

                t.status = "scheduled"
                store.save_post(p)
                store.append_audit("user", "bulk_reschedule", p.id, target_id=t.id, note=f"Rescheduled to {t.scheduled_at}")
                results.append({"id": tid, "success": True, "error": None})

            elif payload.action == "duplicate_to":
                target_account_id = payload.params.get("account_id")
                if not target_account_id:
                    results.append({"id": tid, "success": False, "error": "Missing target account_id"})
                    continue
                acc = store.get_account(target_account_id)
                if not acc:
                    results.append({"id": tid, "success": False, "error": f"Account {target_account_id} not found"})
                    continue
                import uuid as _uuid
                new_tgt = t.model_copy(update={
                    "id": f"tgt_{_uuid.uuid4().hex[:10]}",
                    "account_id": target_account_id,
                    "platform": acc.platform,
                    "status": "draft",
                    "scheduled_at": None,
                    "external_id": None,
                    "external_url": None,
                })
                p.targets.append(new_tgt)
                store.save_post(p)
                store.append_audit("user", "bulk_duplicate", p.id, target_id=t.id, note=f"Duplicated to {target_account_id}")
                results.append({"id": tid, "success": True, "error": None})

            elif payload.action == "cancel":
                t.status = "cancelled"
                store.save_post(p)
                store.append_audit("user", "bulk_cancel", p.id, target_id=t.id, note="Bulk cancelled")
                results.append({"id": tid, "success": True, "error": None})

            elif payload.action == "delete_draft":
                p.targets = [other for other in p.targets if other.id != t.id]
                if not p.targets:
                    store.delete_post(p.id)
                else:
                    store.save_post(p)
                store.append_audit("user", "bulk_delete_draft", p.id, target_id=t.id, note="Draft deleted")
                results.append({"id": tid, "success": True, "error": None})

            elif payload.action == "retry":
                t.status = "scheduled"
                t.last_error = None
                t.attempts = 0
                t.scheduled_at = (now_dt + timedelta(minutes=5)).isoformat()
                store.save_post(p)
                store.append_audit("user", "bulk_retry", p.id, target_id=t.id, note="Bulk retried")
                results.append({"id": tid, "success": True, "error": None})

            else:
                results.append({"id": tid, "success": False, "error": f"Unsupported action '{payload.action}'"})

        except Exception as e:
            results.append({"id": tid, "success": False, "error": str(e)})

    return {"results": results}


@router.post("/social/targets/bulk")
async def bulk_targets_action_alias(payload: BulkActionRequest, project_id: str = Query("soc-nho-tv")):
    return await bulk_targets_action(project_id, payload)



# ==========================================
# Accounts CRUD
# ==========================================

@router.get("/projects/{project_id}/social/accounts", response_model=List[SocialAccount])
async def list_accounts(project_id: str):
    store = SocialStore(project_id)
    return store.list_accounts()


@router.post("/projects/{project_id}/social/accounts", response_model=SocialAccount)
async def create_account(project_id: str, payload: SocialAccount):
    store = SocialStore(project_id)
    accounts = store.list_accounts()
    if not any(a.id == payload.id for a in accounts):
        if len(accounts) >= MAX_ACCOUNTS:
            raise HTTPException(
                status_code=409,
                detail=f"Tối đa {MAX_ACCOUNTS} tài khoản mỗi dự án (MAX_ACCOUNTS = {MAX_ACCOUNTS})",
            )
    try:
        return store.save_account(payload, enforce_limit=True)
    except (ValueError, AccountLimitExceededError) as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/projects/{project_id}/social/accounts/stats")
async def get_accounts_stats_route(project_id: str):
    store = SocialStore(project_id)
    accounts = store.list_accounts()
    posts = store.list_posts()
    now_dt = datetime.now(DEFAULT_TZ)

    start_of_week = (now_dt - timedelta(days=now_dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    today_str = now_dt.strftime("%Y-%m-%d")

    stats = {}
    for a in accounts:
        stats[a.id] = {
            "account_id": a.id,
            "posts_this_week": 0,
            "posts_today": 0,
            "daily_limit": a.daily_limit,
            "quota_remaining_today": a.daily_limit,
            "next_post_time": None,
            "last_posted_at": None,
        }

    for p in posts:
        for t in p.targets:
            acc_stat = stats.get(t.account_id)
            if not acc_stat:
                continue

            if t.published_at:
                if not acc_stat["last_posted_at"] or t.published_at > acc_stat["last_posted_at"]:
                    acc_stat["last_posted_at"] = t.published_at

            if t.scheduled_at:
                try:
                    t_dt = ensure_tz(datetime.fromisoformat(t.scheduled_at.replace("Z", "+00:00")))
                    if t_dt >= start_of_week:
                        acc_stat["posts_this_week"] += 1
                    if t.scheduled_at[:10] == today_str:
                        acc_stat["posts_today"] += 1
                    if t_dt >= now_dt:
                        if not acc_stat["next_post_time"] or t.scheduled_at < acc_stat["next_post_time"]:
                            acc_stat["next_post_time"] = t.scheduled_at
                except Exception:
                    pass

    for s in stats.values():
        s["quota_remaining_today"] = max(0, s["daily_limit"] - s["posts_today"])

    return list(stats.values())


@router.get("/social/accounts/stats")
async def get_accounts_stats_alias(project_id: str = Query("soc-nho-tv")):
    return await get_accounts_stats_route(project_id)


@router.get("/projects/{project_id}/social/accounts/{account_id}", response_model=SocialAccount)
async def get_account(project_id: str, account_id: str):
    store = SocialStore(project_id)
    account = store.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.put("/projects/{project_id}/social/accounts/{account_id}", response_model=SocialAccount)
async def update_account(project_id: str, account_id: str, payload: SocialAccount):
    store = SocialStore(project_id)
    payload.id = account_id
    try:
        return store.save_account(payload)
    except (ValueError, AccountLimitExceededError) as e:
        raise HTTPException(status_code=409, detail=str(e))


# ==========================================
# Templates CRUD
# ==========================================

@router.get("/projects/{project_id}/social/templates", response_model=List[ContentTemplate])
async def list_templates_route(project_id: str):
    store = SocialStore(project_id)
    return store.list_templates()


@router.get("/social/templates", response_model=List[ContentTemplate])
async def list_templates_alias(project_id: str = Query("soc-nho-tv")):
    store = SocialStore(project_id)
    return store.list_templates()


@router.post("/projects/{project_id}/social/templates", response_model=ContentTemplate)
async def create_template_route(project_id: str, payload: ContentTemplate):
    store = SocialStore(project_id)
    return store.save_template(payload)


@router.post("/social/templates", response_model=ContentTemplate)
async def create_template_alias(payload: ContentTemplate, project_id: str = Query("soc-nho-tv")):
    store = SocialStore(project_id)
    return store.save_template(payload)


@router.put("/projects/{project_id}/social/templates/{template_id}", response_model=ContentTemplate)
async def update_template_route(project_id: str, template_id: str, payload: ContentTemplate):
    store = SocialStore(project_id)
    payload.id = template_id
    payload.updated_at = now_iso()
    return store.save_template(payload)


@router.put("/social/templates/{template_id}", response_model=ContentTemplate)
async def update_template_alias(template_id: str, payload: ContentTemplate, project_id: str = Query("soc-nho-tv")):
    store = SocialStore(project_id)
    payload.id = template_id
    payload.updated_at = now_iso()
    return store.save_template(payload)


@router.delete("/projects/{project_id}/social/templates/{template_id}")
async def delete_template_route(project_id: str, template_id: str):
    store = SocialStore(project_id)
    deleted = store.delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"status": "deleted", "template_id": template_id}


@router.delete("/social/templates/{template_id}")
async def delete_template_alias(template_id: str, project_id: str = Query("soc-nho-tv")):
    store = SocialStore(project_id)
    deleted = store.delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"status": "deleted", "template_id": template_id}



@router.delete("/projects/{project_id}/social/accounts/{account_id}")
async def delete_account(project_id: str, account_id: str):
    store = SocialStore(project_id)
    deleted = store.delete_account(account_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"status": "deleted", "account_id": account_id}


# ==========================================
# Posts CRUD & Workflow
# ==========================================

@router.get("/projects/{project_id}/social/posts", response_model=List[Post])
async def list_posts(
    project_id: str,
    status: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    account: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    q: Optional[str] = Query(None),
):
    store = SocialStore(project_id)
    return store.list_posts(
        status=status,
        platform=platform,
        account_id=account,
        from_date=from_date,
        to_date=to_date,
        q=q,
    )


@router.post("/projects/{project_id}/social/posts", response_model=Post)
async def create_post(project_id: str, payload: Post):
    store = SocialStore(project_id)
    payload.project_id = project_id
    saved = store.save_post(payload)
    store.append_audit("api", "create_post", saved.id, note="Created via API")
    return saved


@router.post("/projects/{project_id}/social/posts/draft")
async def create_post_draft(project_id: str, payload: Dict[str, Any] = Body(...)):
    """Used by Session A / B UI to easily create a draft post."""
    post_id = create_draft_post(
        project_id=project_id,
        media_path=payload.get("media_path", ""),
        title=payload.get("title", "Untitled Draft"),
        caption=payload.get("caption", ""),
        platforms=payload.get("platforms", ["youtube"]),
        source_ref=payload.get("source_ref"),
        render_job_id=payload.get("render_job_id"),
    )
    store = SocialStore(project_id)
    post = store.get_post(post_id)
    return post.model_dump() if post else {"id": post_id, "status": "draft"}


@router.get("/projects/{project_id}/social/posts/{post_id}", response_model=Post)
async def get_post(project_id: str, post_id: str):
    store = SocialStore(project_id)
    post = store.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.patch("/projects/{project_id}/social/posts/{post_id}", response_model=Post)
async def patch_post(project_id: str, post_id: str, payload: Dict[str, Any] = Body(...)):
    store = SocialStore(project_id)
    post = store.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    data = post.model_dump()
    for k, v in payload.items():
        if k in data and k not in ("id", "project_id", "created_at"):
            data[k] = v

    updated_post = Post.model_validate(data)
    store.save_post(updated_post)
    store.append_audit("api", "patch_post", post_id, note="Fields updated via PATCH")
    return updated_post


@router.delete("/projects/{project_id}/social/posts/{post_id}")
async def delete_post(project_id: str, post_id: str):
    store = SocialStore(project_id)
    deleted = store.delete_post(post_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    store.append_audit("api", "delete_post", post_id)
    return {"status": "deleted", "post_id": post_id}


@router.post("/projects/{project_id}/social/posts/{post_id}/submit", response_model=Post)
async def submit_post(project_id: str, post_id: str, payload: Dict[str, Any] = Body(default={})):
    svc = SocialService(project_id)
    actor = str(payload.get("actor", "user"))
    note = str(payload.get("note", ""))
    try:
        return svc.submit_for_approval(post_id, actor=actor, note=note)
    except KeyError:
        raise HTTPException(status_code=404, detail="Post not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/projects/{project_id}/social/posts/{post_id}/approve", response_model=Post)
async def approve_post(project_id: str, post_id: str, payload: Dict[str, Any] = Body(default={})):
    svc = SocialService(project_id)
    actor = str(payload.get("actor", "user"))
    note = str(payload.get("note", ""))
    try:
        return svc.approve(post_id, actor=actor, note=note)
    except KeyError:
        raise HTTPException(status_code=404, detail="Post not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/projects/{project_id}/social/posts/{post_id}/reject", response_model=Post)
async def reject_post(project_id: str, post_id: str, payload: Dict[str, Any] = Body(default={})):
    svc = SocialService(project_id)
    actor = str(payload.get("actor", "user"))
    reason = str(payload.get("reason", ""))
    try:
        return svc.reject(post_id, actor=actor, reason=reason)
    except KeyError:
        raise HTTPException(status_code=404, detail="Post not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/projects/{project_id}/social/posts/{post_id}/schedule", response_model=Post)
async def schedule_post(project_id: str, post_id: str, payload: Dict[str, Any] = Body(...)):
    svc = SocialService(project_id)
    actor = str(payload.get("actor", "user"))
    target_times = payload.get("targets", {})
    if not isinstance(target_times, dict):
        target_times = {}
    try:
        return svc.schedule(post_id, target_times=target_times, actor=actor)
    except KeyError:
        raise HTTPException(status_code=404, detail="Post not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/projects/{project_id}/social/posts/{post_id}/cancel", response_model=Post)
async def cancel_post(project_id: str, post_id: str, payload: Dict[str, Any] = Body(default={})):
    svc = SocialService(project_id)
    actor = str(payload.get("actor", "user"))
    try:
        return svc.cancel(post_id, actor=actor)
    except KeyError:
        raise HTTPException(status_code=404, detail="Post not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/projects/{project_id}/social/posts/{post_id}/duplicate", response_model=Post)
async def duplicate_post(project_id: str, post_id: str, payload: Dict[str, Any] = Body(default={})):
    svc = SocialService(project_id)
    actor = str(payload.get("actor", "user"))
    try:
        return svc.duplicate(post_id, actor=actor)
    except KeyError:
        raise HTTPException(status_code=404, detail="Post not found")


@router.put("/projects/{project_id}/social/posts/{post_id}/targets/{target_id}/time", response_model=Post)
async def update_target_time(
    project_id: str,
    post_id: str,
    target_id: str,
    payload: Dict[str, Any] = Body(...),
):
    """Drag-and-drop time update for a specific target."""
    svc = SocialService(project_id)
    new_time = payload.get("time") or payload.get("scheduled_at")
    if not new_time:
        raise HTTPException(status_code=400, detail="Missing 'time' or 'scheduled_at' in payload")
    actor = str(payload.get("actor", "user"))
    try:
        return svc.update_target_time(post_id, target_id, str(new_time), actor=actor)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# ==========================================
# Calendar, Slots, Notes & Helpers
# ==========================================

@router.get("/projects/{project_id}/social/calendar")
async def get_calendar(
    project_id: str,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    view: str = Query("month"),
):
    store = SocialStore(project_id)
    posts = store.list_posts(from_date=from_date, to_date=to_date)
    accounts = {a.id: a for a in store.list_accounts()}

    # Flatten targets
    metrics_map = store.list_all_latest_metrics()
    items = []
    for p in posts:
        thumb = p.media[0].thumb if p.media and p.media[0].thumb else ""
        for t in p.targets:
            snap = metrics_map.get(t.id)
            views = snap.views if snap else 0
            items.append({
                "post_id": p.id,
                "target_id": t.id,
                "title": p.title,
                "platform": t.platform,
                "account_id": t.account_id,
                "account_name": accounts.get(t.account_id).display_name if accounts.get(t.account_id) else t.account_id,
                "scheduled_at": t.scheduled_at,
                "status": t.status,
                "caption": t.caption,
                "thumb": thumb,
                "views": views,
            })

    notes = store.list_notes(from_date=from_date, to_date=to_date)
    slots = store.list_slots()

    # Generate empty golden slots suggestions if view == week
    empty_slots = []
    if view == "week" and from_date and to_date:
        for acc in accounts.values():
            for w in acc.posting_windows:
                empty_slots.append({
                    "account_id": acc.id,
                    "platform": acc.platform,
                    "weekday": w.weekday,
                    "start": w.start,
                    "end": w.end,
                    "label": f"Khung giờ vàng ({w.start}-{w.end})",
                })

    return {
        "view": view,
        "from": from_date,
        "to": to_date,
        "items": items,
        "empty_slots": empty_slots,
        "notes": [n.model_dump() for n in notes],
        "slots": [s.model_dump() for s in slots],
    }


@router.get("/projects/{project_id}/social/slots", response_model=List[RecurringSlot])
async def list_slots(project_id: str, account_id: Optional[str] = Query(None)):
    store = SocialStore(project_id)
    return store.list_slots(account_id=account_id)


@router.put("/projects/{project_id}/social/slots", response_model=List[RecurringSlot])
async def update_slots(project_id: str, payload: List[RecurringSlot] = Body(...)):
    store = SocialStore(project_id)
    return store.save_slots(payload)


@router.get("/projects/{project_id}/social/notes", response_model=List[CalendarNote])
async def list_notes(
    project_id: str,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
):
    store = SocialStore(project_id)
    return store.list_notes(from_date=from_date, to_date=to_date)


@router.put("/projects/{project_id}/social/notes", response_model=List[CalendarNote])
async def update_notes(project_id: str, payload: List[CalendarNote] = Body(...)):
    store = SocialStore(project_id)
    return store.save_notes(payload)


@router.post("/projects/{project_id}/social/ideas/{idea_id}/schedule", response_model=Post)
async def schedule_idea(project_id: str, idea_id: str, payload: Dict[str, Any] = Body(...)):
    svc = SocialService(project_id)
    account_id = payload.get("account_id")
    if not account_id:
        raise HTTPException(status_code=400, detail="Missing account_id in payload")
    at = payload.get("at")
    try:
        return svc.schedule_idea(idea_id=idea_id, account_id=str(account_id), at=at)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/social/suggest-time")
async def suggest_time(project_id: str, payload: Dict[str, Any] = Body(...)):
    svc = SocialService(project_id)
    account_id = payload.get("account_id")
    if not account_id:
        raise HTTPException(status_code=400, detail="Missing account_id in payload")
    after = payload.get("after")
    suggested = svc.suggest_time(str(account_id), after=after)
    return {"account_id": account_id, "suggested_time": suggested}


@router.post("/projects/{project_id}/social/caption-variants")
async def caption_variants(project_id: str, payload: Dict[str, Any] = Body(...)):
    svc = SocialService(project_id)
    title = str(payload.get("title", ""))
    caption = str(payload.get("caption", ""))
    hashtags = payload.get("hashtags", [])
    platforms = payload.get("platforms", ["tiktok", "youtube"])
    product_link = str(payload.get("product_link", ""))
    footer = str(payload.get("footer", ""))

    variants = svc.generate_caption_variants(
        title=title,
        caption=caption,
        hashtags=hashtags,
        platforms=platforms,
        product_link=product_link,
        footer=footer,
    )
    return {"variants": variants}


@router.post("/projects/{project_id}/social/migrate")
async def migrate_data(project_id: str, force: bool = Query(False)):
    res = migrate_legacy_publishing(project_id, force=force)
    return res


@router.get("/projects/{project_id}/social/audit")
async def get_audit(project_id: str, post_id: Optional[str] = Query(None), limit: int = Query(100)):
    store = SocialStore(project_id)
    return store.get_audit_log(post_id=post_id, limit=limit)


# ==========================================
# C3: Official OAuth, Publishing & Packages
# ==========================================

@router.get("/projects/{project_id}/social/accounts/{account_id}/connect")
async def get_oauth_connect_url(
    project_id: str,
    account_id: str,
    redirect_uri: str = Query("http://localhost:3000/api/auth/callback"),
):
    store = SocialStore(project_id)
    account = store.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    adapter = get_adapter(account.platform, mode="oauth")
    url = adapter.connect_url(account, redirect_uri=redirect_uri)
    return {"account_id": account_id, "platform": account.platform, "connect_url": url}


@router.get("/social/oauth/callback/{platform}")
async def oauth_callback(
    platform: str,
    code: str = Query(...),
    state: Optional[str] = Query(None),
    redirect_uri: str = Query("http://localhost:3000/api/auth/callback"),
):
    adapter = get_adapter(platform, mode="oauth")
    dummy_acc = SocialAccount(id=state or "unknown", platform=platform, handle="", display_name="")
    tokens = adapter.exchange_code(dummy_acc, code=code, redirect_uri=redirect_uri)
    vault = get_key_vault()
    if state:
        vault.set_key(f"oauth_{platform}_{state}_access", tokens.get("access_token", ""))
        if "refresh_token" in tokens:
            vault.set_key(f"oauth_{platform}_{state}_refresh", tokens.get("refresh_token", ""))
    return {"status": "connected", "platform": platform, "account_id": state}


@router.post("/projects/{project_id}/social/accounts/{account_id}/refresh")
async def refresh_account_token(project_id: str, account_id: str):
    store = SocialStore(project_id)
    account = store.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    adapter = get_adapter(account.platform, mode=account.auth.mode)
    res = adapter.refresh(account)
    return {"status": "refreshed", "details": res}


@router.post("/projects/{project_id}/social/posts/{post_id}/targets/{target_id}/validate")
async def validate_target(project_id: str, post_id: str, target_id: str):
    store = SocialStore(project_id)
    post = store.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    target = next((t for t in post.targets if t.id == target_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    account = store.get_account(target.account_id)
    mode = account.auth.mode if account else "manual"
    adapter = get_adapter(target.platform, mode=mode)
    media = post.media[0] if post.media else None
    issues = adapter.validate(target, media)
    return {"target_id": target_id, "issues": [i.model_dump() for i in issues]}


@router.post("/projects/{project_id}/social/posts/{post_id}/publish-now")
async def publish_now(project_id: str, post_id: str):
    store = SocialStore(project_id)
    post = store.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.approval.required and post.status not in ("approved", "scheduled"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bài viết cần được phê duyệt trước khi xuất bản (approval required)",
        )

    results = []
    for target in post.targets:
        if target.status == "published":
            continue

        account = store.get_account(target.account_id)
        auth_mode = account.auth.mode if account else "manual"
        if not account:
            account = SocialAccount(
                id=target.account_id,
                platform=target.platform,
                handle=target.account_id,
                display_name=target.account_id,
            )

        adapter = get_adapter(target.platform, mode=auth_mode)
        media = post.media[0] if post.media else None

        if hasattr(adapter, "publish"):
            if target.platform not in ("youtube", "tiktok", "facebook", "instagram") or auth_mode == "manual":
                pub_res = adapter.publish(
                    account=account,
                    target=target,
                    media=media,
                    project_id=project_id,
                    post_id=post.id,
                )
            else:
                pub_res = adapter.publish(account=account, target=target, media=media)

            if pub_res.status == "published":
                target.status = "published"
                target.external_id = pub_res.external_id
                target.external_url = pub_res.url
                target.published_at = now_iso()
                store.append_audit("api", "publish_now_success", post.id, target_id=target.id, to_status="published")
            else:
                target.status = "failed"
                target.last_error = pub_res.error
                store.append_audit("api", "publish_now_failed", post.id, target_id=target.id, note=str(pub_res.error))

            results.append({"target_id": target.id, "platform": target.platform, "status": target.status, "url": pub_res.url, "error": pub_res.error})

    if all(t.status == "published" for t in post.targets):
        post.status = "published"
    store.save_post(post)
    return {"post_id": post.id, "status": post.status, "targets": results}


@router.post("/projects/{project_id}/social/posts/{post_id}/targets/{target_id}/mark-published")
async def mark_target_published(
    project_id: str,
    post_id: str,
    target_id: str,
    payload: Dict[str, Any] = Body(...),
):
    """Mark a manual target as published with user-supplied URL."""
    store = SocialStore(project_id)
    post = store.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    target = next((t for t in post.targets if t.id == target_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    url = payload.get("url") or payload.get("external_url", "")
    target.status = "published"
    target.external_url = url
    target.published_at = now_iso()

    if all(t.status == "published" for t in post.targets):
        post.status = "published"

    store.save_post(post)
    store.append_audit(
        "user",
        "manual_mark_published",
        post.id,
        target_id=target.id,
        to_status="published",
        note=f"Manual URL: {url}",
    )
    return {"post_id": post.id, "target_id": target.id, "status": "published", "url": url}


@router.get("/projects/{project_id}/social/scheduler/status")
async def get_scheduler_status(project_id: str):
    sched = SocialScheduler(project_id)
    heartbeat = sched.get_heartbeat()
    store = SocialStore(project_id)
    upcoming_posts = store.list_posts(status="scheduled")
    recent_audit = store.get_audit_log(limit=10)
    return {
        "heartbeat": heartbeat,
        "scheduled_count": len(upcoming_posts),
        "recent_activity": recent_audit,
    }


@router.get("/projects/{project_id}/social/packages/{post_id}/{platform}.zip")
async def download_package_zip(project_id: str, post_id: str, platform: str):
    try:
        zip_path = export_package_zip(project_id, post_id, platform)
        return FileResponse(
            zip_path,
            filename=f"{platform}_package_{post_id}.zip",
            media_type="application/zip",
        )
    except FileNotFoundError:
        # Generate package first if not exists
        store = SocialStore(project_id)
        post = store.get_post(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        target = next((t for t in post.targets if t.platform == platform), None)
        if not target:
            target = PostTarget(account_id=f"acc_{platform}", platform=platform, caption=post.title)
        acc = store.get_account(target.account_id) or SocialAccount(id=target.account_id, platform=platform, handle=platform, display_name=platform)
        adapter = get_adapter(platform, mode="manual")
        adapter.publish(account=acc, target=target, media=post.media[0] if post.media else None, project_id=project_id, post_id=post.id)
        zip_path = export_package_zip(project_id, post_id, platform)
        return FileResponse(
            zip_path,
            filename=f"{platform}_package_{post_id}.zip",
            media_type="application/zip",
        )


# ==========================================
# C4: Analytics, Heatmap, Learning & Automation
# ==========================================

@router.get("/projects/{project_id}/social/analytics/overview")
async def get_analytics_overview(
    project_id: str,
    window: str = Query("30d"),
    platform: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
):
    engine = AnalyticsEngine(project_id)
    kpis = engine.calculate_kpis(time_window=window, platform=platform, account_id=account_id)
    daily = engine.export_daily_insights()
    return {
        "kpis": kpis.model_dump(),
        "views_by_day": daily.get("views_by_day", {}),
        "outliers": daily.get("outliers", {}),
    }


@router.get("/projects/{project_id}/social/analytics/heatmap")
async def get_analytics_heatmap(project_id: str):
    engine = AnalyticsEngine(project_id)
    return engine.calculate_golden_hours()


@router.post("/projects/{project_id}/social/analytics/apply-golden-windows")
async def apply_golden_windows(
    project_id: str,
    payload: Dict[str, Any] = Body(...),
):
    """Applies recommended golden posting windows to one or all accounts."""
    account_id = payload.get("account_id")
    windows_data = payload.get("windows")

    store = SocialStore(project_id)
    accounts = store.list_accounts()
    if account_id:
        accounts = [a for a in accounts if a.id == account_id]

    if not windows_data:
        engine = AnalyticsEngine(project_id)
        golden = engine.calculate_golden_hours()
        windows_data = golden.get("recommended_windows", [])

    new_windows = [PostingWindow.model_validate(w) for w in windows_data]

    updated_accounts = []
    for acc in accounts:
        acc.posting_windows = new_windows
        store.save_account(acc)
        updated_accounts.append(acc.id)

    store.append_audit("user", "apply_golden_windows", post_id="all", note=f"Updated accounts: {updated_accounts}")
    return {"status": "applied", "updated_accounts": updated_accounts, "windows": [w.model_dump() for w in new_windows]}


@router.get("/projects/{project_id}/social/analytics/creatives")
async def get_creative_performance(project_id: str):
    engine = AnalyticsEngine(project_id)
    return engine.join_creative_performance()


@router.get("/projects/{project_id}/social/analytics/outliers")
async def get_analytics_outliers(project_id: str):
    engine = AnalyticsEngine(project_id)
    return engine.detect_outliers()


@router.get("/projects/{project_id}/social/analytics/learnings")
async def get_analytics_learnings(project_id: str):
    engine = AnalyticsEngine(project_id)
    md = engine.generate_learnings_md()
    recs = engine.generate_recommendations_json()
    return {"learnings_md": md, "recommendations": recs}


@router.post("/projects/{project_id}/social/analytics/collect")
async def trigger_analytics_collect(project_id: str):
    sched = SocialScheduler(project_id)
    count = await sched.collect_metrics()
    return {"status": "collected", "count": count}


@router.post("/projects/{project_id}/social/analytics/manual-metrics")
async def save_manual_metrics(
    project_id: str,
    payload: Dict[str, Any] = Body(...),
):
    target_id = payload.get("target_id")
    if not target_id:
        raise HTTPException(status_code=400, detail="target_id is required")

    store = SocialStore(project_id)
    snapshot = PostMetricsSnapshot(
        post_id=payload.get("post_id", ""),
        target_id=target_id,
        platform=payload.get("platform", "youtube"),
        checkpoint="manual",
        views=int(payload.get("views", 0)),
        likes=int(payload.get("likes", 0)),
        comments=int(payload.get("comments", 0)),
        shares=int(payload.get("shares", 0)),
        saves=int(payload.get("saves", 0)),
        watch_time_s=float(payload.get("watch_time_s", 0.0)),
        avg_retention_pct=float(payload.get("avg_retention_pct", 0.0)),
        subscribers_gained=int(payload.get("subscribers_gained", 0)),
        ctr=float(payload.get("ctr", 0.0)),
        revenue=float(payload.get("revenue", 0.0)),
    )
    store.append_metrics_snapshot(snapshot)
    return {"status": "saved", "snapshot": snapshot.model_dump()}


@router.post("/projects/{project_id}/social/analytics/import-csv")
async def import_metrics_csv(
    project_id: str,
    payload: Dict[str, Any] = Body(...),
):
    csv_text = payload.get("csv_text", "")
    default_platform = payload.get("platform", "youtube")
    if not csv_text.strip():
        raise HTTPException(status_code=400, detail="csv_text is required")

    records = ManualCollector.parse_csv(csv_text, default_platform=default_platform)
    store = SocialStore(project_id)
    posts = store.list_posts()

    matched_count = 0
    for rec in records:
        title = rec.get("title", "").strip().lower()
        if not title:
            continue
        # Find matching post
        matching_post = None
        for p in posts:
            if title in p.title.lower() or p.title.lower() in title:
                matching_post = p
                break

        if matching_post:
            target = next((t for t in matching_post.targets if t.platform == default_platform), None)
            if not target and matching_post.targets:
                target = matching_post.targets[0]
            if target:
                snap = PostMetricsSnapshot(
                    post_id=matching_post.id,
                    target_id=target.id,
                    platform=target.platform,
                    checkpoint="manual",
                    views=rec.get("views", 0),
                    likes=rec.get("likes", 0),
                    comments=rec.get("comments", 0),
                    shares=rec.get("shares", 0),
                    saves=rec.get("saves", 0),
                    watch_time_s=rec.get("watch_time_s", 0.0),
                    avg_retention_pct=rec.get("avg_retention_pct", 0.0),
                    subscribers_gained=rec.get("subscribers_gained", 0),
                    ctr=rec.get("ctr", 0.0),
                    revenue=rec.get("revenue", 0.0),
                    raw=rec,
                )
                store.append_metrics_snapshot(snap)
                matched_count += 1

    return {"status": "imported", "total_records": len(records), "matched_count": matched_count, "records": records[:10]}


# --- Automation Rules API ---
@router.get("/projects/{project_id}/social/automation/rules", response_model=List[AutomationRule])
async def list_automation_rules(project_id: str):
    store = SocialStore(project_id)
    return store.list_automation_rules()


@router.post("/projects/{project_id}/social/automation/rules", response_model=AutomationRule)
async def create_or_update_rule(project_id: str, rule: AutomationRule):
    store = SocialStore(project_id)
    return store.save_automation_rule(rule)


@router.post("/projects/{project_id}/social/automation/rules/{rule_id}/toggle")
async def toggle_rule(project_id: str, rule_id: str):
    store = SocialStore(project_id)
    rule = store.get_automation_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.enabled = not rule.enabled
    store.save_automation_rule(rule)
    return {"id": rule.id, "enabled": rule.enabled}


@router.delete("/projects/{project_id}/social/automation/rules/{rule_id}")
async def delete_rule(project_id: str, rule_id: str):
    store = SocialStore(project_id)
    success = store.delete_automation_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "deleted", "id": rule_id}


@router.post("/projects/{project_id}/social/automation/run")
async def run_automation_rules(
    project_id: str,
    rule_id: Optional[str] = Query(None),
):
    auto = SocialAutomationEngine(project_id)
    if rule_id:
        report = auto.test_run_rule(rule_id)
        return {"reports": [report]}
    else:
        reports = auto.run_rules()
        return {"reports": reports}


# --- Notifications API ---
@router.get("/projects/{project_id}/social/notifications", response_model=List[SocialNotification])
async def list_notifications(
    project_id: str,
    unread_only: bool = Query(False),
    limit: int = Query(50),
):
    store = SocialStore(project_id)
    return store.list_notifications(unread_only=unread_only, limit=limit)


@router.post("/projects/{project_id}/social/notifications/{notif_id}/read")
async def mark_notification_read(project_id: str, notif_id: str):
    store = SocialStore(project_id)
    success = store.mark_notification_read(notif_id)
    return {"status": "ok", "success": success}


@router.delete("/projects/{project_id}/social/notifications")
async def clear_all_notifications(project_id: str):
    store = SocialStore(project_id)
    store.clear_notifications()
    return {"status": "cleared"}

