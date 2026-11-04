from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from socnhotv.sources.downloader import (
    detect_platform,
    download_source,
    extract_audio_wav,
    extract_thumbnail_jpg,
    generate_source_id,
)
from socnhotv.sources.local import ingest_local_file
from socnhotv.workspace import project_path


def test_detect_platform():
    assert detect_platform("https://v.douyin.com/abc") == "douyin"
    assert detect_platform("https://www.tiktok.com/@user/video/123") == "tiktok"
    assert detect_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "youtube"
    assert detect_platform("https://youtu.be/dQw4w9WgXcQ") == "youtube"
    assert detect_platform("https://www.bilibili.com/video/BV1") == "bilibili"
    assert detect_platform("/tmp/test.mp4") == "local"


def test_generate_source_id():
    sid1 = generate_source_id("https://youtube.com/watch?v=123")
    sid2 = generate_source_id("https://youtube.com/watch?v=123")
    assert sid1 == sid2
    assert sid1.startswith("youtube_")


def test_download_source_douyin_captcha_rejection():
    # Verify that captcha / verification errors are caught cleanly without hacking
    with patch("yt_dlp.YoutubeDL") as mock_ydl:
        mock_instance = MagicMock()
        mock_instance.extract_info.side_effect = Exception("douyin verify captcha required")
        mock_ydl.return_value.__enter__.return_value = mock_instance

        item = download_source(
            project_id="soc-nho-tv",
            url="https://www.douyin.com/video/7123456789",
            rights="reference_only",
            max_retries=1,
        )

        assert item.status == "failed"
        assert item.error is not None
        assert "không cố vượt captcha" in item.error
        assert "cookie" in item.error


def test_download_source_mock_success():
    with patch("yt_dlp.YoutubeDL") as mock_ydl:
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            "title": "Sample Educational Animation",
            "description": "Short kids video #cartoon",
            "duration": 30.0,
            "uploader": "TestCreator",
            "uploader_url": "https://youtube.com/@TestCreator",
            "view_count": 50000,
            "like_count": 2500,
            "comment_count": 120,
            "repost_count": 30,
            "tags": ["cartoon", "education"],
        }
        mock_ydl.return_value.__enter__.return_value = mock_instance

        # Also mock file creation in target dir
        with patch("socnhotv.sources.downloader.extract_audio_wav") as mock_audio, \
             patch("socnhotv.sources.downloader.extract_thumbnail_jpg") as mock_thumb:
            item = download_source(
                project_id="soc-nho-tv",
                url="https://youtube.com/watch?v=sample123",
                rights="reference_only",
            )

            assert item.status == "ready"
            assert item.title == "Sample Educational Animation"
            assert item.stats.views == 50000
            assert item.rights == "reference_only"
            assert "cartoon" in item.hashtags
