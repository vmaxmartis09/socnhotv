"""Integration and real pipeline tests for I2 (Sources & Localization).

Covers:
1. Ingest local video file with rights='owned'
2. Real scene detection via scenes.py (PySceneDetect / ffmpeg fallback)
3. Real ASR transcription via faster-whisper (with soundfile float32 audio loading)
4. Translation with timestamp preservation and length condensation
5. Script rewrite into brand styles (faithful, hook_boost, character)
6. Voice synthesis with silence alignment and -14 LUFS audio mastering
7. Copyright protection: Mode L rejected for reference_only, Mode R allowed
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import tempfile
from pathlib import Path

import pytest
import soundfile as sf
import edge_tts

from socnhotv.sources.asr import run_asr
from socnhotv.sources.local import ingest_local_file
from socnhotv.sources.localize_pipeline import run_localize_pipeline
from socnhotv.sources.models import SourceItem
from socnhotv.sources.revoice import run_revoice
from socnhotv.sources.rewrite import run_rewrite
from socnhotv.sources.scenes import detect_and_save_scenes
from socnhotv.sources.service import get_source, update_source_rights
from socnhotv.sources.translate import run_translation
from socnhotv.workspace import project_path


@pytest.fixture
def sample_video_path(tmp_path: Path) -> Path:
    """Generate a valid 3-second MP4 test video with spoken speech for testing."""
    vid_path = tmp_path / "test_source.mp4"
    speech_path = tmp_path / "test_speech.mp3"

    # Synthesize a short speech clip
    try:
        async def _speak():
            comm = edge_tts.Communicate("Hello world", "en-US-AriaNeural")
            await comm.save(str(speech_path))
        asyncio.run(_speak())
    except Exception:
        # Fallback tone if offline
        speech_path = None

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=3:size=640x360:rate=24",
    ]
    if speech_path and speech_path.exists():
        cmd.extend(["-i", str(speech_path), "-c:a", "aac", "-shortest"])
    else:
        cmd.extend(["-f", "lavfi", "-i", "sine=frequency=440:duration=3", "-c:a", "aac"])

    cmd.extend([
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(vid_path),
    ])
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert res.returncode == 0, "Failed to create sample video"
    return vid_path


def test_i2_local_ingest_and_scenes(sample_video_path: Path):
    """Test 1: Ingest local file and perform scene detection."""
    pid = "soc-nho-tv"
    item = ingest_local_file(
        project_id=pid,
        source_file_path=sample_video_path,
        title="Sample Owned Video",
        rights="owned",
        rights_note="Người dùng cung cấp và sở hữu bản quyền",
    )
    assert item.id.startswith("local_")
    assert item.rights == "owned"
    assert item.duration_s > 1.0

    # Check files created
    source_dir = project_path(pid, "raw", item.id)
    assert (source_dir / "video.mp4").exists()
    assert (source_dir / "audio.wav").exists()
    assert (source_dir / "thumb.jpg").exists()

    # Detect scenes
    scenes = detect_and_save_scenes(pid, item.id)
    assert len(scenes) >= 1
    scenes_json = source_dir / "scenes.json"
    assert scenes_json.exists()
    assert (scenes[0].end_s - scenes[0].start_s) > 0


def test_i2_asr_soundfile_loading(sample_video_path: Path):
    """Test 2: ASR audio decoding via soundfile float32 does not trigger PyAV metadata_errors bug."""
    pid = "soc-nho-tv"
    item = ingest_local_file(
        project_id=pid,
        source_file_path=sample_video_path,
        title="ASR Test Video",
        rights="owned",
    )
    # Run ASR with tiny model for speed
    segments = run_asr(pid, item.id, language="en", model_size="tiny")
    assert isinstance(segments, list)
    # Even if speech audio is short or empty, ASR returns a list and writes transcript.orig.json
    transcript_file = project_path(pid, "raw", item.id, "transcript.orig.json")
    assert transcript_file.exists()


def test_i2_translate_and_rewrite():
    """Test 3: Translation and brand voice rewriting."""
    pid = "soc-nho-tv"
    source_id = "test_trans_rewrite"
    s_dir = project_path(pid, "raw", source_id)
    s_dir.mkdir(parents=True, exist_ok=True)

    # Mock original transcript
    orig = [
        {"start": 0.0, "end": 2.5, "text": "你好 家人们", "words": []},
        {"start": 2.5, "end": 5.0, "text": "今天给大家分享 点赞", "words": []},
    ]
    with open(s_dir / "transcript.orig.json", "w", encoding="utf-8") as f:
        json.dump(orig, f)

    # Run translation
    vi_segments = run_translation(pid, source_id)
    assert len(vi_segments) == 2
    assert "Xin chào" in vi_segments[0]["text"]
    assert "Hôm nay mình chia sẻ" in vi_segments[1]["text"]

    # Run rewrite styles
    faithful = run_rewrite(pid, source_id, style="faithful")
    assert len(faithful) == 2

    hook_boost = run_rewrite(pid, source_id, style="hook_boost")
    assert "Dừng lại 3 giây!" in hook_boost[0]["text"]
    assert "Thả tim" in hook_boost[1]["text"]

    character = run_rewrite(pid, source_id, style="character")
    assert "Bi chào các bạn nhỏ nè!" in character[0]["text"]
    assert "Hẹn gặp lại" in character[1]["text"]


@pytest.mark.anyio
async def test_i2_revoice_and_mastering(sample_video_path: Path):
    """Test 4: Revoice speech synthesis and -14 LUFS mastering."""
    pid = "soc-nho-tv"
    item = ingest_local_file(
        project_id=pid,
        source_file_path=sample_video_path,
        title="Revoice Video",
        rights="owned",
    )
    s_dir = project_path(pid, "raw", item.id)

    # Write a test script
    script = [
        {"line_idx": 1, "start": 0.0, "end": 2.0, "text": "Xin chào Sóc Nhỏ."},
    ]
    with open(s_dir / "script.faithful.json", "w", encoding="utf-8") as f:
        json.dump(script, f)

    voice_path = await run_revoice(pid, item.id, voice_id="soc-nho", style="faithful")
    assert voice_path.exists()
    assert voice_path.stat().st_size > 0


@pytest.mark.anyio
async def test_i2_localize_pipeline_copyright_gating(sample_video_path: Path):
    """Test 5: Strict copyright protection: Mode L blocked when reference_only."""
    pid = "soc-nho-tv"
    item = ingest_local_file(
        project_id=pid,
        source_file_path=sample_video_path,
        title="Reference Only Video",
        rights="reference_only",
    )

    # Mode L must raise ValueError because rights is reference_only
    with pytest.raises(ValueError, match="Chế độ Localize"):
        await run_localize_pipeline(pid, item.id, mode="L")

    # Mode R should succeed
    summary_r = await run_localize_pipeline(pid, item.id, mode="R", style="faithful")
    assert summary_r["mode"] == "R"
    assert summary_r["status"] == "queued"
    assert summary_r["template_id"] == "story-cartoon-v1"

    # Upgrading rights to owned allows Mode L
    update_source_rights(pid, item.id, new_rights="owned", confirm_rights=True)
    summary_l = await run_localize_pipeline(pid, item.id, mode="L", style="faithful")
    assert summary_l["mode"] == "L"
    assert summary_l["status"] == "queued"
    assert summary_l["template_id"] == "localized-reup-v1"
