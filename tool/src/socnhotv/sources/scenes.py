from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from socnhotv.sources.local import probe_video_duration
from socnhotv.sources.models import SceneCut
from socnhotv.workspace import project_path

logger = logging.getLogger(__name__)


def extract_scene_frame(video_path: Path, timestamp_s: float, out_img: Path) -> bool:
    try:
        out_img.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", f"{timestamp_s:.3f}",
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(out_img),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return res.returncode == 0 and out_img.exists()
    except Exception as e:
        logger.warning("Failed to extract scene frame at %.2f: %s", timestamp_s, e)
        return False


def detect_scenes_ffmpeg_fallback(video_path: Path, duration_s: float) -> List[tuple[float, float]]:
    """Fallback: detect scene cuts using ffmpeg select filter, or uniform segments."""
    cuts = [0.0]
    try:
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-filter_complex", "select='gt(scene,0.3)',metadata=print:file=-",
            "-f", "null",
            "-",
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        import re
        for line in res.stdout.splitlines() + res.stderr.splitlines():
            m = re.search(r"pts_time:([0-9.]+)", line)
            if m:
                pts = float(m.group(1))
                if pts > cuts[-1] + 1.0:
                    cuts.append(pts)
    except Exception as e:
        logger.warning("ffmpeg scene fallback failed: %s", e)

    if cuts[-1] < duration_s:
        cuts.append(duration_s)

    # If only 0 and duration, or no cuts found, create at least 1 scene
    if len(cuts) <= 1:
        return [(0.0, max(duration_s, 1.0))]

    scenes = []
    for i in range(len(cuts) - 1):
        scenes.append((cuts[i], cuts[i + 1]))
    return scenes


def detect_and_save_scenes(project_id: str, source_id: str) -> List[SceneCut]:
    """Run scene detection on raw/<source_id>/video.mp4 and save scenes.json."""
    source_dir = project_path(project_id, "raw", source_id)
    video_path = source_dir / "video.mp4"
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found at: {video_path}")

    duration_s = probe_video_duration(video_path)
    scenes_dir = source_dir / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    raw_scenes: List[tuple[float, float]] = []

    # 1. Try PySceneDetect
    try:
        from scenedetect import ContentDetector, detect
        scene_list = detect(str(video_path), ContentDetector(threshold=27.0))
        for scene in scene_list:
            raw_scenes.append((scene[0].get_seconds(), scene[1].get_seconds()))
    except Exception as e:
        logger.warning("PySceneDetect error: %s. Falling back to ffmpeg.", e)

    # 2. Fallback if empty
    if not raw_scenes:
        raw_scenes = detect_scenes_ffmpeg_fallback(video_path, duration_s)

    # If still empty (e.g. video very short), 1 scene for full video
    if not raw_scenes:
        raw_scenes = [(0.0, max(duration_s, 1.0))]

    results: List[SceneCut] = []
    for idx, (st, en) in enumerate(raw_scenes, start=1):
        mid = (st + en) / 2.0
        thumb_name = f"scene_{idx:03d}.jpg"
        thumb_path = scenes_dir / thumb_name
        extract_scene_frame(video_path, mid, thumb_path)
        
        results.append(
            SceneCut(
                scene_idx=idx,
                start_s=round(st, 2),
                end_s=round(en, 2),
                thumb=f"raw/{source_id}/scenes/{thumb_name}" if thumb_path.exists() else "",
            )
        )

    # Save scenes.json
    scenes_json = source_dir / "scenes.json"
    with open(scenes_json, "w", encoding="utf-8") as f:
        json.dump([s.model_dump() for s in results], f, indent=2)

    return results
