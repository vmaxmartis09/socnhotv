#!/usr/bin/env python3
"""Đóng gói kịch bản + nhân vật + ảnh cảnh (làm ở local) thành 1 tệp JSON để nạp vào tool "Sóc Nhỏ Director" trên Flow.

Tệp kịch bản: mỗi dòng một cảnh, dạng
    [Prompt ảnh] | [Prompt video] | [chuyển cảnh, tuỳ chọn: cut|fade|dissolve|wipe[:giây]]
Dòng bắt đầu bằng # là chú thích, bỏ qua.

Ảnh cảnh làm sẵn (tuỳ chọn): thư mục chứa canh_01.png, canh_02.png... đúng thứ tự cảnh.
Cảnh nào có ảnh sẽ nạp sẵn, tool không tạo lại ảnh đó (không xê dịch).

Ví dụ:
    python3 scripts/flow_ai/build_flow_package.py \
        --script work/tap01/kich_ban.txt --scene-images work/tap01/anh \
        --out work/tap01/goi_tap01.json
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "assets/soc_nho/soc_nho_profile.json"
DEFAULT_CHARACTER_IMAGE = ROOT / "assets/soc_nho/soc_nho_01.png"
DEFAULT_STYLE_BIBLE = (
    "3D Pixar-style animation, ánh sáng studio mềm ấm, màu rực cân bằng, "
    "mắt to bóng có highlight, tỉ lệ 16:9, không chữ, không watermark"
)
TRANSITIONS = {"cut", "fade", "dissolve", "wipe"}


def encode_image(path: Path) -> tuple[str, str]:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return base64.b64encode(path.read_bytes()).decode("ascii"), mime


def parse_transition(token: str) -> dict:
    kind, _, secs = token.strip().lower().partition(":")
    if kind not in TRANSITIONS:
        raise ValueError(f"chuyển cảnh không hợp lệ: {token!r} (chọn {sorted(TRANSITIONS)})")
    return {"type": kind, "seconds": float(secs) if secs else (0.0 if kind == "cut" else 0.5)}


def build_characters(extra: list[str]) -> list[dict]:
    lock = json.loads(PROFILE.read_text(encoding="utf-8"))["prompt_lock"]
    chars = []
    entries = [("Sóc Nhỏ", DEFAULT_CHARACTER_IMAGE)] + [
        (Path(p).stem, Path(p)) for p in extra
    ]
    for idx, (name, img) in enumerate(entries):
        b64, mime = encode_image(img)
        chars.append({
            "id": f"char-{idx + 1}",
            "name": name,
            "description": lock if idx == 0 else name,
            "prompt": lock if idx == 0 else name,
            "base64": b64,
            "mimeType": mime,
            "status": "ready",
        })
    return chars


def build_scenes(script: Path, images_dir: Path | None, chars: list[dict]) -> list[dict]:
    scenes = []
    stamp = int(time.time() * 1000)
    lines = [l.strip() for l in script.read_text(encoding="utf-8").splitlines()]
    lines = [l for l in lines if l and not l.startswith("#")]
    for idx, line in enumerate(lines, start=1):
        parts = [p.strip() for p in line.split("|")]
        image_prompt = parts[0]
        video_prompt = parts[1] if len(parts) > 1 and parts[1] else image_prompt
        transition = parse_transition(parts[2]) if len(parts) > 2 and parts[2] else {"type": "cut", "seconds": 0.0}
        text = f"{image_prompt} {video_prompt}".lower()
        scene = {
            "id": f"scene-{stamp}-{idx}",
            "sceneIndex": idx,
            "imagePrompt": image_prompt,
            "videoPrompt": video_prompt,
            "detectedCharacters": [c["name"] for c in chars if c["name"].lower() in text],
            "transition": transition,
            "locked": True,
            "imageStatus": "idle",
            "videoStatus": "idle",
        }
        if images_dir:
            img = next((images_dir / f"canh_{idx:02d}{ext}" for ext in (".png", ".jpg", ".jpeg", ".webp")
                        if (images_dir / f"canh_{idx:02d}{ext}").exists()), None)
            if img:
                scene["imageBase64"], scene["imageMimeType"] = encode_image(img)
                scene["imageStatus"] = "ready"
        scenes.append(scene)
    return scenes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--script", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--scene-images", type=Path, default=None)
    ap.add_argument("--extra-character", action="append", default=[],
                    help="ảnh nhân vật phụ (tên nhân vật = tên tệp)")
    ap.add_argument("--style-bible", default=DEFAULT_STYLE_BIBLE)
    ap.add_argument("--duration", type=int, choices=(4, 6, 8), default=6)
    ap.add_argument("--name", default="Soc_Nho_Director_Package")
    args = ap.parse_args()

    chars = build_characters(args.extra_character)
    scenes = build_scenes(args.script, args.scene_images, chars)
    if not scenes:
        print("Kịch bản trống.", file=sys.stderr)
        return 1

    package = {
        "version": 2,
        "name": args.name,
        "styleBible": args.style_bible,
        "selectedImageModel": "🍌 Nano Banana Pro",
        "selectedVideoModel": "Omni 1.1 Flash",
        "clipDuration": args.duration,
        "characters": chars,
        "scenes": scenes,
        "rawScript": args.script.read_text(encoding="utf-8"),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    ready = sum(1 for s in scenes if s["imageStatus"] == "ready")
    print(f"{args.out}  {args.out.stat().st_size / 1e6:.1f} MB | {len(chars)} nhân vật, "
          f"{len(scenes)} cảnh, {ready} cảnh có ảnh sẵn")
    return 0


if __name__ == "__main__":
    sys.exit(main())
