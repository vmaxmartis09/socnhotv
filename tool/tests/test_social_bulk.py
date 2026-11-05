from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from socnhotv.core.api.app import app
from socnhotv.social.models import Post, PostMedia, PostTarget, SocialAccount
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


def test_bulk_targets_actions():
    client = TestClient(app)
    pid = "proj_bulk_test"
    store = SocialStore(pid)

    acc1 = SocialAccount(id="acc_yt", platform="youtube", handle="@yt", display_name="YT")
    acc2 = SocialAccount(id="acc_tt", platform="tiktok", handle="@tt", display_name="TT")
    store.save_account(acc1)
    store.save_account(acc2)

    post1 = Post(
        id="post_1",
        project_id=pid,
        title="Post 1",
        media=[PostMedia(path="dummy.mp4")],
        targets=[
            PostTarget(
                id="tgt_1",
                account_id="acc_yt",
                platform="youtube",
                scheduled_at="2026-11-10T10:00:00+07:00",
                status="pending_approval",
            ),
            PostTarget(
                id="tgt_2",
                account_id="acc_yt",
                platform="youtube",
                scheduled_at="2026-11-10T12:00:00+07:00",
                status="failed",
                last_error="Upload timeout",
            ),
        ],
    )
    store.save_post(post1)

    # 1. Bulk approve
    res = client.post(
        f"/projects/{pid}/social/targets/bulk",
        json={"ids": ["tgt_1"], "action": "approve"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["results"][0]["success"] is True
    p = store.get_post("post_1")
    t1 = next(t for t in p.targets if t.id == "tgt_1")
    assert t1.status == "scheduled"

    # 2. Bulk reschedule (+1 day)
    res = client.post(
        f"/projects/{pid}/social/targets/bulk",
        json={"ids": ["tgt_1"], "action": "reschedule", "params": {"shift_days": 1}},
    )
    assert res.status_code == 200
    p = store.get_post("post_1")
    t1 = next(t for t in p.targets if t.id == "tgt_1")
    assert "2026-11-11" in t1.scheduled_at

    # 3. Bulk duplicate to acc2
    res = client.post(
        f"/projects/{pid}/social/targets/bulk",
        json={"ids": ["tgt_1"], "action": "duplicate_to", "params": {"account_id": "acc_tt"}},
    )
    assert res.status_code == 200
    p = store.get_post("post_1")
    assert len(p.targets) == 3
    tt_target = next(t for t in p.targets if t.account_id == "acc_tt")
    assert tt_target.platform == "tiktok"
    assert tt_target.status == "draft"

    # 4. Bulk retry failed
    res = client.post(
        f"/projects/{pid}/social/targets/bulk",
        json={"ids": ["tgt_2"], "action": "retry"},
    )
    assert res.status_code == 200
    p = store.get_post("post_1")
    t2 = next(t for t in p.targets if t.id == "tgt_2")
    assert t2.status == "scheduled"
    assert t2.last_error is None

    # 5. Bulk cancel
    res = client.post(
        f"/projects/{pid}/social/targets/bulk",
        json={"ids": ["tgt_1"], "action": "cancel"},
    )
    assert res.status_code == 200
    p = store.get_post("post_1")
    t1 = next(t for t in p.targets if t.id == "tgt_1")
    assert t1.status == "cancelled"
