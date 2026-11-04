import json
import httpx
import pytest

from socnhotv.social.adapters.meta import MetaAdapter
from socnhotv.social.adapters.tiktok import TikTokAdapter
from socnhotv.social.adapters.youtube import YouTubeAdapter
from socnhotv.social.models import PostMedia, PostTarget, SocialAccount


def test_youtube_adapter_resumable_mock():
    adapter = YouTubeAdapter()
    account = SocialAccount(
        id="acc_yt_test",
        platform="youtube",
        handle="@test",
        display_name="YT Test",
    )
    target = PostTarget(
        account_id=account.id,
        platform="youtube",
        title="Video thử nghiệm YouTube",
        description="Mô tả video chi tiết",
        privacy="public",
    )
    media = PostMedia(path="dummy.mp4", duration_s=45.0)

    # Mock HTTP transport
    def handler(request: httpx.Request):
        url = str(request.url)
        if "videos?uploadType=resumable" in url:
            return httpx.Response(
                200,
                headers={"Location": "https://www.googleapis.com/upload/session_123"},
                content=b"",
            )
        elif "session_123" in url:
            return httpx.Response(
                200,
                json={"id": "yt_vid_success_123", "snippet": {"title": "Uploaded"}},
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    res = adapter.publish(account, target, media, transport=transport)

    assert res.status == "published"
    assert res.external_id == "yt_vid_success_123"
    assert "https://www.youtube.com/watch?v=yt_vid_success_123" in (res.url or "")


def test_youtube_quota_exceeded():
    adapter = YouTubeAdapter()
    account = SocialAccount(id="acc_yt", platform="youtube", handle="@test", display_name="YT")
    target = PostTarget(account_id=account.id, platform="youtube", title="Title")

    def handler(request: httpx.Request):
        return httpx.Response(
            403,
            json={"error": {"errors": [{"reason": "quotaExceeded"}]}},
        )

    transport = httpx.MockTransport(handler)
    res = adapter.publish(account, target, PostMedia(path="dummy.mp4"), transport=transport)
    assert res.status == "failed"
    assert "quota" in (res.error or "").lower()


def test_tiktok_adapter_mock():
    adapter = TikTokAdapter()
    account = SocialAccount(id="acc_tt", platform="tiktok", handle="@test", display_name="TT")
    target = PostTarget(account_id=account.id, platform="tiktok", caption="TikTok test caption")

    def handler(request: httpx.Request):
        url = str(request.url)
        if "video/init" in url:
            return httpx.Response(
                200,
                json={"data": {"publish_id": "tt_pub_999", "upload_url": "https://upload.tiktok.com/chunk"}},
            )
        elif "upload.tiktok.com" in url:
            return httpx.Response(200, content=b"")
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    res = adapter.publish(account, target, PostMedia(path="dummy.mp4"), transport=transport)
    assert res.status == "published"
    assert res.external_id == "tt_pub_999"


def test_meta_instagram_reels_mock():
    adapter = MetaAdapter(platform="instagram")
    account = SocialAccount(id="acc_ig", platform="instagram", handle="@ig", display_name="IG")
    target = PostTarget(account_id=account.id, platform="instagram", caption="IG Reels test")

    def handler(request: httpx.Request):
        path = request.url.path
        if path.endswith("/media_publish"):
            return httpx.Response(200, json={"id": "media_789"})
        elif path.endswith("/media"):
            return httpx.Response(200, json={"id": "container_456"})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    res = adapter.publish(account, target, PostMedia(path="dummy.mp4"), transport=transport)
    assert res.status == "published"
    assert res.external_id == "media_789"
