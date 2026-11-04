"""Social Publication Scheduler Worker.

Runs periodically (every 30s) to discover scheduled targets, lock them (publishing),
invoke the official or manual adapter, handle retries with exponential backoff (2/10/30m),
and mark published status idempotently.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from socnhotv.social.adapters import get_adapter
from socnhotv.social.adapters.manual import ManualAdapter
from socnhotv.social.models import (
    DEFAULT_TZ,
    Post,
    PostMetricsSnapshot,
    PostTarget,
    SocialAccount,
    SocialNotification,
    ensure_tz,
    now_iso,
)
from socnhotv.social.store import SocialStore
from socnhotv.workspace.paths import project_path


class SocialScheduler:
    def __init__(self, project_id: str, poll_interval: int = 30):
        self.project_id = project_id
        self.poll_interval = poll_interval
        self.store = SocialStore(project_id)
        self.heartbeat_file = project_path(project_id, "publishing", "scheduler.heartbeat", ensure=True)
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def write_heartbeat(self) -> None:
        try:
            self.heartbeat_file.write_text(now_iso(), encoding="utf-8")
        except Exception:
            pass

    def get_heartbeat(self) -> Optional[str]:
        if not self.heartbeat_file.exists():
            return None
        try:
            return self.heartbeat_file.read_text(encoding="utf-8").strip()
        except Exception:
            return None

    def tick(self, now_dt: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Executes one scheduler evaluation cycle. Can accept an injected `now_dt` for deterministic testing.
        """
        self.write_heartbeat()
        now = ensure_tz(now_dt or datetime.now(DEFAULT_TZ))
        results: List[Dict[str, Any]] = []

        scheduled_posts = self.store.list_posts(status="scheduled")
        for post in scheduled_posts:
            # Check approval gate: must not publish if approval is required and post was not approved
            if post.approval.required and post.status not in ("approved", "scheduled"):
                continue

            post_modified = False
            for target in post.targets:
                if target.status != "scheduled" or not target.scheduled_at:
                    continue

                try:
                    target_time = ensure_tz(datetime.fromisoformat(target.scheduled_at))
                except Exception:
                    continue

                if target_time <= now:
                    # 1. Lock Target to 'publishing'
                    target.status = "publishing"
                    self.store.save_post(post)
                    self.store.append_audit(
                        "scheduler",
                        "lock_target",
                        post.id,
                        target_id=target.id,
                        from_status="scheduled",
                        to_status="publishing",
                    )

                    # 2. Find associated Account
                    account = self.store.get_account(target.account_id)
                    auth_mode = account.auth.mode if account else "manual"
                    if not account:
                        account = SocialAccount(
                            id=target.account_id,
                            platform=target.platform,
                            handle=target.account_id,
                            display_name=target.account_id,
                        )

                    # 3. Publish via Adapter
                    adapter = get_adapter(target.platform, mode=auth_mode)
                    media = post.media[0] if post.media else None

                    # If manual adapter, supply post_id and project_id for bundle generation
                    if isinstance(adapter, ManualAdapter):
                        pub_res = adapter.publish(
                            account=account,
                            target=target,
                            media=media,
                            project_id=self.project_id,
                            post_id=post.id,
                        )
                    else:
                        pub_res = adapter.publish(account=account, target=target, media=media)

                    # 4. Handle Result
                    if pub_res.status == "published":
                        target.status = "published"
                        target.external_id = pub_res.external_id
                        target.external_url = pub_res.url
                        target.published_at = now_iso()
                        post_modified = True

                        self.store.append_audit(
                            "scheduler",
                            "publish_success",
                            post.id,
                            target_id=target.id,
                            to_status="published",
                            note=f"Published to {target.platform}: {pub_res.url}",
                        )
                        self.store.add_notification(
                            SocialNotification(
                                type="publish_success",
                                title=f"Đăng bài thành công lên {target.platform.capitalize()}",
                                message=f"Bài '{post.title}' đã xuất bản thành công: {pub_res.url or ''}",
                                action_url=pub_res.url or "/social?tab=posts",
                                data={"post_id": post.id, "target_id": target.id, "platform": target.platform},
                            )
                        )
                        results.append({
                            "post_id": post.id,
                            "target_id": target.id,
                            "status": "published",
                            "url": pub_res.url,
                        })

                    elif pub_res.status == "failed":
                        target.attempts += 1
                        target.last_error = pub_res.error
                        err_str = str(pub_res.error or "").lower()

                        # Permanent errors: quota exceeded, auth error, or >= 3 attempts
                        is_permanent = (
                            "quota" in err_str
                            or "unauthorized" in err_str
                            or "401" in err_str
                            or "forbidden" in err_str
                            or target.attempts >= 3
                        )

                        if is_permanent:
                            target.status = "failed"
                            if ("quota" in err_str or "unauthorized" in err_str or "401" in err_str) and account:
                                account.status = "expired"
                                self.store.save_account(account)
                                self.store.add_notification(
                                    SocialNotification(
                                        type="token_expired",
                                        title=f"Token tài khoản {account.display_name} đã hết hạn",
                                        message=f"Lỗi xác thực hoặc vượt hạn ngạch: {pub_res.error}. Vui lòng kết nối lại tài khoản.",
                                        action_url="/social?tab=accounts",
                                        data={"account_id": account.id},
                                    )
                                )
                            self.store.add_notification(
                                SocialNotification(
                                    type="publish_failed",
                                    title=f"Đăng bài thất bại ({target.platform.capitalize()})",
                                    message=f"Bài '{post.title}' không thể đăng: {pub_res.error}",
                                    action_url="/social?tab=posts",
                                    data={"post_id": post.id, "target_id": target.id, "error": pub_res.error},
                                )
                            )
                        else:
                            # Backoff retry (2, 10, 30 minutes)
                            backoff_minutes = [2, 10, 30][min(target.attempts - 1, 2)]
                            retry_time = (now + timedelta(minutes=backoff_minutes)).isoformat()
                            target.scheduled_at = retry_time
                            target.status = "scheduled"

                        post_modified = True
                        self.store.append_audit(
                            "scheduler",
                            "publish_failed",
                            post.id,
                            target_id=target.id,
                            note=f"Error: {pub_res.error} (attempt {target.attempts})",
                        )
                        results.append({
                            "post_id": post.id,
                            "target_id": target.id,
                            "status": target.status,
                            "error": pub_res.error,
                        })

            # Check if all targets in post reached published state
            if post_modified:
                if all(t.status == "published" for t in post.targets):
                    post.status = "published"
                elif all(t.status in ("published", "failed") for t in post.targets):
                    post.status = "failed" if any(t.status == "failed" for t in post.targets) else "published"
                self.store.save_post(post)

        return results

    async def run_loop(self) -> None:
        self._running = True
        while self._running:
            try:
                self.tick()
            except Exception as e:
                pass
            await asyncio.sleep(self.poll_interval)

    async def collect_metrics(self) -> int:
        """Collects metrics snapshots for all published targets."""
        from socnhotv.social.analytics.collectors import get_collector

        posts = self.store.list_posts(status="published")
        collected_count = 0
        for p in posts:
            for t in p.targets:
                if t.status == "published":
                    account = self.store.get_account(t.account_id)
                    auth_mode = account.auth.mode if account else "manual"
                    collector = get_collector(t.platform, mode=auth_mode)
                    try:
                        snap = await collector.collect(account, t, checkpoint="custom")
                        snap.post_id = p.id
                        self.store.append_metrics_snapshot(snap)
                        collected_count += 1
                    except Exception:
                        continue
        return collected_count

    def start(self) -> None:
        if not self._running:
            self._task = asyncio.create_task(self.run_loop())

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
