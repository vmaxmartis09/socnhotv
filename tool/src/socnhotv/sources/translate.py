from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from socnhotv.workspace import project_path, shared_path

logger = logging.getLogger(__name__)

# Basic offline fallback glossary for common Chinese social media phrases
DEFAULT_ZH_VI_MAP = {
    "你好": "Xin chào",
    "家人们": "Cả nhà ơi",
    "老铁们": "Các bạn ơi",
    "今天给大家分享": "Hôm nay mình chia sẻ",
    "点赞": "thả tim",
    "关注": "bấm theo dõi",
    "真的太好用了": "thật sự quá tiện lợi",
    "赶紧试试吧": "thử ngay nhé",
    "看这个": "Xem cái này nè",
    "非常棒": "rất tuyệt vời",
}


def load_project_glossary(project_id: str) -> Dict[str, str]:
    """Load project or shared glossary if available."""
    glossary: Dict[str, str] = dict(DEFAULT_ZH_VI_MAP)
    
    # 1. Shared glossary
    shared_g = shared_path("knowledge", "glossary.json")
    if shared_g.exists():
        try:
            with open(shared_g, "r", encoding="utf-8") as f:
                glossary.update(json.load(f))
        except Exception:
            pass

    # 2. Project glossary
    proj_g = project_path(project_id, "knowledge", "glossary.json")
    if proj_g.exists():
        try:
            with open(proj_g, "r", encoding="utf-8") as f:
                glossary.update(json.load(f))
        except Exception:
            pass

    return glossary


def condense_text(text: str, max_chars: int) -> str:
    """Shorten Vietnamese text to fit the maximum speaking duration."""
    if len(text) <= max_chars or max_chars < 15:
        return text

    # Truncate at natural punctuation or word boundary
    words = text.split()
    condensed = ""
    for w in words:
        if len(condensed) + len(w) + 1 <= max_chars:
            condensed += (" " if condensed else "") + w
        else:
            break
    return condensed if condensed else text[:max_chars]


def translate_segments(
    project_id: str,
    segments: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Translate list of segments into Vietnamese with length checking."""
    glossary = load_project_glossary(project_id)
    translated_list: List[Dict[str, Any]] = []

    for seg in segments:
        orig = seg.get("text", "")
        start_s = float(seg.get("start", 0.0))
        end_s = float(seg.get("end", 0.0))
        dur = max(end_s - start_s, 1.0)
        max_chars = int(dur * 15 * 1.25)  # 15 chars/s * 1.25 ceiling

        vi_text = orig

        # Apply glossary replacement
        for zh_term, vi_term in glossary.items():
            if zh_term in vi_text:
                vi_text = vi_text.replace(zh_term, vi_term)

        # Enforce max length constraint
        if len(vi_text) > max_chars:
            vi_text = condense_text(vi_text, max_chars)

        translated_list.append({
            "start": round(start_s, 2),
            "end": round(end_s, 2),
            "text": vi_text,
            "orig_text": orig,
            "char_count": len(vi_text),
            "max_allowed_chars": max_chars,
        })

    return translated_list


def run_translation(project_id: str, source_id: str) -> List[Dict[str, Any]]:
    """Translate raw/<source_id>/transcript.orig.json -> transcript.vi.json."""
    source_dir = project_path(project_id, "raw", source_id)
    orig_json = source_dir / "transcript.orig.json"
    out_json = source_dir / "transcript.vi.json"

    if not orig_json.exists():
        raise FileNotFoundError(f"Original transcript not found at: {orig_json}")

    with open(orig_json, "r", encoding="utf-8") as f:
        orig_segments = json.load(f)

    vi_segments = translate_segments(project_id, orig_segments)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(vi_segments, f, ensure_ascii=False, indent=2)

    return vi_segments
