from __future__ import annotations

import json
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from socnhotv.video.hyperframes_engine import HyperFramesEngine
from socnhotv.video.platforms import get_platform
from socnhotv.core.providers.mock_provider import create_minimal_png_bytes, create_minimal_wav_bytes


def test_video_engine_build_bundle():
    engine = HyperFramesEngine()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        mock_audio = tmp_path / "voice.mp3"
        mock_audio.write_bytes(create_minimal_wav_bytes(duration_sec=2.5))

        mock_img = tmp_path / "img1.png"
        mock_img.write_bytes(create_minimal_png_bytes(1080, 1920))

        scenes = [
            {"image": str(mock_img), "durationSec": 2.5, "dialogue": "Xin chào!"}
        ]

        bundle_dir = tmp_path / "bundle_tt"
        res_dir = engine.build_from_scenes(
            scenes=scenes,
            audio_voiceover_path=mock_audio,
            platform="tiktok",
            target_dir=bundle_dir,
            title_badge="TEST BUNDLE",
        )

        assert res_dir.resolve() == bundle_dir.resolve()
        assert (bundle_dir / "index.html").exists()
        assert (bundle_dir / "hyperframes.json").exists()
        assert (bundle_dir / "assets" / "voiceover.mp3").exists()

        html = (bundle_dir / "index.html").read_text(encoding="utf-8")
        assert "TEST BUNDLE" in html
        assert "Xin chào!" in html

        config = json.loads((bundle_dir / "hyperframes.json").read_text(encoding="utf-8"))
        assert config["width"] == 1080
        assert config["height"] == 1920
        assert config["fps"] == 30


def test_video_engine_check():
    engine = HyperFramesEngine()
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Bundle with index.html
        (tmp_path / "index.html").write_text("<!DOCTYPE html><html><body></body></html>", encoding="utf-8")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='{"ok": true}', stderr="")
            res = engine.check(tmp_path)
            assert res["ok"] is True


def test_video_engine_render_fallback_ffmpeg():
    engine = HyperFramesEngine()
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        bundle_dir = tmp_path / "bundle"
        assets_dir = bundle_dir / "assets"
        assets_dir.mkdir(parents=True)

        (assets_dir / "scene_01.png").write_bytes(create_minimal_png_bytes(1080, 1920))
        (assets_dir / "voiceover.mp3").write_bytes(create_minimal_wav_bytes(duration_sec=2.0))
        (bundle_dir / "index.html").write_text("dummy", encoding="utf-8")
        (bundle_dir / "hyperframes.json").write_text("{}", encoding="utf-8")

        out_mp4 = tmp_path / "out_tiktok.mp4"

        # Tắt CLI để ép dùng fallback ffmpeg
        with patch.dict("os.environ", {"HYPERFRAMES_USE_CLI": "0"}):
            rendered = engine.render(bundle_dir, out_mp4, platform="tiktok")
            assert rendered.exists()
            assert rendered.stat().st_size > 0
            assert engine.last_engine == "ffmpeg_fallback"

            # Kiểm tra thumbnail
            thumb = out_mp4.with_suffix(".jpg")
            assert thumb.exists()
            assert thumb.stat().st_size > 0


def test_video_engine_render_cli_mock():
    engine = HyperFramesEngine()
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        bundle_dir = tmp_path / "bundle"
        bundle_dir.mkdir()
        out_mp4 = tmp_path / "out_cli.mp4"

        # Mock npx hyperframes render thành công tạo file out_mp4
        def fake_run(cmd, *args, **kwargs):
            if "hyperframes" in cmd and "render" in cmd:
                out_mp4.write_bytes(b"dummy_mp4_bytes")
                return MagicMock(returncode=0, stdout="Render complete", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            with patch.object(engine, "post_process_audio", return_value=out_mp4):
                with patch.object(engine, "extract_thumbnail", return_value=out_mp4.with_suffix(".jpg")):
                    rendered = engine.render(bundle_dir, out_mp4, platform="tiktok")
                    assert rendered.exists()
                    assert engine.last_engine == "hyperframes"
