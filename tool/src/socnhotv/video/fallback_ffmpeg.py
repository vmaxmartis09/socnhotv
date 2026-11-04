from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess
from typing import Optional

import imageio_ffmpeg
import soundfile as sf

from socnhotv.video.platforms import PlatformPreset, get_platform

logger = logging.getLogger("socnhotv.video.fallback")
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


def get_audio_duration(audio_path: str | Path, ffmpeg_exe: str = FFMPEG_EXE) -> float:
    """Đo thời lượng file audio chính xác."""
    audio_file = Path(audio_path).resolve()
    if not audio_file.exists():
        return 4.0

    try:
        with sf.SoundFile(str(audio_file)) as f:
            return round(len(f) / f.samplerate, 3)
    except Exception:
        pass

    # Fallback ffprobe/ffmpeg
    cmd = [
        ffmpeg_exe,
        "-i",
        str(audio_file),
        "-f",
        "null",
        "-",
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    except Exception:
        pass

    return 4.0


def render_fallback_ffmpeg(
    project_dir: Path,
    output_mp4: Path,
    platform: Optional[PlatformPreset] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    fps: int = 30,
    ffmpeg_exe: str = FFMPEG_EXE,
) -> Path:
    """Render video fallback tốc độ cao bằng ffmpeg:
    Nối các hình ảnh/clip phân cảnh + audio voiceover + nhạc nền thành MP4 theo đúng preset nền tảng.
    Cảnh báo FALLBACK_USED khi được gọi.
    """
    logger.warning("FALLBACK_USED: Rendering via FFmpeg fallback instead of HyperFrames CLI.")

    target_w = width or (platform.width if platform else 1080)
    target_h = height or (platform.height if platform else 1920)
    target_fps = fps or (platform.fps if platform else 30)

    output_mp4 = Path(output_mp4).resolve()
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    assets_dir = project_dir / "assets"
    voice_file = assets_dir / "voiceover.mp3"
    bgm_file = assets_dir / "bgm.mp3"

    # Tìm các video clip hoặc ảnh trong assets/
    media_files = []
    if assets_dir.exists():
        media_files = sorted(
            [f for f in assets_dir.iterdir() if f.name.startswith("scene_") and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".webm")],
            key=lambda p: p.name,
        )

    total_dur = get_audio_duration(voice_file, ffmpeg_exe) if voice_file.exists() else 4.0
    dur_per_scene = total_dur / max(1, len(media_files))

    if not media_files:
        # Tạo placeholder video theo kích thước nếu assets rỗng
        cmd = [
            ffmpeg_exe,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x111625:s={target_w}x{target_h}:d={total_dur}",
        ]
        if voice_file.exists():
            cmd.extend(["-i", str(voice_file), "-c:a", "aac", "-b:a", "192k"])
        cmd.extend([
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(target_fps),
            "-t",
            f"{total_dur:.3f}",
            str(output_mp4),
        ])
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, timeout=30)
        return output_mp4

    # Dựng filter_complex ghép các scenes
    inputs = []
    filter_parts = []
    for i, m in enumerate(media_files):
        is_img = m.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
        if is_img:
            inputs.extend(["-loop", "1", "-framerate", str(target_fps), "-t", f"{dur_per_scene:.3f}"])
        else:
            inputs.extend(["-t", f"{dur_per_scene:.3f}"])
        inputs.extend(["-i", str(m)])
        filter_parts.append(
            f"[{i}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
            f"crop={target_w}:{target_h},setsar=1[v{i}];"
        )

    concat_in = "".join(f"[v{i}]" for i in range(len(media_files)))
    filter_parts.append(f"{concat_in}concat=n={len(media_files)}:v=1:a=0[vout]")

    cmd = [ffmpeg_exe, "-y"]
    cmd.extend(inputs)

    has_audio = voice_file.exists() or bgm_file.exists()
    audio_inputs_count = 0
    if voice_file.exists():
        cmd.extend(["-i", str(voice_file)])
        audio_inputs_count += 1
    if bgm_file.exists():
        cmd.extend(["-i", str(bgm_file)])
        audio_inputs_count += 1

    cmd.extend([
        "-filter_complex",
        "".join(filter_parts),
        "-map",
        "[vout]",
    ])

    if voice_file.exists():
        voice_idx = len(media_files)
        cmd.extend(["-map", f"{voice_idx}:a", "-c:a", "aac", "-b:a", "192k"])

    cmd.extend([
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        str(output_mp4),
    ])

    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=30)
        if res.returncode != 0:
            raise RuntimeError(res.stderr)
    except Exception as e:
        # Fallback đơn giản với cảnh đầu tiên nếu concat gặp lỗi
        logger.warning(f"Concat filter fallback failed ({e}), falling back to single scene loop.")
        simple_cmd = [
            ffmpeg_exe,
            "-y",
            "-loop",
            "1",
            "-framerate",
            str(target_fps),
            "-t",
            f"{total_dur:.3f}",
            "-i",
            str(media_files[0]),
        ]
        if voice_file.exists():
            simple_cmd.extend(["-i", str(voice_file), "-c:a", "aac", "-b:a", "192k"])
        simple_cmd.extend([
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-vf",
            f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h}",
            "-shortest",
            str(output_mp4),
        ])
        subprocess.run(simple_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, timeout=30)

    return output_mp4
