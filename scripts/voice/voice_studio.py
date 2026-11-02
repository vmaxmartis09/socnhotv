#!/usr/bin/env python3
"""Voice Studio: clone | speak | oneshot | list

  uv run python scripts/voice/voice_studio.py clone --input mau.mp4 --name voice-be-trai --dialect south
  uv run python scripts/voice/voice_studio.py speak --voice voice-be-trai --script "Xin chào" --output output/x.mp3
  uv run python scripts/voice/voice_studio.py oneshot --input mau.mp3 --script "..." --output output/x.mp3
  uv run python scripts/voice/voice_studio.py list
"""

import argparse
import os
import sys
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
from gobi.services.voice import VoiceCloner  # noqa: E402


def read_script(value: str) -> str:
    return Path(value).read_text(encoding="utf-8").strip() if os.path.isfile(value) else value


def main():
    parser = argparse.ArgumentParser(description="Vietnamese Voice Clone + Voice Vault")
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("clone", help="Tạo giọng mới trong Voice Vault")
    c.add_argument("--input", "-i", required=True)
    c.add_argument("--name", "-n", required=True)
    c.add_argument("--dialect", "-d", default="north", choices=["north", "south", "central"])
    c.add_argument("--text", "-t", default=None, help="Transcript khớp lát mẫu (mặc định Whisper tự chép)")
    c.add_argument("--duration", type=float, default=4.5, help="Độ dài lát mẫu, 3.5-6.0s")

    s = sub.add_parser("speak", help="Đọc kịch bản bằng giọng trong vault")
    s.add_argument("--voice", "-v", required=True)
    s.add_argument("--script", "-s", required=True, help="Văn bản hoặc đường dẫn file .txt")
    s.add_argument("--output", "-o", default=None)
    s.add_argument("--engine", "-e", default="omnivoice", choices=["omnivoice", "edge_tts"])
    s.add_argument("--tempo", type=float, default=1.10, help="1.00-1.30")
    s.add_argument("--no-master", action="store_true")

    o = sub.add_parser("oneshot", aliases=["one-shot"], help="Clone và đọc trong một lệnh")
    o.add_argument("--input", "-i", required=True)
    o.add_argument("--script", "-s", required=True)
    o.add_argument("--output", "-o", required=True)
    o.add_argument("--engine", "-e", default="omnivoice", choices=["omnivoice", "edge_tts"])
    o.add_argument("--name", "-n", default=None, help="Có tên thì lưu vào vault")

    sub.add_parser("list", help="Liệt kê giọng trong vault")

    args = parser.parse_args()
    cloner = VoiceCloner()

    if args.command == "clone":
        meta = cloner.create_profile(
            args.input, args.name, dialect=args.dialect,
            custom_transcript=args.text, target_duration=args.duration,
        )
        print(f"\n[OK] Đã tạo giọng: {meta['profile_id']}")

    elif args.command == "speak":
        out = args.output or f"output/{args.voice}_script.mp3"
        res = cloner.speak(
            args.voice, read_script(args.script), out,
            engine=args.engine, master=not args.no_master, tempo_factor=args.tempo,
        )
        print(f"\n[OK] {res}")

    elif args.command in ("oneshot", "one-shot"):
        res = cloner.clone_and_speak(args.input, read_script(args.script), args.output, args.name, args.engine)
        print(f"\n[OK] {res}")

    elif args.command == "list":
        rows = cloner.list_profiles()
        print("\nVOICE VAULT")
        for d in rows:
            folder = Path(d["_dir"])
            print(f" - [{d['profile_id']}] {d.get('speaker_name', '')} ({d.get('dialect', 'N/A')}) {d.get('duration', '?')}s")
            print(f"   Text mẫu: \"{d.get('transcript', '')[:65]}\"")
            for label, key in (("Source gốc", "source_preview"), ("Clone mẫu", "cloned_sample")):
                f = folder / d.get("files", {}).get(key, "")
                if f.is_file():
                    print(f"   {label}: {f}")
        if not rows:
            print("Chưa có giọng nào trong vault.")


if __name__ == "__main__":
    main()
