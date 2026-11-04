from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from socnhotv.social.contracts import create_draft_post
from socnhotv.social.models import (
    DEFAULT_TZ,
    AutomationRule,
    SocialNotification,
    ensure_tz,
    now_iso,
)
from socnhotv.social.service import SocialService
from socnhotv.social.store import SocialStore
from socnhotv.workspace.paths import project_path


class SocialAutomationEngine:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.store = SocialStore(project_id)
        self.service = SocialService(project_id)

    def run_rules(self, trigger_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Executes all active automation rules matching trigger_filter (or all active if None).
        Returns a list of execution reports.
        """
        rules = self.store.list_automation_rules()
        reports: List[Dict[str, Any]] = []

        for rule in rules:
            if not rule.enabled:
                continue
            if trigger_filter and rule.trigger != trigger_filter:
                continue

            report = self._execute_rule(rule)
            reports.append(report)

        return reports

    def test_run_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        Executes a single rule immediately for test or dry-run, ignoring enabled state.
        """
        rule = self.store.get_automation_rule(rule_id)
        if not rule:
            raise KeyError(f"Rule {rule_id} not found")
        return self._execute_rule(rule)

    def _execute_rule(self, rule: AutomationRule) -> Dict[str, Any]:
        executed_actions: List[str] = []
        created_post_ids: List[str] = []

        try:
            if rule.trigger == "render_done":
                # Scan Session A render events and render_queue
                created_post_ids = self._handle_render_done(rule, executed_actions)
            elif rule.trigger == "idea_scripted":
                # Scan Session B scripted ideas
                created_post_ids = self._handle_idea_scripted(rule, executed_actions)
            elif rule.trigger == "schedule_gap":
                # Check upcoming calendar density
                self._handle_schedule_gap(rule, executed_actions)

            rule.last_run_at = now_iso()
            rule.run_count += 1
            rule.last_log = f"Thành công: {', '.join(executed_actions) if executed_actions else 'Không có mục mới phù hợp điều kiện'}"
            self.store.save_automation_rule(rule)

            return {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "status": "success",
                "actions": executed_actions,
                "created_post_ids": created_post_ids,
            }
        except Exception as e:
            rule.last_run_at = now_iso()
            rule.last_log = f"Lỗi: {str(e)}"
            self.store.save_automation_rule(rule)
            return {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "status": "error",
                "error": str(e),
            }

    def _handle_render_done(self, rule: AutomationRule, actions: List[str]) -> List[str]:
        cond = rule.conditions
        prefix = cond.get("template_id_prefix", "")
        exact_template = cond.get("template_id")
        created_ids: List[str] = []

        render_queue_dir = project_path(self.project_id, "runs", "render_queue", ensure=False)
        if not render_queue_dir.exists():
            return created_ids

        # Gather existing posts to avoid duplicate drafts
        existing_posts = self.store.list_posts()
        existing_jobs = {p.render_job_id for p in existing_posts if p.render_job_id}

        # Check render queue JSON files
        for req_file in sorted(render_queue_dir.glob("render_*.req.json")):
            job_id = req_file.stem.replace(".req", "")
            if job_id in existing_jobs:
                continue

            try:
                with open(req_file, "r", encoding="utf-8") as f:
                    req_data = json.load(f)
            except Exception:
                continue

            tpl_id = req_data.get("template_id", "")
            if exact_template and tpl_id != exact_template:
                continue
            if prefix and not tpl_id.startswith(prefix):
                continue

            # Check if job is completed
            job_file = render_queue_dir / f"{job_id}.json"
            if not job_file.exists():
                continue
            try:
                with open(job_file, "r", encoding="utf-8") as f:
                    job_data = json.load(f)
            except Exception:
                continue

            if job_data.get("status") != "done":
                continue

            outputs = job_data.get("outputs", {})
            if not outputs:
                continue

            # Get main media file
            media_path = next(iter(outputs.values()))
            platforms = rule.actions.get("platforms") or list(outputs.keys())
            title = req_data.get("output_name") or f"Video {tpl_id}"

            # 1. Create Draft Post
            post_id = create_draft_post(
                project_id=self.project_id,
                media_path=media_path,
                title=title,
                caption=f"Video mới tự động render từ mẫu #{tpl_id}!",
                platforms=platforms,
                render_job_id=job_id,
            )
            created_ids.append(post_id)
            actions.append(f"Tạo bài nháp {post_id} từ render {job_id}")

            # 2. Suggest optimal times & captions
            post = self.store.get_post(post_id)
            if post:
                for target in post.targets:
                    try:
                        suggested_time = self.service.suggest_time(target.account_id)
                        target.scheduled_at = suggested_time
                    except Exception:
                        pass
                self.store.save_post(post)

                # 3. State transition: Default is pending_approval
                auto_approve = rule.actions.get("auto_approve", False)
                if auto_approve:
                    # User explicitly opted in to auto-approval
                    self.service.submit_for_approval(post_id, actor="automation")
                    self.service.approve(post_id, actor="automation_rule", note="Tự động duyệt theo quy tắc")
                    t_times = {t.id: t.scheduled_at or now_iso() for t in post.targets}
                    self.service.schedule(post_id, target_times=t_times, actor="automation_rule")
                    actions.append(f"Tự động duyệt và lên lịch {post_id}")
                else:
                    self.service.submit_for_approval(post_id, actor="automation", note="Chờ người dùng duyệt từ Render")
                    actions.append(f"Gửi bài {post_id} vào hàng chờ duyệt")

            # Notification
            self.store.add_notification(
                SocialNotification(
                    type="publish_success" if rule.actions.get("auto_approve") else "manual_package_due",
                    title="Đã tạo bài viết từ video render",
                    message=f"Bản render '{title}' ({job_id}) đã được tạo bài viết và đặt lịch.",
                    action_url=f"/social?tab={'calendar' if rule.actions.get('auto_approve') else 'approvals'}",
                    data={"post_id": post_id, "job_id": job_id},
                )
            )

        return created_ids

    def _handle_idea_scripted(self, rule: AutomationRule, actions: List[str]) -> List[str]:
        ideas_dir = project_path(self.project_id, "content", "ideas", ensure=False)
        created_ids: List[str] = []
        if not ideas_dir.exists():
            return created_ids

        existing_posts = self.store.list_posts()
        existing_ideas = {p.idea_id for p in existing_posts if p.idea_id}

        for idea_file in sorted(ideas_dir.glob("*.json")):
            try:
                with open(idea_file, "r", encoding="utf-8") as f:
                    idata = json.load(f)
            except Exception:
                continue

            idea_id = idata.get("id")
            if not idea_id or idea_id in existing_ideas:
                continue

            if idata.get("status") == "scripted":
                title = idata.get("title", f"Ý tưởng {idea_id}")
                platforms = idata.get("platform_targets") or ["tiktok", "youtube"]
                post_id = create_draft_post(
                    project_id=self.project_id,
                    media_path="",
                    title=title,
                    caption=f"{title}\n\n#socnhotv #viral",
                    platforms=platforms,
                )
                post = self.store.get_post(post_id)
                if post:
                    post.idea_id = idea_id
                    self.store.save_post(post)
                created_ids.append(post_id)
                actions.append(f"Tạo bài nháp {post_id} từ kịch bản {idea_id}")

        return created_ids

    def _handle_schedule_gap(self, rule: AutomationRule, actions: List[str]) -> None:
        min_posts = rule.conditions.get("min_weekly_posts", 3)
        now = datetime.now(DEFAULT_TZ)
        next_week = now + timedelta(days=7)

        posts = self.store.list_posts()
        upcoming_count = 0
        for p in posts:
            for t in p.targets:
                if t.status in ("scheduled", "approved") and t.scheduled_at:
                    try:
                        s_dt = ensure_tz(datetime.fromisoformat(t.scheduled_at))
                        if now <= s_dt <= next_week:
                            upcoming_count += 1
                    except Exception:
                        pass

        if upcoming_count < min_posts:
            msg = f"Tuần tới chỉ có {upcoming_count} bài được lên lịch (mục tiêu tối thiểu: {min_posts} bài). Hãy chọn thêm kịch bản để lấp lịch trống!"
            self.store.add_notification(
                SocialNotification(
                    type="schedule_gap",
                    title="Cảnh báo: Lịch xuất bản tuần tới còn trống",
                    message=msg,
                    action_url="/social?tab=calendar",
                    data={"upcoming_count": upcoming_count, "target_min": min_posts},
                )
            )
            actions.append(f"Phát hiện thiếu bài ({upcoming_count}/{min_posts}), đã gửi cảnh báo lấp lịch trống")
