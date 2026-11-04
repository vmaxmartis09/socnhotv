"""CLI module cho hệ thống Voice Cloner (OmniVoice).

Sử dụng:
    python -m socnhotv voice list
    python -m socnhotv voice clone --input <audio_or_video> --name <voice_id> [--dialect south|north|central] [--project <project_id>] [--character <character_id>]
    python -m socnhotv voice speak --voice <voice_id> --text "Xin chào các bạn" [--output <file.mp3>]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from socnhotv.core.storage.project_store import get_repo_root, ProjectStore


def setup_voice_parser(subparsers: argparse._SubParsersAction) -> None:
    voice_parser = subparsers.add_parser("voice", help="Quản lý Voice Vault & Nhân bản giọng nói OmniVoice")
    voice_subs = voice_parser.add_subparsers(dest="voice_command", required=True)

    # 1. clone
    c = voice_subs.add_parser("clone", help="Nhân bản giọng từ tệp âm thanh hoặc video (.mp3, .wav, .mp4, .mov)")
    c.add_argument("--input", "-i", required=True, help="Đường dẫn tới tệp âm thanh/video nguồn")
    c.add_argument("--name", "-n", required=True, help="Mã giọng (voice_id), ví dụ: be-an, soc-nho-warm")
    c.add_argument("--dialect", "-d", default="south", choices=["south", "north", "central"], help="Phương ngữ (mặc định: south)")
    c.add_argument("--project", "-p", default=None, help="Mã dự án (nếu muốn gắn vào nhân vật)")
    c.add_argument("--character", "-c", default=None, help="Mã nhân vật trong dự án (nếu muốn tự động gán giọng)")

    # 2. list
    l = voice_subs.add_parser("list", help="Liệt kê danh sách giọng trong Voice Vault")
    l.add_argument("--json", action="store_true", help="Xuất định dạng JSON")

    # 3. speak
    s = voice_subs.add_parser("speak", help="Đọc văn bản bằng giọng đã clone")
    s.add_argument("--voice", "-v", required=True, help="Mã giọng trong Voice Vault")
    s.add_argument("--text", "-t", required=True, help="Đoạn văn bản cần đọc")
    s.add_argument("--output", "-o", default=None, help="Tệp xuất âm thanh (.mp3)")
    s.add_argument("--tempo", type=float, default=1.05, help="Tốc độ đọc (1.00 - 1.30)")


def handle_voice_cli(args: argparse.Namespace) -> int:
    repo_root = get_repo_root()
    vault_dir = repo_root / "data" / "shared" / "voice_vault"
    vault_dir.mkdir(parents=True, exist_ok=True)

    # Thêm src vào sys.path để gọi VoiceCloner
    root_src = str(repo_root / "src")
    if root_src not in sys.path:
        sys.path.insert(0, root_src)

    from gobi.services.voice import VoiceCloner

    cloner = VoiceCloner(profiles_dir=vault_dir)

    if args.voice_command == "list":
        profiles = cloner.list_profiles()
        if getattr(args, "json", False):
            print(json.dumps(profiles, ensure_ascii=False, indent=2))
            return 0

        print(f"\n🎙️  VOICE VAULT ({len(profiles)} giọng nói sẵn sàng):")
        print("─" * 65)
        for p in profiles:
            vid = p.get("profile_id", "unknown")
            dialect = p.get("dialect", "south")
            speaker = p.get("speaker_name", vid)
            dur = p.get("duration", 0)
            sample = "🔊 Có mẫu" if p.get("sample_path") else "—"
            print(f" • [{vid:<18}] {speaker:<18} | {dialect:<7} | {dur:4.1f}s | {sample}")
        print("─" * 65 + "\n")
        return 0

    if args.voice_command == "clone":
        input_path = Path(args.input).resolve()
        if not input_path.exists():
            print(f"❌ Lỗi: Không tìm thấy tệp đầu vào '{args.input}'", file=sys.stderr)
            return 1

        print(f"⚡ Đang nhân bản giọng '{args.name}' từ '{input_path.name}' (phương ngữ: {args.dialect})...")
        meta = cloner.create_profile(
            media_path=str(input_path),
            profile_id=args.name,
            dialect=args.dialect,
            speaker_name=args.name,
        )

        print(f"✅ Nhân bản thành công giọng: {args.name}")
        print(f"   - Thư mục lưu trữ: data/shared/voice_vault/{args.name}/")
        print(f"   - Thời lượng mẫu: {meta.get('duration', 0):.1f}s")
        if meta.get("transcript"):
            print(f"   - Transcript: \"{meta.get('transcript')}\"")
        print(f"   - Mastering: -14 LUFS · 44.1kHz · 192kbps")

        # Gắn vào nhân vật nếu có --project và --character
        if args.project and args.character:
            store = ProjectStore(args.project)
            p_json = store.project_dir / "project.json"
            if p_json.exists():
                try:
                    p_data = json.loads(p_json.read_text(encoding="utf-8"))
                    if "characters" in p_data and args.character in p_data["characters"]:
                        p_data["characters"][args.character]["voice_id"] = args.name
                        p_data["characters"][args.character]["sample_audio_url"] = f"/voices/{args.name}/sample"
                        p_json.write_text(json.dumps(p_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                        print(f"   - Đã gán vào nhân vật '{args.character}' trong dự án '{args.project}'")
                except Exception as e:
                    print(f"⚠️ Không thể cập nhật project.json: {e}", file=sys.stderr)

        return 0

    if args.voice_command == "speak":
        out_file = args.output
        if not out_file:
            out_file = str(repo_root / "output" / f"{args.voice}_speak_{int(Path(args.voice).stat().st_mtime if False else 1)}.mp3")

        print(f"🗣️ Đang tổng hợp giọng '{args.voice}' đọc: \"{args.text[:50]}...\"")
        result_path = cloner.synthesize(
            profile_id=args.voice,
            text=args.text,
            output_path=out_file,
            tempo=args.tempo,
        )
        print(f"✅ Đã tạo tệp âm thanh thành công: {result_path}")
        return 0

    return 0
