"""Unit tests cho luồng G1: Nguồn AI miễn phí (Pollinations.ai, Cloudflare, Local, Factories, C1/C2)."""
from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest

from socnhotv.core.contracts.types import ArtifactKind
from socnhotv.core.models_registry.registry import ModelRegistry
from socnhotv.core.providers.errors import ProviderError, ProviderErrorKind
from socnhotv.core.providers.factories import PROVIDER_FACTORIES, PROVIDER_META
from socnhotv.core.providers.key_vault import KeyVault
from socnhotv.core.providers.pollinations_provider import PollinationsProvider
from socnhotv.core.providers.spend_guard import SpendGuard
from socnhotv.core.storage.project_store import ProjectStore

DUMMY_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"


@pytest.fixture
def tmp_store(tmp_path: Path) -> ProjectStore:
    return ProjectStore("test-project", repo_root=tmp_path)


@pytest.fixture
def dummy_guard(tmp_path: Path) -> SpendGuard:
    return SpendGuard(tmp_path / "runs")


def test_provider_meta_and_factories_contract_c1(tmp_store: ProjectStore, dummy_guard: SpendGuard) -> None:
    """Kiểm tra hợp đồng C1: bảng PROVIDER_META và PROVIDER_FACTORIES."""
    assert "pollinations" in PROVIDER_FACTORIES
    assert "cloudflare" in PROVIDER_FACTORIES
    assert "local" in PROVIDER_FACTORIES

    assert "pollinations" in PROVIDER_META
    meta_pol = PROVIDER_META["pollinations"]
    assert meta_pol["tier"] == "free"
    assert meta_pol["needs_key"] is False

    meta_cf = PROVIDER_META["cloudflare"]
    assert meta_cf["tier"] == "freemium"
    assert meta_cf["needs_key"] is True

    # Khởi tạo qua factory
    provider = PROVIDER_FACTORIES["pollinations"](tmp_store, dummy_guard, None, "api")
    assert provider.provider_name() == "pollinations"
    caps = provider.capabilities()
    assert caps["supportsReferences"] is True
    assert caps["supportsImageEdit"] is True


def test_models_registry_contract_c2() -> None:
    """Kiểm tra hợp đồng C2: các trường tier, supports_reference, quota_note trong models.yaml."""
    reg = ModelRegistry()

    m_flux = reg.get("pollinations-flux")
    assert m_flux is not None
    assert m_flux.tier == "free"
    assert m_flux.supports_reference is True
    assert m_flux.max_references >= 1
    assert "miễn phí" in m_flux.quota_note.lower() or "free" in m_flux.quota_note.lower()

    m_cf = reg.get("cf-flux-schnell")
    assert m_cf is not None
    assert m_cf.tier == "freemium"
    assert m_cf.supports_reference is False

    m_local = reg.get("local-flux-schnell")
    assert m_local is not None
    assert m_local.tier == "local"


def test_key_vault_supports_new_providers(tmp_path: Path) -> None:
    """Kiểm tra KeyVault nhận diện được các provider mới (pollinations, cloudflare)."""
    vault = KeyVault(repo_root=tmp_path, persist_local=False)
    status_list = {item["provider"]: item for item in vault.list_status()}

    assert "pollinations" in status_list
    assert "cloudflare" in status_list


def test_pollinations_provider_generate_image_mock_transport(
    tmp_store: ProjectStore,
    dummy_guard: SpendGuard,
) -> None:
    """Kiểm tra sinh ảnh với mock HTTP transport (không gọi mạng)."""
    recorded_urls: list[str] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        recorded_urls.append(str(request.url))
        return httpx.Response(
            status_code=200,
            headers={"content-type": "image/jpeg"},
            content=DUMMY_JPEG_BYTES,
        )

    transport = httpx.MockTransport(mock_handler)
    provider = PollinationsProvider(
        store=tmp_store,
        guard=dummy_guard,
        transport=transport,
    )

    async def _run():
        return await provider.generate_images(
            prompt="Sóc Bi đang xếp tháp gỗ",
            references=[],
            aspect_ratio="16:9",
            node_id="n_keyframes",
            run_id="run_test",
            model="pollinations-flux",
        )

    artifacts = asyncio.run(_run())

    assert len(artifacts) == 1
    art = artifacts[0]
    assert art.kind == ArtifactKind.IMAGE
    assert art.provenance.provider == "pollinations"
    assert art.provenance.model == "flux"
    assert art.provenance.cost_usd == 0.0
    assert art.meta.aspect == "16:9"
    assert art.meta.width == 1280
    assert art.meta.height == 720

    # Kiểm tra tệp thực tế được lưu trong store
    saved_file = tmp_store.project_dir / art.uri
    assert saved_file.exists()
    assert saved_file.read_bytes() == DUMMY_JPEG_BYTES


def test_pollinations_rate_limit_quota_error(
    tmp_store: ProjectStore,
    dummy_guard: SpendGuard,
) -> None:
    """Kiểm tra xử lý lỗi 402/429 rate limit nâng thành ProviderErrorKind.QUOTA."""
    def mock_402_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=402,
            headers={"content-type": "application/json"},
            text='{"error":{"code":"FREE_LIMIT","message":"Free limit reached: 1 image every 45 seconds per IP. Retry after 40s"}}',
        )

    transport = httpx.MockTransport(mock_402_handler)
    provider = PollinationsProvider(
        store=tmp_store,
        guard=dummy_guard,
        transport=transport,
        max_retries=1,
    )

    async def _run():
        await provider.generate_images(
            prompt="Test rate limit",
            node_id="n_test",
            run_id="run_test",
        )

    with pytest.raises(ProviderError) as exc_info:
        asyncio.run(_run())

    assert exc_info.value.kind == ProviderErrorKind.QUOTA
    assert exc_info.value.provider == "pollinations"


def test_pollinations_unsupported_methods_raise_invalid_params(
    tmp_store: ProjectStore,
    dummy_guard: SpendGuard,
) -> None:
    """Kiểm tra các phương thức không hỗ trợ ném lỗi INVALID_PARAMS rõ ràng."""
    provider = PollinationsProvider(store=tmp_store, guard=dummy_guard)

    with pytest.raises(ProviderError) as exc_video:
        asyncio.run(provider.generate_video(prompt="test video"))
    assert exc_video.value.kind == ProviderErrorKind.INVALID_PARAMS

    with pytest.raises(ProviderError) as exc_voice:
        asyncio.run(provider.speak_voice(text="test voice"))
    assert exc_voice.value.kind == ProviderErrorKind.INVALID_PARAMS
