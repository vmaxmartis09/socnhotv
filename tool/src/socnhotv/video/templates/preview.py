from __future__ import annotations

import json
import logging
from pathlib import Path
import tempfile
from typing import Optional

from socnhotv.core.providers.mock_provider import create_minimal_png_bytes, create_minimal_wav_bytes
from socnhotv.video.hyperframes_engine import HyperFramesEngine
from socnhotv.video.platforms import get_platform
from socnhotv.video.templates.compose import compose_template
from socnhotv.video.templates.loader import get_template, get_template_dir

logger = logging.getLogger("socnhotv.video.templates.preview")


def generate_template_preview(
    template_id: str,
    output_mp4: Optional[Path] = None,
    output_jpg: Optional[Path] = None,
    engine: Optional[HyperFramesEngine] = None,
) -> Path:
    """Render preview 540p cho template từ sample.data.json -> preview.mp4 + preview.jpg."""
    t_dir = get_template_dir(template_id)
    template = get_template(template_id)
    engine = engine or HyperFramesEngine()

    sample_file = t_dir / "sample.data.json"
    if not sample_file.exists():
        raise FileNotFoundError(f"Không tìm thấy sample.data.json cho template '{template_id}'")

    with open(sample_file, "r", encoding="utf-8") as f:
        sample_data = json.load(f)

    platform_id = template.default_platform or "tiktok"
    preset = get_platform(platform_id)

    # 540p preview size (nửa kích thước chuẩn)
    preview_w = preset.width // 2
    preview_h = preset.height // 2

    output_mp4 = output_mp4 or (t_dir / "preview.mp4")
    output_jpg = output_jpg or (t_dir / "preview.jpg")

    with tempfile.TemporaryDirectory(prefix=f"preview_{template_id}_") as tmp:
        tmp_dir = Path(tmp)
        mock_voice = tmp_dir / "dummy_voice.wav"
        mock_voice.write_bytes(create_minimal_wav_bytes(duration_sec=3.0))

        # Soạn HTML
        html = compose_template(
            template_id=template_id,
            data=sample_data,
            platform=preset,
            voice_audio_path=mock_voice,
            total_duration=3.0,
        )

        assets_map = {
            "voiceover.mp3": mock_voice,
        }

        # Tìm các đường dẫn media trong sample_data để đưa vào assets nếu có
        for k, v in sample_data.items():
            if isinstance(v, str) and Path(v).exists():
                assets_map[Path(v).name] = Path(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, str) and Path(item).exists():
                        assets_map[Path(item).name] = Path(item)

        bundle_dir = engine.build(
            composition_html=html,
            assets=assets_map,
            platform=preset,
            target_dir=tmp_dir / "bundle",
            duration=3.0,
        )

        # Render fallback ffmpeg tốc độ cao cho preview 540p
        from socnhotv.video.fallback_ffmpeg import render_fallback_ffmpeg
        render_fallback_ffmpeg(
            project_dir=bundle_dir,
            output_mp4=output_mp4,
            width=preview_w,
            height=preview_h,
            fps=24,
            ffmpeg_exe=engine.ffmpeg,
        )

        # Trích thumbnail jpg
        engine.extract_thumbnail(output_mp4, output_jpg, timestamp=1.0)

    logger.info(f"Đã tạo preview thành công cho template {template_id}: {output_mp4.name}, {output_jpg.name}")
    return output_jpg
