from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from socnhotv.video.templates.schema import TemplateCategory, TemplateMeta
from socnhotv.workspace.paths import shared_path

logger = logging.getLogger("socnhotv.video.templates.loader")

_TEMPLATES_CACHE: Dict[str, TemplateMeta] = {}


def get_templates_root() -> Path:
    return shared_path("templates")


def load_template_from_dir(template_dir: Path) -> Optional[TemplateMeta]:
    meta_file = template_dir / "template.json"
    if not meta_file.exists():
        return None
    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return TemplateMeta(**data)
    except Exception as e:
        logger.warning(f"Lỗi đọc template {template_dir.name}: {e}")
        return None


def reload_templates() -> Dict[str, TemplateMeta]:
    global _TEMPLATES_CACHE
    root = get_templates_root()
    cache: Dict[str, TemplateMeta] = {}
    if root.exists():
        for d in root.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                t = load_template_from_dir(d)
                if t:
                    cache[t.id] = t
    _TEMPLATES_CACHE = cache
    return _TEMPLATES_CACHE


def list_templates(
    category: Optional[TemplateCategory | str] = None,
    platform: Optional[str] = None,
) -> List[TemplateMeta]:
    """Danh sách các template có thể lọc theo category hoặc platform."""
    if not _TEMPLATES_CACHE:
        reload_templates()

    results = list(_TEMPLATES_CACHE.values())
    if category:
        cat_lower = str(category).lower().strip()
        results = [t for t in results if str(t.category).lower() == cat_lower]
    if platform:
        plat_lower = str(platform).lower().strip()
        results = [t for t in results if plat_lower in [p.lower() for p in t.platforms]]

    return results


def get_template(template_id: str) -> TemplateMeta:
    """Lấy metadata của template theo ID."""
    if not _TEMPLATES_CACHE:
        reload_templates()
    if template_id in _TEMPLATES_CACHE:
        return _TEMPLATES_CACHE[template_id]

    # Thử nạp trực tiếp từ thư mục
    t_dir = get_templates_root() / template_id
    t = load_template_from_dir(t_dir)
    if t:
        _TEMPLATES_CACHE[t.id] = t
        return t

    raise FileNotFoundError(f"Template '{template_id}' không tồn tại trong {get_templates_root()}")


def get_template_dir(template_id: str) -> Path:
    """Trả về đường dẫn thư mục của template."""
    t_dir = get_templates_root() / template_id
    if not t_dir.exists():
        raise FileNotFoundError(f"Thư mục template '{template_id}' không tồn tại: {t_dir}")
    return t_dir
