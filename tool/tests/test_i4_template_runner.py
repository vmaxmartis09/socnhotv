"""I4 — template chạy thật: CSS Jinja phải được render, khung thiết kế bù zoom, runner dựng MP4 + báo cáo trung thực.

Chạy trong sandbox của conftest (không ghi data/ thật). Test render thật cần hyperframes + ffmpeg, tự bỏ qua nếu thiếu.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from socnhotv.video.hyperframes_engine import FFMPEG_EXE, find_hyperframes_bin
from socnhotv.video.templates.compose import compose_template
from socnhotv.video.templates.loader import get_template_dir, list_templates
from socnhotv.video.templates.runner import run_template

ALL_IDS = sorted(t.id for t in list_templates())


@pytest.mark.parametrize("template_id", ALL_IDS)
def test_composed_html_has_no_unresolved_jinja(template_id):
    """Trước I4, {{ safe_zone.top }} trong styles.css lọt nguyên vào HTML -> css_parse_error, bố cục vỡ."""
    t_dir = get_template_dir(template_id)
    sample = json.loads((t_dir / "sample.data.json").read_text(encoding="utf-8"))
    for plat in ("tiktok", "youtube"):
        html = compose_template(template_id, sample, platform=plat, total_duration=5.0)
        assert "{{" not in html and "{%" not in html, f"{template_id}/{plat}: Jinja chưa được render"
        assert "zoom: 2.0" in html or "zoom: 1.0" in html, "thiếu bù khung thiết kế (zoom)"


def test_design_safe_zone_is_half_of_preset():
    """Khung thiết kế là nửa preset: tiktok top=180 -> CSS thấy 90 (khớp mặc định `or 90` của template)."""
    html = compose_template("shorts-fact-v1", {"fact_question": "q", "fact_statement": "s"}, platform="tiktok", total_duration=5.0)
    assert "top: 90px;" in html
    assert "bottom: 176px;" in html  # (160 + 16) = 320/2 + 16


def test_report_flags_sample_data_and_missing_voice(tmp_path):
    """Không voice_audio + slot trống: báo cáo phải nói thật (không im lặng nhận là dữ liệu người dùng)."""
    if not find_hyperframes_bin():
        pytest.skip("không có hyperframes CLI")
    rep = run_template("shorts-fact-v1", tmp_path / "out", slots={"fact_question": "CÂU HỎI RIÊNG", "fact_statement": "Sự thật riêng"})
    assert "fact_question" in rep.slots_from_user
    assert "stat_number" in rep.slots_from_sample
    assert rep.audio_source in ("template_sample_asset", "none")
    assert any("sample.data.json" in w for w in rep.warnings)
    assert (tmp_path / "out" / "report.json").exists()


@pytest.mark.skipif(not (find_hyperframes_bin() and shutil.which("ffprobe")), reason="cần hyperframes + ffprobe")
def test_real_render_with_user_voice(tmp_path):
    """Dựng MP4 thật 1080x1920 qua HyperFrames, có audio stream, vùng nội dung không rỗng."""
    voice = tmp_path / "voice.mp3"
    subprocess.run(
        [FFMPEG_EXE, "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=3", "-q:a", "5", str(voice)],
        check=True, capture_output=True,
    )
    t_dir = get_template_dir("shorts-fact-v1")
    sample = json.loads((t_dir / "sample.data.json").read_text(encoding="utf-8"))
    rep = run_template("shorts-fact-v1", tmp_path / "out", slots=sample, voice_audio=voice, platform="tiktok")
    assert rep.ok, rep.error
    assert rep.engine == "hyperframes"
    assert (rep.width, rep.height) == (1080, 1920)
    assert rep.has_audio_stream
    assert rep.audio_source == "voice_audio"
    assert 2.5 <= rep.duration_sec <= 6.0
    assert Path(rep.mp4).stat().st_size > 20_000
    assert rep.slots_from_sample == []
