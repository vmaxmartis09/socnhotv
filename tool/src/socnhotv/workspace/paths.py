from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional


def repo_root() -> Path:
    """Traverse up from this file until reaching directory containing data/workspace.json."""
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "data" / "workspace.json").exists():
            return parent
    # Fallback to current working directory or grandparent
    cwd = Path.cwd().resolve()
    for parent in [cwd] + list(cwd.parents):
        if (parent / "data" / "workspace.json").exists():
            return parent
    return Path(__file__).resolve().parents[3]


def data_root() -> Path:
    return repo_root() / "data"


def _read_workspace_data() -> dict[str, Any]:
    ws_file = data_root() / "workspace.json"
    if not ws_file.exists():
        return {}
    try:
        with open(ws_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def active_project_id() -> str:
    ws = _read_workspace_data()
    return str(ws.get("active_project", "soc-nho-tv"))


def list_projects() -> List[dict[str, Any]]:
    ws = _read_workspace_data()
    return list(ws.get("projects", []))


def project_path(project_id: str, *parts: str | Path, ensure: bool = False) -> Path:
    target = data_root() / "projects" / project_id
    for part in parts:
        target = target / part
    if ensure:
        if parts:
            target.parent.mkdir(parents=True, exist_ok=True)
        else:
            target.mkdir(parents=True, exist_ok=True)
    return target


def shared_path(*parts: str | Path, ensure: bool = False) -> Path:
    target = data_root() / "shared"
    for part in parts:
        target = target / part
    if ensure:
        if parts:
            target.parent.mkdir(parents=True, exist_ok=True)
        else:
            target.mkdir(parents=True, exist_ok=True)
    return target
