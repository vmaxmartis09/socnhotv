import json
import shutil
import tempfile
from pathlib import Path

import pytest

from socnhotv.social.migrate import migrate_legacy_publishing
from socnhotv.social.store import SocialStore


@pytest.fixture
def isolated_project(monkeypatch):
    temp_dir = Path(tempfile.mkdtemp())
    monkeypatch.setattr(
        "socnhotv.social.store.project_path",
        lambda pid, *parts, ensure=False: temp_dir / pid / Path(*parts),
    )
    monkeypatch.setattr(
        "socnhotv.social.migrate.project_path",
        lambda pid, *parts, ensure=False: temp_dir / pid / Path(*parts),
    )

    pid = "soc-nho-tv"
    pub_dir = temp_dir / pid / "publishing"
    pub_dir.mkdir(parents=True, exist_ok=True)

    # Copy real schedule.json sample
    sample_sched = {
        "channels": [
            {
                "id": "chan_yt_1",
                "name": "Sóc Nhỏ TV Official",
                "platform": "youtube",
                "connected": True,
                "defaultHashtags": ["#SocNhoTV", "#HoatHinh3D"],
                "defaultPublishHours": "19:00",
                "requireManualApproval": True,
            },
            {
                "id": "chan_tt_1",
                "name": "@socnhotv.official",
                "platform": "tiktok",
                "connected": True,
                "defaultHashtags": ["#socnhotv", "#cartoon3d"],
                "defaultPublishHours": "20:00",
                "requireManualApproval": True,
            },
        ],
        "posts": [
            {
                "id": "post_ep1_yt",
                "projectId": "soc-nho-tv",
                "title": "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu (16:9)",
                "channelId": "chan_yt_1",
                "platform": "youtube",
                "scheduledDate": "2026-11-05",
                "scheduledTime": "19:00",
                "status": "pending_approval",
                "videoUri": "content/episodes/soc-nho-sau-rang/video.mp4",
            },
            {
                "id": "post_ep1_tt",
                "projectId": "soc-nho-tv",
                "title": "Tập 1: Sóc Bi Đau Răng Vì Ăn Kẹo (Shorts 9:16)",
                "channelId": "chan_tt_1",
                "platform": "tiktok",
                "scheduledDate": "2026-11-05",
                "scheduledTime": "20:00",
                "status": "draft",
                "videoUri": "content/episodes/soc-nho-sau-rang/scenes/canh_01.mp4",
            },
        ],
    }
    with open(pub_dir / "schedule.json", "w", encoding="utf-8") as f:
        json.dump(sample_sched, f, indent=2)

    yield pid, temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_migration_and_idempotence(isolated_project):
    pid, _ = isolated_project
    res1 = migrate_legacy_publishing(pid)
    assert res1["status"] == "success"
    assert res1["migrated_accounts"] == 2
    assert res1["migrated_posts"] == 2
    assert res1["migrated_slots"] == 2

    store = SocialStore(pid)
    accounts = store.list_accounts()
    assert len(accounts) == 2
    assert any(a.id == "chan_yt_1" for a in accounts)

    posts = store.list_posts()
    assert len(posts) == 2
    yt_post = next(p for p in posts if p.id == "post_ep1_yt")
    assert yt_post.status == "pending_approval"
    assert len(yt_post.targets) == 1
    assert yt_post.targets[0].scheduled_at == "2026-11-05T19:00:00+07:00"

    slots = store.list_slots()
    assert len(slots) == 2

    # Second run without force should not duplicate
    res2 = migrate_legacy_publishing(pid)
    assert res2["status"] == "already_migrated"
    assert res2["migrated_accounts"] == 0
    assert res2["migrated_posts"] == 0

    assert len(store.list_accounts()) == 2
    assert len(store.list_posts()) == 2
