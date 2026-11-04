from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from socnhotv.social.models import (
    AccountAuth,
    Post,
    PostApproval,
    PostMedia,
    PostTarget,
    PostingWindow,
    RecurringSlot,
    SocialAccount,
    now_iso,
)
from socnhotv.social.store import SocialStore, atomic_read_json
from socnhotv.workspace.paths import project_path


def _parse_hour_min(time_str: Optional[str]) -> tuple[int, int]:
    """Parse time string like '19:00' or 'Hàng ngày · 19:00' into (hour, minute)."""
    if not time_str:
        return 19, 0
    match = re.search(r"(\d{1,2}):(\d{2})", time_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 19, 0


def migrate_legacy_publishing(project_id: str, force: bool = False) -> Dict[str, Any]:
    """
    Migrate legacy publishing/schedule.json and channels.json into the new
    SocialStore schema (accounts, posts, slots). Idempotent.
    """
    pub_dir = project_path(project_id, "publishing", ensure=True)
    marker_file = pub_dir / ".migrated_v1"

    if marker_file.exists() and not force:
        return {
            "status": "already_migrated",
            "migrated_accounts": 0,
            "migrated_posts": 0,
            "migrated_slots": 0,
        }

    store = SocialStore(project_id)
    sched_file = pub_dir / "schedule.json"
    channels_file = pub_dir / "channels.json"

    raw_sched = atomic_read_json(sched_file, default={})
    raw_channels = atomic_read_json(channels_file, default=[])

    channels_data: List[Dict[str, Any]] = []
    if isinstance(raw_channels, list):
        channels_data.extend(raw_channels)
    if isinstance(raw_sched, dict) and "channels" in raw_sched:
        for c in raw_sched["channels"]:
            if not any(x.get("id") == c.get("id") for x in channels_data):
                channels_data.append(c)

    posts_data: List[Dict[str, Any]] = []
    if isinstance(raw_sched, dict) and "posts" in raw_sched:
        posts_data.extend(raw_sched["posts"])

    migrated_accounts = 0
    migrated_slots = 0
    migrated_posts = 0

    existing_accounts = {a.id: a for a in store.list_accounts()}
    existing_slots = {s.id: s for s in store.list_slots()}
    existing_posts = {p.id: p for p in store.list_posts()}

    # 1. Migrate channels -> SocialAccount + RecurringSlot
    for c in channels_data:
        cid = str(c.get("id", ""))
        if not cid:
            continue

        platform = c.get("platform", "youtube").lower()
        if platform not in ["youtube", "tiktok", "facebook", "instagram", "douyin", "threads", "x"]:
            platform = "youtube"

        h, m = _parse_hour_min(c.get("defaultPublishHours"))
        time_str = f"{h:02d}:{m:02d}"
        end_h = min(23, h + 2)
        end_str = f"{end_h:02d}:{m:02d}"

        if cid not in existing_accounts:
            acc = SocialAccount(
                id=cid,
                platform=platform,
                handle=c.get("name", cid),
                display_name=c.get("name", cid),
                auth=AccountAuth(mode="manual"),
                status="connected" if c.get("connected", True) else "manual",
                default_hashtags=c.get("defaultHashtags", []),
                posting_windows=[
                    PostingWindow(weekday=w, start=time_str, end=end_str)
                    for w in range(7)
                ],
                daily_limit=5,
            )
            store.save_account(acc)
            existing_accounts[cid] = acc
            migrated_accounts += 1

        # Add recurring slot for this channel
        slot_id = f"slot_{cid}"
        if slot_id not in existing_slots:
            rrule = f"FREQ=DAILY;BYHOUR={h};BYMINUTE={m}"
            slot = RecurringSlot(
                id=slot_id,
                account_id=cid,
                rrule=rrule,
                label=f"Hàng ngày · {time_str}",
            )
            store.add_slot(slot)
            existing_slots[slot_id] = slot
            migrated_slots += 1

    # 2. Migrate legacy posts -> Post + PostTarget
    for p in posts_data:
        pid = str(p.get("id", ""))
        if not pid or pid in existing_posts:
            continue

        cid = str(p.get("channelId", ""))
        platform = p.get("platform", "youtube").lower()
        if platform not in ["youtube", "tiktok", "facebook", "instagram", "douyin", "threads", "x"]:
            platform = "youtube"

        s_date = p.get("scheduledDate")
        s_time = p.get("scheduledTime", "19:00")
        scheduled_at = None
        if s_date:
            h, m = _parse_hour_min(s_time)
            scheduled_at = f"{s_date}T{h:02d}:{m:02d}:00+07:00"

        status = p.get("status", "pending_approval")
        if status not in ["draft", "pending_approval", "approved", "scheduled", "publishing", "published", "failed", "cancelled"]:
            status = "pending_approval"

        media_items = []
        video_uri = p.get("videoUri")
        if video_uri:
            media_items.append(PostMedia(path=video_uri, kind="video"))

        target = PostTarget(
            id=f"tgt_{pid}",
            account_id=cid,
            platform=platform,
            scheduled_at=scheduled_at,
            title=p.get("title", ""),
            status=status,
        )

        post = Post(
            id=pid,
            project_id=p.get("projectId", project_id),
            title=p.get("title", pid),
            media=media_items,
            status=status,
            approval=PostApproval(required=True),
            targets=[target],
        )

        store.save_post(post)
        existing_posts[pid] = post
        migrated_posts += 1
        store.append_audit("migration", "migrate_legacy", pid, note="Migrated from legacy schedule.json")

    # 3. Write migration marker file
    marker_file.write_text(now_iso(), encoding="utf-8")

    return {
        "status": "success",
        "migrated_accounts": migrated_accounts,
        "migrated_posts": migrated_posts,
        "migrated_slots": migrated_slots,
    }
