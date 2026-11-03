#!/usr/bin/env python3
"""Chạy thử thật 1 ảnh (+ tuỳ chọn 1 video ngắn) qua Gemini/Veo, có khóa chi tiêu cứng.

Mặc định chỉ IN ƯỚC TÍNH, không gọi mạng và không tốn tiền. Phải thêm --confirm mới chi tiền.
  python tool/scripts/real_smoke.py --project soc-nho-tv                   # ước tính
  python tool/scripts/real_smoke.py --project soc-nho-tv --confirm          # 1 ảnh
  python tool/scripts/real_smoke.py --project soc-nho-tv --confirm --video 4  # 1 ảnh + video 4 giây
Khóa: biến GEMINI_API_KEY hoặc dòng GEMINI_API_KEY=... trong .env ở gốc repo. Trần: SOCNHOTV_SPEND_CAP_USD (mặc định 5).
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

# Tự chuyển sang Python của project (.venv) nếu đang chạy bằng python3 hệ thống thiếu thư viện
_VENV_PY = Path(__file__).resolve().parents[2] / ".venv" / "bin" / "python"
try:
    import pydantic  # noqa: F401
except ModuleNotFoundError:
    if _VENV_PY.exists() and Path(sys.executable).resolve() != _VENV_PY.resolve():
        os.execv(str(_VENV_PY), [str(_VENV_PY), *sys.argv])
    raise

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from socnhotv.core.providers.google_provider import (  # noqa: E402
    GoogleProvider, MissingApiKey, estimate_image_usd, estimate_video_usd,
)
from socnhotv.core.providers.spend_guard import SpendCapExceeded, SpendGuard  # noqa: E402
from socnhotv.core.storage.project_store import ProjectStore  # noqa: E402

PROMPT = ("Sóc Nhỏ đứng chính diện trên bãi cỏ xanh trong công viên nắng sớm, mắt to bóng, mỉm cười. "
          "3D Pixar-style animation, ánh sáng studio mềm ấm, không chữ, không watermark")


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="soc-nho-tv")
    ap.add_argument("--video", type=int, default=0, help="số giây video (0 = không tạo video)")
    ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args()

    store = ProjectStore(a.project)
    guard = SpendGuard(store.runs_dir)
    est = estimate_image_usd() + (estimate_video_usd(a.video) if a.video else 0.0)
    print(f"Ước tính: ${est:.2f} | đã chi ${guard.spent():.2f} | trần ${guard.cap:.2f}")
    if not a.confirm:
        print("Chưa chi tiền. Thêm --confirm để chạy thật.")
        return 0
    try:
        p = GoogleProvider(store, guard)
    except MissingApiKey as e:
        print("LỖI:", e)
        return 2
    ref = f"characters/soc_nho/soc_nho_01.png"
    try:
        (img,) = await p.generate_images(PROMPT, references=[ref], aspect_ratio="9:16", node_id="smoke", run_id="smoke")
        print("ảnh:", store.project_dir / img.uri)
        if a.video:
            vid = await p.generate_video("Sóc Nhỏ vẫy tay chào, camera đẩy nhẹ", first_frame_uri=img.uri,
                                         duration_sec=a.video, node_id="smoke", run_id="smoke")
            print("video:", store.project_dir / vid.uri)
    except SpendCapExceeded as e:
        print("DỪNG:", e)
        return 3
    print(f"Đã chi ước tính ${guard.spent():.2f} / ${guard.cap:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
