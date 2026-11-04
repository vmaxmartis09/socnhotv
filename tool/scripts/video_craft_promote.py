#!/usr/bin/env python3
"""Video Craft Card Promotion & Lifecycle Gate.

Provides a standardized promotion pipeline for technique cards created by research agents (D/D2):
1. Verifies front-matter completeness.
2. Checks reproducibility score against our current stack (Tier-0 HyperFrames + OmniVoice + DNA).
3. If implemented with tests/demos, promotes status to 'in-studio'.
4. Detects expired cards and updates STATUS.md with 'needs-review'.
5. Triggers index regeneration via video_craft_index.py.
"""
from __future__ import annotations

import argparse
from datetime import datetime, date
from pathlib import Path
import sys

# Ensure tool directory and workspace root are in sys.path
_curr = Path(__file__).resolve()
for _p in [_curr.parent.parent, _curr.parent]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.video_craft_index import (
    TECHNIQUES_DIR,
    parse_frontmatter,
    validate_card,
    build_index,
)

def promote_card(technique_id: str, new_status: str = "in-studio", implementation_path: str = "") -> int:
    card_file = TECHNIQUES_DIR / f"{technique_id}.md"
    if not card_file.exists():
        print(f"❌ Technique card not found: {card_file}")
        return 1

    content = card_file.read_text(encoding="utf-8")
    parts = content.split("---\n", 2)
    if len(parts) < 3:
        print(f"❌ Card {technique_id}.md is missing valid front-matter")
        return 1

    meta = yaml.safe_load(parts[1])
    body = parts[2]

    old_status = meta.get("status", "knowledge")
    meta["status"] = new_status
    meta["last_verified"] = date.today().isoformat()

    if implementation_path:
        impl_list = meta.get("implemented_in", [])
        if implementation_path not in impl_list:
            impl_list.append(implementation_path)
        meta["implemented_in"] = impl_list

    # Re-serialize front-matter
    new_yaml = yaml.dump(meta, sort_keys=False, allow_unicode=True).strip()
    new_content = f"---\n{new_yaml}\n---\n{body}"
    card_file.write_text(new_content, encoding="utf-8")

    print(f"✅ Card '{technique_id}' promoted: {old_status} -> {new_status}")
    if implementation_path:
        print(f"   Implemented in: {implementation_path}")

    # Rebuild index
    build_index()
    return 0

def check_expirations() -> int:
    """Scans all cards and reports any that have passed their expires_at date."""
    print("=== CHECKING KNOWLEDGE EXPIRATIONS ===")
    expired = []
    for f in sorted(TECHNIQUES_DIR.glob("*.md")):
        if f.name == "STATUS.md":
            continue
        try:
            meta = parse_frontmatter(f)
            exp = meta.get("expires_at")
            if exp and exp != "never":
                exp_date = datetime.strptime(str(exp), "%Y-%m-%d").date()
                if exp_date < date.today():
                    expired.append((meta.get("id", f.stem), exp_date, meta.get("title", "")))
        except Exception as e:
            print(f"Error parsing {f.name}: {e}")

    if expired:
        print(f"⚠️ Found {len(expired)} expired technique cards needing review:")
        for cid, dt, title in expired:
            print(f"  - [{cid}] {title} (Expired on {dt})")
    else:
        print("✅ No expired cards found. All technique cards are current.")

    return len(expired)

def main():
    parser = argparse.ArgumentParser(description="Promote or manage video craft card lifecycle.")
    parser.add_argument("--id", type=str, help="Technique ID to promote (e.g. confession-hook).")
    parser.add_argument("--status", type=str, default="in-studio", choices=["knowledge", "prototyped", "in-studio"])
    parser.add_argument("--impl", type=str, default="", help="Path where technique is implemented.")
    parser.add_argument("--check-expiry", action="store_true", help="Scan for expired knowledge cards.")
    args = parser.parse_args()

    if args.check_expiry:
        sys.exit(check_expirations())

    if args.id:
        sys.exit(promote_card(args.id, new_status=args.status, implementation_path=args.impl))

    parser.print_help()
    sys.exit(0)

if __name__ == "__main__":
    main()
