"""CLI entrypoint for socnhotv.

Chạy:
    python -m socnhotv voice list
    python -m socnhotv voice clone --input ... --name ...
    python -m socnhotv voice speak --voice ... --text ...
"""

from __future__ import annotations

import argparse
import sys

from socnhotv.cli.voice import handle_voice_cli, setup_voice_parser


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="socnhotv",
        description="SocNhoTV Studio & Video Generation Engine CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    setup_voice_parser(subparsers)

    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()

    if args.command == "voice":
        return handle_voice_cli(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
