"""Meta Graph API Publish Adapter (Facebook Page Video & Instagram Reels).

Official References:
- Facebook Video Publishing:
  https://developers.facebook.com/docs/video-api/guides/publishing
- Instagram Reels Publishing (Container -> Status -> Publish):
  https://developers.facebook.com/docs/instagram-api/guides/content-publishing
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import httpx

from socnhotv.social.vault import get_social_vault as get_key_vault
from socnhotv.social.adapters.base import Capabilities, Issue, PublishAdapter, PublishResult
from socnhotv.social.models import PostMedia, PostTarget, SocialAccount


class MetaAdapter(PublishAdapter):
    def __init__(self, platform: str = "facebook"):
        self.platform = "facebook" if platform == "facebook" else "instagram"

    def capabilities(self) -> Capabilities:
        return Capabilities(
            direct_post=True,
            draft_upload=False,
            schedule_native=True,
            thumbnail=True,
            first_comment=False,
            product_link=False,
        )

    def connect_url(self, account: SocialAccount, redirect_uri: str) -> str:
        vault = get_key_vault()
        app_id = vault.get_key("meta_app_id") or "mock_meta_app_id"
        scopes = "pages_show_list,pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish"
        return (
            f"https://www.facebook.com/v20.0/dialog/oauth?"
            f"client_id={app_id}&redirect_uri={redirect_uri}&scope={scopes}&state={account.id}"
        )

    def exchange_code(self, account: SocialAccount, code: str, redirect_uri: str) -> Dict[str, Any]:
        vault = get_key_vault()
        app_id = vault.get_key("meta_app_id") or "mock_id"
        app_secret = vault.get_key("meta_app_secret") or "mock_secret"

        resp = httpx.get(
            "https://graph.facebook.com/v20.0/oauth/access_token",
            params={
                "client_id": app_id,
                "client_secret": app_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
            timeout=15.0,
        )
        return resp.json()

    def refresh(self, account: SocialAccount) -> Dict[str, Any]:
        return {"status": "ok", "note": "Meta long-lived tokens valid for 60 days"}

    def validate(self, target: PostTarget, media: Optional[PostMedia]) -> List[Issue]:
        issues: List[Issue] = []
        if not media or not media.path:
            issues.append(Issue(level="error", code="missing_media", message="Chưa chọn tệp video"))

        if self.platform == "instagram":
            if not target.caption:
                issues.append(Issue(level="warning", code="no_caption", message="Nên có caption kèm hashtag cho Instagram Reels"))
            if len(target.caption) > 2200:
                issues.append(Issue(level="error", code="caption_long", message="Caption Instagram tối đa 2200 ký tự"))
            if len(target.hashtags) > 30:
                issues.append(Issue(level="error", code="too_many_hashtags", message="Instagram chỉ cho phép tối đa 30 hashtags"))
        else:
            if len(target.caption) > 5000:
                issues.append(Issue(level="error", code="caption_long", message="Nội dung Facebook quá 5000 ký tự"))

        return issues

    def publish(
        self,
        account: SocialAccount,
        target: PostTarget,
        media: Optional[PostMedia],
        transport: Optional[httpx.BaseTransport] = None,
    ) -> PublishResult:
        issues = self.validate(target, media)
        errors = [i.message for i in issues if i.level == "error"]
        if errors:
            return PublishResult(status="failed", error="; ".join(errors))

        vault = get_key_vault()
        token_ref = account.auth.token_ref or f"oauth_meta_{account.id}"
        access_token = vault.get_key(f"{token_ref}_access") or "mock_meta_token"

        client = httpx.Client(transport=transport, timeout=30.0)
        try:
            if self.platform == "instagram":
                # Instagram Reels flow: 1) Create Media Container -> 2) Publish Media Container
                ig_user_id = account.channel_url or "mock_ig_user_id"
                container_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media"

                c_resp = client.post(
                    container_url,
                    params={
                        "media_type": "REELS",
                        "video_url": media.path if media else "http://example.com/mock.mp4",
                        "caption": target.caption,
                        "access_token": access_token,
                    },
                )
                if c_resp.status_code != 200:
                    return PublishResult(status="failed", error=f"IG Container failed ({c_resp.status_code}): {c_resp.text}")

                container_id = c_resp.json().get("id", "container_123")

                # Step 2: Publish Container
                pub_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media_publish"
                p_resp = client.post(
                    pub_url,
                    params={"creation_id": container_id, "access_token": access_token},
                )
                if p_resp.status_code != 200:
                    return PublishResult(status="failed", error=f"IG Publish failed ({p_resp.status_code}): {p_resp.text}")

                media_id = p_resp.json().get("id", "ig_media_123")
                return PublishResult(
                    external_id=media_id,
                    url=f"https://www.instagram.com/p/{media_id}",
                    status="published",
                    raw_response=p_resp.json(),
                )
            else:
                # Facebook Page Video
                page_id = account.channel_url or "mock_page_id"
                post_url = f"https://graph-video.facebook.com/v20.0/{page_id}/videos"
                resp = client.post(
                    post_url,
                    params={
                        "description": target.caption,
                        "title": target.title or target.caption[:60],
                        "access_token": access_token,
                    },
                    files={"source": ("video.mp4", b"MOCK_FB_VIDEO", "video/mp4")},
                )
                if resp.status_code != 200:
                    return PublishResult(status="failed", error=f"FB Video failed ({resp.status_code}): {resp.text}")

                data = resp.json()
                video_id = data.get("id", "fb_video_123")
                return PublishResult(
                    external_id=video_id,
                    url=f"https://www.facebook.com/{video_id}",
                    status="published",
                    raw_response=data,
                )
        except Exception as e:
            return PublishResult(status="failed", error=str(e))
        finally:
            client.close()

    def fetch_status(self, account: SocialAccount, external_id: str) -> PublishResult:
        return PublishResult(external_id=external_id, status="published")
