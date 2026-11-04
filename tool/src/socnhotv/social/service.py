from __future__ import annotations

import copy
import json
import uuid
from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from socnhotv.social.models import (
    DEFAULT_TZ,
    Post,
    PostApproval,
    PostStatus,
    PostTarget,
    SocialAccount,
    ensure_tz,
    now_iso,
)
from socnhotv.social.store import SocialStore
from socnhotv.workspace.paths import project_path


class InvalidStateTransitionError(ValueError):
    """Raised when an invalid state transition is requested."""
    def __init__(self, message: str, from_status: str = "", to_status: str = ""):
        super().__init__(message)
        self.from_status = from_status
        self.to_status = to_status


VALID_TRANSITIONS: Dict[str, List[str]] = {
    "draft": ["pending_approval", "cancelled"],
    "pending_approval": ["approved", "draft", "cancelled"],
    "approved": ["scheduled", "publishing", "draft", "cancelled"],
    "scheduled": ["publishing", "approved", "draft", "cancelled"],
    "publishing": ["published", "failed"],
    "failed": ["scheduled", "draft", "cancelled"],
    "published": [],  # Terminal
    "cancelled": ["draft"],
}


class SocialService:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.store = SocialStore(project_id)

    def _verify_transition(self, current: str, target: str) -> None:
        if target not in VALID_TRANSITIONS.get(current, []):
            raise InvalidStateTransitionError(
                f"Cannot transition post status from '{current}' to '{target}'",
                from_status=current,
                to_status=target,
            )

    def submit_for_approval(self, post_id: str, actor: str = "user", note: str = "") -> Post:
        post = self.store.get_post(post_id)
        if not post:
            raise KeyError(f"Post {post_id} not found")

        self._verify_transition(post.status, "pending_approval")
        old_status = post.status
        post.status = "pending_approval"
        if note:
            post.approval.note = note

        for t in post.targets:
            if t.status in ("draft", "cancelled"):
                t.status = "pending_approval"

        self.store.save_post(post)
        self.store.append_audit(actor, "submit_approval", post.id, from_status=old_status, to_status=post.status, note=note)
        return post

    def approve(self, post_id: str, actor: str = "user", note: str = "") -> Post:
        post = self.store.get_post(post_id)
        if not post:
            raise KeyError(f"Post {post_id} not found")

        self._verify_transition(post.status, "approved")
        old_status = post.status
        post.status = "approved"
        post.approval.by = actor
        post.approval.at = now_iso()
        if note:
            post.approval.note = note

        for t in post.targets:
            if t.status == "pending_approval":
                t.status = "approved"

        self.store.save_post(post)
        self.store.append_audit(actor, "approve", post.id, from_status=old_status, to_status=post.status, note=note)
        return post

    def reject(self, post_id: str, actor: str = "user", reason: str = "") -> Post:
        post = self.store.get_post(post_id)
        if not post:
            raise KeyError(f"Post {post_id} not found")

        self._verify_transition(post.status, "draft")
        old_status = post.status
        post.status = "draft"
        post.approval.note = f"Rejected: {reason}" if reason else "Rejected"

        for t in post.targets:
            if t.status == "pending_approval":
                t.status = "draft"

        self.store.save_post(post)
        self.store.append_audit(actor, "reject", post.id, from_status=old_status, to_status=post.status, note=reason)
        return post

    def schedule(self, post_id: str, target_times: Dict[str, str], actor: str = "user") -> Post:
        post = self.store.get_post(post_id)
        if not post:
            raise KeyError(f"Post {post_id} not found")

        if post.approval.required and post.status != "approved":
            raise InvalidStateTransitionError(
                "Post requires approval before scheduling (current status is not approved)",
                from_status=post.status,
                to_status="scheduled",
            )

        self._verify_transition(post.status, "scheduled")
        old_status = post.status

        for t in post.targets:
            if t.id in target_times:
                t.scheduled_at = target_times[t.id]
            elif t.platform in target_times:
                t.scheduled_at = target_times[t.platform]

            if t.scheduled_at:
                t.status = "scheduled"

        post.status = "scheduled"
        self.store.save_post(post)
        self.store.append_audit(actor, "schedule", post.id, from_status=old_status, to_status=post.status)
        return post

    def update_target_time(self, post_id: str, target_id: str, new_time_iso: str, actor: str = "user") -> Post:
        post = self.store.get_post(post_id)
        if not post:
            raise KeyError(f"Post {post_id} not found")

        target = next((t for t in post.targets if t.id == target_id), None)
        if not target:
            raise KeyError(f"Target {target_id} not found on post {post_id}")

        if target.status == "published":
            raise InvalidStateTransitionError("Cannot reschedule an already published target")

        old_time = target.scheduled_at
        target.scheduled_at = new_time_iso
        self.store.save_post(post)
        self.store.append_audit(
            actor,
            "reschedule_target",
            post.id,
            target_id=target.id,
            note=f"From {old_time} to {new_time_iso}",
        )
        return post

    def cancel(self, post_id: str, actor: str = "user") -> Post:
        post = self.store.get_post(post_id)
        if not post:
            raise KeyError(f"Post {post_id} not found")

        self._verify_transition(post.status, "cancelled")
        old_status = post.status
        post.status = "cancelled"
        for t in post.targets:
            if t.status != "published":
                t.status = "cancelled"

        self.store.save_post(post)
        self.store.append_audit(actor, "cancel", post.id, from_status=old_status, to_status=post.status)
        return post

    def duplicate(self, post_id: str, actor: str = "user") -> Post:
        post = self.store.get_post(post_id)
        if not post:
            raise KeyError(f"Post {post_id} not found")

        dup = copy.deepcopy(post)
        dup.id = f"post_{uuid.uuid4().hex[:10]}"
        dup.title = f"{post.title} (Copy)"
        dup.status = "draft"
        dup.approval = PostApproval(required=True)
        dup.created_at = now_iso()
        dup.updated_at = now_iso()

        for t in dup.targets:
            t.id = f"tgt_{uuid.uuid4().hex[:10]}"
            t.status = "draft"
            t.external_id = None
            t.external_url = None
            t.attempts = 0
            t.last_error = None
            t.published_at = None

        self.store.save_post(dup)
        self.store.append_audit(actor, "duplicate", dup.id, note=f"Cloned from {post_id}")
        return dup

    def suggest_time(self, account_id: str, after: Optional[str | datetime] = None) -> str:
        account = self.store.get_account(account_id)
        if not account:
            # Default to now + 2 hours
            base_dt = datetime.now(DEFAULT_TZ) + timedelta(hours=2)
            return base_dt.isoformat()

        if isinstance(after, str):
            try:
                base_dt = ensure_tz(datetime.fromisoformat(after))
            except Exception:
                base_dt = datetime.now(DEFAULT_TZ)
        elif isinstance(after, datetime):
            base_dt = ensure_tz(after)
        else:
            base_dt = datetime.now(DEFAULT_TZ)

        # Get existing scheduled posts for this account
        existing_posts = self.store.list_posts(account_id=account_id)
        scheduled_times: List[datetime] = []
        for p in existing_posts:
            for t in p.targets:
                if t.account_id == account_id and t.scheduled_at and t.status in ("scheduled", "publishing", "published"):
                    try:
                        scheduled_times.append(ensure_tz(datetime.fromisoformat(t.scheduled_at)))
                    except Exception:
                        pass

        windows = account.posting_windows
        daily_limit = account.daily_limit or 5

        # Search the next 14 days
        candidate_dt = base_dt + timedelta(minutes=15)
        for day_offset in range(14):
            day = (candidate_dt + timedelta(days=day_offset)).date()
            weekday = day.weekday()

            # Check posts on this date
            day_posts_count = sum(1 for st in scheduled_times if st.date() == day)
            if day_posts_count >= daily_limit:
                continue

            matching_windows = [w for w in windows if w.weekday == weekday]
            if not matching_windows:
                # Default 19:00 - 21:00 window if none configured
                matching_windows = [{"start": "19:00", "end": "21:00"}]  # type: ignore

            for w in matching_windows:
                start_str = w.start if hasattr(w, "start") else w["start"]
                sh, sm = [int(x) for x in start_str.split(":")]
                slot_candidate = datetime(day.year, day.month, day.day, sh, sm, tzinfo=DEFAULT_TZ)

                if slot_candidate <= base_dt:
                    continue

                # Check conflict with scheduled times: must be >= 2 hours away from other posts
                conflict = False
                for st in scheduled_times:
                    if abs((st - slot_candidate).total_seconds()) < 7200:  # 2 hours
                        conflict = True
                        break

                if not conflict:
                    return slot_candidate.isoformat()

        # Fallback: base_dt + 2 hours
        return (base_dt + timedelta(hours=2)).isoformat()

    def generate_caption_variants(
        self,
        title: str,
        caption: str,
        hashtags: List[str],
        platforms: List[str],
        product_link: str = "",
        footer: str = "",
    ) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        tag_str = " ".join([f"#{t.lstrip('#')}" for t in hashtags])

        for plat in platforms:
            plat_lower = plat.lower()
            if plat_lower == "tiktok":
                body = f"{title}\n\n{caption}".strip()
                if product_link:
                    body += f"\n\n🛒 Mua ngay tại giỏ hàng: {product_link} #affiliate #ad"
                if footer:
                    body += f"\n\n{footer}"
                if tag_str:
                    body += f"\n\n{tag_str}"
                # Limit to 2200 chars
                final_caption = body[:2200]
                results["tiktok"] = {
                    "caption": final_caption,
                    "hashtags": hashtags,
                    "disclosure_ad": bool(product_link),
                }

            elif plat_lower == "youtube":
                yt_title = title[:100]
                body = f"{caption}\n\n{footer}".strip()
                if product_link:
                    body += f"\n\n🔗 Link sản phẩm: {product_link}"
                if tag_str:
                    body += f"\n\n{tag_str}"
                results["youtube"] = {
                    "title": yt_title,
                    "description": body[:5000],
                    "tags": hashtags[:15],
                    "privacy": "public",
                    "made_for_kids": False,
                }

            elif plat_lower == "instagram":
                body = f"{title}\n\n{caption}".strip()
                if product_link:
                    body += f"\n\n(Quảng cáo / Hợp tác) Link trong bio: {product_link}"
                if footer:
                    body += f"\n\n{footer}"
                if tag_str:
                    body += f"\n\n{tag_str}"
                results["instagram"] = {
                    "caption": body[:2200],
                    "hashtags": hashtags[:30],
                }

            elif plat_lower == "facebook":
                body = f"{title}\n\n{caption}".strip()
                if product_link:
                    body += f"\n\n👉 Xem chi tiết sản phẩm tại: {product_link}"
                if footer:
                    body += f"\n\n{footer}"
                if tag_str:
                    body += f"\n\n{tag_str}"
                results["facebook"] = {
                    "caption": body[:5000],
                    "hashtags": hashtags,
                }

            else:
                body = f"{title} - {caption}"
                if tag_str:
                    body += f" {tag_str}"
                results[plat_lower] = {
                    "caption": body[:1000],
                    "hashtags": hashtags,
                }

        return results

    def schedule_idea(self, idea_id: str, account_id: str, at: Optional[str | datetime] = None) -> Post:
        account = self.store.get_account(account_id)
        if not account:
            raise KeyError(f"Account {account_id} not found")

        # Try to read idea file from content/ideas/<idea_id>.json
        idea_file = project_path(self.project_id, "content", "ideas", f"{idea_id}.json")
        idea_data: Dict[str, Any] = {}
        if idea_file.exists():
            try:
                with open(idea_file, "r", encoding="utf-8") as f:
                    idea_data = json.load(f)
            except Exception:
                pass

        title = idea_data.get("title", f"Nội dung từ ý tưởng {idea_id}")
        platform = account.platform

        if at is None:
            scheduled_at = self.suggest_time(account_id)
        elif isinstance(at, datetime):
            scheduled_at = ensure_tz(at).isoformat()
        else:
            scheduled_at = at

        target = PostTarget(
            id=f"tgt_{uuid.uuid4().hex[:10]}",
            account_id=account.id,
            platform=platform,
            scheduled_at=scheduled_at,
            title=title,
            caption=f"Kịch bản cho ý tưởng: {title}",
            hashtags=list(account.default_hashtags),
            status="draft",
        )

        post = Post(
            id=f"post_{uuid.uuid4().hex[:10]}",
            project_id=self.project_id,
            title=title,
            idea_id=idea_id,
            status="draft",
            approval=PostApproval(required=True),
            targets=[target],
        )

        self.store.save_post(post)
        self.store.append_audit("service", "schedule_idea", post.id, note=f"Linked to idea {idea_id}")
        return post
