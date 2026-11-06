#!/usr/bin/env python3
"""Chạy THẬT một template ra MP4 (I4) — thay cho render_template_mp4.py (chỉ chạy trên Windows, dùng dữ liệu mẫu).

Ví dụ:
  .venv/bin/python data/shared/templates/_engine/run_template.py shorts-fact-v1 --out /tmp/x \
      --slots slots.json --voice voice.mp3 --voice-text "lời đã đọc" --asset product.png=/path/p.png
Không gọi nguồn trả phí. Không có --voice thì video im lặng (báo cáo ghi rõ).
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "tool" / "src"))

from socnhotv.video.templates.runner import run_template  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("template_id")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--slots", type=Path, help="JSON slot (thiếu thì lấy sample.data.json và báo cáo)")
    ap.add_argument("--platform")
    ap.add_argument("--voice", type=Path)
    ap.add_argument("--voice-text")
    ap.add_argument("--asset", action="append", default=[], help="tên=đường_dẫn (ghi đè/ bổ sung assets/)")
    ap.add_argument("--quality", default="draft", choices=["draft", "looks", "delivery"])
    a = ap.parse_args()
    slots = json.loads(a.slots.read_text(encoding="utf-8")) if a.slots else {}
    assets = dict(x.split("=", 1) for x in a.asset)
    rep = run_template(a.template_id, a.out, slots=slots, platform=a.platform, voice_audio=a.voice,
                       voice_text=a.voice_text, asset_files=assets, quality=a.quality)
    print(json.dumps(rep.to_dict(), ensure_ascii=False, indent=2))
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
