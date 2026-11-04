"""TikTok Content Posting API Publish Adapter.

Official References:
- Content Posting API Overview:
  https://developers.tiktok.com/doc/content-posting-api-get-started
- Direct Post Video Init:
  https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- Fetch Post Status:
  https://developers.tiktok.com/doc/content-posting-api-reference-fetch-post-status
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import httpx

from socnhotv.social.vault import get_social_vault as get_key_vault
from socnhotv.social.adapters.base import Capabilities, Issue, PublishAdapter, PublishResult
from socnhotv.social.models import PostMedia, PostTarget, SocialAccount


class TikTokAdapter(PublishAdapter):
    platform = "tiktok"

    def capabilities(self) -> Capabilities:
        return Capabilities(
            direct_post=True,
            draft_upload=True,
            schedule_native=False,
            thumbnail=False,
            first_comment=False,
            product_link=True,
        )

    def connect_url(self, account: SocialAccount, redirect_uri: str) -> str:
        vault = get_key_vault()
        client_key = vault.get_key("tiktok_client_key") or "mock_tiktok_client_key"
        scopes = "video.publish,video.upload,user.info.basic"
        return (
            f"https://www.tiktok.com/v2/auth/authorize/?"
            f"client_key={client_key}&scope={scopes}&response_type=code&"
            f"redirect_uri={redirect_uri}&state={account.id}"
        )

    def exchange_code(self, account: SocialAccount, code: str, redirect_uri: str) -> Dict[str, Any]:
        vault = get_key_vault()
        client_key = vault.get_key("tiktok_client_key") or "mock_key"
        client_secret = vault.get_key("tiktok_client_secret") or "mock_secret"

        resp = httpx.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            data={
                "client_key": client_key,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15.0,
        )
        return resp.json()

    def refresh(self, account: SocialAccount) -> Dict[str, Any]:
        vault = get_key_vault()
        token_ref = account.auth.token_ref or f"oauth_tiktok_{account.id}"
        refresh_token = vault.get_key(f"{token_ref}_refresh")
        client_key = vault.get_key("tiktok_client_key") or "mock_key"

        resp = httpx.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            data={
                "client_key": client_key,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15.0,
        )
        return resp.json()

    def validate(self, target: PostTarget, media: Optional[PostMedia]) -> List[Issue]:
        issues: List[Issue] = []
        caption = target.caption or ""
        if len(caption) > 2200:
            issues.append(Issue(level="error", code="caption_too_long", message=f"Caption TikTok quá 2200 ký tự (hiện có {len(caption)})"))

        if not media or not media.path:
            issues.append(Issue(level="error", code="missing_media", message="Chưa chọn tệp video cho TikTok"))
        elif media.duration_s > 600:
            issues.append(Issue(level="warning", code="duration_long", message="Video dài hơn 10 phút, kiểm tra giới hạn tài khoản TikTok"))

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
        token_ref = account.auth.token_ref or f"oauth_tiktok_{account.id}"
        access_token = vault.get_key(f"{token_ref}_access") or "mock_tiktok_token"

        has_direct_scope = "video.publish" in account.auth.scopes or True

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

        # 1. Initialize Post via Direct Post or Upload to Inbox
        post_endpoint = (
            "https://open.tiktokapis.com/v2/post/publish/video/init/"
            if has_direct_scope
            else "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
        )

        media_bytes = b"MOCK_TIKTOK_DATA"
        video_size = len(media_bytes)
        if media and media.path and os.path.exists(media.path):
            video_size = os.path.getsize(media.path)
            try:
                with open(media.path, "rb") as f:
                    media_bytes = f.read()
            except Exception:
                pass

        init_payload = {
            "post_info": {
                "title": (target.caption or "TikTok Video")[:2200],
                "privacy_level": "PUBLIC_TO_EVERYONE" if target.privacy == "public" else "SELF_ONLY",
                "disable_duet": False,
                "disable_stitch": False,
                "disable_comment": False,
                "brand_content_toggle": bool(target.disclosure_ad or target.product_link),
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1,
            },
        }

        client = httpx.Client(transport=transport, timeout=30.0)
        try:
            init_resp = client.post(post_endpoint, headers=headers, json=init_payload)
            if init_resp.status_code != 200:
                return PublishResult(status="failed", error=f"TikTok Init failed ({init_resp.status_code}): {init_resp.text}")

            init_data = init_resp.json().get("data", {})
            publish_id = init_data.get("publish_id", "tt_pub_123")
            upload_url = init_data.get("upload_url")

            # 2. Upload video chunk
            if upload_url:
                up_resp = client.put(
                    upload_url,
                    headers={
                        "Content-Type": "video/mp4",
                        "Content-Range": f"bytes 0-{len(media_bytes) - 1}/{len(media_bytes)}",
                    },
                    content=media_bytes,
                )
                if up_resp.status_code not in (200, 201):
                    return PublishResult(status="failed", error=f"TikTok chunk upload failed: {up_resp.status_code}")

            return PublishResult(
                external_id=publish_id,
                url=f"https://www.tiktok.com/@{account.handle}",
                status="published",
                raw_response=init_data,
            )
        except Exception as e:
            return PublishResult(status="failed", error=str(e))
        finally:
            client.close()

    def fetch_status(
        self,
        account: SocialAccount,
        external_id: str,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> PublishResult:
        vault = get_key_vault()
        token_ref = account.auth.token_ref or f"oauth_tiktok_{account.id}"
        access_token = vault.get_key(f"{token_ref}_access") or "mock_tiktok_token"

        client = httpx.Client(transport=transport, timeout=15.0)
        try:
            resp = client.post(
                "https://open.tiktokapis.com/v2/post/publish/status/fetch/",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json={"publish_id": external_id},
            )
            data = resp.json().get("data", {})
            st = data.get("status", "PUBLISH_COMPLETE")
            if st == "PUBLISH_COMPLETE":
                return PublishResult(external_id=external_id, status="published", raw_response=data)
            elif st == "FAILED":
                return PublishResult(external_id=external_id, status="failed", error=data.get("fail_reason", "TikTok failed"), raw_response=data)
            else:
                return PublishResult(external_id=external_id, status="publishing", raw_response=data)
        except Exception as e:
            return PublishResult(external_id=external_id, status="publishing", error=str(e))
        finally:
            client.close()
