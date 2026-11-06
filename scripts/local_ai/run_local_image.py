#!/usr/bin/env python3
"""Script chạy model ảnh cục bộ trên Apple Silicon qua mflux (MLX FLUX.1 schnell 4-bit)."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_VENV = REPO_ROOT / ".venv-local-ai"
LOCAL_PYTHON = LOCAL_VENV / "bin" / "python"
LOCAL_MFLUX = LOCAL_VENV / "bin" / "mflux-generate"


def is_mflux_available() -> bool:
    return LOCAL_MFLUX.exists() or subprocess.run(["which", "mflux-generate"], capture_output=True).returncode == 0


def generate_local_image(
    prompt: str,
    output_path: Path,
    width: int = 1024,
    height: int = 576,
    steps: int = 4,
    seed: int = 42,
    model: str = "schnell",
) -> None:
    if not is_mflux_available():
        raise RuntimeError(
            "Chưa cài đặt mflux trong môi trường máy. "
            "Để cài đặt mflux trên Mac M4 (venv riêng):\\n"
            "  uv venv .venv-local-ai\\n"
            "  .venv-local-ai/bin/pip install mflux\\n"
            "Mflux chạy FLUX.1 schnell 4-bit trên chip Apple Silicon (~9.2GB checkpoint)."
        )

    cmd = [
        str(LOCAL_MFLUX if LOCAL_MFLUX.exists() else "mflux-generate"),
        "--model", model,
        "--prompt", prompt,
        "--width", str(width),
        "--height", str(height),
        "--steps", str(steps),
        "--seed", str(seed),
        "--output", str(output_path),
    ]

    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Lỗi khi chạy mflux-generate: {res.stderr[:300]}")
    elapsed = time.time() - t0
    print(f"Hoàn thành sinh ảnh mflux trong {elapsed:.2f}s: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=576)
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model", default="schnell")
    args = parser.parse_args()

    out_file = Path(args.output)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    generate_local_image(
        prompt=args.prompt,
        output_path=out_file,
        width=args.width,
        height=args.height,
        steps=args.steps,
        seed=args.seed,
        model=args.model,
    )


if __name__ == "__main__":
    main()
