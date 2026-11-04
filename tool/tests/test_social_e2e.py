from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
import pytest

from socnhotv.social.adapters.base import PublishAdapter, PublishResult
from socnhotv.social.analytics.insights import AnalyticsEngine
from socnhotv.social.contracts import create_draft_post, ingest_inbox
from socnhotv.social.models import (
    DEFAULT_TZ,
    PostMetricsSnapshot,
    SocialAccount,
    ensure_tz,
    now_iso,
)
from socnhotv.social.scheduler import SocialScheduler
from socnhotv.social.service import SocialService
from socnhotv.social.store import SocialStore


class MockE2EAdapter(PublishAdapter):
    platform = "youtube"

    def capabilities(self):
        from socnhotv.social.adapters.base import Capabilities
        return Capabilities(direct_post=True)

    def connect_url(self, account, redirect_uri):
        return "https://example.com/oauth"

    def exchange_code(self, account, code, redirect_uri):
        return {"access_token": "mock_token"}

    def refresh(self, account):
        return {"access_token": "refreshed_token"}

    def validate(self, target, media=None):
        return []

    def publish(self, account, target, media=None, **kwargs):
        return PublishResult(
            status="published",
            external_id="yt_vid_999",
            url="https://youtube.com/watch?v=yt_vid_999",
        )

    def fetch_status(self, account, external_id):
        return PublishResult(status="published", external_id=external_id)


@pytest.fixture
def e2e_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    project_id = "test_e2e_proj"
    data_dir = tmp_path / "data" / "projects" / project_id
    pub_dir = data_dir / "publishing"
    analytics_dir = data_dir / "analytics"

    for d in (pub_dir, analytics_dir):
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
    monkeypatch.setattr("socnhotv.social.scheduler.project_path", mock_project_path)
    monkeypatch.setattr("socnhotv.social.analytics.insights.project_path", mock_project_path)
    monkeypatch.setattr("socnhotv.social.scheduler.get_adapter", lambda platform, mode: MockE2EAdapter())

    store = SocialStore(project_id)
    service = SocialService(project_id)
    sched = SocialScheduler(project_id)
    engine = AnalyticsEngine(project_id)

    # Connected account
    acc = SocialAccount(
        id="acc_yt_e2e",
        platform="youtube",
        handle="@socnho_e2e",
        display_name="Sóc Nhỏ E2E",
        status="connected",
    )
    store.save_account(acc)

    return project_id, store, service, sched, engine


def test_social_full_e2e_pipeline(e2e_setup):
    project_id, store, service, sched, engine = e2e_setup

    # 1. Inbox contract: ingest or create draft post
    post_id = create_draft_post(
        project_id=project_id,
        media_path="output/ep1/video.mp4",
        title="Tập 1: Sóc Nhỏ Khám Phá Rừng Xanh",
        caption="Cuộc phiêu lưu kỳ thú của Sóc Nhỏ Bi!",
        platforms=["youtube"],
    )
    assert post_id is not None
    post = store.get_post(post_id)
    assert post.status == "draft"
    target = post.targets[0]
    assert target.platform == "youtube"

    # 2. Submit for approval
    service.submit_for_approval(post_id, actor="creator", note="Đã hoàn thiện kịch bản")
    post = store.get_post(post_id)
    assert post.status == "pending_approval"

    # 3. Approve
    service.approve(post_id, actor="reviewer", note="Video đạt chuẩn")
    post = store.get_post(post_id)
    assert post.status == "approved"

    # 4. Schedule for 1 minute in the past so scheduler picks it up immediately
    now = datetime.now(DEFAULT_TZ)
    past_time = (now - timedelta(minutes=1)).isoformat()
    service.schedule(post_id, target_times={target.id: past_time}, actor="creator")
    post = store.get_post(post_id)
    assert post.status == "scheduled"
    assert post.targets[0].status == "scheduled"

    # 5. Scheduler ticks: locks target, publishes via Mock adapter, updates status
    tick_results = sched.tick(now_dt=now)
    assert len(tick_results) == 1
    assert tick_results[0]["status"] == "published"
    assert "youtube.com" in tick_results[0]["url"]

    post = store.get_post(post_id)
    assert post.status == "published"
    assert post.targets[0].status == "published"
    assert post.targets[0].external_url == "https://youtube.com/watch?v=yt_vid_999"

    # 6. Metrics collector records snapshot for published target
    store.append_metrics_snapshot(
        PostMetricsSnapshot(
            post_id=post.id,
            target_id=target.id,
            platform="youtube",
            checkpoint="1h",
            views=15000,
            likes=1200,
            comments=85,
            shares=60,
            saves=40,
            watch_time_s=45000.0,
            avg_retention_pct=72.0,
            subscribers_gained=320,
            revenue=75.0,
        )
    )

    # 7. Insights engine calculations include the published post
    kpis = engine.calculate_kpis("all")
    assert kpis.total_views == 15000
    assert kpis.total_likes == 1200
    assert kpis.post_count == 1
    assert kpis.follower_gain == 320

    # 8. Check daily insights export
    insights = engine.export_daily_insights()
    assert insights["kpis"]["total_views"] == 15000
    assert "outliers" in insights
    assert "golden_hours" in insights

    # 9. Verify learnings.md and recommendations.json exist
    assert store.learnings_file.exists()
    assert store.recommendations_file.exists()
    recs = store.get_recommendations_json()
    assert "recommended_posting_windows" in recs
