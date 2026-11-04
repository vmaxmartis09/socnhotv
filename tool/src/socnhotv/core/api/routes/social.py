"""Social API routes plugin.

Prefix: /social (hoặc lồng sau /projects/{project_id}/social khi mở rộng).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException, Query, status

from socnhotv.social.contracts import create_draft_post, ingest_inbox
from socnhotv.social.migrate import migrate_legacy_publishing
from socnhotv.social.models import (
    CalendarNote,
    DEFAULT_TZ,
    Post,
    PostTarget,
    RecurringSlot,
    SocialAccount,
    ensure_tz,
    now_iso,
)
from socnhotv.social.service import InvalidStateTransitionError, SocialService
from socnhotv.social.store import SocialStore

router = APIRouter(tags=["social"])


@router.get("/social/_ping")
async def ping_social():
    return {"status": "ok", "module": "social"}


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
    return store.save_account(payload)


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
    return store.save_account(payload)


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
    items = []
    for p in posts:
        thumb = p.media[0].thumb if p.media and p.media[0].thumb else ""
        for t in p.targets:
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
