from __future__ import annotations

import contextlib
import fcntl
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from socnhotv.social.models import (
    MAX_ACCOUNTS,
    AccountLimitExceededError,
    AutomationRule,
    CalendarNote,
    Post,
    PostMedia,
    PostMetricsSnapshot,
    PostTarget,
    RecurringSlot,
    SocialAccount,
    SocialNotification,
    now_iso,
)
from socnhotv.workspace.paths import project_path


@contextlib.contextmanager
def file_lock(lock_file_path: Path) -> Iterator[None]:
    """Context manager providing inter-process file locking using fcntl."""
    lock_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_file_path, "a") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass


def atomic_write_json(file_path: Path, data: Any, indent: int = 2) -> None:
    """Atomically write JSON data using temporary file and atomic replace."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = file_path.parent / f".tmp_{file_path.name}_{uuid.uuid4().hex}"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, file_path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


def atomic_read_json(file_path: Path, default: Any = None) -> Any:
    """Read JSON safely, return default if file doesn't exist or is empty/corrupt."""
    if not file_path.exists():
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return default
            return json.loads(content)
    except Exception:
        return default


class SocialStore:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.pub_dir = project_path(project_id, "publishing", ensure=True)
        self.posts_dir = self.pub_dir / "posts"
        self.posts_dir.mkdir(parents=True, exist_ok=True)
        self.inbox_dir = self.pub_dir / "inbox"
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.inbox_done_dir = self.inbox_dir / "_done"
        self.inbox_done_dir.mkdir(parents=True, exist_ok=True)

        self.accounts_file = self.pub_dir / "accounts.json"
        self.slots_file = self.pub_dir / "slots.json"
        self.notes_file = self.pub_dir / "notes.json"
        self.audit_file = self.pub_dir / "audit.jsonl"
        self.rules_file = self.pub_dir / "automation_rules.json"
        self.notifications_file = self.pub_dir / "notifications.json"
        self.lock_file = self.pub_dir / ".store.lock"

        # Analytics paths
        self.analytics_dir = project_path(project_id, "analytics", ensure=True)
        self.metrics_dir = self.analytics_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.insights_dir = self.analytics_dir / "insights"
        self.insights_dir.mkdir(parents=True, exist_ok=True)
        self.learnings_file = self.analytics_dir / "learnings.md"
        self.recommendations_file = self.analytics_dir / "recommendations.json"

    # --- Accounts ---
    def list_accounts(self) -> List[SocialAccount]:
        with file_lock(self.lock_file):
            raw = atomic_read_json(self.accounts_file, default=[])
            return [SocialAccount.model_validate(x) for x in raw]

    def get_account(self, account_id: str) -> Optional[SocialAccount]:
        accounts = self.list_accounts()
        for a in accounts:
            if a.id == account_id:
                return a
        return None

    def save_account(self, account: SocialAccount, enforce_limit: bool = False) -> SocialAccount:
        with file_lock(self.lock_file):
            raw = atomic_read_json(self.accounts_file, default=[])
            accounts = [SocialAccount.model_validate(x) for x in raw]
            updated = False
            for idx, a in enumerate(accounts):
                if a.id == account.id:
                    accounts[idx] = account
                    updated = True
                    break
            if not updated:
                if enforce_limit and len(accounts) >= MAX_ACCOUNTS:
                    raise AccountLimitExceededError(
                        f"Tối đa {MAX_ACCOUNTS} tài khoản mỗi dự án (MAX_ACCOUNTS = {MAX_ACCOUNTS})"
                    )
                accounts.append(account)
            atomic_write_json(self.accounts_file, [a.model_dump() for a in accounts])
            return account

    def delete_account(self, account_id: str) -> bool:
        with file_lock(self.lock_file):
            raw = atomic_read_json(self.accounts_file, default=[])
            accounts = [SocialAccount.model_validate(x) for x in raw]
            initial_len = len(accounts)
            accounts = [a for a in accounts if a.id != account_id]
            if len(accounts) < initial_len:
                atomic_write_json(self.accounts_file, [a.model_dump() for a in accounts])
                return True
            return False

    # --- Posts ---
    def list_posts(
        self,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        account_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        q: Optional[str] = None,
    ) -> List[Post]:
        posts: List[Post] = []
        with file_lock(self.lock_file):
            for p_file in self.posts_dir.glob("*.json"):
                data = atomic_read_json(p_file)
                if data:
                    try:
                        post = Post.model_validate(data)
                        posts.append(post)
                    except Exception:
                        continue

        # Sort by updated_at descending
        posts.sort(key=lambda p: p.updated_at, reverse=True)

        filtered = []
        for post in posts:
            if status and post.status != status:
                # also check if any target has that status
                if not any(t.status == status for t in post.targets):
                    continue
            if platform and not any(t.platform == platform for t in post.targets):
                continue
            if account_id and not any(t.account_id == account_id for t in post.targets):
                continue
            if from_date or to_date:
                match_date = False
                for t in post.targets:
                    t_date = t.scheduled_at[:10] if t.scheduled_at else post.created_at[:10]
                    if from_date and t_date < from_date:
                        continue
                    if to_date and t_date > to_date:
                        continue
                    match_date = True
                    break
                if not match_date:
                    continue
            if q:
                q_lower = q.lower()
                title_match = q_lower in post.title.lower()
                caption_match = any(q_lower in t.caption.lower() for t in post.targets)
                if not (title_match or caption_match):
                    continue
            filtered.append(post)

        return filtered

    def get_post(self, post_id: str) -> Optional[Post]:
        post_path = self.posts_dir / f"{post_id}.json"
        with file_lock(self.lock_file):
            data = atomic_read_json(post_path)
            if data:
                try:
                    return Post.model_validate(data)
                except Exception:
                    return None
            return None

    def save_post(self, post: Post) -> Post:
        post.updated_at = now_iso()
        post_path = self.posts_dir / f"{post.id}.json"
        with file_lock(self.lock_file):
            atomic_write_json(post_path, post.model_dump())
        return post

    def delete_post(self, post_id: str) -> bool:
        post_path = self.posts_dir / f"{post_id}.json"
        with file_lock(self.lock_file):
            if post_path.exists():
                post_path.unlink()
                return True
            return False

    # --- Slots ---
    def list_slots(self, account_id: Optional[str] = None) -> List[RecurringSlot]:
        with file_lock(self.lock_file):
            raw = atomic_read_json(self.slots_file, default=[])
            slots = [RecurringSlot.model_validate(x) for x in raw]
            if account_id:
                slots = [s for s in slots if s.account_id == account_id]
            return slots

    def save_slots(self, slots: List[RecurringSlot]) -> List[RecurringSlot]:
        with file_lock(self.lock_file):
            atomic_write_json(self.slots_file, [s.model_dump() for s in slots])
            return slots

    def add_slot(self, slot: RecurringSlot) -> RecurringSlot:
        with file_lock(self.lock_file):
            raw = atomic_read_json(self.slots_file, default=[])
            slots = [RecurringSlot.model_validate(x) for x in raw]
            slots = [s for s in slots if s.id != slot.id]
            slots.append(slot)
            atomic_write_json(self.slots_file, [s.model_dump() for s in slots])
            return slot

    def delete_slot(self, slot_id: str) -> bool:
        with file_lock(self.lock_file):
            raw = atomic_read_json(self.slots_file, default=[])
            slots = [RecurringSlot.model_validate(x) for x in raw]
            init_len = len(slots)
            slots = [s for s in slots if s.id != slot_id]
            if len(slots) < init_len:
                atomic_write_json(self.slots_file, [s.model_dump() for s in slots])
                return True
            return False

    # --- Notes ---
    def list_notes(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[CalendarNote]:
        with file_lock(self.lock_file):
            raw = atomic_read_json(self.notes_file, default=[])
            notes = [CalendarNote.model_validate(x) for x in raw]
            if from_date:
                notes = [n for n in notes if n.date >= from_date]
            if to_date:
                notes = [n for n in notes if n.date <= to_date]
            return notes

    def save_notes(self, notes: List[CalendarNote]) -> List[CalendarNote]:
        with file_lock(self.lock_file):
            atomic_write_json(self.notes_file, [n.model_dump() for n in notes])
            return notes

    def add_note(self, note: CalendarNote) -> CalendarNote:
        with file_lock(self.lock_file):
            raw = atomic_read_json(self.notes_file, default=[])
            notes = [CalendarNote.model_validate(x) for x in raw]
            notes = [n for n in notes if n.id != note.id]
            notes.append(note)
            atomic_write_json(self.notes_file, [n.model_dump() for n in notes])
            return note

    def delete_note(self, note_id: str) -> bool:
        with file_lock(self.lock_file):
            raw = atomic_read_json(self.notes_file, default=[])
            notes = [CalendarNote.model_validate(x) for x in raw]
            init_len = len(notes)
            notes = [n for n in notes if n.id != note_id]
            if len(notes) < init_len:
                atomic_write_json(self.notes_file, [n.model_dump() for n in notes])
                return True
            return False

    # --- Audit Log ---
    def append_audit(
        self,
        actor: str,
        action: str,
        post_id: str,
        target_id: Optional[str] = None,
        from_status: Optional[str] = None,
        to_status: Optional[str] = None,
        note: str = "",
    ) -> None:
        entry = {
            "ts": now_iso(),
            "actor": actor,
            "action": action,
            "post_id": post_id,
            "target_id": target_id,
            "from_status": from_status,
            "to_status": to_status,
            "note": note,
        }
        with file_lock(self.lock_file):
            with open(self.audit_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_audit_log(self, post_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.audit_file.exists():
            return []
        entries: List[Dict[str, Any]] = []
        with file_lock(self.lock_file):
            with open(self.audit_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            if post_id and record.get("post_id") != post_id:
                                continue
                            entries.append(record)
                        except Exception:
                            continue
        return entries[-limit:]

    # --- Analytics & Metrics ---
    def append_metrics_snapshot(self, snapshot: PostMetricsSnapshot) -> None:
        metric_file = self.metrics_dir / f"{snapshot.target_id}.jsonl"
        with file_lock(self.lock_file):
            with open(metric_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(snapshot.model_dump(), ensure_ascii=False) + "\n")

    def get_metrics_snapshots(self, target_id: str) -> List[PostMetricsSnapshot]:
        metric_file = self.metrics_dir / f"{target_id}.jsonl"
        if not metric_file.exists():
            return []
        snapshots: List[PostMetricsSnapshot] = []
        with file_lock(self.lock_file):
            with open(metric_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            snapshots.append(PostMetricsSnapshot.model_validate(json.loads(line)))
                        except Exception:
                            continue
        return snapshots

    def get_latest_metrics(self, target_id: str) -> Optional[PostMetricsSnapshot]:
        snapshots = self.get_metrics_snapshots(target_id)
        return snapshots[-1] if snapshots else None

    def list_all_latest_metrics(self) -> Dict[str, PostMetricsSnapshot]:
        """Returns map of target_id -> latest PostMetricsSnapshot."""
        results: Dict[str, PostMetricsSnapshot] = {}
        with file_lock(self.lock_file):
            for m_file in self.metrics_dir.glob("*.jsonl"):
                target_id = m_file.stem
                try:
                    with open(m_file, "r", encoding="utf-8") as f:
                        lines = [l.strip() for l in f if l.strip()]
                    if lines:
                        last = json.loads(lines[-1])
                        results[target_id] = PostMetricsSnapshot.model_validate(last)
                except Exception:
                    continue
        return results

    def save_insights(self, date_str: str, data: dict) -> None:
        path = self.insights_dir / f"{date_str}.json"
        with file_lock(self.lock_file):
            atomic_write_json(path, data)

    def get_insights(self, date_str: str) -> Optional[dict]:
        path = self.insights_dir / f"{date_str}.json"
        if not path.exists():
            return None
        with file_lock(self.lock_file):
            return atomic_read_json(path)

    def save_learnings_md(self, content: str) -> None:
        with file_lock(self.lock_file):
            self.learnings_file.write_text(content, encoding="utf-8")

    def get_learnings_md(self) -> str:
        if not self.learnings_file.exists():
            return "# Bài học tuần này\n\nChưa có báo cáo phân tích mới."
        try:
            return self.learnings_file.read_text(encoding="utf-8")
        except Exception:
            return "# Bài học tuần này\n\nKhông thể đọc báo cáo phân tích."

    def save_recommendations_json(self, data: dict) -> None:
        with file_lock(self.lock_file):
            atomic_write_json(self.recommendations_file, data)

    def get_recommendations_json(self) -> dict:
        if not self.recommendations_file.exists():
            return {}
        with file_lock(self.lock_file):
            return atomic_read_json(self.recommendations_file, default={})

    # --- Automation Rules ---
    def list_automation_rules(self) -> List[AutomationRule]:
        with file_lock(self.lock_file):
            raw = atomic_read_json(self.rules_file, default=None)
            if raw is None:
                # Default rules
                default_rules = [
                    AutomationRule(
                        id="rule_render_auto",
                        name="Tự động tạo bài nháp khi Render video xong",
                        enabled=False,
                        trigger="render_done",
                        conditions={"template_id_prefix": "tiktok-sales-"},
                        actions={"create_draft": True, "platforms": ["tiktok", "reels"], "auto_approve": False},
                    ),
                    AutomationRule(
                        id="rule_schedule_gap",
                        name="Cảnh báo lấp lịch trống tuần tới",
                        enabled=True,
                        trigger="schedule_gap",
                        conditions={"min_weekly_posts": 3},
                        actions={"notify": True},
                    ),
                ]
                atomic_write_json(self.rules_file, [r.model_dump() for r in default_rules])
                return default_rules
            return [AutomationRule.model_validate(x) for x in raw]

    def save_automation_rules(self, rules: List[AutomationRule]) -> List[AutomationRule]:
        with file_lock(self.lock_file):
            atomic_write_json(self.rules_file, [r.model_dump() for r in rules])
            return rules

    def get_automation_rule(self, rule_id: str) -> Optional[AutomationRule]:
        for r in self.list_automation_rules():
            if r.id == rule_id:
                return r
        return None

    def save_automation_rule(self, rule: AutomationRule) -> AutomationRule:
        rules = self.list_automation_rules()
        updated = False
        for idx, r in enumerate(rules):
            if r.id == rule.id:
                rules[idx] = rule
                updated = True
                break
        if not updated:
            rules.append(rule)
        self.save_automation_rules(rules)
        return rule

    def delete_automation_rule(self, rule_id: str) -> bool:
        rules = self.list_automation_rules()
        init_len = len(rules)
        rules = [r for r in rules if r.id != rule_id]
        if len(rules) < init_len:
            self.save_automation_rules(rules)
            return True
        return False

    # --- Notifications ---
    def list_notifications(self, unread_only: bool = False, limit: int = 50) -> List[SocialNotification]:
        with file_lock(self.lock_file):
            raw = atomic_read_json(self.notifications_file, default=[])
            notifs = [SocialNotification.model_validate(x) for x in raw]
            if unread_only:
                notifs = [n for n in notifs if not n.read]
            notifs.sort(key=lambda n: n.created_at, reverse=True)
            return notifs[:limit]

    def add_notification(self, notif: SocialNotification) -> SocialNotification:
        with file_lock(self.lock_file):
            raw = atomic_read_json(self.notifications_file, default=[])
            notifs = [SocialNotification.model_validate(x) for x in raw]
            # Prepend newest
            notifs.insert(0, notif)
            # Keep max 100
            notifs = notifs[:100]
            atomic_write_json(self.notifications_file, [n.model_dump() for n in notifs])
            return notif

    def mark_notification_read(self, notif_id: str) -> bool:
        with file_lock(self.lock_file):
            raw = atomic_read_json(self.notifications_file, default=[])
            notifs = [SocialNotification.model_validate(x) for x in raw]
            changed = False
            for n in notifs:
                if n.id == notif_id or notif_id == "all":
                    n.read = True
                    changed = True
            if changed:
                atomic_write_json(self.notifications_file, [n.model_dump() for n in notifs])
                return True
            return False

    def clear_notifications(self) -> None:
        with file_lock(self.lock_file):
            atomic_write_json(self.notifications_file, [])

