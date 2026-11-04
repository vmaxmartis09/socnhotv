import shutil
import tempfile
import zipfile
from pathlib import Path

import pytest

from socnhotv.social.adapters.manual import ManualAdapter, export_package_zip
from socnhotv.social.models import PostMedia, PostTarget, SocialAccount


@pytest.fixture
def manual_fixture(monkeypatch):
    temp_dir = Path(tempfile.mkdtemp())
    monkeypatch.setattr(
        "socnhotv.social.adapters.manual.project_path",
        lambda pid, *parts, ensure=False: temp_dir / pid / Path(*parts),
    )
    yield "test-manual-proj", temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_manual_package_generation_and_zip(manual_fixture):
    pid, temp_dir = manual_fixture
    adapter = ManualAdapter(platform="tiktok")

    acc = SocialAccount(
        id="acc_tt_manual",
        platform="tiktok",
        handle="@socnho",
        display_name="Sóc Nhỏ TikTok",
    )
    target = PostTarget(
        id="tgt_manual_1",
        account_id=acc.id,
        platform="tiktok",
        title="Tập 3: Sóc Nhỏ Đi Cắm Trại",
        caption="Cuộc phiêu lưu trong rừng cùng Bi và bạn Koala",
        hashtags=["socnho", "adventure"],
        product_link="https://shop.tiktok.com/p/camp",
        disclosure_ad=True,
        scheduled_at="2026-11-12T19:00:00+07:00",
    )

    # Fake media file
    vid_file = temp_dir / "sample_video.mp4"
    vid_file.write_bytes(b"FAKE_MP4_CONTENT")
    media = PostMedia(path=str(vid_file), thumb=str(vid_file))

    res = adapter.publish(acc, target, media, project_id=pid, post_id="post_camp_01")
    assert res.status == "published"
    assert "packages" in (res.url or "")

    pkg_dir = Path(res.url)
    assert pkg_dir.exists()
    assert (pkg_dir / "video.mp4").exists()
    assert (pkg_dir / "cover.jpg").exists()
    assert (pkg_dir / "caption.txt").exists()
    assert (pkg_dir / "hashtags.txt").exists()
    assert (pkg_dir / "checklist.md").exists()
    assert (pkg_dir / "meta.json").exists()

    # Test zip packaging
    zip_path = export_package_zip(pid, "post_camp_01", "tiktok")
    assert zip_path.exists()
    assert zipfile.is_zipfile(zip_path)

    with zipfile.ZipFile(zip_path, "r") as z:
        namelist = z.namelist()
        assert "caption.txt" in namelist
        assert "checklist.md" in namelist
        assert "video.mp4" in namelist
