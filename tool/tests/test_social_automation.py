from __future__ import annotations

import json
from pathlib import Path
import pytest

from socnhotv.social.automation import SocialAutomationEngine
from socnhotv.social.models import AutomationRule, SocialAccount
from socnhotv.social.store import SocialStore


@pytest.fixture
def automation_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    project_id = "test_auto_proj"
    projects_dir = tmp_path / "data" / "projects" / project_id
    publishing_dir = projects_dir / "publishing"
    runs_dir = projects_dir / "runs" / "render_queue"
    content_dir = projects_dir / "content" / "ideas"

    for d in (publishing_dir, runs_dir, content_dir):
        d.mkdir(parents=True, exist_ok=True)

    def mock_project_path(p_id: str, *subpaths: str, ensure: bool = False) -> Path:
        p = tmp_path / "data" / "projects" / p_id
        for part in subpaths:
            p = p / part
        if ensure:
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.suffix:
                p.mkdir(parents=True, exist_ok=True)
        return p

    monkeypatch.setattr("socnhotv.social.store.project_path", mock_project_path)
    monkeypatch.setattr("socnhotv.social.contracts.project_path", mock_project_path)
    monkeypatch.setattr("socnhotv.social.service.project_path", mock_project_path)
    monkeypatch.setattr("socnhotv.social.automation.project_path", mock_project_path)

    store = SocialStore(project_id)
    acc = SocialAccount(id="acc_tt", platform="tiktok", handle="@socnhotv", display_name="TikTok Sóc Nhỏ")
    store.save_account(acc)

    return project_id, store, runs_dir, content_dir


def test_automation_render_done_default_pending_approval(automation_setup):
    project_id, store, runs_dir, content_dir = automation_setup
    auto = SocialAutomationEngine(project_id)

    # 1. Create completed render job in runs_dir
    job_id = "render_sales_001"
    (runs_dir / f"{job_id}.req.json").write_text(
        json.dumps({
            "template_id": "tiktok-sales-v1",
            "platforms": ["tiktok"],
            "output_name": "Sales Test 1",
        }),
        encoding="utf-8",
    )
    (runs_dir / f"{job_id}.json").write_text(
        json.dumps({
            "job_id": job_id,
            "status": "done",
            "outputs": {"tiktok": "output/sales/tiktok.mp4"},
        }),
        encoding="utf-8",
    )

    # 2. Add rule with auto_approve = False (Default safety behavior)
    rule = AutomationRule(
        id="rule_sales",
        name="Auto draft for sales template",
        enabled=True,
        trigger="render_done",
        conditions={"template_id_prefix": "tiktok-sales-"},
        actions={"create_draft": True, "platforms": ["tiktok"], "auto_approve": False},
    )
    store.save_automation_rule(rule)

    reports = auto.run_rules(trigger_filter="render_done")
    assert len(reports) == 1
    assert reports[0]["status"] == "success"
    assert len(reports[0]["created_post_ids"]) == 1

    post_id = reports[0]["created_post_ids"][0]
    post = store.get_post(post_id)
    assert post is not None
    # Crucial safety check: status MUST be pending_approval, NOT published or approved!
    assert post.status == "pending_approval"
    assert post.approval.required is True
    assert post.targets[0].status == "pending_approval"


def test_automation_render_done_with_explicit_auto_approve(automation_setup):
    project_id, store, runs_dir, content_dir = automation_setup
    auto = SocialAutomationEngine(project_id)

    job_id = "render_sales_002"
    (runs_dir / f"{job_id}.req.json").write_text(
        json.dumps({
            "template_id": "tiktok-sales-v1",
            "platforms": ["tiktok"],
            "output_name": "Sales Auto Approved",
        }),
        encoding="utf-8",
    )
    (runs_dir / f"{job_id}.json").write_text(
        json.dumps({
            "job_id": job_id,
            "status": "done",
            "outputs": {"tiktok": "output/sales/tiktok.mp4"},
        }),
        encoding="utf-8",
    )

    # Rule with auto_approve = True
    rule = AutomationRule(
        id="rule_sales_auto",
        name="Auto draft & approve",
        enabled=True,
        trigger="render_done",
        conditions={"template_id_prefix": "tiktok-sales-"},
        actions={"create_draft": True, "platforms": ["tiktok"], "auto_approve": True},
    )
    store.save_automation_rule(rule)

    reports = auto.run_rules(trigger_filter="render_done")
    assert len(reports) == 1
    post_id = reports[0]["created_post_ids"][0]
    post = store.get_post(post_id)
    assert post.status == "scheduled"
    assert post.targets[0].status == "scheduled"


def test_automation_schedule_gap_warning(automation_setup):
    project_id, store, runs_dir, content_dir = automation_setup
    auto = SocialAutomationEngine(project_id)

    # Disable default rules to test specific rule cleanly
    rules = store.list_automation_rules()
    for r in rules:
        r.enabled = False
    store.save_automation_rules(rules)

    rule = AutomationRule(
        id="rule_gap",
        name="Gap check",
        enabled=True,
        trigger="schedule_gap",
        conditions={"min_weekly_posts": 3},
        actions={"notify": True},
    )
    store.save_automation_rule(rule)

    # There are 0 upcoming posts -> should trigger notification
    reports = auto.run_rules(trigger_filter="schedule_gap")
    assert len(reports) == 1

    notifs = store.list_notifications()
    assert len(notifs) >= 1
    gap_notif = next((n for n in notifs if n.type == "schedule_gap"), None)
    assert gap_notif is not None
    assert "trống" in gap_notif.title.lower()
