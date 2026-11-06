"""Cấu hình chung cho bộ test.

Một số test chạy đồ thị trên dự án thật (vd. ProjectStore("soc-nho-tv")), và bộ chạy lưu lại
đồ thị vào data/projects/<id>/graph.json -> ghi đè flow người dùng đang dựng. Fixture dưới đây
sao lưu graph.json của mọi dự án trước phiên test và khôi phục nguyên vẹn sau phiên test.
"""
from __future__ import annotations

from pathlib import Path

import pytest

_PROJECTS = Path(__file__).resolve().parents[2] / "data" / "projects"


@pytest.fixture(scope="session", autouse=True)
def _preserve_project_graphs():
    saved = {}
    if _PROJECTS.is_dir():
        for p in _PROJECTS.glob("*/graph.json"):
            try:
                saved[p] = p.read_bytes()
            except OSError:
                pass
    existed = set(saved)
    # Ảnh chụp cổng ra node (runs/_node_outputs) do test tạo trên dự án thật -> dọn sau phiên test
    snap_before = set(_PROJECTS.glob("*/runs/_node_outputs/*/*.json")) if _PROJECTS.is_dir() else set()
    yield
    if _PROJECTS.is_dir():
        for f in set(_PROJECTS.glob("*/runs/_node_outputs/*/*.json")) - snap_before:
            try:
                f.unlink()
                if not any(f.parent.iterdir()):
                    f.parent.rmdir()
            except OSError:
                pass
    for p, data in saved.items():
        try:
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
        except OSError:
            pass
    # graph.json do test tạo mới ở dự án chưa từng có flow -> xoá đi
    if _PROJECTS.is_dir():
        for p in _PROJECTS.glob("*/graph.json"):
            if p not in existed:
                try:
                    p.unlink()
                except OSError:
                    pass
