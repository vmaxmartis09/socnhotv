import json
import pytest
from pathlib import Path
from socnhotv.core.storage.project_store import get_repo_root
from socnhotv.social.video_library import VideoLibrary


def test_social_videos_lists_output_package():
    project_id = "soc-nho-tv"
    repo_root = get_repo_root()
    test_slug = "_test_social_pkg"
    test_slug_dir = repo_root / "data" / "projects" / project_id / "output" / test_slug
    test_slug_dir.mkdir(parents=True, exist_ok=True)

    # Tạo file video giả và thumb giả
    fake_mp4 = test_slug_dir / "final_45s.mp4"
    fake_mp4.write_bytes(b"dummy video content")
    fake_thumb = test_slug_dir / "thumb.jpg"
    fake_thumb.write_bytes(b"dummy thumb content")

    manifest_data = {
        "id": f"studio_{test_slug}",
        "title": "Thử nghiệm Video Cầu Vồng 45 Giây",
        "topic": "Cầu Vồng",
        "slug": test_slug,
        "created_at": "2026-11-04T12:00:00Z",
        "duration_s": 45.0,
        "size_mb": 1.0,
        "platforms": ["tiktok", "youtube"],
        "files": {
            "video": f"output/{test_slug}/final_45s.mp4",
            "thumb": f"output/{test_slug}/thumb.jpg",
        },
        "verify": {"pass": True, "scores": {}},
    }
    (test_slug_dir / "video.json").write_text(json.dumps(manifest_data, ensure_ascii=False), encoding="utf-8")

    lib = VideoLibrary(project_id)
    videos = lib.list_videos()

    # Tìm video vừa tạo
    found = [v for v in videos if v["id"] == f"studio_{test_slug}"]
    assert len(found) == 1, f"Video {test_slug} không xuất hiện trong VideoLibrary.list_videos()"
    v = found[0]
    assert v["title"] == "Thử nghiệm Video Cầu Vồng 45 Giây"
    assert v["source"] == "studio"
    assert v["primary_path"] == f"output/{test_slug}/final_45s.mp4"
    assert "tiktok" in v["variants"]

    # Dọn dẹp
    try:
        fake_mp4.unlink()
        fake_thumb.unlink()
        (test_slug_dir / "video.json").unlink()
        test_slug_dir.rmdir()
    except Exception:
        pass
