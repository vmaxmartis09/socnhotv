from __future__ import annotations

import httpx
from typing import Optional

from socnhotv.social.analytics.collectors.base import BaseCollector
from socnhotv.social.models import PostMetricsSnapshot, PostTarget, SocialAccount, now_iso


class MetaCollector(BaseCollector):
    def __init__(self, key_vault=None, client: Optional[httpx.AsyncClient] = None):
        super().__init__(key_vault)
        self._client = client

    async def collect(
        self,
        account: SocialAccount,
        target: PostTarget,
        checkpoint: str = "custom",
    ) -> PostMetricsSnapshot:
        media_id = target.external_id
        snapshot = PostMetricsSnapshot(
            post_id="",
            target_id=target.id,
            platform=target.platform,
            checkpoint=checkpoint,
            timestamp=now_iso(),
        )

        token = self.key_vault.get_token(account.auth.token_ref) if account.auth.token_ref else None
        if not token or not media_id:
            return snapshot

        client = self._client or httpx.AsyncClient()
        close_client = self._client is None
        try:
            if target.platform == "instagram":
                # Instagram Insights API
                resp = await client.get(
                    f"https://graph.facebook.com/v21.0/{media_id}/insights",
                    params={
                        "metric": "plays,reach,saved,shares,total_interactions",
                        "access_token": token,
                    },
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    metrics_map = {item.get("name"): item.get("values", [{}])[0].get("value", 0) for item in data}
                    snapshot.views = int(metrics_map.get("plays", metrics_map.get("reach", 0)))
                    snapshot.saves = int(metrics_map.get("saved", 0))
                    snapshot.shares = int(metrics_map.get("shares", 0))
                    snapshot.raw = resp.json()
            else:
                # Facebook Page Video Insights
                resp = await client.get(
                    f"https://graph.facebook.com/v21.0/{media_id}/video_insights",
                    params={"access_token": token},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    for item in data:
                        name = item.get("name")
                        val = item.get("values", [{}])[0].get("value", 0)
                        if name == "total_video_views":
                            snapshot.views = int(val)
                        elif name == "total_video_avg_time_watched":
                            snapshot.watch_time_s = float(val) / 1000.0 if isinstance(val, (int, float)) else 0.0
                    snapshot.raw = resp.json()
        except Exception as e:
            snapshot.raw = {"error": str(e)}
        finally:
            if close_client:
                await client.aclose()

        return snapshot
