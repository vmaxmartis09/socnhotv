import pytest
from socnhotv.social.models import PostTarget, SocialAccount
from socnhotv.social.platform_rules import (
    Issue,
    get_platform_rule,
    pick_best_variant,
    validate,
)


def test_platform_rules_definitions():
    yt_rule = get_platform_rule("youtube")
    assert yt_rule.max_title_length == 100
    assert yt_rule.max_caption_length == 5000
    assert yt_rule.daily_quota_limit == 6

    tt_rule = get_platform_rule("tiktok")
    assert tt_rule.max_caption_length == 2200
    assert tt_rule.recommended_aspect_ratios == ["9:16"]
    assert tt_rule.daily_quota_limit == 10

    th_rule = get_platform_rule("threads")
    assert th_rule.max_caption_length == 500

    x_rule = get_platform_rule("x")
    assert x_rule.max_caption_length == 280


def test_validate_video_duration_and_size():
    video = {
        "title": "Long Video",
        "duration_s": 700.0,  # exceeds TikTok 600s
        "size_mb": 5000.0,    # exceeds TikTok 4000MB
        "width": 1080,
        "height": 1920,
    }
    target = {"platform": "tiktok", "title": "Test", "caption": "Cap"}
    issues = validate(video, target)

    codes = [i.code for i in issues]
    assert "duration_exceeded" in codes
    assert "size_exceeded" in codes
    assert any(i.level == "error" for i in issues)


def test_validate_aspect_ratio_mismatch():
    # 16:9 video onto TikTok without 9:16 variant
    video_16x9 = {
        "title": "Horizontal",
        "duration_s": 45.0,
        "size_mb": 15.0,
        "width": 1920,
        "height": 1080,
        "variants": {"youtube": "output/yt.mp4"},
    }
    target_tt = {"platform": "tiktok", "title": "Test", "caption": "Cap"}
    issues = validate(video_16x9, target_tt)
    codes = [i.code for i in issues]
    assert "ratio_mismatch" in codes

    # With 9:16 variant available, no ratio mismatch warning
    video_with_variant = {
        "title": "Horizontal with variant",
        "duration_s": 45.0,
        "size_mb": 15.0,
        "width": 1920,
        "height": 1080,
        "variants": {"youtube": "output/yt.mp4", "tiktok": "output/tt.mp4"},
    }
    issues_ok = validate(video_with_variant, target_tt)
    assert "ratio_mismatch" not in [i.code for i in issues_ok]


def test_validate_text_limits_and_account_status():
    target = {
        "platform": "x",
        "title": "Short title",
        "caption": "A" * 300,  # X max is 280
        "hashtags": ["#1", "#2", "#3", "#4", "#5"],  # X max is 4
    }
    acc_expired = SocialAccount(
        id="acc_exp",
        platform="x",
        handle="@test",
        display_name="Test X",
        status="expired",
    )
    issues = validate(None, target, acc_expired)
    codes = [i.code for i in issues]
    assert "caption_too_long" in codes
    assert "too_many_hashtags" in codes
    assert "account_expired" in codes


def test_pick_best_variant():
    variants = {
        "youtube": "output/yt.mp4",
        "shorts": "output/shorts.mp4",
        "tiktok": "output/tt.mp4",
    }
    k_tt, path_tt = pick_best_variant(variants, "tiktok")
    assert k_tt == "tiktok"
    assert path_tt == "output/tt.mp4"

    k_yt, path_yt = pick_best_variant(variants, "youtube")
    assert k_yt == "youtube"
    assert path_yt == "output/yt.mp4"

    k_ig, path_ig = pick_best_variant(variants, "instagram")
    assert k_ig in ["tiktok", "shorts"]  # priority order
