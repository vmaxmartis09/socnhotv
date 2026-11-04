"""Cinematography Camera Presets for HyperFrames.

Implements the 5 classic camera moves and lens presets:
1. Dramatic Push-In (Slow subtle zoom into subject's eyes/acorns)
2. Dolly-Out Reveal (Starts tight, pulls back to reveal grandeur)
3. Lateral Parallax Pan (Horizontal sliding movement with depth disparity)
4. Dutch Angle Accent (Dynamic slight tilt for intrigue or excitement)
5. Punch-In Beat (Instant 15-25% crop on key audio punchlines)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class CameraPreset:
    name: str
    description: str
    focal_length_equiv: str
    scale_from: float
    scale_to: float
    translate_x_from_px: float
    translate_x_to_px: float
    translate_y_from_px: float
    translate_y_to_px: float
    rotation_from_deg: float
    rotation_to_deg: float
    easing: str

CAMERA_PRESETS: Dict[str, CameraPreset] = {
    "push-in": CameraPreset(
        name="push-in",
        description="Dramatic Push-In (tiêu cự 50mm, tiến gần chủ thể tăng độ tập trung)",
        focal_length_equiv="50mm",
        scale_from=1.0,
        scale_to=1.08,
        translate_x_from_px=0.0,
        translate_x_to_px=0.0,
        translate_y_from_px=0.0,
        translate_y_to_px=-15.0,
        rotation_from_deg=0.0,
        rotation_to_deg=0.0,
        easing="power1.out"
    ),
    "dolly-out": CameraPreset(
        name="dolly-out",
        description="Dolly-Out Reveal (tiêu cự 35mm, lùi rộng để mở rộng bối cảnh)",
        focal_length_equiv="35mm",
        scale_from=1.12,
        scale_to=1.0,
        translate_x_from_px=0.0,
        translate_x_to_px=0.0,
        translate_y_from_px=-20.0,
        translate_y_to_px=0.0,
        rotation_from_deg=0.0,
        rotation_to_deg=0.0,
        easing="power2.out"
    ),
    "lateral-pan": CameraPreset(
        name="lateral-pan",
        description="Lateral Parallax Pan (lướt ngang tạo cảm giác nhân vật di chuyển)",
        focal_length_equiv="50mm",
        scale_from=1.05,
        scale_to=1.05,
        translate_x_from_px=-40.0,
        translate_x_to_px=40.0,
        translate_y_from_px=0.0,
        translate_y_to_px=0.0,
        rotation_from_deg=0.0,
        rotation_to_deg=0.0,
        easing="sine.inOut"
    ),
    "dutch-angle": CameraPreset(
        name="dutch-angle",
        description="Dutch Angle (góc nghiêng nhẹ 2-3 độ tạo kịch tính hoặc tò mò)",
        focal_length_equiv="28mm",
        scale_from=1.04,
        scale_to=1.08,
        translate_x_from_px=0.0,
        translate_x_to_px=0.0,
        translate_y_from_px=0.0,
        translate_y_to_px=-10.0,
        rotation_from_deg=-2.5,
        rotation_to_deg=1.5,
        easing="power1.inOut"
    ),
    "punch-in": CameraPreset(
        name="punch-in",
        description="Punch-In Beat (cắt giật nhanh cận cảnh tại khoảnh khắc hé lộ bí mật)",
        focal_length_equiv="85mm",
        scale_from=1.0,
        scale_to=1.22,
        translate_x_from_px=0.0,
        translate_x_to_px=0.0,
        translate_y_from_px=0.0,
        translate_y_to_px=-30.0,
        rotation_from_deg=0.0,
        rotation_to_deg=0.0,
        easing="power3.out"
    )
}

def get_camera_preset(name: str) -> CameraPreset:
    """Retrieves a camera preset by name, defaulting to push-in."""
    key = name.lower().strip()
    return CAMERA_PRESETS.get(key, CAMERA_PRESETS["push-in"])

def build_camera_gsap_snippet(
    preset_name: str,
    target_selector: str = "#cameraTarget",
    duration_sec: float = 4.0
) -> str:
    """Generates GSAP code implementing the camera preset smoothly."""
    preset = get_camera_preset(preset_name)
    snippet = f"""
// Camera Move: {preset.description}
gsap.fromTo("{target_selector}",
  {{
    scale: {preset.scale_from},
    x: {preset.translate_x_from_px},
    y: {preset.translate_y_from_px},
    rotation: {preset.rotation_from_deg}
  }},
  {{
    scale: {preset.scale_to},
    x: {preset.translate_x_to_px},
    y: {preset.translate_y_to_px},
    rotation: {preset.rotation_to_deg},
    duration: {duration_sec},
    ease: "{preset.easing}"
  }}
);
""".strip()
    return snippet
