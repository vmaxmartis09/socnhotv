import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from socnhotv.social.models import (
    DEFAULT_TZ,
    Post,
    PostApproval,
    PostTarget,
    PostingWindow,
    SocialAccount,
)
from socnhotv.social.service import InvalidStateTransitionError, SocialService


@pytest.fixture
def service_fixture(monkeypatch):
    temp_dir = Path(tempfile.mkdtemp())
    monkeypatch.setattr(
        "socnhotv.social.store.project_path",
        lambda pid, *parts, ensure=False: temp_dir / pid / Path(*parts),
    )
    monkeypatch.setattr(
        "socnhotv.social.service.project_path",
        lambda pid, *parts, ensure=False: temp_dir / pid / Path(*parts),
    )

    pid = "test-project"
    svc = SocialService(pid)

    # Setup 1 test account
    acc = SocialAccount(
        id="acc_tiktok_1",
        platform="tiktok",
        handle="@socnhotv",
        display_name="Sóc Nhỏ TikTok",
        posting_windows=[
            PostingWindow(weekday=w, start="19:00", end="21:00")
            for w in range(7)
        ],
        daily_limit=3,
        default_hashtags=["#socnho", "#hoathinh"],
        default_caption_footer="Theo dõi kênh nhé!",
    )
    svc.store.save_account(acc)

    yield svc, acc
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_post_lifecycle_flow(service_fixture):
    svc, acc = service_fixture

    post = Post(
        id="p1",
        project_id="test-project",
        title="Tập thử nghiệm",
        status="draft",
        targets=[PostTarget(id="t1", account_id=acc.id, platform="tiktok", status="draft")],
    )
    svc.store.save_post(post)

    # Cannot jump from draft to scheduled directly without approval
    with pytest.raises(InvalidStateTransitionError):
        svc.schedule("p1", {"t1": "2026-11-06T19:00:00+07:00"})

    # 1. Submit for approval
    p_submitted = svc.submit_for_approval("p1", actor="editor_1", note="Please review")
    assert p_submitted.status == "pending_approval"
    assert p_submitted.targets[0].status == "pending_approval"

    # 2. Approve
    p_approved = svc.approve("p1", actor="admin_chief", note="Looks good!")
    assert p_approved.status == "approved"
    assert p_approved.approval.by == "admin_chief"
    assert p_approved.targets[0].status == "approved"

    # 3. Schedule
    p_scheduled = svc.schedule("p1", {"t1": "2026-11-06T19:00:00+07:00"})
    assert p_scheduled.status == "scheduled"
    assert p_scheduled.targets[0].status == "scheduled"
    assert p_scheduled.targets[0].scheduled_at == "2026-11-06T19:00:00+07:00"

    # 4. Drag & drop time update
    p_rescheduled = svc.update_target_time("p1", "t1", "2026-11-06T20:30:00+07:00")
    assert p_rescheduled.targets[0].scheduled_at == "2026-11-06T20:30:00+07:00"


def test_rejection_flow(service_fixture):
    svc, acc = service_fixture
    post = Post(
        id="p_rej",
        project_id="test-project",
        title="Bài lỗi",
        status="draft",
        targets=[PostTarget(id="t_rej", account_id=acc.id, platform="tiktok", status="draft")],
    )
    svc.store.save_post(post)
    svc.submit_for_approval("p_rej")

    # Reject
    p_rejected = svc.reject("p_rej", actor="boss", reason="Audio too quiet")
    assert p_rejected.status == "draft"
    assert "Audio too quiet" in (p_rejected.approval.note or "")


def test_cannot_reschedule_published_target(service_fixture):
    svc, acc = service_fixture
    post = Post(
        id="p_pub",
        project_id="test-project",
        title="Bài đã đăng",
        status="published",
        targets=[PostTarget(id="t_pub", account_id=acc.id, platform="tiktok", status="published")],
    )
    svc.store.save_post(post)

    with pytest.raises(InvalidStateTransitionError):
        svc.update_target_time("p_pub", "t_pub", "2026-11-07T19:00:00+07:00")


def test_suggest_time_conflict_avoidance(service_fixture):
    svc, acc = service_fixture

    base_date = datetime(2026, 11, 10, 12, 0, tzinfo=DEFAULT_TZ)

    # First suggestion
    suggested_1 = svc.suggest_time(acc.id, after=base_date)
    dt1 = datetime.fromisoformat(suggested_1)
    assert dt1.hour == 19
    assert dt1.minute == 0

    # Book this slot
    p_book = Post(
        id="p_book",
        project_id="test-project",
        title="Slot 1",
        status="scheduled",
        targets=[PostTarget(id="t_b", account_id=acc.id, platform="tiktok", status="scheduled", scheduled_at=suggested_1)],
    )
    svc.store.save_post(p_book)

    # Next suggestion should not collide (< 2h away) on the same day if window only has 19:00 or it finds next available slot
    suggested_2 = svc.suggest_time(acc.id, after=base_date)
    dt2 = datetime.fromisoformat(suggested_2)
    # Must be at least 2 hours away or on next day
    assert abs((dt2 - dt1).total_seconds()) >= 7200


def test_caption_variants_generation(service_fixture):
    svc, _ = service_fixture
    res = svc.generate_caption_variants(
        title="Sóc Nhỏ Đi Học",
        caption="Tập mới siêu vui nhộn về ngày đầu đến trường.",
        hashtags=["socnho", "cartoontiktok"],
        platforms=["tiktok", "youtube"],
        product_link="https://shop.tiktok.com/p/123",
        footer="Hotline hỗ trợ: 1900xxxx",
    )
    assert "tiktok" in res
    assert "youtube" in res

    tt = res["tiktok"]
    assert "#affiliate" in tt["caption"]
    assert tt["disclosure_ad"] is True
    assert "#socnho" in tt["caption"]

    yt = res["youtube"]
    assert yt["title"] == "Sóc Nhỏ Đi Học"
    assert "https://shop.tiktok.com/p/123" in yt["description"]
    assert "Hotline" in yt["description"]
