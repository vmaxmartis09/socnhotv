from pathlib import Path
import pytest

from socnhotv.social.captions import CaptionGenerateRequest, CaptionGenerator
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
    monkeypatch.setattr("socnhotv.social.captions.project_path", fake_path)
    monkeypatch.setattr("socnhotv.workspace.paths.project_path", fake_path)


def test_caption_platform_limits_and_disclosure():
    pid = "test_captions_proj"
    generator = CaptionGenerator(pid)

    monkeypatch_ctx = {
        "id": "vid_test_1",
        "title": "Bé Sóc Nhỏ Đi Khám Răng Bác Sĩ Koala",
        "script_excerpt": "Hôm nay Sóc Bi bị sâu răng vì ăn kẹo ngọt quá nhiều. Bác sĩ Koala khuyên bé phải đánh răng sáng và tối.",
    }
    generator._get_video_context = lambda vid: monkeypatch_ctx

    req = CaptionGenerateRequest(
        video_id="vid_test_1",
        platforms=["tiktok", "youtube", "threads", "x"],
        goal="education",
        include_affiliate=True,
        affiliate_link="https://shopee.vn/banchai-soc-nho",
    )
    results = generator.generate(req)
    assert len(results) == 4

    by_plat = {r.platform: r for r in results}

    # Threads max is 500
    assert len(by_plat["threads"].caption) <= 500
    # X max is 280
    assert len(by_plat["x"].caption) <= 280
    # TikTok max is 2200
    assert len(by_plat["tiktok"].caption) <= 2200
    # YouTube title max is 100, description <= 5000
    assert len(by_plat["youtube"].title) <= 100
    assert len(by_plat["youtube"].description) <= 5000

    # Affiliate disclosure verification
    for r in results:
        assert r.disclosure_ad is True
        assert "quangcao" in r.disclosure_text.lower() or "quảng cáo" in r.disclosure_text.lower()


def test_caption_vary_per_account():
    pid = "test_captions_vary"
    store = SocialStore(pid)
    generator = CaptionGenerator(pid)

    # 3 TikTok accounts
    acc1 = SocialAccount(id="acc_tt_1", platform="tiktok", handle="@tt_one", display_name="Kênh Chính", default_hashtags=["#tag1"])
    acc2 = SocialAccount(id="acc_tt_2", platform="tiktok", handle="@tt_two", display_name="Kênh Vui Nhộn", default_hashtags=["#tag2"])
    acc3 = SocialAccount(id="acc_tt_3", platform="tiktok", handle="@tt_three", display_name="Kênh Bán Hàng", default_hashtags=["#tag3"])
    for a in [acc1, acc2, acc3]:
        store.save_account(a)

    generator._get_video_context = lambda vid: {"id": vid, "title": "Hoạt hình Sóc Nhỏ", "script_excerpt": "Nội dung vui vẻ."}

    req = CaptionGenerateRequest(
        video_id="vid_123",
        platforms=["tiktok"],
        account_ids=["acc_tt_1", "acc_tt_2", "acc_tt_3"],
        vary_per_account=True,
        goal="story",
    )
    results = generator.generate(req)
    assert len(results) == 3

    hooks = [r.hook for r in results]
    captions = [r.caption for r in results]

    # Verify that different accounts get different variations
    assert len(set(hooks)) > 1
    assert len(set(captions)) > 1
