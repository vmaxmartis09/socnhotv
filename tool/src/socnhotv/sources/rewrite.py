from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from socnhotv.workspace import project_path

logger = logging.getLogger(__name__)

RewriteStyle = Literal["faithful", "hook_boost", "character"]


def rewrite_script_lines(
    translated_lines: List[Dict[str, Any]],
    style: RewriteStyle = "faithful",
    character_name: str = "Sóc Nhỏ (Bi)",
) -> List[Dict[str, Any]]:
    """Rewrite translated Vietnamese lines into target brand voice style."""
    if not translated_lines:
        return []

    rewritten: List[Dict[str, Any]] = []

    for idx, line in enumerate(translated_lines):
        text = line.get("text", "")
        start = line.get("start", 0.0)
        end = line.get("end", 0.0)
        dur = max(end - start, 1.0)

        new_text = text

        if style == "faithful":
            new_text = text

        elif style == "hook_boost":
            if idx == 0:
                # Strong hook for the first 3s
                new_text = f"Dừng lại 3 giây! {text} bạn đã biết chưa?"
            elif idx == len(translated_lines) - 1:
                # Strong CTA for the final line
                new_text = f"{text}. Thả tim và theo dõi ngay nhé!"
            else:
                new_text = text

        elif style == "character":
            if idx == 0:
                new_text = f"Bi chào các bạn nhỏ nè! Hôm nay cùng Bi xem {text} nhé!"
            elif idx == len(translated_lines) - 1:
                new_text = f"{text}. Hẹn gặp lại các bạn ở tập sau nha!"
            else:
                new_text = text.replace("mình", "Bi").replace("tôi", "Bi")

        rewritten.append({
            "line_idx": idx + 1,
            "start": round(start, 2),
            "end": round(end, 2),
            "target_duration_s": round(dur, 2),
            "text": new_text,
            "original_vi": text,
        })

    return rewritten


def run_rewrite(
    project_id: str,
    source_id: str,
    style: RewriteStyle = "faithful",
) -> List[Dict[str, Any]]:
    """Rewrite transcript.vi.json into content/scripts/<source_id>.<style>.json."""
    source_dir = project_path(project_id, "raw", source_id)
    vi_json = source_dir / "transcript.vi.json"

    if not vi_json.exists():
        raise FileNotFoundError(f"Vietnamese transcript not found at: {vi_json}")

    with open(vi_json, "r", encoding="utf-8") as f:
        vi_lines = json.load(f)

    rewritten_lines = rewrite_script_lines(vi_lines, style=style)

    # Save to content/scripts/<source_id>.<style>.json
    content_script = project_path(
        project_id, "content", "scripts", f"{source_id}.{style}.json", ensure=True
    )
    with open(content_script, "w", encoding="utf-8") as f:
        json.dump(rewritten_lines, f, ensure_ascii=False, indent=2)

    # Save local copy in raw/<source_id>/
    local_script = source_dir / f"script.{style}.json"
    with open(local_script, "w", encoding="utf-8") as f:
        json.dump(rewritten_lines, f, ensure_ascii=False, indent=2)

    return rewritten_lines
