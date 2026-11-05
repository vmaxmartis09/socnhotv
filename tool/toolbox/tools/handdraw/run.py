#!/usr/bin/env python3
"""
Whiteboard Hand-drawn Video Generator Runner (U-06)
Learned from masihsultani/whiteboard-animator (MIT) and subroy13/handanim (MIT).
Renders authentic progressive hand-drawing stroke-by-stroke video into MP4.
"""
import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[4]
FFMPEG_BIN = REPO_ROOT / "data" / "shared" / "models" / "ffmpeg-bin" / "ffmpeg.exe"
ANIMATIONS_VAULT_DIR = REPO_ROOT / "data" / "shared" / "assets" / "animations"
INDEX_PATH = ANIMATIONS_VAULT_DIR / "index.jsonl"


def create_hand_marker_surface(size: int = 160) -> Image.Image:
    """Create a stylized hand holding a marker pen on transparent RGBA."""
    hand = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(hand)
    
    # Pen tip at (0, 0) - oriented down-left
    # Marker body (diagonal from (0,0) to (100, 100))
    pen_body = [(10, 5), (18, 0), (90, 80), (82, 88)]
    d.polygon(pen_body, fill=(30, 30, 35))
    
    # Pen nib (black ink tip pointing at 0, 0)
    nib = [(0, 0), (10, 5), (5, 10)]
    d.polygon(nib, fill=(15, 23, 42))
    
    # Marker accent band
    accent = [(25, 20), (32, 14), (40, 22), (33, 28)]
    d.polygon(accent, fill=(59, 130, 246))

    # Hand fingers gripping the pen
    # Thumb
    d.ellipse([50, 45, 95, 85], fill=(250, 204, 155), outline=(225, 175, 130), width=2)
    # Index finger
    d.ellipse([35, 30, 75, 65], fill=(255, 214, 168), outline=(225, 175, 130), width=2)
    # Knuckles / Palm
    d.ellipse([65, 60, 140, 130], fill=(245, 195, 145), outline=(225, 175, 130), width=2)
    
    return hand


def generate_handdraw_video(
    input_image_path: Path,
    output_mp4_path: Path,
    width: int = 540,
    height: int = 960,
    duration_sec: float = 3.0,
    fps: int = 24,
    show_hand: bool = True,
) -> Path:
    output_mp4_path = Path(output_mp4_path).resolve()
    output_mp4_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Load source image and fit onto whiteboard canvas
    orig = Image.open(input_image_path).convert("L")
    
    # Resize preserving aspect ratio to fit inside whiteboard
    max_w = int(width * 0.8)
    max_h = int(height * 0.5)
    orig.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    
    # Binarize strokes (dark ink vs white bg)
    arr = np.array(orig)
    # Threshold: dark pixels < 180
    stroke_mask = arr < 180
    
    # Centered placement
    offset_x = (width - orig.width) // 2
    offset_y = (height - orig.height) // 2 - 40
    
    # Collect coordinates of all stroke pixels in order (snake scan top-to-bottom)
    stroke_coords = []
    h_orig, w_orig = arr.shape
    for y in range(h_orig):
        row_x = range(w_orig) if y % 2 == 0 else range(w_orig - 1, -1, -1)
        for x in row_x:
            if stroke_mask[y, x]:
                stroke_coords.append((x + offset_x, y + offset_y, arr[y, x]))

    total_strokes = len(stroke_coords)
    total_frames = int(duration_sec * fps)
    
    # Hand sprite
    hand_sprite = create_hand_marker_surface(size=140) if show_hand else None

    # 2. Pipe frames to FFmpeg
    cmd = [
        str(FFMPEG_BIN),
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-t", f"{duration_sec:.3f}",
        str(output_mp4_path),
    ]

    pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    # Whiteboard canvas background
    board_base = Image.new("RGB", (width, height), (252, 252, 254))
    draw_base = ImageDraw.Draw(board_base)

    # Draw whiteboard subtle border
    draw_base.rounded_rectangle([15, 15, width - 15, height - 15], radius=24, outline=(220, 225, 235), width=4)

    drawn_count = 0
    cur_x, cur_y = width // 2, height // 2

    for frame_idx in range(total_frames):
        progress = frame_idx / max(1, total_frames - int(fps * 0.5))  # Finish 0.5s before end to show full art
        progress = min(1.0, max(0.0, progress))
        
        target_drawn = int(progress * total_strokes)
        
        # Draw newly revealed strokes
        while drawn_count < target_drawn and drawn_count < total_strokes:
            x, y, lum = stroke_coords[drawn_count]
            color = (int(lum), int(lum), int(lum))
            draw_base.point((x, y), fill=color)
            cur_x, cur_y = x, y
            drawn_count += 1

        # Clone current board
        frame_img = board_base.copy()

        # Overlay hand if drawing and active
        if show_hand and progress < 1.0 and hand_sprite:
            # Tip of nib at (cur_x, cur_y)
            hand_pos = (cur_x, cur_y)
            frame_img.paste(hand_sprite, hand_pos, mask=hand_sprite)

        # Pipe raw RGB bytes
        pipe.stdin.write(frame_img.tobytes())

    pipe.stdin.close()
    pipe.wait()

    if pipe.returncode != 0:
        err = pipe.stderr.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"FFmpeg encoding failed: {err}")

    return output_mp4_path


def main():
    parser = argparse.ArgumentParser(description="Handdraw whiteboard video generator runner")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON config file")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON result file")
    args = parser.parse_args()

    start_time = time.time()
    in_file = Path(args.in_path).resolve()
    out_file = Path(args.out_file if hasattr(args, "out_file") else args.out_path).resolve()

    with open(in_file, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    inputs = cfg.get("inputs", [])
    params = cfg.get("params", {})
    if not inputs:
        raise ValueError("Missing inputs in config")

    input_img = Path(inputs[0]).resolve()
    duration = float(params.get("duration_sec", 3.0))
    fps = int(params.get("fps", 24))
    width = int(params.get("width", 540))
    height = int(params.get("height", 960))
    show_hand = params.get("show_hand", True)

    with open(input_img, "rb") as f:
        sha8 = hashlib.sha256(f.read()).hexdigest()[:8]

    out_dir = ANIMATIONS_VAULT_DIR / sha8
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / "whiteboard.mp4"

    generate_handdraw_video(
        input_image_path=input_img,
        output_mp4_path=out_mp4,
        width=width,
        height=height,
        duration_sec=duration,
        fps=fps,
        show_hand=show_hand,
    )

    outputs = [
        {
            "path": str(out_mp4.resolve()),
            "kind": "video",
            "sha256": hashlib.sha256(out_mp4.read_bytes()).hexdigest(),
        }
    ]

    record = {
        "id": sha8,
        "created_by_tool": "handdraw",
        "tool_version": "1.0.0",
        "source": str(input_img),
        "license": "MIT",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "files": {"video": str(out_mp4)},
        "metadata": {"width": width, "height": height, "duration": duration, "fps": fps},
    }

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    out_data = {
        "ok": True,
        "outputs": outputs,
        "store_records": [record],
        "warnings": [],
        "error": None,
        "elapsed_s": round(time.time() - start_time, 4),
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)

    print(str(out_file))
    sys.exit(0)


if __name__ == "__main__":
    main()
