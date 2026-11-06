"""Kiểm thử tự động cho Luồng G2 / I0: Chế độ chạy lai (RunPolicy) & Bộ định tuyến Model."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
    GraphRunRequest,
    NodeInstance,
    RunPolicy,
)
from socnhotv.core.engine.graph_runner import GraphRunner
from socnhotv.core.providers.errors import ProviderError, ProviderErrorKind
from socnhotv.core.providers.mock_provider import MockProvider
from socnhotv.core.providers.router import ProviderRouter
from socnhotv.core.storage.project_store import ProjectStore


def _make_dummy_artifact(kind: ArtifactKind = ArtifactKind.AUDIO, uri: str = "assets/dummy.mp3") -> Artifact:
    return Artifact(
        id="art_dummy_123",
        kind=kind,
        uri=uri,
        mime="audio/mpeg" if kind == ArtifactKind.AUDIO else "image/png",
        size=1024,
        hash="hash_dummy_123",
        meta=ArtifactMeta(duration=2.5 if kind == ArtifactKind.AUDIO else None),
        provenance=ArtifactProvenance(
            nodeId="dummy_node",
            runId="run_dummy",
            provider="test",
            model="test_model",
            createdAt="2026-11-06T12:00:00Z",
        ),
    )


def test_run_policy_defaults_and_backward_compatibility():
    """Hợp đồng C3: Thiếu runPolicy thì suy từ mockMode cũ (mockMode: true -> tất cả mock, TRỪ voice='local')."""
    # 1. Mặc định mockMode=True: ảnh mock, video mock, text mock, NHƯNG voice='local'
    req_mock = GraphRunRequest(projectId="soc-nho-tv", mockMode=True)
    p_mock = req_mock.resolve_run_policy()
    assert p_mock.image == "mock"
    assert p_mock.video == "mock"
    assert p_mock.text == "mock"
    assert p_mock.voice == "local"

    # 2. mockMode=False: tất cả thật
    req_real = GraphRunRequest(projectId="soc-nho-tv", mockMode=False)
    p_real = req_real.resolve_run_policy()
    assert p_real.image == "real"
    assert p_real.video == "real"
    assert p_real.text == "real"
    assert p_real.voice == "local"

    # 3. Truyền rõ runPolicy: ghi đè hoàn toàn
    custom_policy = RunPolicy(image="real", video="off", text="mock", voice="mock")
    req_custom = GraphRunRequest(projectId="soc-nho-tv", runPolicy=custom_policy)
    assert req_custom.resolve_run_policy().image == "real"
    assert req_custom.resolve_run_policy().video == "off"
    assert req_custom.resolve_run_policy().voice == "mock"

    # 4. Truyền runPolicy dạng dict trong payload
    req_dict = GraphRunRequest.model_validate(
        {"projectId": "soc-nho-tv", "runPolicy": {"image": "real", "voice": "local"}}
    )
    assert req_dict.resolve_run_policy().image == "real"
    assert req_dict.resolve_run_policy().voice == "local"


def test_hybrid_mode_voice_real_and_image_mock():
    """(a) Chế độ lai: image mock + voice local. Kiểm hàm giọng thật được gọi."""
    async def _test():
        store = ProjectStore("soc-nho-tv")
        policy = RunPolicy(image="mock", video="off", text="mock", voice="local")
        router = ProviderRouter(store=store, run_policy=policy)

        # 1. Ảnh ở chế độ lai -> rơi vào mock
        images = await router.generate_images(prompt="Sóc Nhỏ đang cười")
        assert len(images) > 0
        assert images[0].provenance.provider == "mock"

        # 2. Giọng ở chế độ lai -> gọi VoiceAdapter thật (mock để không tốn CPU)
        dummy_art = _make_dummy_artifact(kind=ArtifactKind.AUDIO)
        with patch("socnhotv.core.adapters.voice_adapter.VoiceAdapter.synthesize", new_callable=AsyncMock) as mock_synth:
            mock_synth.return_value = dummy_art
            voice_art = await router.speak_voice(text="Xin chào các bạn nhỏ", voice_id="soc-nho")
            assert voice_art.id == dummy_art.id
            mock_synth.assert_awaited_once()

    asyncio.run(_test())


def test_mock_mode_with_mock_voice_preserves_mock_behavior():
    """(b) Khi explicitly đặt voice='mock', router dùng MockProvider và không gọi VoiceAdapter."""
    async def _test():
        store = ProjectStore("soc-nho-tv")
        policy = RunPolicy(image="mock", video="mock", text="mock", voice="mock")
        router = ProviderRouter(store=store, run_policy=policy)

        with patch("socnhotv.core.adapters.voice_adapter.VoiceAdapter.synthesize", new_callable=AsyncMock) as mock_synth:
            art = await router.speak_voice(text="Thử nghiệm mock voice", voice_id="soc-nho")
            assert art.provenance.provider == "mock"
            mock_synth.assert_not_called()

    asyncio.run(_test())


def test_router_factories_integration():
    """(2) Router tra cứu qua PROVIDER_FACTORIES của G1."""
    store = ProjectStore("soc-nho-tv")
    router = ProviderRouter(store=store, run_policy=RunPolicy(image="real", voice="local"))

    # Local và Pollinations không cần key -> lấy thành công từ factory
    local_prov = router.get_provider("local")
    assert local_prov is not None
    assert local_prov.provider_name() == "local"

    poll_prov = router.get_provider("pollinations")
    assert poll_prov is not None
    assert poll_prov.provider_name() == "pollinations"


def test_fallback_chain_only_free_or_local():
    """(c) Nguồn free hết hạn mức thì chuyển sang dự phòng free/local, KHÔNG chuyển sang paid."""
    async def _test():
        store = ProjectStore("soc-nho-tv")
        policy = RunPolicy(image="real", voice="local")
        router = ProviderRouter(store=store, run_policy=policy)

        called_providers: list[str] = []

        class FakeCF(MockProvider):
            async def generate_images(self, **kwargs):
                called_providers.append("cloudflare")
                raise ProviderError("Hết quota Cloudflare", kind=ProviderErrorKind.QUOTA, provider="cloudflare")

        class FakeLocal(MockProvider):
            async def generate_images(self, **kwargs):
                called_providers.append("local")
                return [_make_dummy_artifact(kind=ArtifactKind.IMAGE)]

        class FakeGoogle(MockProvider):
            async def generate_images(self, **kwargs):
                called_providers.append("google")
                return [_make_dummy_artifact(kind=ArtifactKind.IMAGE)]

        router._instances["cloudflare"] = FakeCF(store)
        router._instances["local"] = FakeLocal(store)
        router._instances["google"] = FakeGoogle(store)

        # fallback_models chứa 'gemini-2.5-flash-image' (tier paid) và 'local-flux-schnell' (tier local)
        result = await router.generate_images(
            prompt="Test prompt",
            model="cf-flux-schnell",
            fallback_models=["gemini-2.5-flash-image", "local-flux-schnell"],
        )

        assert len(result) == 1
        # Kiểm tra provider paid 'google' TUYỆT ĐỐI KHÔNG ĐƯỢC GỌI
        assert "google" not in called_providers
        assert called_providers == ["cloudflare", "local"]

    asyncio.run(_test())


def test_fallback_fails_if_no_free_candidates_succeed():
    """Nếu mọi nguồn free/local đều lỗi, router trả lại lỗi ban đầu chứ không tự gọi model trả phí."""
    async def _test():
        store = ProjectStore("soc-nho-tv")
        router = ProviderRouter(store=store, run_policy=RunPolicy(image="real", voice="local"))

        class FakeCF(MockProvider):
            async def generate_images(self, **kwargs):
                raise ProviderError("Hết quota Cloudflare", kind=ProviderErrorKind.QUOTA, provider="cloudflare")

        class FakeLocal(MockProvider):
            async def generate_images(self, **kwargs):
                raise ProviderError("Lỗi phần cứng Mac", kind=ProviderErrorKind.QUOTA, provider="local")

        router._instances["cloudflare"] = FakeCF(store)
        router._instances["local"] = FakeLocal(store)

        with pytest.raises(ProviderError) as exc_info:
            await router.generate_images(
                prompt="Test prompt",
                model="cf-flux-schnell",
                fallback_models=["local-flux-schnell", "fal-flux-schnell"],  # fal là paid, bị bỏ qua
            )
        assert exc_info.value.kind == ProviderErrorKind.QUOTA

    asyncio.run(_test())


def test_snapshots_and_cache_do_not_mix_mock_and_real():
    """(d) Snapshot/cache không trộn mock với thật."""
    store = ProjectStore("soc-nho-tv")
    runner = GraphRunner(store=store)

    req_hybrid = GraphRunRequest(
        projectId="soc-nho-tv",
        runPolicy=RunPolicy(image="mock", video="off", text="mock", voice="local"),
    )

    # 1. Kiểm tra _is_mock_for phân định đúng theo node type
    img_node = NodeInstance(id="n_img", type="image_gen", position={"x": 0, "y": 0})
    voice_node = NodeInstance(id="n_voice", type="voice_tts", position={"x": 0, "y": 0})

    assert runner._is_mock_for(img_node, req_hybrid) is True  # image là mock
    assert runner._is_mock_for(voice_node, req_hybrid) is False  # voice là local (thật)
    assert runner._is_mock_for("voice", req_hybrid) is False

    # 2. Snapshot lưu độc lập giữa mock và real
    outputs_mock = {"image": "art_mock"}
    outputs_real = {"image": "art_real"}

    runner._save_outputs_snapshot("graph_1", img_node, outputs_mock, is_mock=True)
    runner._save_outputs_snapshot("graph_1", img_node, outputs_real, is_mock=False)

    # Đọc lại khi is_mock=True -> phải ra mock
    loaded_mock = runner._load_outputs_snapshot("graph_1", img_node, is_mock=True)
    assert loaded_mock is not None
    assert loaded_mock["image"] == "art_mock"

    # Đọc lại khi is_mock=False -> phải ra real
    loaded_real = runner._load_outputs_snapshot("graph_1", img_node, is_mock=False)
    assert loaded_real is not None
    assert loaded_real["image"] == "art_real"


def test_api_models_and_providers_endpoints():
    """GET /models trả về available và C2 fields; GET /providers trả về tier, needs_key."""
    from fastapi.testclient import TestClient
    from socnhotv.core.api.app import app

    client = TestClient(app)

    # 1. /models
    r_models = client.get("/models")
    assert r_models.status_code == 200
    models_data = r_models.json()
    assert isinstance(models_data, list)
    assert len(models_data) > 0

    # Kiểm tra model có trường available, tier, supports_reference
    for m in models_data:
        assert "available" in m
        assert "tier" in m
        assert "supports_reference" in m
        if m["tier"] in ("free", "local"):
            assert m["available"] is True

    # 2. /providers
    r_providers = client.get("/providers")
    assert r_providers.status_code == 200
    prov_data = r_providers.json()["providers"]
    prov_ids = [p["id"] for p in prov_data]

    assert "mock" in prov_ids
    assert "local" in prov_ids
    assert "pollinations" in prov_ids
    assert "cloudflare" in prov_ids

    local_entry = next(p for p in prov_data if p["id"] == "local")
    assert local_entry["tier"] == "local"
    assert local_entry["needs_key"] is False
    assert local_entry["configured"] is True


def test_api_verify_key_endpoint():
    """Endpoint POST /settings/api-keys/verify kiểm tra key trực tiếp."""
    from fastapi.testclient import TestClient
    from socnhotv.core.api.app import app

    client = TestClient(app)

    # Test key giả lập sai định dạng hoặc thiếu key
    r_bad = client.post("/settings/api-keys/verify", json={"provider": "gemini", "apiKey": "short"})
    assert r_bad.status_code == 400
    assert r_bad.json()["valid"] is False

