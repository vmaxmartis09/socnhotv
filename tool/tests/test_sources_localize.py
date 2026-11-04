from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from socnhotv.core.api.app import app
from socnhotv.sources.asr import parse_vtt_subtitles
from socnhotv.sources.models import SourceItem
from socnhotv.sources.rewrite import rewrite_script_lines
from socnhotv.sources.translate import condense_text, translate_segments
from socnhotv.workspace import project_path

client = TestClient(app)


def test_vtt_parser(tmp_path: Path):
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:04.500
大家好，今天给大家分享一个好东西。

00:00:05.000 --> 00:00:08.000
看这个超级实用的工具。
"""
    vtt_file = tmp_path / "sub.vtt"
    vtt_file.write_text(vtt_content, encoding="utf-8")

    segments = parse_vtt_subtitles(vtt_file)
    assert len(segments) == 2
    assert segments[0]["start"] == 1.0
    assert segments[0]["end"] == 4.5
    assert "大家好" in segments[0]["text"]


def test_translation_condense_length_constraint():
    # Long text exceeding 15 chars/s * 1.25
    long_vi = "Đây là một câu văn tiếng Việt cực kỳ dài dòng vượt quá giới hạn thời lượng cho phép của câu gốc"
    # Duration 1.5s -> max chars = int(1.5 * 15 * 1.25) = 28
    condensed = condense_text(long_vi, max_chars=28)
    assert len(condensed) <= 28
    assert len(condensed) > 0


def test_translation_glossary_replacement():
    raw_segments = [{
        "start": 0.0,
        "end": 3.0,
        "text": "家人们，看这个，非常棒！",
    }]
    trans = translate_segments("soc-nho-tv", raw_segments)
    assert len(trans) == 1
    text = trans[0]["text"]
    assert "Cả nhà ơi" in text or "Xem cái này nè" in text or "tuyệt vời" in text


def test_rewrite_styles():
    translated = [
        {"start": 0.0, "end": 3.0, "text": "Hôm nay mình chia sẻ sản phẩm này"},
        {"start": 3.0, "end": 6.0, "text": "Cách sử dụng rất đơn giản"},
        {"start": 6.0, "end": 9.0, "text": "Mọi người hãy dùng thử"},
    ]

    # Faithful
    faithful = rewrite_script_lines(translated, style="faithful")
    assert len(faithful) == 3
    assert faithful[0]["text"] == "Hôm nay mình chia sẻ sản phẩm này"

    # Hook boost
    hook = rewrite_script_lines(translated, style="hook_boost")
    assert "3 giây" in hook[0]["text"]
    assert "theo dõi ngay" in hook[2]["text"]

    # Character (Sóc Nhỏ Bi)
    char = rewrite_script_lines(translated, style="character")
    assert "Bi" in char[0]["text"]
    assert "hẹn gặp lại" in char[2]["text"].lower() or "tập sau" in char[2]["text"].lower()


def test_mode_l_blocked_for_reference_only():
    # Create reference_only source
    s = SourceItem(
        id="douyin_test_ref_only",
        project_id="soc-nho-tv",
        platform="douyin",
        url="https://v.douyin.com/test1",
        rights="reference_only",
    )
    source_dir = project_path("soc-nho-tv", "raw", "douyin_test_ref_only")
    source_dir.mkdir(parents=True, exist_ok=True)
    meta_p = source_dir / "meta.json"
    with open(meta_p, "w", encoding="utf-8") as f:
        f.write(s.model_dump_json())

    # Call /localize with mode="L" -> expect 400 rejection
    res = client.post(
        "/projects/soc-nho-tv/sources/douyin_test_ref_only/localize",
        json={"mode": "L", "style": "faithful"},
    )
    assert res.status_code == 400
    assert "reference_only" in res.json()["detail"]


def test_mode_r_creates_render_request_with_source_ref():
    s = SourceItem(
        id="douyin_test_mode_r",
        project_id="soc-nho-tv",
        platform="douyin",
        url="https://v.douyin.com/test2",
        rights="reference_only",  # Mode R is safe for reference_only!
    )
    source_dir = project_path("soc-nho-tv", "raw", "douyin_test_mode_r")
    source_dir.mkdir(parents=True, exist_ok=True)
    with open(source_dir / "meta.json", "w", encoding="utf-8") as f:
        f.write(s.model_dump_json())

    # Create dummy transcript.orig.json
    with open(source_dir / "transcript.orig.json", "w", encoding="utf-8") as f:
        json.dump([{"start": 0.0, "end": 3.0, "text": "你好"}], f)

    with patch("socnhotv.sources.localize_pipeline.run_revoice") as mock_revoice:
        mock_revoice.return_value = source_dir / "voice.vi.mp3"

        res = client.post(
            "/projects/soc-nho-tv/sources/douyin_test_mode_r/localize",
            json={
                "mode": "R",
                "style": "hook_boost",
                "voice_id": "soc-nho",
                "platforms": ["tiktok", "youtube"],
            },
        )

        assert res.status_code == 200
        data = res.json()
        assert data["mode"] == "R"
        assert data["source_id"] == "douyin_test_mode_r"
        assert "tiktok" in data["platforms"]
        assert "youtube" in data["platforms"]

        # Verify render job file in runs/render_queue
        from socnhotv.video.contracts import get_render
        job = get_render("soc-nho-tv", data["render_job_id"])
        assert job.status in ["queued", "rendering", "done"]
