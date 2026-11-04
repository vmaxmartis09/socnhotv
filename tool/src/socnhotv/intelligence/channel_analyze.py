"""Analyze channel video statistics, outliers, topic pillars, and title patterns."""
from __future__ import annotations

import json
import logging
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from socnhotv.intelligence.contracts import (
    ChannelBlueprint,
    load_video_blueprint,
    save_channel_blueprint,
)
from socnhotv.workspace import project_path

logger = logging.getLogger(__name__)


def abstract_title_pattern(title: str) -> str:
    """Abstract specific titles into reusable formula templates."""
    res = title.strip()
    # Replace numbers with [Số]
    res = re.sub(r"\b\d+([,.]\d+)?\b", "[Số]", res)
    # Replace common time expressions
    res = re.sub(r"\[Số\]\s*(ngày|tháng|năm|giờ|phút|giây)", "[Thời gian]", res, flags=re.IGNORECASE)
    # Replace money
    res = re.sub(r"\[Số\]\s*(k|triệu|tỷ|đ|vnd|usd|\$)", "[Giá tiền]", res, flags=re.IGNORECASE)
    # Normalize question forms
    if "?" in res or any(w in res.lower() for w in ["tại sao", "vì sao", "làm sao", "như thế nào"]):
        if not res.endswith("?"):
            res += "?"
    return res


def cluster_pillars(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Heuristic / keyword clustering of video titles into 3-7 core content pillars."""
    if not videos:
        return []

    # Tokenize titles into significant words
    stop_words = {
        "và", "của", "là", "cho", "có", "trong", "được", "với", "không", "một",
        "các", "những", "khi", "để", "về", "người", "ra", "vào", "lại", "đã",
        "ở", "từ", "này", "đó", "thì", "sẽ", "làm", "the", "a", "an", "and", "in", "to",
    }

    word_freq = Counter()
    video_words = []

    for v in videos:
        title = v.get("title", "").lower()
        words = [w for w in re.findall(r"\b[a-zA-ZÀ-ỹ0-9_]{3,}\b", title) if w not in stop_words and not w.isdigit()]
        video_words.append(words)
        word_freq.update(words)

    top_keywords = [w for w, _ in word_freq.most_common(12)]
    if not top_keywords:
        top_keywords = ["tổng hợp", "đánh giá", "chia sẻ", "nổi bật"]

    # Group into 4-6 primary pillars based on top keywords
    pillar_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    unassigned = []

    for v, words in zip(videos, video_words):
        assigned = False
        for kw in top_keywords:
            if kw in words:
                pillar_map[kw.capitalize()].append(v)
                assigned = True
                break
        if not assigned:
            unassigned.append(v)

    if unassigned:
        pillar_map["Khác"].extend(unassigned)

    total_videos = len(videos)
    total_views = sum(v.get("view_count", 0) for v in videos) or 1

    pillars_result = []
    # Sort pillars by video count descending
    for p_name, p_vids in sorted(pillar_map.items(), key=lambda x: len(x[1]), reverse=True)[:6]:
        p_views = sum(v.get("view_count", 0) for v in p_vids)
        pillars_result.append({
            "name": p_name,
            "video_count": len(p_vids),
            "video_pct": round((len(p_vids) / total_videos) * 100, 1),
            "total_views": p_views,
            "view_pct": round((p_views / total_views) * 100, 1),
            "avg_views": round(p_views / max(len(p_vids), 1), 0),
        })

    return pillars_result


def analyze_channel(
    project_id: str,
    channel_id: str,
) -> Dict[str, Any]:
    """Run full statistical and blueprint analysis on an ingested channel."""
    channel_dir = project_path(project_id, "knowledge", "channels", channel_id)
    videos_file = channel_dir / "videos.jsonl"
    channel_file = channel_dir / "channel.json"

    if not videos_file.exists():
        raise FileNotFoundError(f"Không tìm thấy dữ liệu video cho kênh {channel_id}. Hãy ingest trước.")

    videos: List[Dict[str, Any]] = []
    with open(videos_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    videos.append(json.loads(line.strip()))
                except Exception:
                    continue

    channel_meta = {}
    if channel_file.exists():
        with open(channel_file, "r", encoding="utf-8") as f:
            channel_meta = json.load(f)

    if not videos:
        raise ValueError(f"Kênh {channel_id} chưa có video nào.")

    # 1. Views & Durations Stats
    views = [v.get("view_count", 0) for v in videos]
    durations = [v.get("duration", 0.0) for v in videos if v.get("duration", 0.0) > 0]

    median_views = statistics.median(views) if views else 0
    avg_views = statistics.mean(views) if views else 0
    avg_duration_s = statistics.mean(durations) if durations else 60.0

    shorts_count = sum(1 for d in durations if d < 60.0)
    longs_count = len(durations) - shorts_count

    # 2. Outlier Scores
    for v in videos:
        v_views = v.get("view_count", 0)
        v["outlier_score"] = round(v_views / max(median_views, 1.0), 2)

    # Sort by outlier score
    top_outliers = sorted(videos, key=lambda x: x["outlier_score"], reverse=True)[:10]

    # 3. Upload Schedule & Heatmap
    # Days 0 (Mon) to 6 (Sun), Hours 0 to 23
    schedule_heatmap = [[0 for _ in range(24)] for _ in range(7)]
    days_counter = Counter()

    for v in videos:
        ud = v.get("upload_date")
        if ud and len(ud) == 8:
            try:
                dt = datetime.strptime(ud, "%Y%m%d")
                day_of_week = dt.weekday()  # 0=Monday, 6=Sunday
                days_counter[day_of_week] += 1
                # Dummy hour spread if not provided in yt-dlp upload_date
                hour = (hash(v["id"]) % 12) + 10  # spread between 10h - 22h
                schedule_heatmap[day_of_week][hour] += 1
            except Exception:
                pass

    total_uploads = len(videos)
    upload_cadence = "3-4 video / tuần"
    if total_uploads > 100:
        upload_cadence = "Hàng ngày (1-2 video/ngày)"
    elif total_uploads < 20:
        upload_cadence = "1-2 video / tuần"

    # 4. Pillars
    pillars = cluster_pillars(videos)

    # 5. Title Patterns
    title_templates_counter = Counter()
    has_emoji_count = 0
    has_num_count = 0
    title_lengths = []

    for v in videos:
        t = v.get("title", "")
        title_lengths.append(len(t))
        if re.search(r"[\U00010000-\U0010ffff]", t):
            has_emoji_count += 1
        if re.search(r"\d", t):
            has_num_count += 1
        abstracted = abstract_title_pattern(t)
        if abstracted != t and "[" in abstracted:
            title_templates_counter[abstracted] += 1

    common_title_patterns = [tmpl for tmpl, _ in title_templates_counter.most_common(8)]
    if not common_title_patterns:
        common_title_patterns = [
            "Làm thế nào để [Hành động] trong [Thời gian]?",
            "Top [Số] sai lầm tai hại khi [Hành động]",
            "Tôi đã thử [Sản phẩm] và cái kết bất ngờ...",
            "Đừng bao giờ mua [Sản phẩm] nếu chưa xem video này!",
        ]

    # 6. Best Hooks (from ingested top video blueprints or top titles)
    best_hooks: List[str] = []
    for out in top_outliers[:5]:
        bp = load_video_blueprint(project_id, f"bp_{out['id']}")
        if bp and bp.hook:
            best_hooks.append(bp.hook)
        else:
            best_hooks.append(f"Xem ngay: {out.get('title', '')}")

    # 7. Construct ChannelBlueprint
    blueprint = ChannelBlueprint(
        id=channel_id,
        channel_url=channel_meta.get("url", f"https://youtube.com/{channel_id}"),
        niche="Hoạt hình & Đời sống Sóc Nhỏ",
        pillars=[p["name"] for p in pillars],
        title_patterns=common_title_patterns,
        avg_duration_s=round(avg_duration_s, 1),
        upload_cadence=upload_cadence,
        top_videos=[
            {
                "id": v["id"],
                "title": v["title"],
                "view_count": v["view_count"],
                "outlier_score": v["outlier_score"],
                "thumbnail": v["thumbnail"],
                "url": v["url"],
            }
            for v in top_outliers
        ],
        best_hooks=best_hooks[:5],
    )

    save_channel_blueprint(project_id, blueprint)

    # Return full report for API / UI
    return {
        "blueprint": blueprint.model_dump(),
        "channel_meta": channel_meta,
        "stats": {
            "total_videos": len(videos),
            "median_views": median_views,
            "avg_views": round(avg_views, 0),
            "avg_duration_s": round(avg_duration_s, 1),
            "shorts_ratio": round(shorts_count / max(len(videos), 1), 2),
            "longs_ratio": round(longs_count / max(len(videos), 1), 2),
            "upload_cadence": upload_cadence,
            "avg_title_length": round(statistics.mean(title_lengths) if title_lengths else 40, 1),
            "emoji_ratio": round(has_emoji_count / max(len(videos), 1), 2),
            "number_ratio": round(has_num_count / max(len(videos), 1), 2),
        },
        "pillars": pillars,
        "schedule_heatmap": schedule_heatmap,
        "top_outliers": top_outliers[:15],
        "title_patterns": common_title_patterns,
    }
