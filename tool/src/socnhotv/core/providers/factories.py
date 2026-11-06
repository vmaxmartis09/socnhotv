"""Nhà máy khởi tạo Provider (C1) và siêu dữ liệu (tier, key_name, quota_note)."""
from __future__ import annotations

from typing import Callable, Dict, Optional

from socnhotv.core.providers.base import BaseProvider
from socnhotv.core.providers.spend_guard import SpendGuard
from socnhotv.core.storage.project_store import ProjectStore

# Siêu dữ liệu chuẩn cho các nhà cung cấp AI
PROVIDER_META: Dict[str, Dict[str, object]] = {
    "pollinations": {
        "label": "Pollinations.ai (FLUX / Sana)",
        "tier": "free",
        "needs_key": False,
        "key_name": "POLLINATIONS_API_KEY",
        "quota_note": "Miễn phí 1 ảnh/45s theo IP; hỗ trợ ảnh tham chiếu; không giới hạn nếu có Pollen key",
    },
    "cloudflare": {
        "label": "Cloudflare Workers AI",
        "tier": "freemium",
        "needs_key": True,
        "key_name": "CLOUDFLARE_API_TOKEN",
        "quota_note": "10.000 neurons/ngày free (~55 ảnh FLUX.1 schnell/ngày)",
    },
    "local": {
        "label": "Local MLX / mflux (Mac M4)",
        "tier": "local",
        "needs_key": False,
        "key_name": None,
        "quota_note": "$0 hoàn toàn offline trên Apple Silicon M4, ~10-15s/ảnh",
    },
    "mock": {
        "label": "Mock Provider (Giả lập)",
        "tier": "free",
        "needs_key": False,
        "key_name": None,
        "quota_note": "Dữ liệu mẫu cho kiểm thử nhanh, không tốn tài nguyên",
    },
    "google": {
        "label": "Google Gemini & Veo",
        "tier": "paid",
        "needs_key": True,
        "key_name": "GEMINI_API_KEY",
        "quota_note": "Key Google AI Studio; model ảnh/video cần tài khoản Pay-as-you-go",
    },
    "fal": {
        "label": "fal.ai Queue API",
        "tier": "paid",
        "needs_key": True,
        "key_name": "FAL_KEY",
        "quota_note": "Hàng đợi đám mây FLUX & LTX Video (trả phí theo giây)",
    },
    "replicate": {
        "label": "Replicate",
        "tier": "paid",
        "needs_key": True,
        "key_name": "REPLICATE_API_TOKEN",
        "quota_note": "Trả phí theo phần cứng / thời gian chạy",
    },
}


def _create_pollinations(
    store: ProjectStore,
    guard: SpendGuard,
    key: Optional[str],
    source: str = "api",
) -> BaseProvider:
    from socnhotv.core.providers.pollinations_provider import PollinationsProvider

    return PollinationsProvider(store=store, guard=guard, key=key, source=source)


def _create_cloudflare(
    store: ProjectStore,
    guard: SpendGuard,
    key: Optional[str],
    source: str = "api",
) -> BaseProvider:
    from socnhotv.core.providers.cloudflare_provider import CloudflareProvider

    return CloudflareProvider(store=store, guard=guard, key=key, source=source)


def _create_local(
    store: ProjectStore,
    guard: SpendGuard,
    key: Optional[str],
    source: str = "api",
) -> BaseProvider:
    from socnhotv.core.providers.local_image_provider import LocalImageProvider

    return LocalImageProvider(store=store, guard=guard, key=key, source=source)


def _create_mock(
    store: ProjectStore,
    guard: SpendGuard,
    key: Optional[str],
    source: str = "api",
) -> BaseProvider:
    from socnhotv.core.providers.mock_provider import MockProvider

    return MockProvider(store=store)


def _create_google(
    store: ProjectStore,
    guard: SpendGuard,
    key: Optional[str],
    source: str = "api",
) -> BaseProvider:
    from socnhotv.core.providers.google_provider import GoogleProvider

    return GoogleProvider(store=store, guard=guard, key=key, source=source)


def _create_fal(
    store: ProjectStore,
    guard: SpendGuard,
    key: Optional[str],
    source: str = "api",
) -> BaseProvider:
    from socnhotv.core.providers.fal_provider import FalProvider

    return FalProvider(store=store, guard=guard, key=key, source=source)


def _create_replicate(
    store: ProjectStore,
    guard: SpendGuard,
    key: Optional[str],
    source: str = "api",
) -> BaseProvider:
    from socnhotv.core.providers.replicate_provider import ReplicateProvider

    return ReplicateProvider(store=store, guard=guard, key=key, source=source)


# Bảng tra cứu hàm tạo provider theo chuẩn Hợp đồng C1
PROVIDER_FACTORIES: Dict[str, Callable[[ProjectStore, SpendGuard, Optional[str], str], BaseProvider]] = {
    "pollinations": _create_pollinations,
    "cloudflare": _create_cloudflare,
    "local": _create_local,
    "mock": _create_mock,
    "google": _create_google,
    "gemini": _create_google,
    "fal": _create_fal,
    "fal.ai": _create_fal,
    "replicate": _create_replicate,
}
