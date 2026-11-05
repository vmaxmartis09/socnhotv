#!/usr/bin/env python3
"""
Voice Vault Resolver & Index Generator
Complies with T0_TOOLBOX_PROMPT §2.4 and §3 (T-04).
"""
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
VOICE_VAULT_DIR = REPO_ROOT / "data" / "shared" / "voice_vault"
INDEX_PATH = VOICE_VAULT_DIR / "index.jsonl"


def scan_and_index_voices() -> list[dict]:
    """Scan all voice subdirectories and return normalized records."""
    if not VOICE_VAULT_DIR.exists():
        return []

    records = []
    # Sort subdirectories for deterministic indexing
    subdirs = sorted([d for d in VOICE_VAULT_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")])

    for sdir in subdirs:
        voice_file = sdir / "voice.json"
        if not voice_file.exists():
            continue

        with open(voice_file, "r", encoding="utf-8") as f:
            vdata = json.load(f)

        vid = vdata.get("id", sdir.name)
        status = vdata.get("status", "ready")
        rec = {
            "id": vid,
            "created_by_tool": "voice_vault_indexer",
            "tool_version": "1.0.0",
            "source": f"voice_vault/{sdir.name}",
            "license": "SocNhoTV Internal" if status == "ready" else "Pending Collection",
            "created_at": "2026-11-05T00:00:00",
            "files": {
                "voice_json": f"{sdir.name}/voice.json",
                "samples": vdata.get("sample_paths", [])
            },
            "metadata": {
                "display_name": vdata.get("display_name", vid),
                "aliases": vdata.get("aliases", []),
                "engine": vdata.get("engine", "omnivoice"),
                "lang": vdata.get("lang", "vi"),
                "status": status,
                "loudness": vdata.get("loudness", -14.0),
                "consent_note": vdata.get("consent_note", "")
            }
        }
        records.append(rec)

    return records


def rebuild_index():
    """Atomically rewrite index.jsonl with all scanned voices."""
    records = scan_and_index_voices()
    from store import atomic_write
    lines = [json.dumps(r, ensure_ascii=False) for r in records]
    content = "\n".join(lines) + "\n"
    atomic_write(INDEX_PATH, content)
    return records


def resolve_voice_id(query_id: str) -> dict | None:
    """Resolve a voice by its exact ID or any alias."""
    norm = query_id.strip().lower()
    for sdir in VOICE_VAULT_DIR.iterdir():
        if not sdir.is_dir() or sdir.name.startswith("."):
            continue
        vfile = sdir / "voice.json"
        if not vfile.exists():
            continue
        try:
            with open(vfile, "r", encoding="utf-8") as f:
                data = json.load(f)
            vid = data.get("id", "").lower()
            aliases = [a.lower() for a in data.get("aliases", [])]
            if norm == vid or norm in aliases or norm == sdir.name.lower():
                return data
        except Exception:
            continue
    return None


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    recs = rebuild_index()
    print(f"Indexed {len(recs)} voices into {INDEX_PATH}")
    for r in recs:
        m = r["metadata"]
        print(f" - {r['id']:<15} [{m['status']:<10}] aliases: {m['aliases']}")
