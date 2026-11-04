"""Unit tests for camera presets and GSAP code generation."""
from socnhotv.video.craft.camera import get_camera_preset, build_camera_gsap_snippet, CAMERA_PRESETS

def test_camera_presets_integrity():
    assert "push-in" in CAMERA_PRESETS
    assert "dolly-out" in CAMERA_PRESETS
    assert "lateral-pan" in CAMERA_PRESETS
    assert "dutch-angle" in CAMERA_PRESETS
    assert "punch-in" in CAMERA_PRESETS

    for name, p in CAMERA_PRESETS.items():
        assert p.scale_from > 0
        assert p.scale_to > 0
        assert p.easing != ""
        assert p.focal_length_equiv != ""

def test_camera_snippet_generation():
    snippet = build_camera_gsap_snippet("push-in", target_selector="#characterScene", duration_sec=3.5)
    assert 'gsap.fromTo("#characterScene"' in snippet
    assert "duration: 3.5" in snippet
    assert "scale:" in snippet
