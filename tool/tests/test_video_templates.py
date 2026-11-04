from __future__ import annotations

import json
from pathlib import Path
import pytest

from socnhotv.core.nodes.registry import NodeRegistry
from socnhotv.video.templates.compose import compose_template
from socnhotv.video.templates.loader import get_template, get_template_dir, list_templates
from socnhotv.video.templates.preview import generate_template_preview
from socnhotv.video.templates.schema import validate_template_data


def test_all_eight_templates_validity():
    templates = list_templates()
    assert len(templates) == 8, f"Expected 8 templates, found {len(templates)}"

    expected_ids = {
        "tiktok-sales-v1",
        "koc-review-v1",
        "affiliate-compare-v1",
        "unboxing-v1",
        "localized-reup-v1",
        "yt-animation-episode-v1",
        "shorts-fact-v1",
        "story-cartoon-v1",
    }
    assert {t.id for t in templates} == expected_ids

    for t in templates:
        assert t.name
        assert t.category in ("sales", "review", "reup", "animation", "education", "affiliate", "story")
        assert len(t.platforms) >= 2
        assert len(t.slots) >= 1

        t_dir = get_template_dir(t.id)
        assert (t_dir / "template.json").exists()
        assert (t_dir / "composition.html.j2").exists()
        assert (t_dir / "styles.css").exists()
        assert (t_dir / "sample.data.json").exists()

        # Validate sample.data.json
        with open(t_dir / "sample.data.json", "r", encoding="utf-8") as f:
            sample_data = json.load(f)
        errors = validate_template_data(t, sample_data)
        assert len(errors) == 0, f"Sample data for {t.id} has validation errors: {errors}"


def test_compose_all_templates():
    for tid in [
        "tiktok-sales-v1",
        "koc-review-v1",
        "affiliate-compare-v1",
        "unboxing-v1",
        "localized-reup-v1",
        "yt-animation-episode-v1",
        "shorts-fact-v1",
        "story-cartoon-v1",
    ]:
        t = get_template(tid)
        t_dir = get_template_dir(tid)
        with open(t_dir / "sample.data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        html = compose_template(
            template_id=tid,
            data=data,
            platform=t.default_platform,
            total_duration=5.0,
        )

        assert "<!DOCTYPE html>" in html
        assert 'data-composition-id="main"' in html
        assert "gsap.timeline" in html
        assert 'window.__timelines["main"] = tl;' in html


def test_node_plugins_registration():
    NodeRegistry.initialize_defaults()
    names = [n.type_name for n in NodeRegistry.list_all()]
    assert "template_render" in names
    assert "platform_export" in names

    t_render = NodeRegistry.get("template_render")
    assert t_render is not None
    assert t_render.category == "Composition"

    p_export = NodeRegistry.get("platform_export")
    assert p_export is not None
    assert p_export.category == "Output"


def test_template_previews_generated():
    # Render preview thật cho ít nhất 3 template
    for tid in ["tiktok-sales-v1", "shorts-fact-v1", "affiliate-compare-v1"]:
        jpg_path = generate_template_preview(tid)
        assert jpg_path.exists()
        assert jpg_path.stat().st_size > 0
        mp4_path = jpg_path.with_suffix(".mp4")
        assert mp4_path.exists()
        assert mp4_path.stat().st_size > 0
