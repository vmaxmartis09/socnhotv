from __future__ import annotations

import json
import logging
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Optional

from socnhotv.sources.downloader import extract_audio_wav, extract_thumbnail_jpg
from socnhotv.sources.models import RightsType, SourceFiles, SourceItem, SourceStats
from socnhotv.workspace import project_path

logger = logging.getLogger(__name__)


def probe_video_duration(video_path: Path) -> float:
    """Get video duration in seconds via ffprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        if res.returncode == 0 and res.stdout.strip():
            return float(res.stdout.strip())
    except Exception as e:
        logger.warning("ffprobe failed on %s: %s", video_path, e)
    return 0.0


def ingest_local_file(
    project_id: str,
    source_file_path: Path | str,
    title: Optional[str] = None,
    rights: RightsType = "owned",  # Default owned for local uploads
    rights_note: str = "Tập tin tải lên từ máy cục bộ",
) -> SourceItem:
    """Ingest a local mp4/mov video file into raw/<source_id>/."""
    src = Path(source_file_path)
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {source_file_path}")

    source_id = f"local_{uuid.uuid4().hex[:12]}"
    target_dir = project_path(project_id, "raw", source_id)
    target_dir.mkdir(parents=True, exist_ok=True)

    video_dest = target_dir / "video.mp4"
    audio_dest = target_dir / "audio.wav"
    thumb_dest = target_dir / "thumb.jpg"
    meta_dest = target_dir / "meta.json"

    # Copy video
    shutil.copy2(src, video_dest)

    # Probe duration
    duration = probe_video_duration(video_dest)

    # Extract thumbnail & audio
    extract_thumbnail_jpg(video_dest, thumb_dest)
    extract_audio_wav(video_dest, audio_dest)

    item = SourceItem(
        id=source_id,
        project_id=project_id,
        platform="local",
        url=f"file://{src.name}",
        author="User",
        title=title or src.stem,
        duration_s=duration,
        rights=rights,
        rights_note=rights_note,
        files=SourceFiles(
            video=f"raw/{source_id}/video.mp4" if video_dest.exists() else None,
            audio=f"raw/{source_id}/audio.wav" if audio_dest.exists() else None,
            thumb=f"raw/{source_id}/thumb.jpg" if thumb_dest.exists() else None,
        ),
        status="ready",
    )

    with open(meta_dest, "w", encoding="utf-8") as f:
        f.write(item.model_dump_json(indent=2))

    return item
