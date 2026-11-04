from __future__ import annotations

import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from socnhotv.social.models import (
    DEFAULT_TZ,
    GoldenSlotRecommendation,
    KPISummary,
    OutlierItem,
    PostingWindow,
    PostMetricsSnapshot,
    ensure_tz,
    now_iso,
)
from socnhotv.social.store import SocialStore
from socnhotv.workspace.paths import project_path


class AnalyticsEngine:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.store = SocialStore(project_id)

    def calculate_kpis(
        self,
        time_window: str = "all",
        platform: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> KPISummary:
        """
        Calculates aggregate KPIs over the specified time window ('7d', '30d', 'all').
        """
        posts = self.store.list_posts()
        metrics_map = self.store.list_all_latest_metrics()
        now = datetime.now(DEFAULT_TZ)

        cutoff = None
        if time_window == "7d":
            cutoff = now - timedelta(days=7)
        elif time_window == "30d":
            cutoff = now - timedelta(days=30)

        total_views = 0
        total_likes = 0
        total_comments = 0
        total_shares = 0
        total_saves = 0
        total_watch_time = 0.0
        total_subs = 0
        total_revenue = 0.0
        retentions: List[float] = []
        ctrs: List[float] = []
        post_count = 0

        for post in posts:
            for target in post.targets:
                if platform and target.platform != platform:
                    continue
                if account_id and target.account_id != account_id:
                    continue

                # Filter by publication date
                if cutoff and target.published_at:
                    try:
                        pub_dt = ensure_tz(datetime.fromisoformat(target.published_at))
                        if pub_dt < cutoff:
                            continue
                    except Exception:
                        pass

                snapshot = metrics_map.get(target.id)
                if not snapshot:
                    # If target is published but no metric snapshot yet, count as 0
                    if target.status == "published":
                        post_count += 1
                    continue

                post_count += 1
                total_views += snapshot.views
                total_likes += snapshot.likes
                total_comments += snapshot.comments
                total_shares += snapshot.shares
                total_saves += snapshot.saves
                total_watch_time += snapshot.watch_time_s
                total_subs += snapshot.subscribers_gained
                total_revenue += snapshot.revenue
                if snapshot.avg_retention_pct > 0:
                    retentions.append(snapshot.avg_retention_pct)
                if snapshot.ctr > 0:
                    ctrs.append(snapshot.ctr)

        er = (
            ((total_likes + total_comments + total_shares + total_saves) / max(total_views, 1)) * 100.0
            if total_views > 0
            else 0.0
        )
        avg_retention = statistics.mean(retentions) if retentions else 0.0
        avg_ctr = statistics.mean(ctrs) if ctrs else 0.0

        return KPISummary(
            total_views=total_views,
            total_watch_time_s=total_watch_time,
            avg_retention_pct=round(avg_retention, 2),
            engagement_rate=round(er, 2),
            total_likes=total_likes,
            total_comments=total_comments,
            total_shares=total_shares,
            total_saves=total_saves,
            follower_gain=total_subs,
            avg_ctr=round(avg_ctr, 2),
            affiliate_revenue=round(total_revenue, 2),
            post_count=post_count,
        )

    def calculate_golden_hours(self) -> Dict[str, Any]:
        """
        Builds a 7x24 heatmap (weekday 0..6, hour 0..23) based on median 24h views of published posts.
        Generates best recommended posting windows.
        """
        posts = self.store.list_posts()
        metrics_map = self.store.list_all_latest_metrics()

        # grid: [weekday][hour] -> list of views
        grid: List[List[List[int]]] = [[[] for _ in range(24)] for _ in range(7)]

        for post in posts:
            for target in post.targets:
                if target.status != "published":
                    continue
                dt_str = target.published_at or target.scheduled_at
                if not dt_str:
                    continue
                try:
                    dt = ensure_tz(datetime.fromisoformat(dt_str))
                    w = dt.weekday()  # 0=Monday..6=Sunday
                    h = dt.hour
                    snap = metrics_map.get(target.id)
                    views = snap.views if snap else 0
                    grid[w][h].append(views)
                except Exception:
                    continue

        matrix: List[List[Dict[str, Any]]] = []
        best_slots: List[Dict[str, Any]] = []

        # Default heuristic baseline for sparse slots (social media Vietnam prime times)
        def heuristic_score(w: int, h: int) -> float:
            score = 10.0
            if h in (11, 12):  # lunch break
                score += 35.0
            elif h in (19, 20, 21):  # evening prime time
                score += 55.0
            elif h in (8, 9):  # morning scroll
                score += 20.0
            if w in (5, 6):  # Weekend
                score += 15.0
            return score

        for w in range(7):
            row: List[Dict[str, Any]] = []
            for h in range(24):
                vals = grid[w][h]
                if vals:
                    med = float(statistics.median(vals))
                    count = len(vals)
                    score = med * 0.7 + count * 5.0 + heuristic_score(w, h) * 0.3
                else:
                    med = 0.0
                    count = 0
                    score = heuristic_score(w, h)

                slot_info = {
                    "weekday": w,
                    "hour": h,
                    "median_views": round(med, 1),
                    "sample_count": count,
                    "score": round(score, 1),
                }
                row.append(slot_info)
                best_slots.append(slot_info)
            matrix.append(row)

        # Sort best slots descending
        best_slots.sort(key=lambda s: s["score"], reverse=True)

        # Build recommended posting windows (pick top 4 distinct weekdays or peak times)
        recommended_windows: List[PostingWindow] = []
        seen_days = set()
        for slot in best_slots:
            w = slot["weekday"]
            h = slot["hour"]
            # e.g., slot 19 -> window 19:00 - 21:00
            start_str = f"{h:02d}:00"
            end_str = f"{min(h+2, 23):02d}:00"
            if w not in seen_days or len(recommended_windows) < 4:
                recommended_windows.append(PostingWindow(weekday=w, start=start_str, end=end_str))
                seen_days.add(w)
            if len(recommended_windows) >= 5:
                break

        return {
            "matrix": matrix,
            "top_slots": best_slots[:10],
            "recommended_windows": [rw.model_dump() for rw in recommended_windows],
        }

    def join_creative_performance(self) -> Dict[str, Any]:
        """
        Cross-references Social posts with:
        - Session A: Video templates (via `Post.render_job_id` -> `runs/render_queue/render_<id>.req.json`)
        - Session B: Content ideas & blueprints (via `Post.idea_id` -> `content/ideas/*.json` and `content/blueprints/`)
        """
        posts = self.store.list_posts()
        metrics_map = self.store.list_all_latest_metrics()

        # Cache render requests
        render_queue_dir = project_path(self.project_id, "runs", "render_queue", ensure=False)
        ideas_dir = project_path(self.project_id, "content", "ideas", ensure=False)
        blueprints_dir = project_path(self.project_id, "content", "blueprints", ensure=False)

        template_stats: Dict[str, Dict[str, Any]] = {}
        blueprint_stats: Dict[str, Dict[str, Any]] = {}

        for post in posts:
            # 1. Determine template_id
            template_id = "unknown"
            if post.render_job_id and render_queue_dir.exists():
                req_file = render_queue_dir / f"{post.render_job_id}.req.json"
                if req_file.exists():
                    try:
                        with open(req_file, "r", encoding="utf-8") as f:
                            req_data = json.load(f)
                            template_id = req_data.get("template_id", "unknown")
                    except Exception:
                        pass
                else:
                    job_file = render_queue_dir / f"{post.render_job_id}.json"
                    if job_file.exists():
                        try:
                            with open(job_file, "r", encoding="utf-8") as f:
                                j_data = json.load(f)
                                template_id = j_data.get("template_id", "unknown")
                        except Exception:
                            pass

            # 2. Determine blueprint & pillar
            blueprint_ref = "none"
            if post.idea_id and ideas_dir.exists():
                idea_file = ideas_dir / f"{post.idea_id}.json"
                if not idea_file.exists():
                    idea_file = ideas_dir / f"idea_{post.idea_id}.json"
                if idea_file.exists():
                    try:
                        with open(idea_file, "r", encoding="utf-8") as f:
                            idata = json.load(f)
                            blueprint_ref = idata.get("blueprint_ref") or "none"
                            if template_id == "unknown" and idata.get("template_id"):
                                template_id = idata.get("template_id")
                    except Exception:
                        pass

            # Calculate total metrics across targets
            post_views = 0
            post_interactions = 0
            for t in post.targets:
                snap = metrics_map.get(t.id)
                if snap:
                    post_views += snap.views
                    post_interactions += snap.likes + snap.comments + snap.shares + snap.saves

            # Aggregate template
            if template_id not in template_stats:
                template_stats[template_id] = {
                    "template_id": template_id,
                    "post_count": 0,
                    "total_views": 0,
                    "total_interactions": 0,
                }
            template_stats[template_id]["post_count"] += 1
            template_stats[template_id]["total_views"] += post_views
            template_stats[template_id]["total_interactions"] += post_interactions

            # Aggregate blueprint
            if blueprint_ref != "none":
                if blueprint_ref not in blueprint_stats:
                    blueprint_stats[blueprint_ref] = {
                        "blueprint_ref": blueprint_ref,
                        "post_count": 0,
                        "total_views": 0,
                        "total_interactions": 0,
                    }
                blueprint_stats[blueprint_ref]["post_count"] += 1
                blueprint_stats[blueprint_ref]["total_views"] += post_views
                blueprint_stats[blueprint_ref]["total_interactions"] += post_interactions

        # Compute averages & ER
        templates_list = []
        for t_id, data in template_stats.items():
            cnt = max(data["post_count"], 1)
            v = data["total_views"]
            er = round((data["total_interactions"] / max(v, 1)) * 100.0, 2)
            templates_list.append({
                "template_id": t_id,
                "post_count": data["post_count"],
                "total_views": v,
                "avg_views": round(v / cnt, 1),
                "avg_er": er,
            })
        templates_list.sort(key=lambda x: x["avg_views"], reverse=True)

        blueprints_list = []
        for bp_ref, data in blueprint_stats.items():
            cnt = max(data["post_count"], 1)
            v = data["total_views"]
            er = round((data["total_interactions"] / max(v, 1)) * 100.0, 2)
            blueprints_list.append({
                "blueprint_ref": bp_ref,
                "post_count": data["post_count"],
                "total_views": v,
                "avg_views": round(v / cnt, 1),
                "avg_er": er,
            })
        blueprints_list.sort(key=lambda x: x["avg_views"], reverse=True)

        return {
            "templates": templates_list,
            "blueprints": blueprints_list,
        }

    def detect_outliers(self, benchmark_days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detects top performing posts (views >= 2x median) and underperforming posts (views <= 0.5x median).
        Provides automated hypotheses for the performance difference.
        """
        posts = self.store.list_posts()
        metrics_map = self.store.list_all_latest_metrics()

        items: List[Dict[str, Any]] = []
        for post in posts:
            for target in post.targets:
                if target.status != "published":
                    continue
                snap = metrics_map.get(target.id)
                views = snap.views if snap else 0
                items.append({
                    "post_id": post.id,
                    "target_id": target.id,
                    "title": post.title,
                    "platform": target.platform,
                    "views": views,
                    "likes": snap.likes if snap else 0,
                    "shares": snap.shares if snap else 0,
                    "published_at": target.published_at or post.created_at,
                })

        if not items:
            return {"top_outliers": [], "underperforming": []}

        all_views = [it["views"] for it in items]
        median_views = max(float(statistics.median(all_views)), 1.0)

        top_outliers: List[Dict[str, Any]] = []
        underperforming: List[Dict[str, Any]] = []

        for it in items:
            ratio = round(it["views"] / median_views, 2)
            if ratio >= 2.0:
                hypo = "Hook 3s cuốn hút, chủ đề đánh trúng insight khán giả và phát hành đúng khung giờ vàng tương tác cao."
                top_outliers.append({
                    "post_id": it["post_id"],
                    "target_id": it["target_id"],
                    "title": it["title"],
                    "platform": it["platform"],
                    "views": it["views"],
                    "benchmark_views": median_views,
                    "ratio": ratio,
                    "kind": "top_outlier",
                    "hypothesis": hypo,
                })
            elif ratio <= 0.5 and it["views"] > 0:
                hypo = "Nội dung mở đầu thiếu nhịp giật gân, đăng lệch khung giờ hoặc hình ảnh cover chưa nổi bật."
                underperforming.append({
                    "post_id": it["post_id"],
                    "target_id": it["target_id"],
                    "title": it["title"],
                    "platform": it["platform"],
                    "views": it["views"],
                    "benchmark_views": median_views,
                    "ratio": ratio,
                    "kind": "underperforming",
                    "hypothesis": hypo,
                })

        top_outliers.sort(key=lambda x: x["views"], reverse=True)
        underperforming.sort(key=lambda x: x["views"])

        return {
            "top_outliers": top_outliers,
            "underperforming": underperforming,
        }

    def generate_learnings_md(self) -> str:
        """
        Synthesizes learnings into a clear markdown document saved to analytics/learnings.md.
        """
        kpis = self.calculate_kpis("30d")
        golden = self.calculate_golden_hours()
        creatives = self.join_creative_performance()
        outliers = self.detect_outliers()

        top_template = creatives["templates"][0]["template_id"] if creatives["templates"] else "tiktok-sales-v1"
        top_slots = golden["top_slots"][:3]
        slot_desc = ", ".join([f"Thứ {s['weekday']+2} lúc {s['hour']:02d}:00" for s in top_slots]) if top_slots else "19:00 - 21:00 các ngày trong tuần"

        now_str = datetime.now(DEFAULT_TZ).strftime("%Y-%m-%d")
        md = f"""# Báo cáo Phân tích & Đúc kết Tự học ({now_str})

## 1. Chỉ số Tổng quan (30 ngày gần nhất)
- **Tổng lượt xem:** {kpis.total_views:,} views
- **Tỷ lệ tương tác (ER):** {kpis.engagement_rate}%
- **Thời gian xem tích lũy:** {round(kpis.total_watch_time_s / 3600, 1)} giờ
- **Người theo dõi mới:** +{kpis.follower_gain:,}
- **Tổng số bài đã xuất bản:** {kpis.post_count} video

## 2. Khung Giờ Vàng Đề Xuất
- Các khung giờ đạt median views và điểm tương tác cao nhất: **{slot_desc}**.
- Đề xuất: Tập trung lên lịch các video bán hàng và KOC review vào các khung giờ này để đạt tỷ lệ phân phối thuật toán tối đa.

## 3. Hiệu Quả Mẫu Video & Kịch Bản
- **Template dẫn đầu:** `{top_template}` mang lại lượt xem trung bình và tỷ lệ chuyển đổi cao nhất.
- Khuyến nghị Session A: Tiếp tục tối ưu hóa biến thể hook cho `{top_template}`.
- Khuyến nghị Session B: Tăng cường các ý tưởng nội dung theo chủ đề giải đáp thắc mắc và so sánh trực diện.

## 4. Phân Tích Bài Đột Phá & Kém Hiệu Quả
- **Bài bùng nổ ({len(outliers['top_outliers'])} bài):**
"""
        for o in outliers["top_outliers"][:3]:
            md += f"  - **{o['title']}** ({o['views']:,} views, {o['ratio']}x trung bình): {o['hypothesis']}\n"
        if not outliers["top_outliers"]:
            md += "  - Chưa có bài đột phá vượt ngưỡng 2x trung bình.\n"

        md += "\n- **Bài cần cải thiện:**\n"
        for u in outliers["underperforming"][:3]:
            md += f"  - **{u['title']}** ({u['views']:,} views): {u['hypothesis']}\n"
        if not outliers["underperforming"]:
            md += "  - Không có bài viết nào dưới ngưỡng 0.5x trung bình.\n"

        md += """
## 5. Kế hoạch Hành động Tuần Tới
1. Áp dụng ngay bộ khung giờ vàng mới vào cấu hình đăng của các tài khoản chính.
2. Tự động chuyển đổi các kịch bản đạt rating cao sang trạng thái dựng video.
3. Duy trì nhịp đăng tối thiểu 1 video/ngày cho TikTok và YouTube Shorts.
"""
        self.store.save_learnings_md(md)
        return md

    def generate_recommendations_json(self) -> Dict[str, Any]:
        """
        Generates structured recommendations for Session A (templates) and Session B (blueprints/ideas).
        Stored in analytics/recommendations.json.
        """
        creatives = self.join_creative_performance()
        golden = self.calculate_golden_hours()

        top_templates = [t["template_id"] for t in creatives["templates"] if t["template_id"] != "unknown"]
        if not top_templates:
            top_templates = ["tiktok-sales-v1", "koc-review-v1", "shorts-fact-v1"]

        top_bps = [b["blueprint_ref"] for b in creatives["blueprints"] if b["blueprint_ref"] != "none"]

        recs = {
            "updated_at": now_iso(),
            "priority_templates_for_session_a": top_templates[:5],
            "priority_blueprints_for_session_b": top_bps[:5],
            "best_posting_slots": golden["top_slots"][:5],
            "recommended_posting_windows": golden["recommended_windows"],
        }
        self.store.save_recommendations_json(recs)
        return recs

    def export_daily_insights(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Exports full daily insights snapshot to analytics/insights/<date>.json.
        """
        d_str = date_str or datetime.now(DEFAULT_TZ).strftime("%Y-%m-%d")
        kpis = self.calculate_kpis("30d")
        golden = self.calculate_golden_hours()
        creatives = self.join_creative_performance()
        outliers = self.detect_outliers()

        # Compute views by day for the last 14 days
        posts = self.store.list_posts()
        metrics_map = self.store.list_all_latest_metrics()
        views_by_day: Dict[str, Dict[str, int]] = {}

        now = datetime.now(DEFAULT_TZ)
        for i in range(14):
            day_key = (now - timedelta(days=13 - i)).strftime("%Y-%m-%d")
            views_by_day[day_key] = {"tiktok": 0, "youtube": 0, "facebook": 0, "instagram": 0, "total": 0}

        for post in posts:
            for target in post.targets:
                if target.status != "published":
                    continue
                pub_d = (target.published_at or post.created_at)[:10]
                if pub_d in views_by_day:
                    snap = metrics_map.get(target.id)
                    v = snap.views if snap else 0
                    p = target.platform if target.platform in views_by_day[pub_d] else "tiktok"
                    views_by_day[pub_d][p] += v
                    views_by_day[pub_d]["total"] += v

        data = {
            "date": d_str,
            "generated_at": now_iso(),
            "kpis": kpis.model_dump(),
            "views_by_day": views_by_day,
            "golden_hours": golden,
            "creatives": creatives,
            "outliers": outliers,
        }
        self.store.save_insights(d_str, data)
        self.generate_learnings_md()
        self.generate_recommendations_json()
        return data
