#!/usr/bin/env python3
"""
FFmpeg Binary Bundle Tool Runner (T-08)
Downloads static Windows FFmpeg CPU binary into data/shared/models/ffmpeg-bin/ and verifies execution.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
TARGET_DIR = REPO_ROOT / "data" / "shared" / "models" / "ffmpeg-bin"
DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def ensure_ffmpeg() -> tuple[Path, Path, str]:
    """Ensure ffmpeg.exe and ffprobe.exe exist in TARGET_DIR. Download if missing."""
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = TARGET_DIR / "ffmpeg.exe"
    ffprobe_exe = TARGET_DIR / "ffprobe.exe"

    if not ffmpeg_exe.exists() or not ffprobe_exe.exists():
        zip_path = TARGET_DIR / "ffmpeg_temp.zip"
        req = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": "SocNhoTV-Toolbox/1.0"})
        with urllib.request.urlopen(req) as resp, open(zip_path, "wb") as out_f:
            shutil.copyfileobj(resp, out_f)

        # Extract binaries
        with zipfile.ZipFile(zip_path, "r") as z:
            for member in z.namelist():
                if member.endswith("ffmpeg.exe"):
                    with z.open(member) as src, open(ffmpeg_exe, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                elif member.endswith("ffprobe.exe"):
                    with z.open(member) as src, open(ffprobe_exe, "wb") as dst:
                        shutil.copyfileobj(src, dst)

        if zip_path.exists():
            zip_path.unlink()

    # Verify execution
    proc = subprocess.run([str(ffmpeg_exe), "-version"], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg binary verification failed with exit code {proc.returncode}")

    ver_line = proc.stdout.splitlines()[0] if proc.stdout else "ffmpeg version unknown"
    return ffmpeg_exe, ffprobe_exe, ver_line


def main():
    parser = argparse.ArgumentParser(description="FFmpeg Binary Bundle Runner")
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    start_t = time.time()
    out_file = Path(args.out_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        ffmpeg_path, ffprobe_path, ver_str = ensure_ffmpeg()
        ffmpeg_sha = compute_sha256(ffmpeg_path)
        ffprobe_sha = compute_sha256(ffprobe_path)

        out_data = {
            "ok": True,
            "outputs": [
                {
                    "path": str(ffmpeg_path),
                    "kind": "ffmpeg_binary",
                    "sha256": ffmpeg_sha
                },
                {
                    "path": str(ffprobe_path),
                    "kind": "ffprobe_binary",
                    "sha256": ffprobe_sha
                }
            ],
            "store_records": [
                {
                    "id": "ffmpeg-bin",
                    "created_by_tool": "ffmpeg-bin",
                    "tool_version": "7.1.0",
                    "source": DOWNLOAD_URL,
                    "license": "GPL-3.0",
                    "metadata": {
                        "version_string": ver_str,
                        "binaries": ["ffmpeg.exe", "ffprobe.exe"]
                    }
                }
            ],
            "warnings": [],
            "error": None,
            "elapsed_s": round(time.time() - start_t, 4)
        }
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2)

        print(str(out_file))
        sys.exit(0)

    except Exception as e:
        err_data = {
            "ok": False,
            "outputs": [],
            "store_records": [],
            "warnings": [],
            "error": {
                "code": "FFMPEG_SETUP_FAILED",
                "message": str(e),
                "fix_hint": "Check network connection to gyan.dev or place static ffmpeg.exe into data/shared/models/ffmpeg-bin/"
            },
            "elapsed_s": round(time.time() - start_t, 4)
        }
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(err_data, f, indent=2)

        print(str(out_file))
        sys.exit(2)


if __name__ == "__main__":
    main()
