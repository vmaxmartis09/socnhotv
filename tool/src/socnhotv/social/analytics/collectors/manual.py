from __future__ import annotations

import csv
import io
import re
from typing import Any, Dict, List, Optional

from socnhotv.social.analytics.collectors.base import BaseCollector
from socnhotv.social.models import PostMetricsSnapshot, PostTarget, SocialAccount, now_iso


def _clean_num(val: Any) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(",", "").replace("%", "").replace(" ", "")
    if not s or s == "-":
        return 0.0
    # Handle 'K', 'M' suffixes
    factor = 1.0
    if s.endswith("k") or s.endswith("K"):
        factor = 1000.0
        s = s[:-1]
    elif s.endswith("m") or s.endswith("M"):
        factor = 1000000.0
        s = s[:-1]
    try:
        return float(s) * factor
    except Exception:
        return 0.0


class ManualCollector(BaseCollector):
    async def collect(
        self,
        account: SocialAccount,
        target: PostTarget,
        checkpoint: str = "manual",
    ) -> PostMetricsSnapshot:
        """Manual collector returns current target info or blank snapshot."""
        return PostMetricsSnapshot(
            post_id="",
            target_id=target.id,
            platform=target.platform,
            checkpoint=checkpoint,
            timestamp=now_iso(),
        )

    @staticmethod
    def parse_csv(csv_text: str, default_platform: str = "youtube") -> List[Dict[str, Any]]:
        """
        Parses CSV export from YouTube Studio, TikTok Studio, or generic social media export.
        Returns a list of standardized record dicts with keys:
        {title, views, likes, comments, shares, saves, watch_time_s, avg_retention_pct, subscribers_gained, ctr, revenue}
        """
        records: List[Dict[str, Any]] = []
        if not csv_text.strip():
            return records

        f = io.StringIO(csv_text.strip())
        reader = csv.reader(f)
        header_row = None
        for row in reader:
            if not row or not any(row):
                continue
            # Look for header line containing 'title' or 'views' or 'tiêu đề' or 'lượt xem'
            row_lower = [c.strip().lower() for c in row]
            if any("title" in c or "tiêu đề" in c or "video" in c for c in row_lower) and any(
                "view" in c or "xem" in c for c in row_lower
            ):
                header_row = row_lower
                break
            elif not header_row and len(row) >= 3:
                # Default first non-empty row as header if no explicit match
                header_row = row_lower
                break

        if not header_row:
            return records

        # Helper to find column index by multiple regex or substrings
        def find_col(patterns: List[str]) -> Optional[int]:
            for idx, col in enumerate(header_row):
                for p in patterns:
                    if p in col:
                        return idx
            return None

        title_idx = find_col(["video title", "tiêu đề", "title", "tên video"])
        views_idx = find_col(["view", "lượt xem", "views", "total views"])
        likes_idx = find_col(["like", "thích", "likes"])
        comments_idx = find_col(["comment", "bình luận", "comments"])
        shares_idx = find_col(["share", "chia sẻ", "shares"])
        saves_idx = find_col(["save", "lưu", "saves", "bookmark"])
        watch_time_idx = find_col(["watch time", "thời gian xem", "giờ xem", "watch_time"])
        retention_idx = find_col(["retention", "percentage", "giữ chân", "avg view duration %"])
        subs_idx = find_col(["subscriber", "người đăng ký", "follow", "subs"])
        ctr_idx = find_col(["click-through", "ctr", "tỷ lệ nhấp", "tỷ lệ click"])
        revenue_idx = find_col(["revenue", "doanh thu", "estimated revenue", "tiền"])

        for row in reader:
            if not row or len(row) <= (views_idx or 0):
                continue
            
            title = row[title_idx].strip() if title_idx is not None and title_idx < len(row) else ""
            if not title and title_idx is not None:
                continue

            views = int(_clean_num(row[views_idx])) if views_idx is not None and views_idx < len(row) else 0
            likes = int(_clean_num(row[likes_idx])) if likes_idx is not None and likes_idx < len(row) else 0
            comments = int(_clean_num(row[comments_idx])) if comments_idx is not None and comments_idx < len(row) else 0
            shares = int(_clean_num(row[shares_idx])) if shares_idx is not None and shares_idx < len(row) else 0
            saves = int(_clean_num(row[saves_idx])) if saves_idx is not None and saves_idx < len(row) else 0
            
            raw_wt = _clean_num(row[watch_time_idx]) if watch_time_idx is not None and watch_time_idx < len(row) else 0.0
            # If watch time header has 'hour' or 'giờ', convert to seconds
            watch_time_s = raw_wt * 3600.0 if watch_time_idx and ("hour" in header_row[watch_time_idx] or "giờ" in header_row[watch_time_idx]) else raw_wt

            avg_ret = _clean_num(row[retention_idx]) if retention_idx is not None and retention_idx < len(row) else 0.0
            subs = int(_clean_num(row[subs_idx])) if subs_idx is not None and subs_idx < len(row) else 0
            ctr = _clean_num(row[ctr_idx]) if ctr_idx is not None and ctr_idx < len(row) else 0.0
            revenue = _clean_num(row[revenue_idx]) if revenue_idx is not None and revenue_idx < len(row) else 0.0

            records.append({
                "title": title,
                "views": views,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "saves": saves,
                "watch_time_s": watch_time_s,
                "avg_retention_pct": avg_ret,
                "subscribers_gained": subs,
                "ctr": ctr,
                "revenue": revenue,
            })

        return records
