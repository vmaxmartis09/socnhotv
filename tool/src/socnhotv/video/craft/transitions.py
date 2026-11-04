"""Transition Foresight & Continuity Resolver.

Implements motion vector continuity between Scene N and Scene N+1:
Analyzes the final 0.5s motion direction/velocity of the previous scene
and automatically selects the matching transition style (Push, Whip, Zoom-Match, Cut).
Also provides Rapid Montage Proof timeline generation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

SUPPORTED_TRANSITIONS = {
    "push-right", "push-left", "push-up", "push-down",
    "whip-right", "whip-left",
    "zoom-match", "zoom-in", "zoom-out",
    "crossfade", "hard-cut", "flash-cut"
}

@dataclass
class MotionVector:
    direction: str  # "left", "right", "up", "down", "zoom-in", "zoom-out", "static"
    speed: float    # 0.0 to 2.0 (1.0 = normal)
    has_accent: bool = False

@dataclass
class TransitionDecision:
    style: str
    duration_sec: float
    easing: str
    reasoning: str

def resolve_transition(
    prev_motion: Optional[MotionVector] = None,
    requested_style: str = "auto",
    is_climax_or_beat: bool = False
) -> TransitionDecision:
    """Selects the smoothest transition style based on transition foresight motion analysis."""
    if requested_style != "auto" and requested_style in SUPPORTED_TRANSITIONS:
        return TransitionDecision(
            style=requested_style,
            duration_sec=0.35,
            easing="power2.out",
            reasoning=f"User specified style: {requested_style}"
        )

    if prev_motion is None or prev_motion.direction == "static":
        if is_climax_or_beat:
            return TransitionDecision(
                style="flash-cut",
                duration_sec=0.1,
                easing="power1.in",
                reasoning="Static scene ending on audio beat -> Flash cut accent"
            )
        return TransitionDecision(
            style="crossfade",
            duration_sec=0.4,
            easing="power1.inOut",
            reasoning="Static dialogue scene -> Smooth crossfade"
        )

    dir_clean = prev_motion.direction.lower()

    if dir_clean == "right":
        if prev_motion.speed > 1.2:
            return TransitionDecision(
                style="whip-right",
                duration_sec=0.25,
                easing="power3.inOut",
                reasoning="High velocity rightward motion -> Whip Pan Right"
            )
        return TransitionDecision(
            style="push-right",
            duration_sec=0.4,
            easing="power2.out",
            reasoning="Continuous rightward motion -> Push Right"
        )

    if dir_clean == "left":
        if prev_motion.speed > 1.2:
            return TransitionDecision(
                style="whip-left",
                duration_sec=0.25,
                easing="power3.inOut",
                reasoning="High velocity leftward motion -> Whip Pan Left"
            )
        return TransitionDecision(
            style="push-left",
            duration_sec=0.4,
            easing="power2.out",
            reasoning="Continuous leftward motion -> Push Left"
        )

    if dir_clean in {"zoom-in", "forward", "push-in"}:
        return TransitionDecision(
            style="zoom-match",
            duration_sec=0.35,
            easing="power2.inOut",
            reasoning="Zooming in forward -> Zoom Match Hand-off"
        )

    if dir_clean in {"zoom-out", "backward", "pull-out"}:
        return TransitionDecision(
            style="zoom-out",
            duration_sec=0.4,
            easing="power2.out",
            reasoning="Camera pulling back -> Seamless zoom-out reveal"
        )

    return TransitionDecision(
        style="crossfade",
        duration_sec=0.35,
        easing="power1.inOut",
        reasoning="Default fallback transition"
    )

def build_rapid_montage_gsap(
    image_urls: List[str],
    total_duration_sec: float = 2.0,
    container_id: str = "montageContainer"
) -> str:
    """Builds a Rapid Montage Proof GSAP code snippet flashing 3-5 images in 2 seconds."""
    if not image_urls:
        return ""
    
    count = len(image_urls)
    clip_dur = round(total_duration_sec / count, 3)

    script_lines = [
        f"// Rapid Montage Proof ({count} frames, {total_duration_sec}s total)",
        f"const montageTl = gsap.timeline();"
    ]

    for idx, url in enumerate(image_urls):
        start_time = round(idx * clip_dur, 3)
        script_lines.append(
            f"montageTl.set('#{container_id} .frame-{idx}', {{ display: 'block', scale: 1.05 }}, {start_time})"
        )
        script_lines.append(
            f"montageTl.to('#{container_id} .frame-{idx}', {{ scale: 1.0, duration: {clip_dur}, ease: 'none' }}, {start_time})"
        )
        if idx > 0:
            script_lines.append(
                f"montageTl.set('#{container_id} .frame-{idx-1}', {{ display: 'none' }}, {start_time})"
            )

    return "\n".join(script_lines)
