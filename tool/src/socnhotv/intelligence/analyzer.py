from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from rapidfuzz import fuzz

from socnhotv.intelligence.contracts import Beat, VideoBlueprint, save_video_blueprint
from socnhotv.sources.service import get_source
from socnhotv.workspace import project_path

logger = logging.getLogger(__name__)

# Standard role order templates for matching
TEMPLATE_PATTERNS = {
    "koc-review-v1": ["hook", "problem", "reveal", "demo", "proof", "cta"],
    "tiktok-sales-v1": ["hook", "agitate", "reveal", "demo", "offer", "urgency", "cta"],
    "affiliate-compare-v1": ["hook", "compare", "demo", "proof", "offer", "cta"],
}


def infer_beat_role(
    idx: int,
    total_beats: int,
    start_s: float,
    duration_s: float,
    text: str,
) -> str:
    """Infer marketing beat role based on timeline position and linguistic cues."""
    t_low = text.lower()

    # First 3-4s is almost always a hook
    if start_s <= 3.5 or idx == 0:
        return "hook"

    # Final 10-15% of the video or CTA keywords
    if idx == total_beats - 1 or "theo dõi" in t_low or "mua ngay" in t_low or "giỏ hàng" in t_low or "link" in t_low:
        return "cta"

    # Keywords detection
    if any(k in t_low for k in ["so sánh", "khác biệt", "hơn hẳn", "thay vì"]):
        return "compare"
    if any(k in t_low for k in ["vấn đề", "mệt mỏi", "khó chịu", "phiền phức", "đau đầu"]):
        return "problem"
    if any(k in t_low for k in ["thì ra", "hóa ra", "đây là", "giải pháp"]):
        return "reveal"
    if any(k in t_low for k in ["thử", "cách dùng", "dùng thử", "hướng dẫn", "xem này"]):
        return "demo"
    if any(k in t_low for k in ["hiệu quả", "đã kiểm chứng", "chứng nhận", "đánh giá", "sao"]):
        return "proof"
    if any(k in t_low for k in ["giá", "ưu đãi", "giảm", "sale", "khuyến mãi", "chỉ"]):
        return "offer"
    if any(k in t_low for k in ["nhanh tay", "hôm nay", "kẻo lỡ", "gấp"]):
        return "urgency"

    # Positional heuristics
    rel_pos = start_s / max(duration_s, 1.0)
    if rel_pos < 0.25:
        return "problem"
    elif rel_pos < 0.45:
        return "reveal"
    elif rel_pos < 0.70:
        return "demo"
    elif rel_pos < 0.85:
        return "offer"
    return "cta"


def analyze_video(project_id: str, source_id: str) -> VideoBlueprint:
    """Analyze video structure and scenes into a structured VideoBlueprint."""
    source_dir = project_path(project_id, "raw", source_id)
    source = get_source(project_id, source_id)
    if not source:
        raise FileNotFoundError(f"Source not found: {source_id}")

    # Load scenes if available
    scenes_file = source_dir / "scenes.json"
    scenes_data: List[Dict[str, Any]] = []
    if scenes_file.exists():
        try:
            with open(scenes_file, "r", encoding="utf-8") as f:
                scenes_data = json.load(f)
        except Exception:
            pass

    # Load transcript if available
    transcript_file = source_dir / "transcript.vi.json"
    if not transcript_file.exists():
        transcript_file = source_dir / "transcript.orig.json"

    transcript_data: List[Dict[str, Any]] = []
    if transcript_file.exists():
        try:
            with open(transcript_file, "r", encoding="utf-8") as f:
                transcript_data = json.load(f)
        except Exception:
            pass

    duration_s = max(source.duration_s, 5.0)

    # Build beats: combine scenes with spoken text
    beats: List[Beat] = []
    total_beats = max(len(scenes_data), len(transcript_data), 3)

    if scenes_data:
        for idx, sc in enumerate(scenes_data):
            st = float(sc.get("start_s", 0.0))
            en = float(sc.get("end_s", st + 3.0))
            # Find matching transcript text
            matched_text = ""
            for t_item in transcript_data:
                t_st = float(t_item.get("start", 0.0))
                t_en = float(t_item.get("end", 0.0))
                if (t_st <= en and t_en >= st):
                    matched_text += " " + t_item.get("text", "")

            role = infer_beat_role(idx, len(scenes_data), st, duration_s, matched_text)
            beats.append(
                Beat(
                    t_start=st,
                    t_end=en,
                    role=role,
                    summary=matched_text.strip() or f"Cảnh {idx + 1}",
                    visual=f"Cảnh hành động {idx + 1}",
                    on_screen_text=matched_text.strip()[:30] if matched_text else "",
                )
            )
    else:
        # Fallback to 4 segments
        seg_dur = duration_s / 4.0
        roles = ["hook", "problem", "demo", "cta"]
        for idx, r in enumerate(roles):
            st = idx * seg_dur
            en = (idx + 1) * seg_dur
            beats.append(
                Beat(
                    t_start=round(st, 2),
                    t_end=round(en, 2),
                    role=r,
                    summary=f"Phần {r} của video",
                )
            )

    # Calculate pacing: cuts per 10s
    total_cuts = max(len(beats) - 1, 1)
    pacing = round((total_cuts / duration_s) * 10.0, 2)

    # Suggest template via fuzzy sequence similarity
    role_sequence = " ".join([b.role for b in beats])
    best_template = "koc-review-v1"
    highest_score = 0.0

    for tmpl_id, tmpl_roles in TEMPLATE_PATTERNS.items():
        pattern_str = " ".join(tmpl_roles)
        score = fuzz.ratio(role_sequence, pattern_str)
        if score > highest_score:
            highest_score = score
            best_template = tmpl_id

    hook_text = beats[0].summary if beats else "Xem video này ngay!"
    cta_text = beats[-1].summary if len(beats) > 1 else "Bấm theo dõi nhé!"

    blueprint = VideoBlueprint(
        id=f"bp_{source_id}",
        source_ref=source_id,
        duration_s=duration_s,
        platform=source.platform,
        hook=hook_text,
        beats=beats,
        cta=cta_text,
        pacing_cuts_per_10s=pacing,
        suggested_template_id=best_template,
    )

    save_video_blueprint(project_id, blueprint)
    return blueprint
