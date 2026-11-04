from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import jinja2

from socnhotv.video.fallback_ffmpeg import get_audio_duration
from socnhotv.video.platforms import PlatformPreset, get_platform
from socnhotv.video.templates.loader import get_template, get_template_dir
from socnhotv.video.templates.schema import validate_template_data

logger = logging.getLogger("socnhotv.video.templates.compose")


def parse_dur_seconds(dur_str: str | float | int | None, default_sec: float = 3.0) -> float:
    if dur_str is None:
        return default_sec
    if isinstance(dur_str, (int, float)):
        return float(dur_str)
    s = str(dur_str).strip().lower()
    if s.endswith("s"):
        try:
            return float(s[:-1])
        except ValueError:
            pass
    try:
        return float(s)
    except ValueError:
        return default_sec


def compose_template(
    template_id: str,
    data: Dict[str, Any],
    platform: str | PlatformPreset = "tiktok",
    voice_audio_path: Optional[str | Path] = None,
    bgm_path: Optional[str | Path] = None,
    total_duration: Optional[float] = None,
) -> str:
    """Nạp template và render Jinja2 ra mã HTML5 HyperFrames hoàn chỉnh.

    Args:
        template_id: Mã ID của template (vd: 'tiktok-sales-v1').
        data: Dict dữ liệu slot người dùng cung cấp.
        platform: Nền tảng mục tiêu (tiktok, youtube, facebook...).
        voice_audio_path: Đường dẫn audio thoại.
        bgm_path: Đường dẫn nhạc nền.
        total_duration: Thời lượng mong muốn nếu không tự đo từ voice.

    Returns:
        Chuỗi HTML5 HyperFrames hợp lệ.
    """
    template = get_template(template_id)
    t_dir = get_template_dir(template_id)

    # 1. Validate data
    errors = validate_template_data(template, data)
    if errors:
        raise ValueError(f"Dữ liệu template '{template_id}' không hợp lệ: " + " | ".join(errors))

    preset = get_platform(platform) if isinstance(platform, str) else platform

    # 2. Xác định tổng thời lượng
    if voice_audio_path and Path(voice_audio_path).exists():
        dur = get_audio_duration(voice_audio_path)
    elif total_duration is not None and total_duration > 0:
        dur = total_duration
    elif template.duration.fixed_duration:
        dur = template.duration.fixed_duration
    else:
        dur = 15.0

    # 3. Phân bổ thời lượng các scenes
    scenes_meta = template.scenes or []
    computed_scenes: List[Dict[str, Any]] = []

    if scenes_meta:
        # Tính các scene có dur cố định
        fixed_sum = 0.0
        flexible_count = 0
        for sc in scenes_meta:
            if sc.dur:
                fixed_sum += parse_dur_seconds(sc.dur)
            else:
                flexible_count += 1

        rem_dur = max(1.0, dur - fixed_sum)
        flex_dur = rem_dur / max(1, flexible_count)

        curr_t = 0.0
        for sc in scenes_meta:
            sc_dur = parse_dur_seconds(sc.dur) if sc.dur else flex_dur
            computed_scenes.append({
                "role": sc.role,
                "start": round(curr_t, 3),
                "duration": round(sc_dur, 3),
                "end": round(curr_t + sc_dur, 3),
                "summary": sc.summary or "",
            })
            curr_t += sc_dur
    else:
        # 1 scene bao quát toàn bộ
        computed_scenes.append({
            "role": "main",
            "start": 0.0,
            "duration": round(dur, 3),
            "end": round(dur, 3),
            "summary": "Main scene",
        })

    # 4. Nạp styles.css
    css_content = ""
    css_file = t_dir / "styles.css"
    if css_file.exists():
        css_content = css_file.read_text(encoding="utf-8")

    # 5. Nạp Jinja2 template
    j2_file = t_dir / "composition.html.j2"
    if not j2_file.exists():
        raise FileNotFoundError(f"File composition.html.j2 không tồn tại ở {t_dir}")

    j2_text = j2_file.read_text(encoding="utf-8")
    env = jinja2.Environment(autoescape=False)
    j2_tmpl = env.from_string(j2_text)

    # 6. Render context
    context = {
        "template": template,
        "data": data,
        "platform": preset,
        "width": preset.width,
        "height": preset.height,
        "fps": preset.fps,
        "safe_zone": preset.safe_zone,
        "total_duration": round(dur, 3),
        "scenes": computed_scenes,
        "styles_css": css_content,
        "voiceover_src": "assets/voiceover.mp3",
        "bgm_src": "assets/bgm.mp3" if bgm_path else None,
        "bgm_duck_db": template.bgm.duck_db,
    }

    return j2_tmpl.render(**context)
