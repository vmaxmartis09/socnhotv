from __future__ import annotations

from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Literal, Optional
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field

from socnhotv.social.models import (
    DEFAULT_TZ,
    PlatformType,
    Post,
    PostApproval,
    PostMedia,
    PostTarget,
    SocialAccount,
    ensure_tz,
    now_iso,
)
from socnhotv.social.platform_rules import (
    Issue,
    get_platform_rule,
    pick_best_variant,
    validate,
)
from socnhotv.social.store import SocialStore
from socnhotv.social.video_library import VideoLibrary


class PlannedTarget(BaseModel):
    video_id: str
    video_title: str
    account_id: str
    account_name: str
    platform: PlatformType
    scheduled_at: str
    issues: List[Issue] = Field(default_factory=list)
    variant_used: Optional[str] = None
    media_path: Optional[str] = None


class PlanPreviewRequest(BaseModel):
    video_ids: List[str]
    account_ids: List[str]
    strategy: Literal["now", "fixed", "auto"] = "auto"
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    per_day_limit: Optional[int] = None
    caption_mode: Optional[str] = "auto"


class TargetCommitSpec(BaseModel):
    video_id: str
    account_id: str
    scheduled_at: str
    title: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    privacy: Optional[str] = "public"
    made_for_kids: bool = False
    ai_generated_label: bool = False
    comment_enabled: bool = True
    duet_enabled: bool = True
    stitch_enabled: bool = True
    first_comment: Optional[str] = ""
    product_link: Optional[str] = ""
    disclosure_ad: bool = False


class PlanCommitRequest(BaseModel):
    targets: List[TargetCommitSpec]
    approval_required: bool = True


def _parse_time_str(time_str: str) -> Tuple[int, int]:
    try:
        parts = time_str.strip().split(":")
        return int(parts[0]), int(parts[1])
    except Exception:
        return 19, 0


class SocialPlanner:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.store = SocialStore(project_id)
        self.library = VideoLibrary(project_id)

    def preview_plan(self, req: PlanPreviewRequest) -> List[PlannedTarget]:
        now_dt = datetime.now(DEFAULT_TZ)

        # Base start time
        if req.start_at:
            try:
                base_start = ensure_tz(datetime.fromisoformat(req.start_at.replace("Z", "+00:00")))
            except Exception:
                base_start = now_dt
        else:
            base_start = now_dt

        # Ensure not in the past
        if base_start < now_dt:
            base_start = now_dt

        all_accounts = {a.id: a for a in self.store.list_accounts()}
        selected_accounts = [all_accounts[aid] for aid in req.account_ids if aid in all_accounts]

        all_videos = {v["id"]: v for v in self.library.list_videos()}
        selected_videos = [all_videos[vid] for vid in req.video_ids if vid in all_videos]

        planned: List[PlannedTarget] = []

        if req.strategy == "now":
            # Schedule immediately (5 minutes from now)
            sched_time = (now_dt + timedelta(minutes=5)).isoformat()
            for v in selected_videos:
                for acc in selected_accounts:
                    v_key, v_path = pick_best_variant(v.get("variants", {}), acc.platform)
                    issues = validate(v, {"platform": acc.platform, "title": v.get("title", "")}, acc)
                    planned.append(
                        PlannedTarget(
                            video_id=v["id"],
                            video_title=v.get("title", ""),
                            account_id=acc.id,
                            account_name=acc.display_name or acc.handle,
                            platform=acc.platform,
                            scheduled_at=sched_time,
                            issues=issues,
                            variant_used=v_key,
                            media_path=v_path or v.get("primary_path"),
                        )
                    )
            return planned

        if req.strategy == "fixed":
            # Fixed time for all, or stepped by 10 minutes
            step_dt = base_start
            for v in selected_videos:
                for acc in selected_accounts:
                    v_key, v_path = pick_best_variant(v.get("variants", {}), acc.platform)
                    issues = validate(v, {"platform": acc.platform, "title": v.get("title", "")}, acc)
                    planned.append(
                        PlannedTarget(
                            video_id=v["id"],
                            video_title=v.get("title", ""),
                            account_id=acc.id,
                            account_name=acc.display_name or acc.handle,
                            platform=acc.platform,
                            scheduled_at=step_dt.isoformat(),
                            issues=issues,
                            variant_used=v_key,
                            media_path=v_path or v.get("primary_path"),
                        )
                    )
                    step_dt += timedelta(minutes=10)
            return planned

        # Strategy: AUTO
        # Group scheduling day by day
        current_date = base_start.date()

        # Track usage per day: date -> account_id -> count
        daily_account_count: Dict[str, Dict[str, int]] = {}
        # Track platform quota per day: date -> platform -> count
        daily_platform_count: Dict[str, Dict[str, int]] = {}
        # Track last scheduled time per account: date -> account_id -> datetime
        daily_account_last_time: Dict[str, Dict[str, datetime]] = {}
        # Track occupied minutes per platform to stagger: date -> platform -> list[datetime]
        daily_platform_times: Dict[str, Dict[str, List[datetime]]] = {}

        for v_idx, v in enumerate(selected_videos):
            for acc in selected_accounts:
                rule = get_platform_rule(acc.platform)
                acc_limit = req.per_day_limit or acc.daily_limit or 5
                min_gap = timedelta(minutes=acc.min_gap_minutes or 120)

                # Find valid day
                cand_date = current_date
                quota_pushed = False
                while True:
                    d_key = cand_date.isoformat()
                    acc_posts = daily_account_count.setdefault(d_key, {}).get(acc.id, 0)
                    plat_posts = daily_platform_count.setdefault(d_key, {}).get(acc.platform, 0)

                    # Check daily limits and platform quota
                    if acc_posts < acc_limit and plat_posts < rule.daily_quota_limit:
                        break
                    # If quota reached, push to next day
                    quota_pushed = True
                    cand_date += timedelta(days=1)

                d_key = cand_date.isoformat()

                # Determine target time on this day
                # Find matching window for cand_date's weekday (0=Monday, 6=Sunday)
                weekday = cand_date.weekday()
                matching_window = None
                for w in acc.posting_windows:
                    if w.weekday == weekday:
                        matching_window = w
                        break

                if matching_window:
                    hour, minute = _parse_time_str(matching_window.start)
                elif acc.posting_windows:
                    hour, minute = _parse_time_str(acc.posting_windows[0].start)
                else:
                    # Default golden evening
                    hour, minute = 19, 30

                target_dt = datetime.combine(cand_date, time(hour, minute), tzinfo=DEFAULT_TZ)

                # Ensure target_dt is not in the past
                if target_dt <= now_dt:
                    target_dt = now_dt + timedelta(minutes=15)

                # Ensure min_gap from previous post of this account today
                last_time = daily_account_last_time.setdefault(d_key, {}).get(acc.id)
                if last_time and (target_dt - last_time) < min_gap:
                    target_dt = last_time + min_gap

                # Stagger across accounts of the same platform (no two posts at same minute)
                plat_times = daily_platform_times.setdefault(d_key, {}).setdefault(acc.platform, [])
                for existing_t in plat_times:
                    if abs((target_dt - existing_t).total_seconds()) < 900:  # within 15 mins
                        target_dt = existing_t + timedelta(minutes=15)

                # Record scheduling
                daily_account_count[d_key][acc.id] = daily_account_count[d_key].get(acc.id, 0) + 1
                daily_platform_count[d_key][acc.platform] = daily_platform_count[d_key].get(acc.platform, 0) + 1
                daily_account_last_time[d_key][acc.id] = target_dt
                plat_times.append(target_dt)

                # Pick variant and validate
                v_key, v_path = pick_best_variant(v.get("variants", {}), acc.platform)
                issues = validate(v, {"platform": acc.platform, "title": v.get("title", "")}, acc)

                if quota_pushed:
                    issues.append(
                        Issue(
                            level="warn",
                            code="quota_pushed",
                            message_vi=f"Hạn ngạch API {rule.name_vi} ({rule.daily_quota_limit} video/ngày) đã đầy ở ngày trước, đã tự động dời sang {cand_date.strftime('%d/%m/%Y')}.",
                        )
                    )

                planned.append(
                    PlannedTarget(
                        video_id=v["id"],
                        video_title=v.get("title", ""),
                        account_id=acc.id,
                        account_name=acc.display_name or acc.handle,
                        platform=acc.platform,
                        scheduled_at=target_dt.isoformat(),
                        issues=issues,
                        variant_used=v_key,
                        media_path=v_path or v.get("primary_path"),
                    )
                )

        return planned

    def commit_plan(self, req: PlanCommitRequest) -> Dict[str, Any]:
        """Commit confirmed plan targets to real Posts and PostTargets."""
        all_videos = {v["id"]: v for v in self.library.list_videos()}
        all_accounts = {a.id: a for a in self.store.list_accounts()}

        # Group targets by video_id
        by_video: Dict[str, List[TargetCommitSpec]] = {}
        for t in req.targets:
            by_video.setdefault(t.video_id, []).append(t)

        created_posts: List[Post] = []
        created_targets_count = 0

        for vid, target_specs in by_video.items():
            v_info = all_videos.get(vid, {})
            title = v_info.get("title") or target_specs[0].title or f"Video {vid[:8]}"
            variants = v_info.get("variants", {})

            # Prepare post media
            primary_path = v_info.get("primary_path", "")
            media_list = []
            if primary_path:
                media_list.append(
                    PostMedia(
                        path=primary_path,
                        kind="video",
                        duration_s=float(v_info.get("duration_s", 0.0)),
                        thumb=v_info.get("thumb", ""),
                    )
                )

            # Build PostTargets
            targets: List[PostTarget] = []
            for spec in target_specs:
                acc = all_accounts.get(spec.account_id)
                platform = acc.platform if acc else "youtube"

                # If captions or hashtags not provided, take defaults
                final_caption = spec.caption or title
                final_hashtags = spec.hashtags if spec.hashtags is not None else (acc.default_hashtags if acc else [])

                target = PostTarget(
                    account_id=spec.account_id,
                    platform=platform,
                    scheduled_at=spec.scheduled_at,
                    title=spec.title or title,
                    caption=final_caption,
                    hashtags=final_hashtags,
                    privacy=spec.privacy or "public",
                    made_for_kids=spec.made_for_kids,
                    ai_generated_label=spec.ai_generated_label,
                    comment_enabled=spec.comment_enabled,
                    duet_enabled=spec.duet_enabled,
                    stitch_enabled=spec.stitch_enabled,
                    first_comment=spec.first_comment or "",
                    product_link=spec.product_link or "",
                    disclosure_ad=spec.disclosure_ad,
                    status="scheduled",
                )
                targets.append(target)
                created_targets_count += 1

            post = Post(
                project_id=self.project_id,
                title=title,
                media=media_list,
                render_job_id=vid if vid.startswith("render_") else None,
                status="scheduled",
                approval=PostApproval(required=req.approval_required),
                targets=targets,
            )

            self.store.save_post(post)
            created_posts.append(post)

        return {
            "created_posts_count": len(created_posts),
            "created_targets_count": created_targets_count,
            "posts": [p.model_dump() for p in created_posts],
        }
