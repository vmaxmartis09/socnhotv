"""Unit tests for Transition Foresight and Rapid Montage continuity."""
from socnhotv.video.craft.transitions import (
    resolve_transition,
    build_rapid_montage_gsap,
    MotionVector,
)

def test_resolve_transition_foresight():
    # Moving rightward with normal speed -> push-right
    decision_right = resolve_transition(MotionVector(direction="right", speed=1.0))
    assert decision_right.style == "push-right"
    assert decision_right.duration_sec > 0

    # High velocity right -> whip-right
    decision_whip = resolve_transition(MotionVector(direction="right", speed=1.5))
    assert decision_whip.style == "whip-right"

    # Moving leftward -> push-left
    decision_left = resolve_transition(MotionVector(direction="left", speed=1.0))
    assert decision_left.style == "push-left"

    # Forward zoom -> zoom-match
    decision_zoom = resolve_transition(MotionVector(direction="zoom-in", speed=1.0))
    assert decision_zoom.style == "zoom-match"

    # Static with beat -> flash-cut
    decision_beat = resolve_transition(MotionVector(direction="static", speed=0.0), is_climax_or_beat=True)
    assert decision_beat.style == "flash-cut"

def test_build_rapid_montage_gsap():
    urls = ["img1.png", "img2.png", "img3.png"]
    snippet = build_rapid_montage_gsap(urls, total_duration_sec=1.5)
    assert "Rapid Montage Proof (3 frames" in snippet
    assert "frame-0" in snippet
    assert "frame-1" in snippet
    assert "frame-2" in snippet
