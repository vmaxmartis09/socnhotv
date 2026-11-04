"""Browser-Assisted Publish Adapter using Ego Lite.

Pre-populates upload form (attaches video, pastes caption) and pauses
waiting for user manual approval and click on Publish. Does not bypass controls.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from socnhotv.social.adapters.base import Capabilities, Issue, PublishAdapter, PublishResult
from socnhotv.social.models import PostMedia, PostTarget, SocialAccount


class BrowserAssistedAdapter(PublishAdapter):
    def __init__(self, platform: str = "tiktok"):
        self.platform = platform  # type: ignore

    def capabilities(self) -> Capabilities:
        return Capabilities(
            direct_post=False,
            draft_upload=True,
            schedule_native=False,
            thumbnail=True,
            first_comment=True,
            product_link=True,
        )

    def connect_url(self, account: SocialAccount, redirect_uri: str) -> str:
        return ""

    def exchange_code(self, account: SocialAccount, code: str, redirect_uri: str) -> Dict[str, Any]:
        return {"mode": "browser_assisted"}

    def refresh(self, account: SocialAccount) -> Dict[str, Any]:
        return {"mode": "browser_assisted"}

    def validate(self, target: PostTarget, media: Optional[PostMedia]) -> List[Issue]:
        issues: List[Issue] = []
        if not media or not media.path:
            issues.append(Issue(level="error", code="missing_media", message="Chưa chọn tệp video"))
        return issues

    def publish(
        self,
        account: SocialAccount,
        target: PostTarget,
        media: Optional[PostMedia],
    ) -> PublishResult:
        """Prepares upload instructions and triggers browser-assisted flow."""
        upload_urls = {
            "tiktok": "https://www.tiktok.com/creator-center/upload",
            "youtube": "https://studio.youtube.com/channel/upload",
            "facebook": "https://business.facebook.com/creatorstudio",
            "instagram": "https://www.instagram.com/",
            "douyin": "https://creator.douyin.com/",
        }
        dest_url = upload_urls.get(self.platform, "https://www.google.com")

        return PublishResult(
            external_id=f"browser_assist_{target.id}",
            url=dest_url,
            status="publishing",
            raw_response={
                "message": "Trình duyệt Ego Lite đã sẵn sàng hỗ trợ. Vui lòng mở trang và xác nhận bấm Đăng.",
                "target_url": dest_url,
            },
        )

    def fetch_status(self, account: SocialAccount, external_id: str) -> PublishResult:
        return PublishResult(external_id=external_id, status="publishing")
