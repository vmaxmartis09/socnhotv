from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from socnhotv.core.api.app import app
from socnhotv.social.models import MAX_ACCOUNTS, AccountLimitExceededError, SocialAccount
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


def test_max_accounts_constant():
    assert MAX_ACCOUNTS == 10


def test_store_enforces_limit():
    store = SocialStore("test_limit_proj")
    # Add 10 accounts
    for i in range(10):
        acc = SocialAccount(
            id=f"acc_{i}",
            platform="youtube",
            handle=f"@yt_{i}",
            display_name=f"YT Channel {i}",
        )
        store.save_account(acc, enforce_limit=True)

    assert len(store.list_accounts()) == 10

    # 11th account must raise AccountLimitExceededError
    with pytest.raises(AccountLimitExceededError):
        store.save_account(
            SocialAccount(
                id="acc_11",
                platform="tiktok",
                handle="@extra",
                display_name="Extra Account",
            ),
            enforce_limit=True,
        )


def test_api_account_limit_409():
    client = TestClient(app)
    pid = "test_api_limits"

    # Create 10 accounts via API
    for i in range(10):
        res = client.post(
            f"/projects/{pid}/social/accounts",
            json={
                "id": f"acc_api_{i}",
                "platform": "tiktok" if i % 2 == 0 else "youtube",
                "handle": f"@handle_{i}",
                "display_name": f"Account {i}",
            },
        )
        assert res.status_code == 200, res.text

    # 11th account must return 409 Conflict
    res_11 = client.post(
        f"/projects/{pid}/social/accounts",
        json={
            "id": "acc_api_11",
            "platform": "instagram",
            "handle": "@overflow",
            "display_name": "Overflow Account",
        },
    )
    assert res_11.status_code == 409
    assert "Tối đa 10 tài khoản" in res_11.json()["detail"]
