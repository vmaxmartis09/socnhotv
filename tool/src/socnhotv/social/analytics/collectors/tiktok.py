from __future__ import annotations

import httpx
from typing import Optional

from socnhotv.social.analytics.collectors.base import BaseCollector
from socnhotv.social.models import PostMetricsSnapshot, PostTarget, SocialAccount, now_iso


class TikTokCollector(BaseCollector):
    def __init__(self, key_vault=None, client: Optional[httpx.AsyncClient] = None):
        super().__init__(key_vault)
        self._client = client

    async def collect(
        self,
        account: SocialAccount,
        target: PostTarget,
        checkpoint: str = "custom",
    ) -> PostMetricsSnapshot:
        publish_id = target.external_id
        snapshot = PostMetricsSnapshot(
            post_id="",
            target_id=target.id,
            platform="tiktok",
            checkpoint=checkpoint,
            timestamp=now_iso(),
        )

        token = self.key_vault.get_token(account.auth.token_ref) if account.auth.token_ref else None
        if not token:
            return snapshot

        client = self._client or httpx.AsyncClient()
        close_client = self._client is None
        try:
            # 1. Query status or video metrics
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = {}
            if publish_id:
                payload["publish_id"] = publish_id

            # Try TikTok post status fetch
            resp = await client.post(
                "https://open.tiktokapis.com/v2/post/publish/status/fetch/",
                json=payload,
                headers=headers,
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                snapshot.raw = data
                # If video info available
                if "video_views" in data:
                    snapshot.views = int(data.get("video_views", 0))
                    snapshot.likes = int(data.get("likes", 0))
                    snapshot.comments = int(data.get("comments", 0))
                    snapshot.shares = int(data.get("shares", 0))
        except Exception as e:
            snapshot.raw = {"error": str(e)}
        finally:
            if close_client:
                await client.aclose()

        return snapshot
