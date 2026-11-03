import asyncio

import pytest

from socnhotv.core.providers import google_provider as gp
from socnhotv.core.providers.spend_guard import SpendCapExceeded, SpendGuard
from socnhotv.core.storage.project_store import ProjectStore


def test_guard_blocks_over_cap(tmp_path):
    g = SpendGuard(tmp_path, cap_usd=5.0)
    g.reserve(3.0, "a")
    g.reserve(2.0, "b")
    with pytest.raises(SpendCapExceeded):
        g.reserve(0.01, "c")
    assert g.spent() == 5.0


def test_missing_key_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(gp, "get_repo_root", lambda: tmp_path)
    with pytest.raises(gp.MissingApiKey):
        gp.load_gemini_key()


def test_video_over_cap_fails_before_any_network(tmp_path):
    store = ProjectStore("soc-nho-tv")
    p = gp.GoogleProvider(store, SpendGuard(tmp_path, cap_usd=0.5), key="x")
    with pytest.raises(SpendCapExceeded):
        asyncio.run(p.generate_video("hi", duration_sec=8))
    assert not (tmp_path / "spend.json").exists()


def test_image_parses_response_and_counts_cost(tmp_path, monkeypatch):
    import base64

    store = ProjectStore("soc-nho-tv")
    g = SpendGuard(tmp_path, cap_usd=5.0)
    p = gp.GoogleProvider(store, g, key="x")
    png = base64.b64encode(b"\x89PNG\r\n\x1a\nFAKE").decode()

    async def fake_post(self, client, url, body):
        return {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": png}}]}}]}

    monkeypatch.setattr(gp.GoogleProvider, "_post", fake_post)
    arts = asyncio.run(p.generate_images("x", n=2))
    assert len(arts) == 2 and arts[0].provenance.provider == "google"
    assert abs(g.spent() - 2 * gp.IMAGE_COST_USD) < 1e-9
