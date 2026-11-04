#!/usr/bin/env python3
"""Video Craft Knowledge Indexer & Status Reporter.

Scans data/shared/knowledge/video_craft/techniques/*.md,
validates front-matter schemas, and generates:
1. techniques/registry.json (machine-readable catalog for agents/code)
2. techniques/STATUS.md (human-readable progress and promotion tracker)

Supports --check flag for automated tests and CI.
"""
from __future__ import annotations

import argparse
from datetime import datetime, date
import json
from pathlib import Path
import sys
import yaml

def get_workspace_root() -> Path:
    curr = Path(__file__).resolve()
    for p in [curr] + list(curr.parents):
        if (p / "data" / "shared" / "knowledge" / "video_craft" / "techniques").is_dir():
            return p
    return Path.cwd()

WORKSPACE_ROOT = get_workspace_root()
TECHNIQUES_DIR = WORKSPACE_ROOT / "data" / "shared" / "knowledge" / "video_craft" / "techniques"
REGISTRY_PATH = TECHNIQUES_DIR / "registry.json"
STATUS_MD_PATH = TECHNIQUES_DIR / "STATUS.md"

VALID_STATUSES = {"knowledge", "prototyped", "in-studio"}
VALID_CONFIDENCE = {"high", "medium", "low"}

def parse_frontmatter(file_path: Path) -> dict:
    content = file_path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise ValueError(f"Missing YAML front-matter in {file_path.name}")
    parts = content.split("---\n", 2)
    if len(parts) < 3:
        raise ValueError(f"Malformed YAML front-matter in {file_path.name}")
    
    meta = yaml.safe_load(parts[1])
    if not isinstance(meta, dict):
        raise ValueError(f"Front-matter in {file_path.name} is not a valid dict")
    return meta

def validate_card(meta: dict, filename: str) -> list[str]:
    errors = []
    required_keys = [
        "id", "title", "status", "reproducible_with_our_stack",
        "needs", "confidence", "last_verified", "expires_at"
    ]
    for k in required_keys:
        if k not in meta:
            errors.append(f"{filename}: missing required key '{k}'")

    status = meta.get("status")
    if status not in VALID_STATUSES:
        errors.append(f"{filename}: invalid status '{status}', must be one of {VALID_STATUSES}")

    confidence = meta.get("confidence")
    if confidence not in VALID_CONFIDENCE:
        errors.append(f"{filename}: invalid confidence '{confidence}', must be one of {VALID_CONFIDENCE}")

    # Check expiration
    expires_at = meta.get("expires_at")
    if expires_at and expires_at != "never":
        try:
            if isinstance(expires_at, str):
                exp_date = datetime.strptime(expires_at, "%Y-%m-%d").date()
            elif isinstance(expires_at, date):
                exp_date = expires_at
            else:
                errors.append(f"{filename}: expires_at must be YYYY-MM-DD string or 'never'")
                exp_date = None
            
            if exp_date and exp_date < date.today():
                meta["is_expired"] = True
            else:
                meta["is_expired"] = False
        except Exception as e:
            errors.append(f"{filename}: invalid date format for expires_at: {e}")
    else:
        meta["is_expired"] = False

    return errors

def scan_all_cards() -> tuple[list[dict], list[str]]:
    cards = []
    all_errors = []
    md_files = sorted(TECHNIQUES_DIR.glob("*.md"))
    # Exclude STATUS.md
    md_files = [f for f in md_files if f.name != "STATUS.md"]

    for f in md_files:
        try:
            meta = parse_frontmatter(f)
            meta["filename"] = f.name
            meta["file_path"] = str(f)
            errs = validate_card(meta, f.name)
            if errs:
                all_errors.extend(errs)
            else:
                cards.append(meta)
        except Exception as ex:
            all_errors.append(f"Error reading {f.name}: {ex}")

    return cards, all_errors

def generate_registry(cards: list[dict]) -> dict:
    registry = {
        "version": "1.0.0",
        "generated_at": datetime.now().isoformat(),
        "total_cards": len(cards),
        "in_studio_count": sum(1 for c in cards if c.get("status") == "in-studio"),
        "prototyped_count": sum(1 for c in cards if c.get("status") == "prototyped"),
        "knowledge_count": sum(1 for c in cards if c.get("status") == "knowledge"),
        "expired_count": sum(1 for c in cards if c.get("is_expired")),
        "techniques": {c["id"]: c for c in cards}
    }
    return registry

def generate_status_md(cards: list[dict], registry: dict) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Trạng Thái Kho Kỹ Thuật Video Craft (Techniques Status)",
        "",
        f"- **Cập nhật tự động**: {now_str}",
        f"- **Tổng số kỹ thuật**: {registry['total_cards']}",
        f"- **Đã tích hợp vào Studio (`in-studio`)**: **{registry['in_studio_count']}** thẻ",
        f"- **Đang thử nghiệm (`prototyped`)**: {registry['prototyped_count']} thẻ",
        f"- **Kho kiến thức tham chiếu (`knowledge`)**: {registry['knowledge_count']} thẻ",
        f"- **Hết hạn / Cần đánh giá lại (`needs-review`)**: {registry['expired_count']} thẻ",
        "",
        "---",
        "",
        "## 1. Kỹ Thuật Đã Vào Studio (`in-studio` - Sẵn Sàng Sản Xuất)",
        "",
        "| ID | Tên Kỹ Thuật | Tái Lập Được? | Nơi Triển Khai | Bằng Chứng (Video ID) |",
        "| :--- | :--- | :---: | :--- | :---: |"
    ]

    in_studio = [c for c in cards if c.get("status") == "in-studio"]
    for c in in_studio:
        impl = ", ".join(f"`{p}`" for p in c.get("implemented_in", [])) or "Sẵn có"
        ev = ", ".join(c.get("evidence_videos", []))
        repro = "✅ " + c.get("reproducible_with_our_stack", "yes")
        lines.append(f"| `{c['id']}` | **{c['title']}** | {repro} | {impl} | {ev} |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Hàng Chờ Triển Khai (`prototyped` hoặc `knowledge` ưu tiên cao)",
        "",
        "| ID | Tên Kỹ Thuật | Khả Năng Tái Lập | Công Cụ Cần | Đánh Giá Ưu Tiên |",
        "| :--- | :--- | :--- | :--- | :---: |"
    ])

    pending = [c for c in cards if c.get("status") in {"prototyped", "knowledge"} and c.get("build") != "no"]
    for c in pending:
        needs = ", ".join(c.get("needs", []))
        lines.append(f"| `{c['id']}` | {c['title']} | {c.get('reproducible_with_our_stack', '')} | {needs} | {c.get('confidence', '').upper()} |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Kiến Thức Tham Chiếu / Ngoài Phạm Vi (`knowledge` / `build: no`)",
        "",
        "| ID | Tên Kỹ Thuật | Lý Do Giữ Mức Kiến Thức | Hết Hạn |",
        "| :--- | :--- | :--- | :---: |"
    ])

    out_of_scope = [c for c in cards if c.get("build") == "no"]
    for c in out_of_scope:
        exp = c.get("expires_at", "never")
        lines.append(f"| `{c['id']}` | {c['title']} | {c.get('reproducible_with_our_stack', '')} | {exp} |")

    lines.append("")
    return "\n".join(lines)

def build_index(check_only: bool = False, print_json: bool = False) -> int:
    cards, errors = scan_all_cards()
    if errors:
        print(f"❌ Found {len(errors)} validation errors:")
        for e in errors:
            print(f"  - {e}")
        return 1

    registry = generate_registry(cards)

    if print_json:
        print(json.dumps(registry, indent=2, ensure_ascii=False))
        return 0

    if check_only:
        print(f"✅ All {len(cards)} technique cards are valid!")
        return 0

    # Write files
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    status_md = generate_status_md(cards, registry)
    STATUS_MD_PATH.write_text(status_md, encoding="utf-8")
    print(f"✅ Generated {REGISTRY_PATH} and {STATUS_MD_PATH} successfully ({len(cards)} cards).")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Index video craft techniques.")
    parser.add_argument("--check", action="store_true", help="Validate front-matter without writing.")
    parser.add_argument("--json", action="store_true", help="Output registry JSON to stdout.")
    args = parser.parse_args()

    sys.exit(build_index(check_only=args.check, print_json=args.json))

if __name__ == "__main__":
    main()
