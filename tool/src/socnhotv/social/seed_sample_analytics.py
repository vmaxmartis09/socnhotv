from datetime import datetime, timedelta
from socnhotv.social.store import SocialStore
from socnhotv.social.models import Post, PostTarget, PostMetricsSnapshot, SocialNotification, DEFAULT_TZ
from socnhotv.social.analytics.insights import AnalyticsEngine

def main():
    pid = "soc-nho-tv"
    store = SocialStore(pid)
    now = datetime.now(DEFAULT_TZ)

    posts_data = [
        {
            "id": "post_viral_sales",
            "title": "Bán Hàng TikTok: Sóc Nhỏ và Hạt Dẻ Thần Kỳ (Hook 3s)",
            "render_job_id": "render_fa11cee3ad4c",
            "idea_id": "idea_123",
            "status": "published",
            "targets": [
                PostTarget(
                    id="tgt_viral_tt",
                    account_id="chan_tt_1",
                    platform="tiktok",
                    status="published",
                    scheduled_at=(now - timedelta(days=2, hours=1)).isoformat(),
                    published_at=(now - timedelta(days=2, hours=1)).isoformat(),
                    caption="Sóc Nhỏ ăn hạt dẻ phát sáng! Link giỏ hàng bên dưới nha các bạn #socnhotv #sales",
                ),
                PostTarget(
                    id="tgt_viral_yt",
                    account_id="chan_yt_1",
                    platform="youtube",
                    status="published",
                    scheduled_at=(now - timedelta(days=2, hours=1)).isoformat(),
                    published_at=(now - timedelta(days=2, hours=1)).isoformat(),
                    caption="Sóc Nhỏ ăn hạt dẻ phát sáng! #shorts #socnhotv",
                )
            ]
        },
        {
            "id": "post_koc_review",
            "title": "KOC Review: Bàn Chải Điện Trẻ Em Hình Sóc",
            "render_job_id": "render_32692140f071",
            "idea_id": "idea_script_975fe56043",
            "status": "published",
            "targets": [
                PostTarget(
                    id="tgt_koc_tt",
                    account_id="chan_tt_1",
                    platform="tiktok",
                    status="published",
                    scheduled_at=(now - timedelta(days=5, hours=2)).isoformat(),
                    published_at=(now - timedelta(days=5, hours=2)).isoformat(),
                    caption="Đánh răng vui vẻ cùng Sóc Bi #koc #review",
                )
            ]
        },
        {
            "id": "post_shorts_fact",
            "title": "Kiến Thức Thú Vị: Vì Sao Đuôi Sóc Lại Xù?",
            "render_job_id": "render_6d7c25dc69ca",
            "idea_id": "idea_script_b15db21a06",
            "status": "published",
            "targets": [
                PostTarget(
                    id="tgt_fact_yt",
                    account_id="chan_yt_1",
                    platform="youtube",
                    status="published",
                    scheduled_at=(now - timedelta(days=1, hours=3)).isoformat(),
                    published_at=(now - timedelta(days=1, hours=3)).isoformat(),
                    caption="Vì sao đuôi sóc lại xù? #shorts #kienthuc",
                )
            ]
        },
        {
            "id": "post_under_fact",
            "title": "Thử Thách: Sóc Nhỏ Đếm Số Bằng Tiếng Anh",
            "render_job_id": "render_7c56496e192e",
            "idea_id": "idea_script_c505e16679",
            "status": "published",
            "targets": [
                PostTarget(
                    id="tgt_under_tt",
                    account_id="chan_tt_1",
                    platform="tiktok",
                    status="published",
                    scheduled_at=(now - timedelta(days=4, hours=6)).isoformat(),
                    published_at=(now - timedelta(days=4, hours=6)).isoformat(),
                    caption="Tập đếm số cùng Sóc Nhỏ #tienganh",
                )
            ]
        }
    ]

    for pd in posts_data:
        post = Post(
            id=pd["id"],
            project_id=pid,
            title=pd["title"],
            render_job_id=pd["render_job_id"],
            idea_id=pd["idea_id"],
            status=pd["status"],
            targets=pd["targets"],
        )
        store.save_post(post)

    metrics_data = [
        ("tgt_viral_tt", "post_viral_sales", "tiktok", 28500, 2400, 310, 180, 120, 85000.0, 78.5, 450, 4.2, 120.0),
        ("tgt_viral_yt", "post_viral_sales", "youtube", 14200, 1100, 95, 60, 45, 42000.0, 71.0, 210, 3.8, 45.0),
        ("tgt_koc_tt", "post_koc_review", "tiktok", 12400, 950, 120, 70, 50, 36000.0, 64.0, 180, 2.9, 85.0),
        ("tgt_fact_yt", "post_shorts_fact", "youtube", 9800, 780, 65, 40, 30, 28000.0, 68.0, 140, 3.1, 0.0),
        ("tgt_under_tt", "post_under_fact", "tiktok", 1200, 85, 8, 4, 2, 3200.0, 32.0, 12, 1.1, 0.0),
    ]

    for tid, pid_post, plat, v, l, c, s, sv, wt, ret, sub, ctr, rev in metrics_data:
        snap = PostMetricsSnapshot(
            post_id=pid_post,
            target_id=tid,
            platform=plat,
            views=v,
            likes=l,
            comments=c,
            shares=s,
            saves=sv,
            watch_time_s=wt,
            avg_retention_pct=ret,
            subscribers_gained=sub,
            ctr=ctr,
            revenue=rev,
        )
        store.append_metrics_snapshot(snap)

    store.add_notification(
        SocialNotification(
            type="publish_success",
            title="Đăng bài thành công lên TikTok",
            message="Video 'Bán Hàng TikTok: Sóc Nhỏ và Hạt Dẻ Thần Kỳ' đã được xuất bản và đạt 28.5K views!",
            action_url="/social?tab=analytics",
        )
    )
    store.add_notification(
        SocialNotification(
            type="schedule_gap",
            title="Nhắc nhở: Lịch đăng bài cuối tuần",
            message="Thứ 7 tuần này chưa có bài đăng nào được lên lịch cho kênh YouTube.",
            action_url="/social?tab=calendar",
        )
    )

    engine = AnalyticsEngine(pid)
    engine.export_daily_insights()
    print("Populated realistic analytics data for soc-nho-tv successfully!")

if __name__ == "__main__":
    main()
