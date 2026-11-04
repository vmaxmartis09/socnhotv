"""Channel video metadata scraper and top outlier video ingester using yt-dlp extract_flat."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import yt_dlp

from socnhotv.sources.downloader import download_source
from socnhotv.sources.models import IngestRequest
from socnhotv.workspace import project_path

logger = logging.getLogger(__name__)


def generate_channel_id(url: str) -> str:
    """Generate a stable channel identifier from URL."""
    clean = url.strip().rstrip("/")
    # Check for handle like @channel
    m = re.search(r"(@[a-zA-Z0-9_\-\.]+)", clean)
    if m:
        handle = m.group(1).lstrip("@").lower()
        return f"ch_{handle}"
    # Otherwise hash URL
    h = hashlib.sha256(clean.encode()).hexdigest()[:12]
    return f"ch_{h}"


def get_channel_dir(project_id: str, channel_id: str) -> Path:
    target = project_path(project_id, "knowledge", "channels", channel_id, ensure=True)
    target.mkdir(parents=True, exist_ok=True)
    return target


def parse_video_item(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize video entry from yt-dlp."""
    vid = entry.get("id") or ""
    title = entry.get("title") or "Untitled"
    duration = entry.get("duration") or 0.0
    upload_date = entry.get("upload_date") or ""
    view_count = int(entry.get("view_count") or 0)
    like_count = int(entry.get("like_count") or 0)
    comment_count = int(entry.get("comment_count") or 0)
    thumb = entry.get("thumbnail") or (entry.get("thumbnails", [{}])[-1].get("url") if entry.get("thumbnails") else "")
    url = entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={vid}"

    # Calculate days since upload
    days_age = 1.0
    if upload_date and len(upload_date) == 8:
        try:
            ud = datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            diff = (now - ud).total_seconds() / 86400.0
            days_age = max(diff, 1.0)
        except Exception:
            days_age = 1.0

    views_per_day = round(view_count / days_age, 2)

    return {
        "id": vid,
        "title": title,
        "duration": float(duration),
        "upload_date": upload_date,
        "view_count": view_count,
        "like_count": like_count,
        "comment_count": comment_count,
        "thumbnail": thumb,
        "url": url,
        "days_age": round(days_age, 1),
        "views_per_day": views_per_day,
    }


def ingest_channel(
    project_id: str,
    channel_url: str,
    max_videos: int = 50,
    download_top_n: int = 5,
) -> Dict[str, Any]:
    """Scrape channel metadata using yt-dlp extract_flat and save to knowledge/channels/."""
    channel_id = generate_channel_id(channel_url)
    channel_dir = get_channel_dir(project_id, channel_id)

    ydl_opts = {
        "extract_flat": True,
        "skip_download": True,
        "playlist_items": f"1-{max_videos}",
        "quiet": True,
        "no_warnings": True,
    }

    info: Dict[str, Any] = {}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            extracted = ydl.extract_info(channel_url, download=False)
            if extracted:
                info = extracted
    except Exception as e:
        logger.warning(f"yt-dlp extract_flat error for {channel_url}: {e}")
        # If extraction failed, check if we have existing cache
        cache_file = channel_dir / "channel.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)

    channel_name = info.get("uploader") or info.get("channel") or info.get("title") or channel_id
    entries = info.get("entries") or []

    videos: List[Dict[str, Any]] = []
    for entry in entries:
        if not entry:
            continue
        v = parse_video_item(entry)
        if v["id"]:
            videos.append(v)

    # Sort by views_per_day descending
    videos.sort(key=lambda x: x["views_per_day"], reverse=True)

    # Save videos.jsonl (delta update / overwrite)
    videos_file = channel_dir / "videos.jsonl"
    with open(videos_file, "w", encoding="utf-8") as f:
        for v in videos:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")

    # Ingest top N full videos into sources (rights = reference_only)
    top_ingested: List[str] = []
    if download_top_n > 0 and videos:
        top_urls = [v["url"] for v in videos[:download_top_n] if v.get("url")]
        try:
            items = download_source(
                project_id=project_id,
                req=IngestRequest(urls=top_urls, rights="reference_only"),
            )
            top_ingested = [item.id for item in items]
        except Exception as e:
            logger.warning(f"Could not download top videos for channel {channel_id}: {e}")

    channel_meta = {
        "id": channel_id,
        "url": channel_url,
        "name": channel_name,
        "uploader_id": info.get("uploader_id", ""),
        "avatar": info.get("thumbnail") or (videos[0]["thumbnail"] if videos else ""),
        "video_count": len(videos),
        "top_ingested_sources": top_ingested,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Save channel.json
    with open(channel_dir / "channel.json", "w", encoding="utf-8") as f:
        json.dump(channel_meta, f, ensure_ascii=False, indent=2)

    return channel_meta
