from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from socnhotv.sources.models import RightsType, SourceItem
from socnhotv.workspace import project_path

logger = logging.getLogger(__name__)


def list_sources(
    project_id: str,
    platform: Optional[str] = None,
    rights: Optional[str] = None,
    q: Optional[str] = None,
) -> List[SourceItem]:
    raw_dir = project_path(project_id, "raw")
    if not raw_dir.exists():
        return []

    results: List[SourceItem] = []
    for s_dir in raw_dir.iterdir():
        if not s_dir.is_dir() or s_dir.name.startswith("_") or s_dir.name.startswith("."):
            continue
        meta_file = s_dir / "meta.json"
        if not meta_file.exists():
            continue
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            item = SourceItem(**data)
            
            # Filter platform
            if platform and item.platform != platform:
                continue
            # Filter rights
            if rights and item.rights != rights:
                continue
            # Search query
            if q:
                ql = q.lower()
                text = f"{item.title} {item.description} {item.author} {' '.join(item.hashtags)}".lower()
                if ql not in text:
                    continue
            results.append(item)
        except Exception as e:
            logger.warning("Error reading source meta %s: %s", meta_file, e)

    # Sort newest first
    results.sort(key=lambda x: x.created_at, reverse=True)
    return results


def get_source(project_id: str, source_id: str) -> Optional[SourceItem]:
    meta_file = project_path(project_id, "raw", source_id, "meta.json")
    if not meta_file.exists():
        return None
    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return SourceItem(**data)
    except Exception as e:
        logger.warning("Error loading source %s: %s", source_id, e)
        return None


def update_source_rights(
    project_id: str,
    source_id: str,
    new_rights: RightsType,
    note: Optional[str] = None,
    confirm_rights: bool = False,
) -> SourceItem:
    meta_file = project_path(project_id, "raw", source_id, "meta.json")
    if not meta_file.exists():
        raise FileNotFoundError(f"Source not found: {source_id}")

    with open(meta_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    item = SourceItem(**data)

    # Strict check: switching from reference_only to anything else requires confirm_rights=True
    if item.rights == "reference_only" and new_rights != "reference_only":
        if not confirm_rights:
            raise ValueError(
                "Đổi bản quyền khỏi 'reference_only' bắt buộc phải có confirm_rights=true "
                "để xác nhận bạn sở hữu hoặc được phép sử dụng nội dung này cho video thương mại."
            )

    item.rights = new_rights
    if note is not None:
        item.rights_note = note

    with open(meta_file, "w", encoding="utf-8") as f:
        f.write(item.model_dump_json(indent=2))

    return item


def delete_source_to_trash(project_id: str, source_id: str) -> bool:
    source_dir = project_path(project_id, "raw", source_id)
    if not source_dir.exists():
        return False
    trash_dir = project_path(project_id, "raw", "_trash", ensure=True)
    target = trash_dir / source_id
    if target.exists():
        shutil.rmtree(target)
    shutil.move(str(source_dir), str(target))
    return True


def get_source_file_path(project_id: str, source_id: str, file_name: str) -> Optional[Path]:
    f = project_path(project_id, "raw", source_id, file_name)
    if f.exists() and f.is_file():
        return f
    # Support nested files like scenes/scene_001.jpg
    parts = file_name.strip("/").split("/")
    f_nested = project_path(project_id, "raw", source_id, *parts)
    if f_nested.exists() and f_nested.is_file():
        return f_nested
    return None
