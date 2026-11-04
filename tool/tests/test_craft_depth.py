"""Unit tests for 3-layer spatial depth prompt enrichment and HyperFrames parallax."""
from socnhotv.video.craft.depth import enrich_3layer_prompt, build_3layer_html_composition

def test_enrich_3layer_prompt():
    enriched = enrich_3layer_prompt(
        action_or_core="chỉ tay lên bầu trời giải thích",
        character_key="soc_nho",
        environment_key="rainbow_sky"
    )
    assert "[Foreground]:" in enriched.combined_prompt
    assert "[Midground]:" in enriched.combined_prompt
    assert "[Background]:" in enriched.combined_prompt
    assert "master character soc_nho" in enriched.midground_prompt
    assert "100cm" in enriched.midground_prompt

def test_build_3layer_html_composition():
    html = build_3layer_html_composition(
        bg_asset_url="bg.jpg",
        mid_asset_url="soc_nho.png",
        duration_sec=4.5,
        title_text="Bí Ẩn Cầu Vồng"
      )
    assert "<!DOCTYPE html>" in html
    assert "bgLayer" in html
    assert "midLayer" in html
    assert "layer-fg-bokeh" in html
    assert "Bí Ẩn Cầu Vồng" in html
    assert "gsap.timeline" in html
    assert "const dur = 4.5;" in html
    assert "window.__duration = dur;" in html
