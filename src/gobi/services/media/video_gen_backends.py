"""Image-to-video generation backends (fal.ai queue API).

Replaces browser automation of Google Flow with a direct API call.
Each backend maps the shared arguments onto a fal endpoint's input schema.
Add a backend by adding an entry to BACKENDS after checking its schema at
https://fal.ai/models/<endpoint_id>/api.

Usage:
    python -m gobi.services.media.video_gen_backends kling3-std \
        --image assets/koc_dna/MASTER_GOBI_OFFICIAL.jpg \
        --prompt "..." --duration 8 --dry-run
"""
import argparse
import base64
import mimetypes
import os
import sys
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
OUT_DIR = os.path.join(ROOT, "output", "videogen")

BACKENDS = {
    "kling3-std": {
        "endpoint": "fal-ai/kling-video/v3/standard/image-to-video",
        "usd_per_sec": 0.084,  # 720p silent; ~0.126 with audio (third-party figures, verify)
        "build": lambda image_url, prompt, duration, audio: {
            "start_image_url": image_url,
            "prompt": prompt,
            "duration": str(duration),
            "generate_audio": audio,
        },
    },
}


def load_env():
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def image_to_data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"


def generate(backend, image_path, prompt, duration=8, audio=False, timeout=900):
    cfg = BACKENDS[backend]
    key = os.environ.get("FAL_KEY")
    if not key:
        raise RuntimeError("FAL_KEY is not set (add it to .env)")
    headers = {"Authorization": f"Key {key}", "Content-Type": "application/json"}
    body = cfg["build"](image_to_data_uri(image_path), prompt, duration, audio)
    r = requests.post(f"https://queue.fal.run/{cfg['endpoint']}", json=body, headers=headers, timeout=120)
    r.raise_for_status()
    job = r.json()
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = requests.get(job["status_url"], headers=headers, timeout=60).json()
        if s.get("status") == "COMPLETED":
            break
        time.sleep(5)
    else:
        raise TimeoutError(f"{backend} did not finish in {timeout}s")
    res = requests.get(job["response_url"], headers=headers, timeout=60)
    res.raise_for_status()
    video_url = res.json()["video"]["url"]
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"{backend}_{int(time.time())}.mp4")
    with open(out, "wb") as f:
        f.write(requests.get(video_url, timeout=300).content)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("backend", choices=sorted(BACKENDS))
    p.add_argument("--image", required=True)
    p.add_argument("--prompt", required=True)
    p.add_argument("--duration", type=int, default=8)
    p.add_argument("--audio", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="print estimated cost only")
    a = p.parse_args()
    load_env()
    est = BACKENDS[a.backend]["usd_per_sec"] * a.duration
    print(f"[{a.backend}] estimated cost: ~${est:.2f}")
    if a.dry_run:
        return 0
    print("saved:", generate(a.backend, a.image, a.prompt, a.duration, a.audio))
    return 0


if __name__ == "__main__":
    sys.exit(main())
