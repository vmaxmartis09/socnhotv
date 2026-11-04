from datetime import datetime, timedelta
from pathlib import Path
import pytest

from socnhotv.social.models import DEFAULT_TZ, Post, PostTarget, SocialAccount
from socnhotv.social.queue import get_social_queue
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
    monkeypatch.setattr("socnhotv.social.queue.project_path", fake_path)
    monkeypatch.setattr("socnhotv.workspace.paths.project_path", fake_path)


def test_queue_upcoming_excludes_past():
    pid = "test_queue_proj"
    store = SocialStore(pid)

    acc = SocialAccount(id="acc_q", platform="youtube", handle="@yt_q", display_name="YT Queue")
    store.save_account(acc)

    now_dt = datetime.now(DEFAULT_TZ)

    # 1. Past post (overdue: not published, scheduled_at 2 days ago)
    past_time = (now_dt - timedelta(days=2)).isoformat()
    post_past = Post(
        id="post_past",
        project_id=pid,
        title="Old Post",
        status="scheduled",
        targets=[
            PostTarget(
                id="tgt_past",
                account_id="acc_q",
                platform="youtube",
                scheduled_at=past_time,
                status="scheduled",
            )
        ],
    )
    store.save_post(post_past)

    # 2. Future post (upcoming: scheduled_at tomorrow)
    future_time = (now_dt + timedelta(days=1)).isoformat()
    post_future = Post(
        id="post_future",
        project_id=pid,
        title="Upcoming Post",
        status="scheduled",
        targets=[
            PostTarget(
                id="tgt_future",
                account_id="acc_q",
                platform="youtube",
                scheduled_at=future_time,
                status="scheduled",
            )
        ],
    )
    store.save_post(post_future)

    # 3. Published post
    post_published = Post(
        id="post_pub",
        project_id=pid,
        title="Done Post",
        status="published",
        targets=[
            PostTarget(
                id="tgt_pub",
                account_id="acc_q",
                platform="youtube",
                scheduled_at=past_time,
                status="published",
                published_at=past_time,
            )
        ],
    )
    store.save_post(post_published)

    # Query 'upcoming' bucket
    q_upcoming = get_social_queue(pid, bucket="upcoming")
    target_ids_upcoming = [item.target_id for item in q_upcoming.items]
    assert "tgt_future" in target_ids_upcoming
    assert "tgt_past" not in target_ids_upcoming  # Past MUST NOT be in upcoming!
    assert "tgt_pub" not in target_ids_upcoming

    # Query 'overdue' bucket
    q_overdue = get_social_queue(pid, bucket="overdue")
    target_ids_overdue = [item.target_id for item in q_overdue.items]
    assert "tgt_past" in target_ids_overdue
    assert "tgt_future" not in target_ids_overdue

    # Check summary counts
    assert q_upcoming.summary.upcoming_count == 1
    assert q_upcoming.summary.overdue_count == 1
    assert q_upcoming.summary.published_count == 1
    assert q_upcoming.summary.accounts_count == 1
    assert q_upcoming.summary.max_accounts == 10
