from __future__ import annotations

import pytest
from socnhotv.video.platforms import (
    PLATFORMS,
    PlatformPreset,
    fit_strategy,
    get_platform,
    list_platforms,
)


def test_platform_presets_completeness():
    expected_ids = {"tiktok", "douyin", "reels", "shorts", "youtube", "facebook"}
    assert set(PLATFORMS.keys()) == expected_ids

    all_presets = list_platforms()
    assert len(all_presets) == 6

    for p in all_presets:
        assert isinstance(p, PlatformPreset)
        assert p.width > 0
        assert p.height > 0
        assert p.fps == 30
        assert p.safe_zone.top > 0
        assert p.safe_zone.bottom > 0
        assert p.loudness_lufs == -14.0
        assert p.audio_bitrate == "192k"
        assert p.codec == "libx264"


def test_get_platform():
    tt = get_platform("tiktok")
    assert tt.id == "tiktok"
    assert tt.width == 1080
    assert tt.height == 1920
    assert tt.safe_zone.top == 180
    assert tt.safe_zone.bottom == 320
    assert tt.safe_zone.left == 40
    assert tt.safe_zone.right == 120

    yt = get_platform("youtube")
    assert yt.width == 1920
    assert yt.height == 1080
    assert yt.safe_zone.top == 60
    assert yt.safe_zone.bottom == 90
    assert yt.max_duration_sec is None

    fb = get_platform("facebook")
    assert fb.width == 1080
    assert fb.height == 1350
    assert fb.aspect_ratio == "4:5"

    with pytest.raises(ValueError):
        get_platform("unsupported_platform")


def test_fit_strategy_cover():
    res = fit_strategy(1920, 1080, 1080, 1920, strategy="cover")
    assert res["strategy"] == "cover"
    assert res["target_w"] == 1080
    assert res["target_h"] == 1920
    assert res["scaled_h"] == 1920
    assert res["crop_x"] > 0
    assert "scale=" in res["ffmpeg_filter"]
    assert "crop=" in res["ffmpeg_filter"]


def test_fit_strategy_contain():
    res = fit_strategy(1920, 1080, 1080, 1920, strategy="contain")
    assert res["strategy"] == "contain"
    assert res["target_w"] == 1080
    assert res["target_h"] == 1920
    assert res["scaled_w"] == 1080
    assert res["pad_y"] > 0
    assert "scale=" in res["ffmpeg_filter"]
    assert "pad=" in res["ffmpeg_filter"]


def test_fit_strategy_blur_pad():
    res = fit_strategy(1920, 1080, 1080, 1920, strategy="blur-pad")
    assert res["strategy"] == "blur-pad"
    assert "boxblur" in res["ffmpeg_filter"]
    assert "overlay" in res["ffmpeg_filter"]
