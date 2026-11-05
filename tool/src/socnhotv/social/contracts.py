from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from socnhotv.social.models import (
    PlatformType,
    Post,
    PostApproval,
    PostMedia,
    PostTarget,
    now_iso,
)
from socnhotv.social.store import SocialStore
from socnhotv.workspace.paths import project_path


class DraftPost(BaseModel):
    post_id: str
    project_id: str
    media_path: str
    title: str
    caption: str
    platforms: List[str]
    source_ref: Optional[str] = None
    render_job_id: Optional[str] = None
    status: str = "draft"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def create_draft_post(
    project_id: str,
    media_path: str,
    title: str,
    caption: str,
    platforms: List[str],
    source_ref: Optional[str] = None,
    render_job_id: Optional[str] = None,
) -> str:
    """
    Creates a full draft Post in SocialStore with PostTarget for each platform,
    matching any connected account. Keeps contract signature intact.
    """
    store = SocialStore(project_id)
    post_id = f"post_{uuid.uuid4().hex[:12]}"

    if not title or title in ("Video mới", "Video moi", "Untitled Draft"):
        if media_path:
            title = Path(media_path).stem.replace("_", " ").title()
        else:
            title = "Video Thành Phẩm"

    accounts = store.list_accounts()
    targets: List[PostTarget] = []

    valid_platforms: List[PlatformType] = ["youtube", "tiktok", "facebook", "instagram", "douyin", "threads", "x"]

    for plat in platforms:
        plat_lower = plat.lower()
        if plat_lower not in valid_platforms:
            plat_type: PlatformType = "youtube"
        else:
            plat_type = plat_lower  # type: ignore

        # Find matching account
        matching_acc = next((a for a in accounts if a.platform == plat_type and a.status == "connected"), None)
        if not matching_acc:
            matching_acc = next((a for a in accounts if a.platform == plat_type), None)

        acc_id = matching_acc.id if matching_acc else f"acc_{plat_type}"
        tgt_caption = caption
        if matching_acc and matching_acc.default_caption_footer:
            tgt_caption = f"{caption}\n\n{matching_acc.default_caption_footer}".strip()

        targets.append(
            PostTarget(
                id=f"tgt_{uuid.uuid4().hex[:10]}",
                account_id=acc_id,
                platform=plat_type,
                caption=tgt_caption,
                hashtags=list(matching_acc.default_hashtags) if matching_acc else [],
                title=title,
                status="draft",
            )
        )

    post = Post(
        id=post_id,
        project_id=project_id,
        title=title,
        media=[PostMedia(path=media_path, kind="video")],
        source_ref=source_ref,
        render_job_id=render_job_id,
        status="draft",
        approval=PostApproval(required=True),
        targets=targets,
    )
    store.save_post(post)
    store.append_audit("contracts", "create_draft_post", post_id, note="Created via social contract")

    # Also write a copy to inbox for backward compatibility with legacy pollers
    inbox_target = project_path(project_id, "publishing", "inbox", f"{post_id}.json", ensure=True)
    try:
        draft = DraftPost(
            post_id=post_id,
            project_id=project_id,
            media_path=media_path,
            title=title,
            caption=caption,
            platforms=platforms,
            source_ref=source_ref,
            render_job_id=render_job_id,
            status="draft",
        )
        with open(inbox_target, "w", encoding="utf-8") as f:
            f.write(draft.model_dump_json(indent=2))
    except Exception:
        pass

    return post_id


def ingest_inbox(project_id: str) -> List[str]:
    """
    Reads publishing/inbox/*.json (from stub contract or other sessions),
    converts them to full Post drafts in SocialStore, and moves processed files
    to publishing/inbox/_done/.
    """
    store = SocialStore(project_id)
    inbox_dir = project_path(project_id, "publishing", "inbox", ensure=True)
    done_dir = inbox_dir / "_done"
    done_dir.mkdir(parents=True, exist_ok=True)

    ingested_ids: List[str] = []

    for file_path in inbox_dir.glob("*.json"):
        if file_path.name.startswith("_") or not file_path.is_file():
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            post_id = data.get("post_id") or data.get("id") or f"post_{uuid.uuid4().hex[:12]}"

            # Check if post already exists in store
            existing = store.get_post(post_id)
            if not existing:
                title = data.get("title", "Draft Post")
                caption = data.get("caption", "")
                media_path = data.get("media_path") or data.get("video_uri", "")
                platforms = data.get("platforms", ["youtube"])
                source_ref = data.get("source_ref")
                render_job_id = data.get("render_job_id")

                create_draft_post(
                    project_id=project_id,
                    media_path=media_path,
                    title=title,
                    caption=caption,
                    platforms=platforms,
                    source_ref=source_ref,
                    render_job_id=render_job_id,
                )

            ingested_ids.append(post_id)

            # Move to _done
            dest = done_dir / file_path.name
            shutil.move(str(file_path), str(dest))
        except Exception:
            continue

    return ingested_ids
