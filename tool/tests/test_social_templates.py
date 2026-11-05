from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from socnhotv.core.api.app import app
from socnhotv.social.models import ContentTemplate
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


def test_templates_crud():
    client = TestClient(app)
    pid = "proj_tpl_test"
    store = SocialStore(pid)

    # 1. Create template via API
    payload = {
        "id": "tpl_test_sales",
        "name": "Mẫu Bán Hàng Trẻ Em",
        "purpose": "sales",
        "platforms": ["tiktok", "facebook"],
        "caption_hook": "Bé thích mê đồ chơi này!",
        "caption_body": "Chi tiết trong clip...",
        "caption_cta": "Bấm vào link bên dưới nha",
        "hashtags": ["#dochoi", "#socnho"],
        "first_comment": "Link mua tại bình luận này nha cả nhà",
        "disclosure": "#quangcao",
    }
    res = client.post(f"/projects/{pid}/social/templates", json=payload)
    assert res.status_code == 200
    created = res.json()
    assert created["id"] == "tpl_test_sales"
    assert created["name"] == "Mẫu Bán Hàng Trẻ Em"

    # 2. List templates
    res = client.get(f"/projects/{pid}/social/templates")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["id"] == "tpl_test_sales"

    # 3. Update template
    res = client.put(
        f"/projects/{pid}/social/templates/tpl_test_sales",
        json={**payload, "name": "Mẫu Bán Hàng Trẻ Em (Cập nhật)"},
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Mẫu Bán Hàng Trẻ Em (Cập nhật)"

    # 4. Delete template
    res = client.delete(f"/projects/{pid}/social/templates/tpl_test_sales")
    assert res.status_code == 200
    assert res.json()["status"] == "deleted"

    # 5. List after delete
    res = client.get(f"/projects/{pid}/social/templates")
    assert res.status_code == 200
    assert len(res.json()) == 0
