from __future__ import annotations

import httpx
from typing import Optional

from socnhotv.social.analytics.collectors.base import BaseCollector
from socnhotv.social.models import PostMetricsSnapshot, PostTarget, SocialAccount, now_iso


class YouTubeCollector(BaseCollector):
    def __init__(self, key_vault=None, client: Optional[httpx.AsyncClient] = None):
        super().__init__(key_vault)
        self._client = client

    async def collect(
        self,
        account: SocialAccount,
        target: PostTarget,
        checkpoint: str = "custom",
    ) -> PostMetricsSnapshot:
        video_id = target.external_id
        snapshot = PostMetricsSnapshot(
            post_id="",
            target_id=target.id,
            platform="youtube",
            checkpoint=checkpoint,
            timestamp=now_iso(),
        )

        if not video_id:
            return snapshot

        token = self.key_vault.get_token(account.auth.token_ref) if account.auth.token_ref else None

        client = self._client or httpx.AsyncClient()
        close_client = self._client is None
        try:
            # 1. YouTube Data API v3: videos.list
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={"part": "statistics,contentDetails", "id": video_id},
                headers=headers,
                timeout=10.0,
            )

            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                if items:
                    stats = items[0].get("statistics", {})
                    snapshot.views = int(stats.get("viewCount", 0))
                    snapshot.likes = int(stats.get("likeCount", 0))
                    snapshot.comments = int(stats.get("commentCount", 0))
                    snapshot.raw = data

            # 2. Try YouTube Analytics API if token available
            if token:
                try:
                    analytics_resp = await client.get(
                        "https://youtubeanalytics.googleapis.com/v2/reports",
                        params={
                            "ids": "channel==MINE",
                            "metrics": "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained",
                            "filters": f"video=={video_id}",
                            "startDate": "2024-01-01",
                            "endDate": "2030-01-01",
                        },
                        headers=headers,
                        timeout=5.0,
                    )
                    if analytics_resp.status_code == 200:
                        adata = analytics_resp.json()
                        rows = adata.get("rows", [])
                        if rows:
                            # row: [views, estimatedMinutesWatched, averageViewDuration, averageViewPercentage, subscribersGained]
                            r = rows[0]
                            if len(r) >= 5:
                                snapshot.watch_time_s = float(r[1]) * 60.0
                                snapshot.avg_retention_pct = float(r[3])
                                snapshot.subscribers_gained = int(r[4])
                except Exception:
                    pass
        except Exception as e:
            snapshot.raw = {"error": str(e)}
        finally:
            if close_client:
                await client.aclose()

        return snapshot
