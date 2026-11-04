from __future__ import annotations

from socnhotv.social.adapters.base import Capabilities, Issue, PublishAdapter, PublishResult
from socnhotv.social.adapters.browser_assisted import BrowserAssistedAdapter
from socnhotv.social.adapters.manual import ManualAdapter, export_package_zip
from socnhotv.social.adapters.meta import MetaAdapter
from socnhotv.social.adapters.tiktok import TikTokAdapter
from socnhotv.social.adapters.youtube import YouTubeAdapter


def get_adapter(platform: str, mode: str = "oauth") -> PublishAdapter:
    """Return appropriate publish adapter based on platform and auth mode."""
    if mode == "browser_assisted":
        return BrowserAssistedAdapter(platform=platform)
    if mode == "manual":
        return ManualAdapter(platform=platform)

    plat_lower = platform.lower()
    if plat_lower == "youtube":
        return YouTubeAdapter()
    elif plat_lower == "tiktok":
        return TikTokAdapter()
    elif plat_lower in ("facebook", "instagram"):
        return MetaAdapter(platform=plat_lower)
    else:
        # Fallback to manual package adapter for douyin, threads, x, etc.
        return ManualAdapter(platform=plat_lower)


__all__ = [
    "PublishAdapter",
    "PublishResult",
    "Issue",
    "Capabilities",
    "YouTubeAdapter",
    "TikTokAdapter",
    "MetaAdapter",
    "ManualAdapter",
    "BrowserAssistedAdapter",
    "get_adapter",
    "export_package_zip",
]
