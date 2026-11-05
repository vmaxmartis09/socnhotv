from pathlib import Path
import pytest
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
    pid = "proj_tpl_test"
    store = SocialStore(pid)

    # 1. Create template
    tmpl = ContentTemplate(
        id="tpl_test_sales",
        name="Mẫu Bán Hàng Trẻ Em",
        purpose="sales",
        platforms=["tiktok", "facebook"],
        caption_hook="Bé thích mê đồ chơi này!",
        caption_body="Chi tiết trong clip...",
        caption_cta="Bấm vào link bên dưới nha",
        hashtags=["#dochoi", "#socnho"],
        first_comment="Link mua tại bình luận này nha cả nhà",
        disclosure="#quangcao",
    )
    saved = store.save_template(tmpl)
    assert saved.id == "tpl_test_sales"
    assert saved.name == "Mẫu Bán Hàng Trẻ Em"

    # 2. List templates
    items = store.list_templates()
    assert len(items) == 1
    assert items[0].id == "tpl_test_sales"

    # 3. Update template
    saved.name = "Mẫu Bán Hàng Trẻ Em (Cập nhật)"
    updated = store.save_template(saved)
    assert updated.name == "Mẫu Bán Hàng Trẻ Em (Cập nhật)"

    # 4. Delete template
    deleted = store.delete_template("tpl_test_sales")
    assert deleted is True

    # 5. List after delete
    items_after = store.list_templates()
    assert len(items_after) == 0
