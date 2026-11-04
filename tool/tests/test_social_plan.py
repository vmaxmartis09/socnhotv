from datetime import datetime, timedelta
from pathlib import Path
import pytest

from socnhotv.social.models import DEFAULT_TZ, PostingWindow, SocialAccount
from socnhotv.social.planner import (
    PlanCommitRequest,
    PlanPreviewRequest,
    SocialPlanner,
    TargetCommitSpec,
)
from socnhotv.social.store import SocialStore


@pytest.fixture(autouse=True)
def isolate_project_path(tmp_path, monkeypatch):
    def fake_path(pid, *parts, **kw):
        p = tmp_path / pid / Path(*parts) if parts else tmp_path / pid
        if kw.get("ensure"):
            p.mkdir(parents=True, exist_ok=True)
        return p

    monkeypatch.setattr("socnhotv.social.store.project_path", fake_path)
    monkeypatch.setattr("socnhotv.social.video_library.project_path", fake_path)
    monkeypatch.setattr("socnhotv.workspace.paths.project_path", fake_path)


def test_auto_schedule_no_past_and_timezone(monkeypatch):
    pid = "test_plan_proj"
    store = SocialStore(pid)
    planner = SocialPlanner(pid)

    # Create account with windows
    acc = SocialAccount(
        id="acc_yt_main",
        platform="youtube",
        handle="@yt_main",
        display_name="YouTube Main",
        posting_windows=[
            PostingWindow(weekday=0, start="19:00", end="21:00"),
            PostingWindow(weekday=1, start="19:00", end="21:00"),
        ],
        daily_limit=3,
        min_gap_minutes=120,
    )
    store.save_account(acc)

    # Mock video in library
    monkeypatch.setattr(
        planner.library,
        "list_videos",
        lambda: [
            {"id": "vid_1", "title": "Episode 1", "variants": {"youtube": "out/ep1.mp4"}, "primary_path": "out/ep1.mp4", "duration_s": 45.0, "size_mb": 10.0},
            {"id": "vid_2", "title": "Episode 2", "variants": {"youtube": "out/ep2.mp4"}, "primary_path": "out/ep2.mp4", "duration_s": 50.0, "size_mb": 12.0},
        ],
    )

    # Request with past date
    past_iso = "2026-01-01T10:00:00+07:00"
    req = PlanPreviewRequest(
        video_ids=["vid_1", "vid_2"],
        account_ids=["acc_yt_main"],
        strategy="auto",
        start_at=past_iso,
    )
    planned = planner.preview_plan(req)
    assert len(planned) == 2

    now_dt = datetime.now(DEFAULT_TZ)
    for p in planned:
        sched_dt = datetime.fromisoformat(p.scheduled_at)
        # Sched time must be in future (>= now)
        assert sched_dt >= now_dt - timedelta(seconds=10)
        # Timezone must be Asia/Ho_Chi_Minh (+07:00)
        assert sched_dt.tzinfo is not None
        assert sched_dt.utcoffset() == timedelta(hours=7)


def test_auto_schedule_min_gap_between_posts(monkeypatch):
    pid = "test_plan_gap"
    store = SocialStore(pid)
    planner = SocialPlanner(pid)

    acc = SocialAccount(
        id="acc_tt_gap",
        platform="tiktok",
        handle="@tt_gap",
        display_name="TikTok Gap",
        daily_limit=5,
        min_gap_minutes=120,  # 2 hours minimum
    )
    store.save_account(acc)

    monkeypatch.setattr(
        planner.library,
        "list_videos",
        lambda: [
            {"id": "v1", "title": "V1", "variants": {"tiktok": "out/v1.mp4"}, "primary_path": "out/v1.mp4"},
            {"id": "v2", "title": "V2", "variants": {"tiktok": "out/v2.mp4"}, "primary_path": "out/v2.mp4"},
        ],
    )

    tomorrow = (datetime.now(DEFAULT_TZ) + timedelta(days=1)).strftime("%Y-%m-%d")
    req = PlanPreviewRequest(
        video_ids=["v1", "v2"],
        account_ids=["acc_tt_gap"],
        strategy="auto",
        start_at=f"{tomorrow}T10:00:00+07:00",
    )
    planned = planner.preview_plan(req)
    assert len(planned) == 2

    t1 = datetime.fromisoformat(planned[0].scheduled_at)
    t2 = datetime.fromisoformat(planned[1].scheduled_at)
    # The gap between post 1 and post 2 on same day must be >= 120 mins
    gap_minutes = abs((t2 - t1).total_seconds()) / 60.0
    assert gap_minutes >= 120.0


def test_quota_pushing_to_next_day(monkeypatch):
    pid = "test_plan_quota"
    store = SocialStore(pid)
    planner = SocialPlanner(pid)

    # YouTube daily_quota_limit is 6 in platform_rules
    acc = SocialAccount(
        id="acc_yt_quota",
        platform="youtube",
        handle="@yt_quota",
        display_name="YT Quota Channel",
        daily_limit=10,  # account allows up to 10, but YouTube platform rule allows 6
    )
    store.save_account(acc)

    videos = [{"id": f"vid_{i}", "title": f"Video {i}", "variants": {"youtube": f"out/{i}.mp4"}, "primary_path": f"out/{i}.mp4"} for i in range(8)]
    monkeypatch.setattr(planner.library, "list_videos", lambda: videos)

    tomorrow = (datetime.now(DEFAULT_TZ) + timedelta(days=2)).strftime("%Y-%m-%d")
    req = PlanPreviewRequest(
        video_ids=[v["id"] for v in videos],
        account_ids=["acc_yt_quota"],
        strategy="auto",
        start_at=f"{tomorrow}T09:00:00+07:00",
    )
    planned = planner.preview_plan(req)
    assert len(planned) == 8

    # Posts 0..5 should be on tomorrow, posts 6..7 pushed to day after tomorrow
    dates = [datetime.fromisoformat(p.scheduled_at).date() for p in planned]
    assert len(set(dates)) >= 2
    # Verify quota_pushed warning on the pushed targets
    pushed_issues = [issue for p in planned[6:] for issue in p.issues if issue.code == "quota_pushed"]
    assert len(pushed_issues) >= 1


def test_commit_plan(monkeypatch):
    pid = "test_plan_commit"
    store = SocialStore(pid)
    planner = SocialPlanner(pid)

    acc = SocialAccount(id="acc_1", platform="tiktok", handle="@tt1", display_name="TikTok 1")
    store.save_account(acc)

    monkeypatch.setattr(
        planner.library,
        "list_videos",
        lambda: [{"id": "v1", "title": "Commit Video", "variants": {}, "primary_path": "out/v1.mp4"}],
    )

    commit_req = PlanCommitRequest(
        targets=[
            TargetCommitSpec(
                video_id="v1",
                account_id="acc_1",
                scheduled_at="2026-11-10T20:00:00+07:00",
                caption="Custom caption for test",
                hashtags=["#test"],
            )
        ],
        approval_required=True,
    )
    res = planner.commit_plan(commit_req)
    assert res["created_posts_count"] == 1
    assert res["created_targets_count"] == 1

    saved_posts = store.list_posts()
    assert len(saved_posts) == 1
    assert saved_posts[0].targets[0].caption == "Custom caption for test"
    assert saved_posts[0].approval.required is True
