import json
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from socnhotv.core.api.routes.social import router as social_router
from socnhotv.social.models import SocialAccount


@pytest.fixture
def client_fixture(monkeypatch):
    temp_dir = Path(tempfile.mkdtemp())
    monkeypatch.setattr(
        "socnhotv.social.store.project_path",
        lambda pid, *parts, ensure=False: temp_dir / pid / Path(*parts),
    )
    monkeypatch.setattr(
        "socnhotv.social.service.project_path",
        lambda pid, *parts, ensure=False: temp_dir / pid / Path(*parts),
    )
    monkeypatch.setattr(
        "socnhotv.social.migrate.project_path",
        lambda pid, *parts, ensure=False: temp_dir / pid / Path(*parts),
    )
    monkeypatch.setattr(
        "socnhotv.social.contracts.project_path",
        lambda pid, *parts, ensure=False: temp_dir / pid / Path(*parts),
    )

    app = FastAPI()
    app.include_router(social_router)
    client = TestClient(app)

    pid = "test-project"
    yield client, pid, temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_ping(client_fixture):
    client, _, _ = client_fixture
    res = client.get("/social/_ping")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "module": "social"}


def test_accounts_api(client_fixture):
    client, pid, _ = client_fixture
    # Create account
    acc_payload = {
        "id": "acc_tt_1",
        "platform": "tiktok",
        "handle": "@test_socnho",
        "display_name": "Test Sóc Nhỏ TikTok",
        "status": "connected",
        "default_hashtags": ["#socnho"],
        "posting_windows": [{"weekday": 0, "start": "19:00", "end": "21:00"}],
    }
    res = client.post(f"/projects/{pid}/social/accounts", json=acc_payload)
    assert res.status_code == 200
    assert res.json()["id"] == "acc_tt_1"

    # List accounts
    res = client.get(f"/projects/{pid}/social/accounts")
    assert res.status_code == 200
    accounts = res.json()
    assert len(accounts) == 1
    assert accounts[0]["handle"] == "@test_socnho"


def test_post_full_lifecycle_api(client_fixture):
    client, pid, _ = client_fixture

    # 1. Create post draft via /posts/draft
    draft_res = client.post(
        f"/projects/{pid}/social/posts/draft",
        json={
            "media_path": "content/video.mp4",
            "title": "Tập 1: Sóc Nhỏ Khám Răng",
            "caption": "Cùng xem tập mới nhé",
            "platforms": ["tiktok", "youtube"],
        },
    )
    assert draft_res.status_code == 200
    post = draft_res.json()
    post_id = post["id"]
    assert post["status"] == "draft"
    assert len(post["targets"]) == 2
    target_tt = next(t for t in post["targets"] if t["platform"] == "tiktok")

    # 2. Try schedule directly (should fail 409 because not approved)
    sched_fail = client.post(
        f"/projects/{pid}/social/posts/{post_id}/schedule",
        json={"targets": {target_tt["id"]: "2026-11-08T19:00:00+07:00"}},
    )
    assert sched_fail.status_code == 409

    # 3. Submit
    submit_res = client.post(
        f"/projects/{pid}/social/posts/{post_id}/submit",
        json={"actor": "editor", "note": "Check please"},
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "pending_approval"

    # 4. Approve
    approve_res = client.post(
        f"/projects/{pid}/social/posts/{post_id}/approve",
        json={"actor": "lead", "note": "Approved for 19:00"},
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"

    # 5. Schedule
    sched_ok = client.post(
        f"/projects/{pid}/social/posts/{post_id}/schedule",
        json={"targets": {target_tt["id"]: "2026-11-08T19:00:00+07:00"}},
    )
    assert sched_ok.status_code == 200
    assert sched_ok.json()["status"] == "scheduled"

    # 6. Drag & drop time update
    move_res = client.put(
        f"/projects/{pid}/social/posts/{post_id}/targets/{target_tt['id']}/time",
        json={"time": "2026-11-08T20:00:00+07:00"},
    )
    assert move_res.status_code == 200
    updated_targets = move_res.json()["targets"]
    moved_target = next(t for t in updated_targets if t["id"] == target_tt["id"])
    assert moved_target["scheduled_at"] == "2026-11-08T20:00:00+07:00"

    # 7. Check calendar endpoint
    cal_res = client.get(f"/projects/{pid}/social/calendar?from=2026-11-01&to=2026-11-30")
    assert cal_res.status_code == 200
    cal_data = cal_res.json()
    assert len(cal_data["items"]) >= 1
    assert any(item["post_id"] == post_id for item in cal_data["items"])


def test_suggest_time_and_variants(client_fixture):
    client, pid, _ = client_fixture
    # Create an account
    client.post(
        f"/projects/{pid}/social/accounts",
        json={
            "id": "acc_sug_1",
            "platform": "youtube",
            "handle": "@yt",
            "display_name": "YT",
            "posting_windows": [{"weekday": 1, "start": "19:00", "end": "20:00"}],
        },
    )

    # Suggest time
    sug_res = client.post(
        f"/projects/{pid}/social/suggest-time",
        json={"account_id": "acc_sug_1"},
    )
    assert sug_res.status_code == 200
    assert "suggested_time" in sug_res.json()

    # Caption variants
    var_res = client.post(
        f"/projects/{pid}/social/caption-variants",
        json={
            "title": "Tập 2: Sóc Nhỏ",
            "caption": "Mô tả tập 2",
            "hashtags": ["socnho"],
            "platforms": ["tiktok", "youtube"],
            "product_link": "https://aff.link/123",
        },
    )
    assert var_res.status_code == 200
    variants = var_res.json()["variants"]
    assert "tiktok" in variants
    assert "youtube" in variants
