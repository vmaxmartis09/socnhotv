import concurrent.futures
import shutil
import tempfile
from pathlib import Path

import pytest

from socnhotv.social.models import CalendarNote, Post, PostTarget, RecurringSlot, SocialAccount
from socnhotv.social.store import SocialStore


@pytest.fixture
def temp_store(monkeypatch):
    temp_dir = Path(tempfile.mkdtemp())
    # Monkeypatch project_path so SocialStore uses isolated test dir
    monkeypatch.setattr(
        "socnhotv.social.store.project_path",
        lambda pid, *parts, ensure=False: temp_dir / pid / Path(*parts),
    )
    store = SocialStore("test-project")
    yield store
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_accounts_crud(temp_store: SocialStore):
    acc = SocialAccount(
        platform="youtube",
        handle="@testchannel",
        display_name="Test YT Channel",
    )
    saved = temp_store.save_account(acc)
    assert saved.id == acc.id

    fetched = temp_store.get_account(acc.id)
    assert fetched is not None
    assert fetched.handle == "@testchannel"

    fetched.display_name = "Updated Title"
    temp_store.save_account(fetched)

    updated = temp_store.get_account(acc.id)
    assert updated.display_name == "Updated Title"

    assert temp_store.delete_account(acc.id) is True
    assert temp_store.get_account(acc.id) is None


def test_posts_crud_and_query(temp_store: SocialStore):
    target_yt = PostTarget(account_id="acc_yt", platform="youtube", status="draft")
    post = Post(
        project_id="test-project",
        title="Video review",
        targets=[target_yt],
    )
    temp_store.save_post(post)

    assert temp_store.get_post(post.id) is not None
    assert len(temp_store.list_posts(platform="youtube")) == 1
    assert len(temp_store.list_posts(platform="tiktok")) == 0
    assert len(temp_store.list_posts(q="review")) == 1
    assert len(temp_store.list_posts(q="unrelated")) == 0


def test_concurrent_writes(temp_store: SocialStore):
    """Test concurrent multi-threaded writes without file corruption."""
    def worker(idx: int):
        acc = SocialAccount(
            id=f"acc_worker_{idx}",
            platform="tiktok",
            handle=f"@worker_{idx}",
            display_name=f"Worker {idx}",
        )
        temp_store.save_account(acc)

        post = Post(
            id=f"post_worker_{idx}",
            project_id="test-project",
            title=f"Concurrent Post {idx}",
            targets=[PostTarget(account_id=acc.id, platform="tiktok")],
        )
        temp_store.save_post(post)
        temp_store.append_audit("worker", "save", post.id, note=f"worker {idx}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker, i) for i in range(24)]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    accounts = temp_store.list_accounts()
    assert len(accounts) == 24
    posts = temp_store.list_posts()
    assert len(posts) == 24
    audit = temp_store.get_audit_log(limit=100)
    assert len(audit) == 24
