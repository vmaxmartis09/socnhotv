from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from socnhotv.core.api.app import app
from socnhotv.social.models import SocialAccount
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


def test_dedupe_account_same_platform_handle():
    client = TestClient(app)
    pid = "proj_dedupe_test"
    store = SocialStore(pid)

    # 1. Add first account
    acc1 = {
        "id": "acc_1",
        "platform": "tiktok",
        "handle": "@socnhotv.official",
        "display_name": "Sóc Nhỏ TikTok Official",
    }
    res = client.post(f"/projects/{pid}/social/accounts", json=acc1)
    assert res.status_code == 200

    # 2. Add second account with SAME platform and SAME handle (case-insensitive) -> MUST fail 409
    acc2 = {
        "id": "acc_2",
        "platform": "tiktok",
        "handle": " @SocNhoTV.Official ",
        "display_name": "Sóc Nhỏ Fake Clone",
    }
    res = client.post(f"/projects/{pid}/social/accounts", json=acc2)
    assert res.status_code == 409
    assert "đã tồn tại" in res.json()["detail"].lower()

    # 3. Add same handle on DIFFERENT platform (e.g. YouTube) -> MUST succeed
    acc_yt = {
        "id": "acc_yt",
        "platform": "youtube",
        "handle": "@socnhotv.official",
        "display_name": "Sóc Nhỏ YouTube Official",
    }
    res = client.post(f"/projects/{pid}/social/accounts", json=acc_yt)
    assert res.status_code == 200
