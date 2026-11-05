from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from socnhotv.social.store import SocialStore, atomic_read_json, atomic_write_json
from socnhotv.workspace.paths import project_path


def _generate_video_thumbnail(project_id: str, video_path: Path, video_id: str) -> str:
    """Extract a 1s frame from video to publishing/.thumbs/{safe_id}.jpg and return relative path."""
    if not video_path.exists():
        return ""
    safe_id = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in video_id)
    thumb_rel = f"publishing/.thumbs/{safe_id}.jpg"
    thumb_abs = project_path(project_id, thumb_rel, ensure=False)
    if thumb_abs.exists():
        return thumb_rel
    try:
        thumb_abs.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            "00:00:01",
            "-i",
            str(video_path),
            "-vframes",
            "1",
            "-q:v",
            "2",
            str(thumb_abs),
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=5)
        if res.returncode == 0 and thumb_abs.exists():
            return thumb_rel
    except Exception:
        pass
    return ""


def _probe_video_file(file_path: Path) -> Dict[str, Any]:
    """Run ffprobe to get duration, width, height, and size_mb."""
    default_meta = {
        "duration_s": 30.0,
        "width": 1080,
        "height": 1920,
        "size_mb": 5.0,
        "aspect_ratio": "9:16",
    }
    if not file_path.exists():
        return default_meta

    try:
        size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(file_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            info = json.loads(result.stdout)
            fmt = info.get("format", {})
            duration = float(fmt.get("duration", 0.0))
            width = 0
            height = 0
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "video":
                    width = int(stream.get("width", 0))
                    height = int(stream.get("height", 0))
                    break

            aspect_ratio = "9:16" if height > width else "16:9"
            if width == height and width > 0:
                aspect_ratio = "1:1"

            return {
                "duration_s": round(duration, 2),
                "width": width,
                "height": height,
                "size_mb": size_mb,
                "aspect_ratio": aspect_ratio,
            }
    except Exception:
        pass

    # Fallback using file size
    try:
        size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)
        default_meta["size_mb"] = size_mb
    except Exception:
        pass

    return default_meta


class VideoLibrary:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.pub_dir = project_path(project_id, "publishing", ensure=True)
        self.cache_file = self.pub_dir / ".video_cache.json"

    def _load_cache(self) -> Dict[str, Any]:
        return atomic_read_json(self.cache_file, default={})

    def _save_cache(self, cache: Dict[str, Any]) -> None:
        atomic_write_json(self.cache_file, cache)

    def list_videos(self) -> List[Dict[str, Any]]:
        """Scan completed render jobs and media folders for publishable videos."""
        cache = self._load_cache()
        videos: List[Dict[str, Any]] = []
        seen_paths = set()

        store = SocialStore(self.project_id)
        existing_posts = store.list_posts()

        # Map video path/id to posted statistics
        posted_stats: Dict[str, Dict[str, Any]] = {}
        for p in existing_posts:
            p_time = p.created_at
            for t in p.targets:
                if t.published_at or t.scheduled_at:
                    p_time = t.published_at or t.scheduled_at
            for m in p.media:
                if m.path:
                    stat = posted_stats.setdefault(m.path, {"count": 0, "last": None})
                    stat["count"] += 1
                    if not stat["last"] or p_time > stat["last"]:
                        stat["last"] = p_time
            if p.render_job_id:
                stat = posted_stats.setdefault(p.render_job_id, {"count": 0, "last": None})
                stat["count"] += 1
                if not stat["last"] or p_time > stat["last"]:
                    stat["last"] = p_time

        # 1. Scan Render Queue for done jobs
        queue_dir = project_path(self.project_id, "runs", "render_queue", ensure=False)
        if queue_dir.exists():
            for job_file in queue_dir.glob("render_*.json"):
                if job_file.name.endswith(".req.json"):
                    continue
                try:
                    job_data = atomic_read_json(job_file)
                    if not job_data or job_data.get("status") != "done":
                        continue

                    job_id = job_data.get("job_id", job_file.stem)
                    outputs: Dict[str, str] = job_data.get("outputs", {})
                    if not outputs:
                        continue

                    # Read req.json for meta
                    req_file = queue_dir / f"{job_id}.req.json"
                    req_data = atomic_read_json(req_file, default={})
                    title = (
                        req_data.get("data", {}).get("title")
                        or req_data.get("data", {}).get("story_title")
                        or req_data.get("output_name")
                        or f"Video render {job_id[:8]}"
                    )
                    script_excerpt = (
                        req_data.get("data", {}).get("book_page_text")
                        or req_data.get("voice", {}).get("script")
                        or ""
                    )

                    # Pick primary output file for probing
                    first_platform, primary_rel_path = next(iter(outputs.items()))
                    primary_abs_path = project_path(self.project_id, primary_rel_path, ensure=False)

                    meta_key = f"{primary_rel_path}_{primary_abs_path.stat().st_mtime if primary_abs_path.exists() else 0}"
                    if meta_key in cache:
                        meta = cache[meta_key]
                    else:
                        meta = _probe_video_file(primary_abs_path)
                        cache[meta_key] = meta

                    # Look for thumbnail in same folder
                    thumb = ""
                    if primary_abs_path.exists():
                        parent_dir = primary_abs_path.parent
                        jpg_files = list(parent_dir.glob("*.jpg")) + list(parent_dir.glob("*.png"))
                        if jpg_files:
                            thumb = str(jpg_files[0].relative_to(project_path(self.project_id, ensure=False)))

                    p_stat = posted_stats.get(job_id) or posted_stats.get(primary_rel_path) or {"count": 0, "last": None}

                    seen_paths.add(primary_rel_path)
                    videos.append({
                        "id": job_id,
                        "title": title,
                        "thumb": thumb,
                        "duration_s": meta.get("duration_s", 0.0),
                        "width": meta.get("width", 1080),
                        "height": meta.get("height", 1920),
                        "size_mb": meta.get("size_mb", 0.0),
                        "aspect_ratio": meta.get("aspect_ratio", "9:16"),
                        "variants": outputs,
                        "primary_path": primary_rel_path,
                        "source": "job",
                        "posted_count": p_stat["count"],
                        "last_posted_at": p_stat["last"],
                        "script_excerpt": script_excerpt,
                    })
                except Exception:
                    continue

        # 2. Scan Episodes folder
        episodes_dir = project_path(self.project_id, "content", "episodes", ensure=False)
        if episodes_dir.exists():
            for ep_mp4 in episodes_dir.rglob("*.mp4"):
                rel_path = str(ep_mp4.relative_to(project_path(self.project_id, ensure=False)))
                if rel_path in seen_paths:
                    continue
                seen_paths.add(rel_path)

                meta_key = f"{rel_path}_{ep_mp4.stat().st_mtime}"
                if meta_key in cache:
                    meta = cache[meta_key]
                else:
                    meta = _probe_video_file(ep_mp4)
                    cache[meta_key] = meta

                p_stat = posted_stats.get(rel_path) or {"count": 0, "last": None}
                title = ep_mp4.stem.replace("_", " ").title()

                videos.append({
                    "id": f"ep_{ep_mp4.stem}",
                    "title": title,
                    "thumb": "",
                    "duration_s": meta.get("duration_s", 0.0),
                    "width": meta.get("width", 1920),
                    "height": meta.get("height", 1080),
                    "size_mb": meta.get("size_mb", 0.0),
                    "aspect_ratio": meta.get("aspect_ratio", "16:9"),
                    "variants": {"main": rel_path},
                    "primary_path": rel_path,
                    "source": "episode",
                    "posted_count": p_stat["count"],
                    "last_posted_at": p_stat["last"],
                    "script_excerpt": "",
                })

        # 3. Scan Output Studio Packages (output/<slug>/video.json)
        output_dir = project_path(self.project_id, "output", ensure=False)
        if output_dir.exists():
            for v_json in output_dir.glob("*/video.json"):
                try:
                    data = atomic_read_json(v_json, default={})
                    slug = v_json.parent.name
                    files_dict = data.get("files", {})
                    rel_video = files_dict.get("video") or f"output/{slug}/final_45s.mp4"
                    abs_video = project_path(self.project_id, rel_video, ensure=False)
                    if not abs_video.exists():
                        continue

                    if rel_video in seen_paths:
                        continue
                    seen_paths.add(rel_video)

                    rel_thumb = files_dict.get("thumb") or f"output/{slug}/thumb.jpg"
                    abs_thumb = project_path(self.project_id, rel_thumb, ensure=False)
                    thumb_str = rel_thumb if abs_thumb.exists() else ""

                    script_excerpt = ""
                    rel_script = files_dict.get("script") or f"output/{slug}/script.md"
                    abs_script = project_path(self.project_id, rel_script, ensure=False)
                    if abs_script.exists():
                        try:
                            script_excerpt = abs_script.read_text(encoding="utf-8")[:200]
                        except Exception:
                            pass

                    meta_key = f"{rel_video}_{abs_video.stat().st_mtime}"
                    if meta_key in cache:
                        meta = cache[meta_key]
                    else:
                        meta = _probe_video_file(abs_video)
                        cache[meta_key] = meta

                    p_stat = posted_stats.get(rel_video) or posted_stats.get(data.get("id")) or {"count": 0, "last": None}
                    title = data.get("title") or slug.replace("_", " ").replace("-", " ").title()

                    variants = {"main": rel_video}
                    for plat in data.get("platforms", ["tiktok", "youtube"]):
                        variants[plat] = rel_video

                    videos.append({
                        "id": data.get("id") or f"studio_{slug}",
                        "title": title,
                        "thumb": thumb_str,
                        "duration_s": data.get("duration_s") or meta.get("duration_s", 0.0),
                        "width": meta.get("width", 1080),
                        "height": meta.get("height", 1920),
                        "size_mb": data.get("size_mb") or meta.get("size_mb", 0.0),
                        "aspect_ratio": "9:16",
                        "variants": variants,
                        "primary_path": rel_video,
                        "source": "studio",
                        "posted_count": p_stat["count"],
                        "last_posted_at": p_stat["last"],
                        "script_excerpt": script_excerpt,
                    })
                except Exception:
                    continue

        # 4. Scan Library / Output remaining mp4s
        for folder_name in ["output", "library"]:
            f_dir = project_path(self.project_id, folder_name, ensure=False)
            if f_dir.exists():
                for mp4 in f_dir.rglob("*.mp4"):
                    rel_path = str(mp4.relative_to(project_path(self.project_id, ensure=False)))
                    if rel_path in seen_paths:
                        continue
                    seen_paths.add(rel_path)

                    meta_key = f"{rel_path}_{mp4.stat().st_mtime}"
                    if meta_key in cache:
                        meta = cache[meta_key]
                    else:
                        meta = _probe_video_file(mp4)
                        cache[meta_key] = meta

                    p_stat = posted_stats.get(rel_path) or {"count": 0, "last": None}
                    title = mp4.stem.replace("_", " ").title()

                    videos.append({
                        "id": f"{folder_name}_{mp4.stem}",
                        "title": title,
                        "thumb": "",
                        "duration_s": meta.get("duration_s", 0.0),
                        "width": meta.get("width", 1080),
                        "height": meta.get("height", 1920),
                        "size_mb": meta.get("size_mb", 0.0),
                        "aspect_ratio": meta.get("aspect_ratio", "9:16"),
                        "variants": {"main": rel_path},
                        "primary_path": rel_path,
                        "source": folder_name,
                        "posted_count": p_stat["count"],
                        "last_posted_at": p_stat["last"],
                        "script_excerpt": "",
                    })

        self._save_cache(cache)
        return videos

    def list_library(
        self,
        filter_type: Optional[str] = None,
        account_id: Optional[str] = None,
        platform: Optional[str] = None,
        q: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        raw_videos = self.list_videos()
        store = SocialStore(self.project_id)
        existing_posts = store.list_posts()

        library_items = []
        for v in raw_videos:
            v_id = v["id"]
            primary_path = v.get("primary_path", "")
            variants = v.get("variants", {})

            # Generate thumb if empty
            if not v.get("thumb"):
                abs_v_path = project_path(self.project_id, primary_path, ensure=False)
                generated_thumb = _generate_video_thumbnail(self.project_id, abs_v_path, v_id)
                if generated_thumb:
                    v["thumb"] = generated_thumb

            # Find matching posts and targets
            matching_targets = []
            for p in existing_posts:
                matches_post = False
                if p.render_job_id and p.render_job_id == v_id:
                    matches_post = True
                elif any(m.path == primary_path or m.path in variants.values() for m in p.media):
                    matches_post = True
                elif p.id == v_id:
                    matches_post = True

                if matches_post:
                    for t in p.targets:
                        matching_targets.append({
                            "account_id": t.account_id,
                            "platform": t.platform,
                            "status": t.status,
                            "scheduled_at": t.scheduled_at,
                            "published_url": t.external_url or "",
                            "post_id": p.id,
                            "target_id": t.id,
                        })

            v["posts_by_account"] = matching_targets

            # Apply search filter
            if q:
                if q.lower() not in v.get("title", "").lower():
                    continue

            # Apply status filter
            if filter_type:
                if filter_type == "unposted":
                    has_scheduled_or_pub = any(t["status"] in ("published", "scheduled") for t in matching_targets)
                    if has_scheduled_or_pub:
                        continue
                elif filter_type == "posted":
                    if not any(t["status"] == "published" for t in matching_targets):
                        continue
                elif filter_type == "scheduled":
                    if not any(t["status"] == "scheduled" for t in matching_targets):
                        continue
                elif filter_type == "draft":
                    if not any(t["status"] == "draft" for t in matching_targets):
                        continue

            # Apply account filter
            if account_id:
                if account_id.startswith("not:"):
                    not_acc = account_id[4:]
                    if any(t["account_id"] == not_acc and t["status"] in ("published", "scheduled") for t in matching_targets):
                        continue
                else:
                    if not any(t["account_id"] == account_id for t in matching_targets):
                        continue

            # Apply platform filter
            if platform:
                if not any(t["platform"] == platform for t in matching_targets):
                    continue

            library_items.append(v)

        return library_items
