#!/usr/bin/env python3
"""
Real MP4 Renderer for SocNhoTV Templates using HyperFrames CLI.
Replaces mock solid-color previews with real 9:16 / 16:9 MP4 video and JPG posters.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from jinja2 import Template

REPO_ROOT = Path(__file__).resolve().parents[4]
ENGINE_RUNNER = REPO_ROOT / "data" / "shared" / "templates" / "_engine" / "hyperframes_run.mjs"
FFMPEG_BIN = REPO_ROOT / "data" / "shared" / "models" / "ffmpeg-bin" / "ffmpeg.exe"
FFPROBE_BIN = REPO_ROOT / "data" / "shared" / "models" / "ffmpeg-bin" / "ffprobe.exe"


def render_template(
    template_id: str,
    width: int = 540,
    height: int = 960,
    fps: int = 24,
    duration: float = 3.5,
    out_filename: str = "preview.mp4",
) -> dict:
    t_dir = REPO_ROOT / "data" / "shared" / "templates" / template_id
    if not t_dir.exists():
        raise FileNotFoundError(f"Template dir not found: {t_dir}")

    comp_j2 = t_dir / "composition.html.j2"
    styles_css = t_dir / "styles.css"
    sample_json = t_dir / "sample.data.json"
    template_json = t_dir / "template.json"

    with open(sample_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    styles = styles_css.read_text(encoding="utf-8") if styles_css.exists() else ""
    # Safe zone for 9:16 or 16:9
    is_landscape = width > height
    safe_zone = {
        "top": int(60 * (height / 540)) if is_landscape else int(180 * (height / 1920)),
        "bottom": int(60 * (height / 540)) if is_landscape else int(320 * (height / 1920)),
        "left": 40 if is_landscape else 20,
        "right": 40 if is_landscape else 20,
    }

    # Render Jinja2 for styles
    styles_rendered = Template(styles).render(safe_zone=safe_zone)

    # Render Jinja2 for composition
    comp_rendered = Template(comp_j2.read_text(encoding="utf-8")).render(
        width=width,
        height=height,
        total_duration=duration,
        data=data,
        styles_css=styles_rendered,
        safe_zone=safe_zone,
        voiceover_src="assets/voiceover.mp3",
    )

    index_html = t_dir / "index.html"
    index_html.write_text(comp_rendered, encoding="utf-8")

    out_mp4 = t_dir / out_filename
    out_jpg = out_mp4.with_suffix(".jpg")

    # Render via HyperFrames
    cmd = [
        "node",
        str(ENGINE_RUNNER),
        "render",
        str(t_dir),
        "-o",
        str(out_mp4),
        "--fps",
        str(fps),
    ]

    print(f"--- Rendering {template_id} to MP4 ({width}x{height} @ {fps}fps, {duration}s) ---")
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
    if proc.returncode != 0:
        print("STDERR:", proc.stderr)
        print("STDOUT:", proc.stdout)
        raise RuntimeError(f"HyperFrames render failed with code {proc.returncode}")

    # Extract thumbnail poster at 1.5s
    thumb_cmd = [
        str(FFMPEG_BIN),
        "-y",
        "-ss",
        "00:00:01.500",
        "-i",
        str(out_mp4),
        "-vframes",
        "1",
        "-q:v",
        "2",
        str(out_jpg),
    ]
    subprocess.run(thumb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)

    # Measure via ffprobe
    probe_cmd = [
        str(FFPROBE_BIN),
        "-v",
        "error",
        "-show_entries",
        "format=duration,size,bit_rate",
        "-show_entries",
        "stream=width,height,codec_name,nb_frames,r_frame_rate",
        "-of",
        "json",
        str(out_mp4),
    ]
    probe_res = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    probe_data = json.loads(probe_res.stdout)

    # Update template.json to verified
    with open(template_json, "r", encoding="utf-8") as f:
        meta = json.load(f)

    meta["status"] = "verified"
    meta["sample_output"] = out_filename
    meta["verified_on"] = "2026-11-05"

    with open(template_json, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    result = {
        "ok": True,
        "template_id": template_id,
        "mp4_path": str(out_mp4),
        "jpg_path": str(out_jpg),
        "probe": probe_data,
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    tid = sys.argv[1] if len(sys.argv) > 1 else "affiliate-compare-v1"
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
    render_template(tid, duration=dur)
