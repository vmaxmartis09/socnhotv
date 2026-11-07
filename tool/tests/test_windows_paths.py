"""Hồi quy Windows: tìm python OmniVoice và binary HyperFrames theo đúng cấu trúc thư mục Windows."""
import os
import sys
from pathlib import Path
from unittest.mock import patch

_REPO_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_REPO_SRC) not in sys.path:
    sys.path.insert(0, str(_REPO_SRC))

from gobi.services.voice import omnivoice_engine as oe
from socnhotv.video import hyperframes_engine as he


def test_omnivoice_python_windows_layout(tmp_path, monkeypatch):
    monkeypatch.delenv("OMNIVOICE_PYTHON", raising=False)
    venv = tmp_path / ".venv" / "Scripts"
    venv.mkdir(parents=True)
    (venv / "python.exe").write_text("x")
    with patch.object(oe, "OMNIVOICE_DIR", tmp_path), patch.object(oe, "_is_windows", return_value=True):
        assert oe.resolve_python().endswith(os.path.join("Scripts", "python.exe"))


def test_omnivoice_python_falls_back_when_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("OMNIVOICE_PYTHON", raising=False)
    with patch.object(oe, "OMNIVOICE_DIR", tmp_path):
        assert oe.resolve_python()  # không có venv: trả interpreter hiện tại, không lỗi


def test_hyperframes_finds_cmd_shim_on_windows(tmp_path, monkeypatch):
    monkeypatch.delenv("HYPERFRAMES_BIN", raising=False)
    binp = tmp_path / "tool" / "dashboard" / "node_modules" / ".bin"
    binp.mkdir(parents=True)
    (binp / "hyperframes.cmd").write_text("@echo off")
    with patch.object(he, "_is_windows", return_value=True):
        found = he.find_hyperframes_bin(tmp_path)
    assert found and found.endswith("hyperframes.cmd")
