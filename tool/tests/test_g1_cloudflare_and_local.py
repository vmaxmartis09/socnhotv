"""Unit tests cho Cloudflare Workers AI và Local Image Provider (G1)."""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from socnhotv.core.contracts.types import ArtifactKind
from socnhotv.core.providers.cloudflare_provider import CloudflareProvider
from socnhotv.core.providers.errors import MissingApiKey, ProviderError, ProviderErrorKind
from socnhotv.core.providers.local_image_provider import LocalImageProvider
from socnhotv.core.providers.spend_guard import SpendGuard
from socnhotv.core.storage.project_store import ProjectStore

DUMMY_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"


@pytest.fixture
def tmp_store(tmp_path: Path) -> ProjectStore:
    return ProjectStore("test-project", repo_root=tmp_path)


@pytest.fixture
def dummy_guard(tmp_path: Path) -> SpendGuard:
    return SpendGuard(tmp_path / "runs")


def test_cloudflare_missing_key_raises(tmp_store: ProjectStore, dummy_guard: SpendGuard) -> None:
    provider = CloudflareProvider(
        store=tmp_store,
        guard=dummy_guard,
        key="",
        account_id="",
    )
    with pytest.raises(MissingApiKey) as exc:
        asyncio.run(provider.generate_images("test prompt"))
    assert "CLOUDFLARE_API_TOKEN" in str(exc.value)


def test_cloudflare_generate_images_mock_transport(
    tmp_store: ProjectStore,
    dummy_guard: SpendGuard,
) -> None:
    def mock_cf(request: httpx.Request) -> httpx.Response:
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer mock_cf_token"
        return httpx.Response(
            status_code=200,
            headers={"content-type": "image/png"},
            content=DUMMY_PNG_BYTES,
        )

    transport = httpx.MockTransport(mock_cf)
    provider = CloudflareProvider(
        store=tmp_store,
        guard=dummy_guard,
        key="mock_cf_token",
        account_id="mock_cf_acc_123",
        transport=transport,
    )

    artifacts = asyncio.run(provider.generate_images("cute squirrel", aspect_ratio="16:9"))
    assert len(artifacts) == 1
    art = artifacts[0]
    assert art.kind == ArtifactKind.IMAGE
    assert art.provenance.provider == "cloudflare"
    assert art.provenance.model == "cf-flux-schnell"
    assert art.provenance.cost_usd == 0.0


def test_cloudflare_429_quota_error(tmp_store: ProjectStore, dummy_guard: SpendGuard) -> None:
    def mock_429(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=429, text="Rate limit exceeded")

    transport = httpx.MockTransport(mock_429)
    provider = CloudflareProvider(
        store=tmp_store,
        guard=dummy_guard,
        key="mock_cf_token",
        account_id="mock_cf_acc_123",
        transport=transport,
    )

    with pytest.raises(ProviderError) as exc:
        asyncio.run(provider.generate_images("test"))
    assert exc.value.kind == ProviderErrorKind.QUOTA


def test_local_provider_capabilities(tmp_store: ProjectStore, dummy_guard: SpendGuard) -> None:
    provider = LocalImageProvider(store=tmp_store, guard=dummy_guard)
    caps = provider.capabilities()
    assert caps["provider"] == "local"
    assert "local-flux-schnell" in caps["models"]
    assert caps["supportsReferences"] is False
