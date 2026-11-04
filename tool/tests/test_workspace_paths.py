from __future__ import annotations

import tempfile
from pathlib import Path
from socnhotv.workspace import (
    repo_root,
    data_root,
    active_project_id,
    list_projects,
    project_path,
    shared_path,
)


def test_repo_and_data_root():
    root = repo_root()
    assert (root / "data" / "workspace.json").exists()
    assert data_root() == root / "data"


def test_active_project_and_list():
    active = active_project_id()
    assert active == "soc-nho-tv"
    projects = list_projects()
    assert isinstance(projects, list)
    assert any(p.get("id") == "soc-nho-tv" for p in projects)


def test_project_path():
    p = project_path("soc-nho-tv", "test_sub", "item.json", ensure=False)
    assert p == data_root() / "projects" / "soc-nho-tv" / "test_sub" / "item.json"
    
    # Test ensure=True creates parent directory
    p_ensure = project_path("soc-nho-tv", "tmp_test_dir", "file.txt", ensure=True)
    assert p_ensure.parent.exists()
    if p_ensure.parent.exists():
        p_ensure.parent.rmdir()


def test_shared_path():
    p = shared_path("models", "test.bin", ensure=False)
    assert p == data_root() / "shared" / "models" / "test.bin"
    
    p_ensure = shared_path("tmp_shared_dir", "file.txt", ensure=True)
    assert p_ensure.parent.exists()
    if p_ensure.parent.exists():
        p_ensure.parent.rmdir()
