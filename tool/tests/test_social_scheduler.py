import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from socnhotv.social.models import DEFAULT_TZ, Post, PostApproval, PostMedia, PostTarget, SocialAccount
from socnhotv.social.scheduler import SocialScheduler


@pytest.fixture
def sched_fixture(monkeypatch):
    temp_dir = Path(tempfile.mkdtemp())
    monkeypatch.setattr(
        "socnhotv.social.store.project_path",
        lambda pid, *parts, ensure=False: temp_dir / pid / Path(*parts),
    )
    monkeypatch.setattr(
        "socnhotv.social.scheduler.project_path",
        lambda pid, *parts, ensure=False: temp_dir / pid / Path(*parts),
    )
    monkeypatch.setattr(
        "socnhotv.social.adapters.manual.project_path",
        lambda pid, *parts, ensure=False: temp_dir / pid / Path(*parts),
    )

    pid = "test-sched-project"
    sched = SocialScheduler(pid)

    acc = SocialAccount(
        id="acc_manual_1",
        platform="youtube",
        handle="@chan",
        display_name="Kênh test",
        auth={"mode": "manual"},
    )
    sched.store.save_account(acc)

    yield sched, acc, temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_scheduler_timing_and_approval(sched_fixture):
    sched, acc, _ = sched_fixture

    now_base = datetime(2026, 11, 10, 19, 0, tzinfo=DEFAULT_TZ)

    # Post 1: In future (scheduled at 19:30) -> should NOT publish
    p_future = Post(
        id="p_future",
        project_id="test-sched-project",
        title="Bài tương lai",
        status="scheduled",
        targets=[
            PostTarget(
                id="t_future",
                account_id=acc.id,
                platform="youtube",
                scheduled_at="2026-11-10T19:30:00+07:00",
                status="scheduled",
            )
        ],
    )
    sched.store.save_post(p_future)

    # Post 2: Ready for now (scheduled at 18:55), but approval required and status is draft -> should NOT publish
    p_unapproved = Post(
        id="p_unapproved",
        project_id="test-sched-project",
        title="Bài chưa duyệt",
        status="draft",
        approval=PostApproval(required=True),
        targets=[
            PostTarget(
                id="t_unapp",
                account_id=acc.id,
                platform="youtube",
                scheduled_at="2026-11-10T18:55:00+07:00",
                status="scheduled",
            )
        ],
    )
    sched.store.save_post(p_unapproved)

    # Post 3: Ready for now (18:50), approved & scheduled -> SHOULD publish
    p_ready = Post(
        id="p_ready",
        project_id="test-sched-project",
        title="Bài xuất bản ngay",
        status="scheduled",
        approval=PostApproval(required=True, by="boss"),
        targets=[
            PostTarget(
                id="t_ready",
                account_id=acc.id,
                platform="youtube",
                scheduled_at="2026-11-10T18:50:00+07:00",
                status="scheduled",
            )
        ],
    )
    sched.store.save_post(p_ready)

    # Run tick with now_base (19:00)
    results = sched.tick(now_dt=now_base)

    assert len(results) == 1
    assert results[0]["post_id"] == "p_ready"
    assert results[0]["status"] == "published"

    # Verify storage updates
    post_check = sched.store.get_post("p_ready")
    assert post_check is not None
    assert post_check.status == "published"
    assert post_check.targets[0].status == "published"

    # Heartbeat file exists
    assert sched.get_heartbeat() is not None
