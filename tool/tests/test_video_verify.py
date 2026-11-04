from __future__ import annotations

import os
from pathlib import Path
import pytest

from socnhotv.video.verify import verify_video, VerifyReport


def test_verify_video_structure():
    """Kiểm tra verify_video với file mp4 thực tế trong dự án."""
    repo_root = Path(__file__).resolve().parents[2]
    candidate = repo_root / "data" / "projects" / "soc-nho-tv" / "output" / "e3_real_output.mp4"

    if not candidate.exists():
        pytest.skip("Chưa có e3_real_output.mp4 để kiểm tra")

    # e3_real_output.mp4 dài 2.57s
    report = verify_video(candidate, expect_duration=2.57, tol=1.0)
    assert isinstance(report, VerifyReport)
    assert report.duration_s > 0
    assert report.width == 1080
    assert report.height == 1920
    assert report.video_codec in ("h264", "hevc", "av1", "vp9")
    assert report.scores["character_consistency"] == 5.0
