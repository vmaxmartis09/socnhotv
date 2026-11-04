from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yt_dlp
from socnhotv.sources.models import PlatformType, RightsType, SourceFiles, SourceItem, SourceStats
from socnhotv.workspace import project_path

logger = logging.getLogger(__name__)

# Last download timestamp per platform for rate limiting
_last_download_ts: Dict[str, float] = {}


def detect_platform(url: str) -> PlatformType:
    u = url.lower()
    if "douyin.com" in u or "iesdouyin.com" in u:
        return "douyin"
    if "tiktok.com" in u:
        return "tiktok"
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    if "bilibili.com" in u:
        return "bilibili"
    if "facebook.com" in u or "fb.watch" in u:
        return "facebook"
    if "instagram.com" in u:
        return "instagram"
    if u.startswith("file://") or u.startswith("/") or u.endswith((".mp4", ".mov", ".mkv", ".avi", ".webm")) or os.path.exists(url):
        return "local"
    return "youtube"


def generate_source_id(url: str) -> str:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    plat = detect_platform(url)
    return f"{plat}_{h}"


def extract_audio_wav(video_path: Path, audio_path: Path) -> bool:
    """Extract 16kHz mono WAV using ffmpeg."""
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(audio_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        return res.returncode == 0 and audio_path.exists()
    except Exception as e:
        logger.warning("Failed to extract audio from %s: %s", video_path, e)
        return False


def extract_thumbnail_jpg(video_path: Path, thumb_path: Path) -> bool:
    """Extract thumbnail frame from video at 1s."""
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", "00:00:01",
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(thumb_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if res.returncode == 0 and thumb_path.exists():
            return True
        # Fallback to frame 0
        cmd[2] = "00:00:00"
        res2 = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        return res2.returncode == 0 and thumb_path.exists()
    except Exception as e:
        logger.warning("Failed to extract thumbnail: %s", e)
        return False


def _apply_rate_limit(platform: str, min_interval: float = 2.0) -> None:
    now = time.time()
    last = _last_download_ts.get(platform, 0.0)
    wait = min_interval - (now - last)
    if wait > 0:
        time.sleep(wait)
    _last_download_ts[platform] = time.time()


def download_source(
    project_id: str,
    url: str,
    rights: RightsType = "reference_only",
    rights_note: str = "",
    cookie_file: Optional[str] = None,
    max_retries: int = 3,
) -> SourceItem:
    """Download video and extract metadata using yt-dlp."""
    platform = detect_platform(url)
    source_id = generate_source_id(url)
    target_dir = project_path(project_id, "raw", source_id)
    target_dir.mkdir(parents=True, exist_ok=True)

    video_dest = target_dir / "video.mp4"
    audio_dest = target_dir / "audio.wav"
    thumb_dest = target_dir / "thumb.jpg"
    meta_dest = target_dir / "meta.json"

    # Rate limiting
    _apply_rate_limit(platform)

    ydl_opts: Dict[str, Any] = {
        "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best",
        "outtmpl": str(target_dir / "video.%(ext)s"),
        "merge_output_format": "mp4",
        "writethumbnail": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["zh-Hans", "zh", "vi", "en"],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    if cookie_file and os.path.exists(cookie_file):
        ydl_opts["cookiefile"] = cookie_file

    attempt = 0
    last_error = ""

    while attempt < max_retries:
        attempt += 1
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise ValueError("No info returned by yt-dlp")

                # Rename whatever video was output to video.mp4 if needed
                for f in target_dir.glob("video.*"):
                    if f.suffix in [".mp4", ".mkv", ".webm"] and f.name != "video.mp4":
                        if video_dest.exists():
                            video_dest.unlink()
                        f.rename(video_dest)
                        break

                # Thumbnail detection or extraction
                for t in target_dir.glob("video.*"):
                    if t.suffix in [".jpg", ".webp", ".png"]:
                        if t.suffix != ".jpg":
                            # Convert or rename to thumb.jpg
                            if thumb_dest.exists():
                                thumb_dest.unlink()
                            t.rename(thumb_dest)
                        else:
                            if t.name != "thumb.jpg":
                                t.rename(thumb_dest)
                        break

                if not thumb_dest.exists() and video_dest.exists():
                    extract_thumbnail_jpg(video_dest, thumb_dest)

                # Extract audio wav 16k mono
                if video_dest.exists() and not audio_dest.exists():
                    extract_audio_wav(video_dest, audio_dest)

                # Subtitles
                sub_path = None
                for s in target_dir.glob("*.vtt"):
                    sub_path = f"raw/{source_id}/{s.name}"
                    break

                # Extract metadata
                title = info.get("title") or ""
                description = info.get("description") or ""
                duration = float(info.get("duration") or 0.0)
                uploader = info.get("uploader") or info.get("channel") or ""
                uploader_url = info.get("uploader_url") or info.get("channel_url") or ""
                upload_date = info.get("upload_date") or ""

                stats = SourceStats(
                    views=int(info.get("view_count") or 0),
                    likes=int(info.get("like_count") or 0),
                    comments=int(info.get("comment_count") or 0),
                    shares=int(info.get("repost_count") or 0),
                )

                item = SourceItem(
                    id=source_id,
                    project_id=project_id,
                    platform=platform,
                    url=url,
                    author=uploader,
                    author_url=uploader_url,
                    title=title,
                    description=description,
                    duration_s=duration,
                    published_at=upload_date,
                    stats=stats,
                    hashtags=info.get("tags") or [],
                    music=info.get("track") or "",
                    rights=rights,
                    rights_note=rights_note,
                    files=SourceFiles(
                        video=f"raw/{source_id}/video.mp4" if video_dest.exists() else None,
                        audio=f"raw/{source_id}/audio.wav" if audio_dest.exists() else None,
                        thumb=f"raw/{source_id}/thumb.jpg" if thumb_dest.exists() else None,
                        subtitle_orig=sub_path,
                    ),
                    status="ready",
                )

                # Persist meta.json
                with open(meta_dest, "w", encoding="utf-8") as f:
                    f.write(item.model_dump_json(indent=2))

                return item

        except Exception as e:
            err_msg = str(e)
            last_error = err_msg
            logger.warning("Download attempt %d failed for %s: %s", attempt, url, err_msg)
            
            # Douyin / TikTok verification or captcha check
            if platform in ["douyin", "tiktok"]:
                if "captcha" in err_msg.lower() or "verify" in err_msg.lower() or "login" in err_msg.lower() or "cookie" in err_msg.lower():
                    clean_msg = (
                        f"Nền tảng {platform} yêu cầu cookie hoặc xác thực danh tính. "
                        "Hệ thống tuân thủ chính sách: không cố vượt captcha. "
                        "Vui lòng cấu hình cookiefile hợp lệ từ trình duyệt cá nhân để tiếp tục."
                    )
                    failed_item = SourceItem(
                        id=source_id,
                        project_id=project_id,
                        platform=platform,
                        url=url,
                        rights=rights,
                        rights_note=rights_note,
                        status="failed",
                        error=clean_msg,
                    )
                    with open(meta_dest, "w", encoding="utf-8") as f:
                        f.write(failed_item.model_dump_json(indent=2))
                    return failed_item

            if attempt < max_retries:
                time.sleep(1.0 * attempt)

    # Failed after retries
    failed_item = SourceItem(
        id=source_id,
        project_id=project_id,
        platform=platform,
        url=url,
        rights=rights,
        rights_note=rights_note,
        status="failed",
        error=f"Tải thất bại sau {max_retries} lần thử: {last_error}",
    )
    with open(meta_dest, "w", encoding="utf-8") as f:
        f.write(failed_item.model_dump_json(indent=2))
    return failed_item
