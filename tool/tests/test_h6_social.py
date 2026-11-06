import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from socnhotv.core.api.app import app
from socnhotv.social.adapters.manual import (
    ManualAdapter,
    create_manual_package,
    export_package_zip,
    get_manual_package_info,
    resolve_media_file,
)
from socnhotv.social.analytics.collectors.manual import ManualCollector
from socnhotv.social.analytics.insights import AnalyticsEngine
from socnhotv.social.models import (
    Post,
    PostMedia,
    PostMetricsSnapshot,
    PostTarget,
    SocialAccount,
)
from socnhotv.social.store import SocialStore


@pytest.fixture
def h6_sandbox(monkeypatch):
    """Isolated temporary sandbox directory for project files."""
    tmp = Path(tempfile.mkdtemp(prefix="socnhotv_h6_test_"))
    pid = "h6-test-proj"

    # Patch project_path in relevant modules
    def fake_project_path(p, *parts, ensure=False):
        d = tmp / p / Path(*parts)
        if ensure:
            d.parent.mkdir(parents=True, exist_ok=True)
            if not parts or parts[-1] in ("publishing", "analytics", "runs", "content", "packages", "posts", "inbox", "metrics", "insights"):
                d.mkdir(parents=True, exist_ok=True)
        return d

    monkeypatch.setattr("socnhotv.workspace.paths.project_path", fake_project_path)
    monkeypatch.setattr("socnhotv.social.store.project_path", fake_project_path)
    monkeypatch.setattr("socnhotv.social.adapters.manual.project_path", fake_project_path)
    monkeypatch.setattr("socnhotv.social.analytics.insights.project_path", fake_project_path)
    monkeypatch.setattr("socnhotv.social.queue.project_path", fake_project_path)

    yield pid, tmp
    shutil.rmtree(tmp, ignore_errors=True)


def test_h6_resolve_media_file(h6_sandbox):
    pid, tmp = h6_sandbox

    # 1. Non-existent returns None
    assert resolve_media_file(pid, None) is None
    assert resolve_media_file(pid, "nonexistent_file_xyz.mp4") is None

    # 2. File in project directory
    proj_dir = tmp / pid
    proj_dir.mkdir(parents=True, exist_ok=True)
    out_vid = proj_dir / "output" / "video.mp4"
    out_vid.parent.mkdir(parents=True, exist_ok=True)
    out_vid.write_bytes(b"TEST_VIDEO_BYTES")

    resolved = resolve_media_file(pid, "output/video.mp4")
    assert resolved is not None
    assert resolved.exists()
    assert resolved.read_bytes() == b"TEST_VIDEO_BYTES"

    # 3. Absolute path
    resolved_abs = resolve_media_file(pid, str(out_vid))
    assert resolved_abs is not None
    assert resolved_abs.exists()


def test_h6_manual_package_generation(h6_sandbox):
    pid, tmp = h6_sandbox
    store = SocialStore(pid)

    # Setup real test video
    proj_dir = tmp / pid
    vid_file = proj_dir / "output" / "tap01.mp4"
    vid_file.parent.mkdir(parents=True, exist_ok=True)
    vid_file.write_bytes(b"REAL_SIMULATED_VIDEO_DATA_FOR_EPISODE_1")

    thumb_file = proj_dir / "output" / "tap01_cover.jpg"
    thumb_file.write_bytes(b"FAKE_COVER_JPEG")

    # Add account
    acc = SocialAccount(
        id="acc_tiktok_main",
        platform="tiktok",
        handle="@socnhotv.official",
        display_name="Sóc Nhỏ TV TikTok",
    )
    store.save_account(acc)

    # Add post
    target = PostTarget(
        id="tgt_ep1_tt",
        account_id=acc.id,
        platform="tiktok",
        title="Tập 1: Núi Lửa Trong Bụng Bi",
        caption="Tập 1: Núi Lửa Trong Bụng Bi - Khi Bi ăn quá nhiều kẹo ngọt!",
        hashtags=["#SocNhoTV", "#HoatHinh3D", "#NuiLuaTrongBungBi"],
        product_link="https://shop.tiktok.com/p/kandy",
        disclosure_ad=True,
        scheduled_at="2026-11-15T20:00:00+07:00",
    )
    post = Post(
        id="post_tap01_main",
        project_id=pid,
        title="Tập 1: Núi Lửa Trong Bụng Bi",
        media=[PostMedia(path="output/tap01.mp4", thumb="output/tap01_cover.jpg", kind="video", duration_s=45.0)],
        targets=[target],
    )
    store.save_post(post)

    # Generate manual package
    pkg = create_manual_package(pid, post.id, "tiktok")
    assert pkg["post_id"] == post.id
    assert pkg["platform"] == "tiktok"
    assert pkg["has_real_video"] is True
    assert "Tập 1: Núi Lửa Trong Bụng Bi" in pkg["caption"]
    assert "#SocNhoTV" in pkg["hashtags"]

    pkg_dir = Path(pkg["package_dir"])
    assert (pkg_dir / "video.mp4").exists()
    assert (pkg_dir / "cover.jpg").exists()
    assert (pkg_dir / "caption.txt").exists()
    assert (pkg_dir / "hashtags.txt").exists()
    assert (pkg_dir / "checklist.md").exists()
    assert (pkg_dir / "meta.json").exists()

    # Verify checklist content has instructions
    checklist_txt = (pkg_dir / "checklist.md").read_text(encoding="utf-8")
    assert "Hướng dẫn đăng bài thủ công: TIKTOK" in checklist_txt
    assert "@socnhotv.official" in checklist_txt
    assert "Tôi đã đăng" in checklist_txt

    # Verify ZIP package
    zip_path = Path(pkg["zip_path"])
    assert zip_path.exists()
    assert zipfile.is_zipfile(zip_path)

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        assert "video.mp4" in names
        assert "caption.txt" in names
        assert "hashtags.txt" in names
        assert "checklist.md" in names
        assert "meta.json" in names

    # Test get_manual_package_info
    info = get_manual_package_info(pid, post.id, "tiktok")
    assert info is not None
    assert info["zip_path"] == str(zip_path)


def test_h6_mark_published_workflow(h6_sandbox):
    pid, tmp = h6_sandbox
    store = SocialStore(pid)

    target = PostTarget(
        id="tgt_publish_check",
        account_id="acc_yt",
        platform="youtube",
        title="Tập 1 YouTube",
        caption="Tập 1 trên YouTube",
        status="scheduled",
    )
    post = Post(
        id="post_publish_check",
        project_id=pid,
        title="Tập 1 YouTube",
        status="scheduled",
        targets=[target],
    )
    store.save_post(post)

    # User clicks "Tôi đã đăng" and provides URL
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    client = TestClient(app)
    resp = client.post(
        f"/projects/{pid}/social/posts/{post.id}/targets/{target.id}/mark-published",
        json={"url": video_url},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "published"
    assert data["url"] == video_url

    # Check store persistence
    saved_post = store.get_post(post.id)
    assert saved_post is not None
    assert saved_post.status == "published"
    assert saved_post.targets[0].status == "published"
    assert saved_post.targets[0].external_url == video_url
    assert saved_post.targets[0].published_at is not None

    # Check audit log
    audit = store.get_audit_log()
    assert any(a.get("action") == "manual_mark_published" and a.get("post_id") == post.id for a in audit)


def test_h6_manual_metrics_and_csv_import(h6_sandbox):
    pid, tmp = h6_sandbox
    store = SocialStore(pid)

    target = PostTarget(
        id="tgt_metrics_ep1",
        account_id="acc_tt",
        platform="tiktok",
        title="Tập 1: Núi Lửa Trong Bụng Bi",
        status="published",
    )
    post = Post(
        id="post_metrics_ep1",
        project_id=pid,
        title="Tập 1: Núi Lửa Trong Bụng Bi",
        status="published",
        targets=[target],
    )
    store.save_post(post)

    client = TestClient(app)

    # 1. Manual metrics entry
    resp = client.post(
        f"/projects/{pid}/social/analytics/manual-metrics",
        json={
            "post_id": post.id,
            "target_id": target.id,
            "platform": "tiktok",
            "views": 15400,
            "avg_retention_pct": 68.5,
            "likes": 1250,
            "comments": 140,
            "shares": 85,
            "watch_time_s": 42000,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "saved"

    # Verify latest metric snapshot
    latest = store.get_latest_metrics(target.id)
    assert latest is not None
    assert latest.views == 15400
    assert latest.avg_retention_pct == 68.5
    assert latest.likes == 1250

    # 2. CSV import
    csv_content = """Video title,Views,Average percentage viewed (%),Likes,Comments,Shares
Tập 1: Núi Lửa Trong Bụng Bi,18200,72.4,1600,210,95
"""
    csv_resp = client.post(
        f"/projects/{pid}/social/analytics/import-csv",
        json={"csv_text": csv_content, "platform": "tiktok"},
    )
    assert csv_resp.status_code == 200
    csv_data = csv_resp.json()
    assert csv_data["matched_count"] >= 1

    # Verify updated snapshot from CSV
    latest_after_csv = store.get_latest_metrics(target.id)
    assert latest_after_csv is not None
    assert latest_after_csv.views == 18200
    assert latest_after_csv.avg_retention_pct == 72.4


def test_h6_analytics_insights_and_next_episode_suggestions(h6_sandbox):
    pid, tmp = h6_sandbox
    store = SocialStore(pid)

    # Add a published post with high retention
    target = PostTarget(
        id="tgt_ep1_insights",
        account_id="acc_yt",
        platform="youtube",
        title="Tập 1: Núi Lửa Trong Bụng Bi",
        status="published",
        published_at="2026-11-05T19:30:00+07:00",
    )
    post = Post(
        id="post_ep1_insights",
        project_id=pid,
        title="Tập 1: Núi Lửa Trong Bụng Bi",
        status="published",
        targets=[target],
    )
    store.save_post(post)

    # Add snapshot
    store.append_metrics_snapshot(
        PostMetricsSnapshot(
            post_id=post.id,
            target_id=target.id,
            platform="youtube",
            checkpoint="manual",
            views=12000,
            avg_retention_pct=64.0,
            likes=950,
            comments=80,
            shares=40,
            watch_time_s=36000,
        )
    )

    client = TestClient(app)

    # Trigger insights generation
    gen_resp = client.post(f"/projects/{pid}/social/analytics/generate-insights")
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    assert gen_data["status"] == "ok"
    assert "Tỷ lệ giữ chân trung bình" in gen_data["learnings_md"]

    # Verify recommendations JSON contains next_episode_suggestions
    recs = gen_data["recommendations"]
    assert "next_episode_suggestions" in recs
    next_ep = recs["next_episode_suggestions"]
    assert "hook_recommendation" in next_ep
    assert "target_duration_s" in next_ep
    assert "recommended_shot_pacing_s" in next_ep
    assert "character_ratio" in next_ep
    assert "Sóc Bi 100cm / Koala 150cm" in next_ep["character_ratio"]

    # Verify files generated in analytics directory
    assert (tmp / pid / "analytics" / "learnings.md").exists()
    assert (tmp / pid / "analytics" / "recommendations.json").exists()


def test_h6_packages_api_endpoints(h6_sandbox):
    pid, tmp = h6_sandbox
    store = SocialStore(pid)

    target = PostTarget(
        id="tgt_api_pkg",
        account_id="acc_yt_pkg",
        platform="youtube",
        title="Tập 2: Mun Sợ Bóng Tối",
        caption="Tập 2 về nỗi sợ của Mun và lòng dũng cảm",
        hashtags=["#SocNhoTV", "#Tap2"],
        status="draft",
    )
    post = Post(
        id="post_api_pkg",
        project_id=pid,
        title="Tập 2: Mun Sợ Bóng Tối",
        targets=[target],
    )
    store.save_post(post)

    client = TestClient(app)

    # 1. GET package info (auto-generates if missing)
    info_resp = client.get(f"/projects/{pid}/social/packages/{post.id}/youtube")
    assert info_resp.status_code == 200
    data = info_resp.json()
    assert data["post_id"] == post.id
    assert data["platform"] == "youtube"
    assert "caption" in data
    assert "hashtags" in data

    # 2. POST package generate
    gen_resp = client.post(f"/projects/{pid}/social/packages/{post.id}/youtube/generate")
    assert gen_resp.status_code == 200
    assert gen_resp.json()["zip_filename"].endswith(".zip")

    # 3. GET package ZIP download
    zip_resp = client.get(f"/projects/{pid}/social/packages/{post.id}/youtube.zip")
    assert zip_resp.status_code == 200
    assert zip_resp.headers["content-type"] == "application/zip"
    assert len(zip_resp.content) > 0
