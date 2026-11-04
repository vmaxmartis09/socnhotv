from __future__ import annotations

import statistics
from typing import Any, Dict, List, Optional
from socnhotv.intelligence.contracts import VideoBlueprint, list_video_blueprints

HOOK_PATTERNS = [
    "{pain_point}? Đây là cách {product} giải quyết chỉ trong 1 phút!",
    "Đừng mua {category} nếu bạn chưa biết bí quyết này!",
    "Top 1 món đồ không thể thiếu nếu bạn đang gặp vấn đề {pain_point}",
    "Tại sao mọi người lại săn lùng {product} nhiều đến vậy?",
]

CTA_PATTERNS = [
    "Bấm ngay vào giỏ hàng góc trái bên dưới để nhận ưu đãi hôm nay!",
    "Link chính hãng mình để sẵn ở bio, các bạn tham khảo nhé!",
    "Thả tim và theo dõi để xem thêm nhiều mẹo hữu ích nữa nha!",
]


def aggregate_patterns(
    project_id: str,
    niche: Optional[str] = None,
) -> Dict[str, Any]:
    """Aggregate statistics and structural patterns across all video blueprints."""
    blueprints = list_video_blueprints(project_id)

    if not blueprints:
        return {
            "total_analyzed": 0,
            "avg_pacing_cuts_per_10s": 2.5,
            "median_hook_duration_s": 3.0,
            "common_role_sequences": [["hook", "problem", "demo", "offer", "cta"]],
            "hook_templates": HOOK_PATTERNS,
            "cta_templates": CTA_PATTERNS,
        }

    hook_durs: List[float] = []
    pacing_list: List[float] = []
    role_seqs: List[List[str]] = []

    for bp in blueprints:
        if bp.beats:
            hook_beat = bp.beats[0]
            hook_durs.append(hook_beat.t_end - hook_beat.t_start)
            role_seqs.append([b.role for b in bp.beats])
        pacing_list.append(bp.pacing_cuts_per_10s)

    median_hook = statistics.median(hook_durs) if hook_durs else 3.0
    avg_pacing = statistics.mean(pacing_list) if pacing_list else 2.5

    return {
        "total_analyzed": len(blueprints),
        "avg_pacing_cuts_per_10s": round(avg_pacing, 2),
        "median_hook_duration_s": round(median_hook, 2),
        "common_role_sequences": role_seqs[:5],
        "hook_templates": HOOK_PATTERNS,
        "cta_templates": CTA_PATTERNS,
    }
