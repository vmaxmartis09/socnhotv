from __future__ import annotations

import json
from pathlib import Path
import pytest

from socnhotv.social.analytics.collectors.manual import ManualCollector
from socnhotv.social.analytics.insights import AnalyticsEngine
from socnhotv.social.models import (
    Post,
    PostMedia,
    PostMetricsSnapshot,
    PostTarget,
    SocialAccount,
    now_iso,
)
from socnhotv.social.store import SocialStore
from socnhotv.workspace.paths import project_path


@pytest.fixture
def analytics_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    project_id = "test_analytics_proj"
    data_dir = tmp_path / "data"
    projects_dir = data_dir / "projects" / project_id
    publishing_dir = projects_dir / "publishing"
    analytics_dir = projects_dir / "analytics"
    runs_dir = projects_dir / "runs" / "render_queue"
    ideas_dir = projects_dir / "content" / "ideas"

    for d in (publishing_dir, analytics_dir, runs_dir, ideas_dir):
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
    monkeypatch.setattr("socnhotv.social.analytics.insights.project_path", mock_project_path)
    monkeypatch.setattr("socnhotv.social.automation.project_path", mock_project_path)

    store = SocialStore(project_id)

    # 1. Add mock account
    acc = SocialAccount(
        id="acc_yt",
        platform="youtube",
        handle="@socnhotv",
        display_name="Sóc Nhỏ TV",
    )
    store.save_account(acc)

    # 2. Add published posts
    p1 = Post(
        id="post_top",
        project_id=project_id,
        title="Top Viral Video",
        render_job_id="render_job_1",
        idea_id="idea_1",
        status="published",
        targets=[
            PostTarget(
                id="tgt_top",
                account_id="acc_yt",
                platform="youtube",
                status="published",
                published_at="2026-11-04T20:00:00+07:00",
            )
        ],
    )
    p2 = Post(
        id="post_mid",
        project_id=project_id,
        title="Average Video",
        render_job_id="render_job_1",
        idea_id="idea_1",
        status="published",
        targets=[
            PostTarget(
                id="tgt_mid",
                account_id="acc_yt",
                platform="youtube",
                status="published",
                published_at="2026-11-04T12:00:00+07:00",
            )
        ],
    )
    p3 = Post(
        id="post_low",
        project_id=project_id,
        title="Underperforming Video",
        render_job_id="render_job_2",
        idea_id="idea_2",
        status="published",
        targets=[
            PostTarget(
                id="tgt_low",
                account_id="acc_yt",
                platform="youtube",
                status="published",
                published_at="2026-11-03T09:00:00+07:00",
            )
        ],
    )
    store.save_post(p1)
    store.save_post(p2)
    store.save_post(p3)

    # 3. Add Metric Snapshots
    store.append_metrics_snapshot(
        PostMetricsSnapshot(
            post_id=p1.id,
            target_id="tgt_top",
            platform="youtube",
            views=10000,
            likes=800,
            comments=100,
            shares=100,
            saves=50,
            watch_time_s=36000.0,
            avg_retention_pct=65.5,
            subscribers_gained=250,
            revenue=50.0,
        )
    )
    store.append_metrics_snapshot(
        PostMetricsSnapshot(
            post_id=p2.id,
            target_id="tgt_mid",
            platform="youtube",
            views=2000,
            likes=100,
            comments=20,
            shares=10,
            saves=10,
            watch_time_s=6000.0,
            avg_retention_pct=45.0,
            subscribers_gained=20,
            revenue=10.0,
        )
    )
    store.append_metrics_snapshot(
        PostMetricsSnapshot(
            post_id=p3.id,
            target_id="tgt_low",
            platform="youtube",
            views=400,
            likes=10,
            comments=2,
            shares=1,
            saves=0,
            watch_time_s=800.0,
            avg_retention_pct=25.0,
            subscribers_gained=1,
            revenue=1.0,
        )
    )

    # 4. Add mock Render Queue files for Session A
    (runs_dir / "render_job_1.req.json").write_text(
        json.dumps({"template_id": "tiktok-sales-v1", "output_name": "Sales 1"}),
        encoding="utf-8",
    )
    (runs_dir / "render_job_2.req.json").write_text(
        json.dumps({"template_id": "koc-review-v1", "output_name": "Review 1"}),
        encoding="utf-8",
    )

    # 5. Add mock Idea files for Session B
    (ideas_dir / "idea_1.json").write_text(
        json.dumps({"id": "idea_1", "title": "Top Idea", "blueprint_ref": "bp_sales_hook"}),
        encoding="utf-8",
    )
    (ideas_dir / "idea_2.json").write_text(
        json.dumps({"id": "idea_2", "title": "Low Idea", "blueprint_ref": "bp_general"}),
        encoding="utf-8",
    )

    return project_id, store


def test_calculate_kpis(analytics_setup):
    project_id, store = analytics_setup
    engine = AnalyticsEngine(project_id)

    kpis = engine.calculate_kpis(time_window="all")
    assert kpis.total_views == 12400
    assert kpis.total_likes == 910
    assert kpis.follower_gain == 271
    assert kpis.post_count == 3
    # ER = (910 + 122 + 111 + 60) / 12400 * 100 = 1203 / 12400 * 100 = 9.7%
    assert round(kpis.engagement_rate, 1) == 9.7


def test_golden_hours_and_heatmap(analytics_setup):
    project_id, store = analytics_setup
    engine = AnalyticsEngine(project_id)

    heatmap = engine.calculate_golden_hours()
    assert "matrix" in heatmap
    assert len(heatmap["matrix"]) == 7  # 7 weekdays
    assert len(heatmap["matrix"][0]) == 24  # 24 hours
    assert "recommended_windows" in heatmap
    assert len(heatmap["recommended_windows"]) > 0


def test_join_creative_performance(analytics_setup):
    project_id, store = analytics_setup
    engine = AnalyticsEngine(project_id)

    creatives = engine.join_creative_performance()
    templates = creatives["templates"]
    assert len(templates) >= 2

    # tiktok-sales-v1 should be top template
    top_tpl = templates[0]
    assert top_tpl["template_id"] == "tiktok-sales-v1"
    assert top_tpl["total_views"] == 12000

    blueprints = creatives["blueprints"]
    assert len(blueprints) >= 2
    assert blueprints[0]["blueprint_ref"] == "bp_sales_hook"


def test_detect_outliers(analytics_setup):
    project_id, store = analytics_setup
    engine = AnalyticsEngine(project_id)

    outliers = engine.detect_outliers()
    top_outliers = outliers["top_outliers"]
    underperforming = outliers["underperforming"]

    # Median of [10000, 2000, 400] is 2000
    # 10000 >= 2x 2000 (ratio 5.0) -> top outlier
    assert len(top_outliers) == 1
    assert top_outliers[0]["post_id"] == "post_top"
    assert top_outliers[0]["ratio"] == 5.0

    # 400 <= 0.5x 2000 (ratio 0.2) -> underperforming
    assert len(underperforming) == 1
    assert underperforming[0]["post_id"] == "post_low"
    assert underperforming[0]["ratio"] == 0.2


def test_generate_learnings_and_recommendations(analytics_setup):
    project_id, store = analytics_setup
    engine = AnalyticsEngine(project_id)

    md = engine.generate_learnings_md()
    assert "Báo cáo Phân tích" in md
    assert "tiktok-sales-v1" in md
    assert store.learnings_file.exists()

    recs = engine.generate_recommendations_json()
    assert "priority_templates_for_session_a" in recs
    assert "tiktok-sales-v1" in recs["priority_templates_for_session_a"]
    assert store.recommendations_file.exists()


def test_manual_csv_parser():
    # Test YouTube Studio CSV format
    yt_csv = """Video title,Video publish time,Views,Watch time (hours),Subscribers,Impressions click-through rate (%)
Top Video 1,Nov 1 2026,15000,120.5,350,7.8
Second Video,Nov 2 2026,3200,25.0,40,5.2
"""
    records = ManualCollector.parse_csv(yt_csv, default_platform="youtube")
    assert len(records) == 2
    assert records[0]["title"] == "Top Video 1"
    assert records[0]["views"] == 15000
    assert records[0]["watch_time_s"] == 120.5 * 3600.0
    assert records[0]["subscribers_gained"] == 350
    assert records[0]["ctr"] == 7.8
