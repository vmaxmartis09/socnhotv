#!/usr/bin/env python3
"""
scene-cut (T-11): phát hiện cảnh bằng PySceneDetect rồi (tuỳ chọn) cắt thành clip bằng ffmpeg.
Dùng để cắt Shorts từ tập dài. params:
  threshold    (float, 3.0)  độ nhạy AdaptiveDetector (nhỏ = nhiều cảnh)
  min_scene_s  (float, 1.0)  độ dài cảnh tối thiểu (giây)
  export_clips (bool, false) cắt ra file mp4 cho từng cảnh
  aspect       ("keep"|"9:16", "keep") 9:16 = cắt giữa khung về dọc (1080x1920)
  max_scenes   (int, 200)    chặn xuất quá nhiều clip
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_DIR.parents[1] / "toolbox_cli"))
from kit import (  # noqa: E402
    SHARED_DIR, BadInput, MissingDependency, ToolError, atomic_write, compute_sha8, out_file, run_tool, store_record,
)

VERSION = "1.0.0"
SCENES_DIR = SHARED_DIR / "assets" / "scenes"
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


def ffprobe_duration(video: Path) -> float:
    exe = shutil.which("ffprobe")
    if not exe:
        raise MissingDependency("Không thấy ffprobe", "Chạy tool ffmpeg-bin trước (toolbox run ffmpeg-bin)")
    r = subprocess.run([exe, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(video)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError as e:
        raise BadInput(f"ffprobe không đọc được video: {r.stderr.strip()[:200]}", "NOT_A_VIDEO") from e


def process(inputs, params, ctx):
    try:
        from scenedetect import AdaptiveDetector, detect
    except ImportError as e:
        raise MissingDependency("Thiếu scenedetect", "python -m pip install -r requirements.txt trong venv của tool") from e

    video = inputs[0]
    if video.suffix.lower() not in VIDEO_EXT:
        raise BadInput(f"Định dạng {video.suffix} không phải video được hỗ trợ")
    threshold = float(params.get("threshold", 3.0))
    min_len = float(params.get("min_scene_s", 1.0))
    export = bool(params.get("export_clips", False))
    aspect = params.get("aspect", "keep")
    max_scenes = int(params.get("max_scenes", 200))
    if aspect not in ("keep", "9:16"):
        raise BadInput("aspect phải là 'keep' hoặc '9:16'")

    duration = ffprobe_duration(video)
    fps_guess = 30.0
    detector = AdaptiveDetector(adaptive_threshold=threshold, min_scene_len=max(1, int(min_len * fps_guess)))
    found = detect(str(video), detector)
    if found:
        scenes = [(s.get_seconds(), e.get_seconds()) for s, e in found]
    else:
        scenes = [(0.0, duration)]  # không có điểm cắt: cả video là một cảnh

    sha8 = compute_sha8(video)
    out_dir = SCENES_DIR / sha8
    out_dir.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    items = []
    for i, (a, b) in enumerate(scenes, 1):
        items.append({"index": i, "start": round(a, 3), "end": round(b, 3), "duration": round(b - a, 3)})

    outputs = []
    clip_paths: list[Path] = []
    if export:
        ff = shutil.which("ffmpeg")
        if not ff:
            raise MissingDependency("Không thấy ffmpeg", "Chạy tool ffmpeg-bin trước")
        if len(items) > max_scenes:
            warnings.append(f"Có {len(items)} cảnh, chỉ xuất {max_scenes} cảnh đầu")
        clips_dir = out_dir / "clips"
        clips_dir.mkdir(exist_ok=True)
        vf = ["-vf", "crop=ih*9/16:ih,scale=1080:1920"] if aspect == "9:16" else []
        for it in items[:max_scenes]:
            dest = clips_dir / f"scene_{it['index']:03d}.mp4"
            cmd = [ff, "-y", "-v", "error", "-ss", str(it["start"]), "-i", str(video), "-t", str(it["duration"]),
                   *vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", str(dest)]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0 or not dest.exists() or dest.stat().st_size == 0:
                raise ToolError("FFMPEG_CUT_FAILED", f"Cắt cảnh {it['index']} lỗi: {r.stderr.strip()[:300]}")
            it["clip"] = str(dest.resolve())
            clip_paths.append(dest)

    manifest = {"source": str(video.resolve()), "duration": round(duration, 3), "scene_count": len(items),
                "params": {"threshold": threshold, "min_scene_s": min_len, "aspect": aspect}, "scenes": items}
    manifest_path = out_dir / "scenes.json"
    atomic_write(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2))
    outputs.append(out_file(manifest_path, "scenes_json"))
    for p in clip_paths:
        outputs.append(out_file(p, "clip"))

    rec = store_record(
        sha8, "scene-cut", VERSION, str(video.resolve()), "BSD-3-Clause (PySceneDetect)",
        {"scenes": manifest_path, **({"clips_dir": out_dir / "clips"} if export else {})},
        {"scene_count": len(items), "duration": round(duration, 3), "clips": len(clip_paths), "aspect": aspect},
        index=SCENES_DIR / "index.jsonl",
    )
    return outputs, [rec], warnings


if __name__ == "__main__":
    run_tool(process)
