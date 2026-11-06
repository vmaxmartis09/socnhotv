"""Hậu kỳ video (mastering âm thanh) không được đổi tốc độ / làm cụt video."""
from __future__ import annotations

import subprocess

import pytest

from socnhotv.video.hyperframes_engine import HyperFramesEngine


def test_post_process_audio_keeps_duration(tmp_path):
    eng = HyperFramesEngine()
    mp4 = tmp_path / "v.mp4"
    subprocess.run(
        [eng.ffmpeg, "-y", "-loglevel", "error",
         "-f", "lavfi", "-i", "color=c=black:s=320x180:d=6",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=6",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(mp4)],
        check=True,
    )
    before = eng.get_audio_duration(mp4)
    eng.post_process_audio(mp4, target_lufs=-14.0)
    after = eng.get_audio_duration(mp4)
    assert before == pytest.approx(6.0, abs=0.15)
    assert after == pytest.approx(before, abs=0.15)  # trước đây ~5.45s (atempo 1.10 + -shortest)
