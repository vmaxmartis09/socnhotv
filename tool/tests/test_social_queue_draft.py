from pathlib import Path
from datetime import datetime, timedelta
import pytest
from socnhotv.social.models import DEFAULT_TZ, Post, PostMedia, PostTarget, SocialAccount
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


def test_queue_draft_isolation_and_upcoming():
    pid = "proj_queue_draft_test"
    store = SocialStore(pid)
    acc = SocialAccount(id="acc_yt", platform="youtube", handle="@yt", display_name="YT")
    store.save_account(acc)

    now_dt = datetime.now(DEFAULT_TZ)
    future_iso = (now_dt + timedelta(hours=3)).isoformat()
    past_iso = (now_dt - timedelta(hours=3)).isoformat()

    # Draft post without scheduled_at
    post_draft = Post(
        id="post_draft",
        project_id=pid,
        title="Draft Video",
        media=[PostMedia(path="dummy.mp4")],
        targets=[
            PostTarget(
                id="tgt_draft",
                account_id="acc_yt",
                platform="youtube",
                scheduled_at=None,
                status="draft",
            )
        ],
    )
    store.save_post(post_draft)

    # Upcoming post with future scheduled_at
    post_upcoming = Post(
        id="post_upcoming",
        project_id=pid,
        title="Upcoming Video",
        media=[PostMedia(path="dummy.mp4")],
        targets=[
            PostTarget(
                id="tgt_upcoming",
                account_id="acc_yt",
                platform="youtube",
                scheduled_at=future_iso,
                status="scheduled",
            )
        ],
    )
    store.save_post(post_upcoming)

    # Overdue post with past scheduled_at
    post_overdue = Post(
        id="post_overdue",
        project_id=pid,
        title="Overdue Video",
        media=[PostMedia(path="dummy.mp4")],
        targets=[
            PostTarget(
                id="tgt_overdue",
                account_id="acc_yt",
                platform="youtube",
                scheduled_at=past_iso,
                status="scheduled",
            )
        ],
    )
    store.save_post(post_overdue)

    # Query upcoming: MUST NOT contain tgt_draft, MUST only contain tgt_upcoming
    q_upcoming = get_social_queue(pid, bucket="upcoming")
    assert len(q_upcoming.items) == 1
    assert q_upcoming.items[0].target_id == "tgt_upcoming"

    # Query draft: MUST contain tgt_draft
    q_draft = get_social_queue(pid, bucket="draft")
    assert len(q_draft.items) == 1
    assert q_draft.items[0].target_id == "tgt_draft"

    # Query overdue: MUST contain tgt_overdue
    q_overdue = get_social_queue(pid, bucket="overdue")
    assert len(q_overdue.items) == 1
    assert q_overdue.items[0].target_id == "tgt_overdue"

    # Check summary counts
    assert q_upcoming.summary.upcoming_count == 1
    assert q_upcoming.summary.draft_count == 1
    assert q_upcoming.summary.overdue_count == 1
