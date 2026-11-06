"""Cinematography Camera Presets for HyperFrames.

Implements classic camera moves and lens presets:
1. Dramatic Push-In (Slow subtle zoom into subject's eyes/acorns)
2. Dolly-Out Reveal (Starts tight, pulls back to reveal grandeur)
3. Lateral Parallax Pan (Horizontal sliding movement with depth disparity)
4. Dutch Angle Accent (Dynamic slight tilt for intrigue or excitement)
5. Punch-In Beat (Instant 15-25% crop on key audio punchlines)
6. Pan Left / Pan Right (Directed horizontal tracking)
7. Tilt Up / Tilt Down (Vertical reveal)
8. Ken Burns (Simultaneous scale and directional drift)
9. Static (Subtle breathing hold, avoid dead freeze)
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
        easing="power1.out",
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
        easing="power2.out",
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
        easing="sine.inOut",
    ),
    "pan-left": CameraPreset(
        name="pan-left",
        description="Pan Left (lia máy sang trái bám theo hướng nhìn)",
        focal_length_equiv="50mm",
        scale_from=1.05,
        scale_to=1.05,
        translate_x_from_px=35.0,
        translate_x_to_px=-35.0,
        translate_y_from_px=0.0,
        translate_y_to_px=0.0,
        rotation_from_deg=0.0,
        rotation_to_deg=0.0,
        easing="sine.inOut",
    ),
    "pan-right": CameraPreset(
        name="pan-right",
        description="Pan Right (lia máy sang phải dẫn ánh mắt sang cảnh mới)",
        focal_length_equiv="50mm",
        scale_from=1.05,
        scale_to=1.05,
        translate_x_from_px=-35.0,
        translate_x_to_px=35.0,
        translate_y_from_px=0.0,
        translate_y_to_px=0.0,
        rotation_from_deg=0.0,
        rotation_to_deg=0.0,
        easing="sine.inOut",
    ),
    "tilt-up": CameraPreset(
        name="tilt-up",
        description="Tilt Up (ngửa máy từ thấp lên cao thể hiện tầm vóc nhân vật/nhà cây)",
        focal_length_equiv="35mm",
        scale_from=1.05,
        scale_to=1.05,
        translate_x_from_px=0.0,
        translate_x_to_px=0.0,
        translate_y_from_px=30.0,
        translate_y_to_px=-25.0,
        rotation_from_deg=0.0,
        rotation_to_deg=0.0,
        easing="power1.out",
    ),
    "tilt-down": CameraPreset(
        name="tilt-down",
        description="Tilt Down (chúc máy từ trên cao xuống tập trung vào hành động nhí)",
        focal_length_equiv="35mm",
        scale_from=1.05,
        scale_to=1.05,
        translate_x_from_px=0.0,
        translate_x_to_px=0.0,
        translate_y_from_px=-30.0,
        translate_y_to_px=25.0,
        rotation_from_deg=0.0,
        rotation_to_deg=0.0,
        easing="power1.out",
    ),
    "ken-burns": CameraPreset(
        name="ken-burns",
        description="Ken Burns (kết hợp zoom chậm và trôi góc mượt mà)",
        focal_length_equiv="50mm",
        scale_from=1.02,
        scale_to=1.10,
        translate_x_from_px=-15.0,
        translate_x_to_px=15.0,
        translate_y_from_px=10.0,
        translate_y_to_px=-15.0,
        rotation_from_deg=0.0,
        rotation_to_deg=0.0,
        easing="power1.inOut",
    ),
    "static": CameraPreset(
        name="static",
        description="Static Breathe (khóa góc nhưng giữ nhịp thở nhẹ tránh đứng hình)",
        focal_length_equiv="35mm",
        scale_from=1.0,
        scale_to=1.025,
        translate_x_from_px=0.0,
        translate_x_to_px=0.0,
        translate_y_from_px=0.0,
        translate_y_to_px=-5.0,
        rotation_from_deg=0.0,
        rotation_to_deg=0.0,
        easing="sine.inOut",
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
        easing="power1.inOut",
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
        easing="power3.out",
    ),
}

def get_camera_preset(name: str) -> CameraPreset:
    """Retrieves a camera preset by name, defaulting to push-in."""
    key = name.lower().strip()
    return CAMERA_PRESETS.get(key, CAMERA_PRESETS["push-in"])

def parse_camera_move(camera_str: Optional[str]) -> str:
    """Ánh xạ chuỗi mô tả camera trong kịch bản (ví dụ 'eye-level, 35mm, static',
    'smooth push-in', 'slow pan left', 'tilt up', 'dolly-out') thành tên camera preset chuẩn.
    """
    if not camera_str:
        return "push-in"
    c = camera_str.lower().strip()
    if "pan left" in c or "pan-left" in c:
        return "pan-left"
    if "pan right" in c or "pan-right" in c:
        return "pan-right"
    if "lateral-pan" in c or "pan" in c or "lướt ngang" in c:
        return "lateral-pan"
    if "tilt up" in c or "tilt-up" in c:
        return "tilt-up"
    if "tilt down" in c or "tilt-down" in c:
        return "tilt-down"
    if "tilt" in c:
        return "tilt-up"
    if "dolly-out" in c or "dolly out" in c or "pull-out" in c or "pull out" in c or "lùi" in c:
        return "dolly-out"
    if "punch-in" in c or "punch in" in c or "close-up" in c:
        return "punch-in"
    if "dutch" in c or "nghiêng" in c:
        return "dutch-angle"
    if "ken-burns" in c or "ken burns" in c:
        return "ken-burns"
    if "static" in c or "tĩnh" in c or "khóa góc" in c:
        return "static"
    if "push-in" in c or "push in" in c or "zoom in" in c or "zoom-in" in c or "tiến" in c:
        return "push-in"
    return "push-in"

def build_camera_gsap_snippet(
    preset_name: str,
    target_selector: str = "#cameraTarget",
    duration_sec: float = 4.0,
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

def build_shot_camera_gsap(
    target_selector: str,
    start_time: float,
    duration_sec: float,
    camera_name: str = "push-in",
    is_video: bool = False,
) -> str:
    """Sinh chuỗi mã GSAP điều khiển camera cho shot:
    - Nếu là clip video: giữ ổn định khung hình, tránh méo motion gốc.
    - Nếu là ảnh tĩnh:
      + Shot <= 6.0s: 1 chuyển động mượt mà.
      + Shot dài > 6.0s (như 20 giây): chia 3 nhịp (Opening move -> Hold & drift -> Settle & prep)
        để không bị đứng hình suốt 20 giây và hoàn toàn deterministic, seek-safe.
    """
    preset = get_camera_preset(camera_name)
    if is_video:
        return f"""
      // Video clip camera: {preset.description} (stabilized motion)
      tl.fromTo("{target_selector}", {{ scale: 1.01, opacity: 0 }}, {{ scale: 1.0, opacity: 1, duration: 0.45, ease: "power2.out" }}, {start_time:.3f});
      tl.to("{target_selector}", {{ scale: 1.005, duration: {duration_sec - 0.45:.3f}, ease: "none" }}, {start_time + 0.45:.3f});
""".strip()

    if duration_sec <= 6.0:
        return f"""
      // Camera Move (Short Shot): {preset.description}
      tl.fromTo("{target_selector}",
        {{ scale: {preset.scale_from}, x: {preset.translate_x_from_px}, y: {preset.translate_y_from_px}, rotation: {preset.rotation_from_deg}, opacity: 0 }},
        {{ scale: {preset.scale_from}, x: {preset.translate_x_from_px}, y: {preset.translate_y_from_px}, rotation: {preset.rotation_from_deg}, opacity: 1, duration: 0.45, ease: "power2.out" }},
        {start_time:.3f}
      );
      tl.to("{target_selector}",
        {{ scale: {preset.scale_to}, x: {preset.translate_x_to_px}, y: {preset.translate_y_to_px}, rotation: {preset.rotation_to_deg}, duration: {duration_sec - 0.45:.3f}, ease: "{preset.easing}" }},
        {start_time + 0.45:.3f}
      );
""".strip()

    # Shot dài (> 6.0s, ví dụ 20 giây) - 3 nhịp:
    t1 = round(duration_sec * 0.35, 3)
    t2 = round(duration_sec * 0.40, 3)
    t3 = round(duration_sec - t1 - t2, 3)

    mid_scale = round((preset.scale_from * 0.4 + preset.scale_to * 0.6), 3)
    drift_x = round((preset.translate_x_from_px + preset.translate_x_to_px) / 2 + (8.0 if preset.translate_x_to_px == 0 else 0.0), 2)
    drift_y = round((preset.translate_y_from_px + preset.translate_y_to_px) / 2 + (-6.0 if preset.translate_y_to_px == 0 else 0.0), 2)
    mid_rot = round((preset.rotation_from_deg + preset.rotation_to_deg) / 2, 2)

    return f"""
      // Camera Move (3-Beat Long Shot {duration_sec}s): {preset.description}
      // Nhịp 1: Xuất hiện & Mở đầu cú máy ({t1}s)
      tl.fromTo("{target_selector}",
        {{ scale: {preset.scale_from}, x: {preset.translate_x_from_px}, y: {preset.translate_y_from_px}, rotation: {preset.rotation_from_deg}, opacity: 0 }},
        {{ scale: {preset.scale_from}, x: {preset.translate_x_from_px}, y: {preset.translate_y_from_px}, rotation: {preset.rotation_from_deg}, opacity: 1, duration: 0.45, ease: "power2.out" }},
        {start_time:.3f}
      );
      tl.to("{target_selector}",
        {{ scale: {mid_scale}, x: {drift_x}, y: {drift_y}, rotation: {mid_rot}, duration: {t1 - 0.45:.3f}, ease: "power1.out" }},
        {start_time + 0.45:.3f}
      );
      // Nhịp 2: Giữ & Trôi góc nhẹ tự nhiên ({t2}s)
      tl.to("{target_selector}",
        {{ scale: {round(mid_scale * 1.015, 3)}, x: {round(drift_x * 0.7 + preset.translate_x_to_px * 0.3, 2)}, y: {round(drift_y * 0.7 + preset.translate_y_to_px * 0.3, 2)}, duration: {t2:.3f}, ease: "sine.inOut" }},
        {start_time + t1:.3f}
      );
      // Nhịp 3: Định hình đích & Chuẩn bị chuyển cảnh ({t3}s)
      tl.to("{target_selector}",
        {{ scale: {preset.scale_to}, x: {preset.translate_x_to_px}, y: {preset.translate_y_to_px}, rotation: {preset.rotation_to_deg}, duration: {t3:.3f}, ease: "power1.inOut" }},
        {start_time + t1 + t2:.3f}
      );
""".strip()
