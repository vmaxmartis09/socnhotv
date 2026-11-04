from __future__ import annotations

from typing import Optional

from socnhotv.social.analytics.collectors.base import BaseCollector
from socnhotv.social.analytics.collectors.manual import ManualCollector
from socnhotv.social.analytics.collectors.meta import MetaCollector
from socnhotv.social.analytics.collectors.tiktok import TikTokCollector
from socnhotv.social.analytics.collectors.youtube import YouTubeCollector


def get_collector(platform: str, mode: str = "oauth") -> BaseCollector:
    if mode == "manual":
        return ManualCollector()
    if platform == "youtube":
        return YouTubeCollector()
    elif platform == "tiktok":
        return TikTokCollector()
    elif platform in ("facebook", "instagram"):
        return MetaCollector()
    return ManualCollector()


__all__ = [
    "BaseCollector",
    "YouTubeCollector",
    "TikTokCollector",
    "MetaCollector",
    "ManualCollector",
    "get_collector",
]
