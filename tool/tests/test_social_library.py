from pathlib import Path
import pytest
from socnhotv.social.models import Post, PostMedia, PostTarget, SocialAccount
from socnhotv.social.store import SocialStore
from socnhotv.social.video_library import VideoLibrary


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


def test_video_library_posts_by_account():
    pid = "proj_lib_test"
    store = SocialStore(pid)
    acc1 = SocialAccount(id="acc_yt", platform="youtube", handle="@yt", display_name="YT")
    acc2 = SocialAccount(id="acc_tt", platform="tiktok", handle="@tt", display_name="TT")
    store.save_account(acc1)
    store.save_account(acc2)

    # Create dummy video output
    from socnhotv.workspace.paths import project_path
    out_dir = project_path(pid, "output", ensure=True)
    v_file = out_dir / "ep01_test.mp4"
    v_file.write_bytes(b"dummy mp4 content")

    # Create post targeting acc1
    post = Post(
        id="post_ep01",
        project_id=pid,
        title="Episode 1 Test",
        media=[PostMedia(path="output/ep01_test.mp4", kind="video")],
        targets=[
            PostTarget(
                id="tgt_ep01_yt",
                account_id="acc_yt",
                platform="youtube",
                scheduled_at="2026-11-10T19:00:00+07:00",
                status="scheduled",
            )
        ],
    )
    store.save_post(post)

    lib = VideoLibrary(pid)
    items = lib.list_library()
    assert len(items) >= 1
    ep1 = next((v for v in items if "ep01" in v["id"]), None)
    assert ep1 is not None
    assert len(ep1["posts_by_account"]) == 1
    assert ep1["posts_by_account"][0]["account_id"] == "acc_yt"
    assert ep1["posts_by_account"][0]["status"] == "scheduled"

    # Test filtering by status
    scheduled_items = lib.list_library(filter_type="scheduled")
    assert any("ep01" in v["id"] for v in scheduled_items)

    unposted_items = lib.list_library(filter_type="unposted")
    assert not any("ep01" in v["id"] for v in unposted_items)

    # Test query filter
    searched = lib.list_library(q="Ep01")
    assert len(searched) >= 1
    empty_searched = lib.list_library(q="NonExistentTitle12345")
    assert len(empty_searched) == 0
