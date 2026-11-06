"""Unit tests cho scripts/maintenance/clean_runs.py."""
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

# Thêm repo root vào sys.path để import scripts.*
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.maintenance.clean_runs import analyze_run_dir, get_dir_stats


def test_get_dir_stats(tmp_path: Path):
    sub = tmp_path / "run_test"
    sub.mkdir()
    (sub / "state.json").write_text('{"status": "completed"}', encoding="utf-8")
    (sub / "dummy.txt").write_text("hello world", encoding="utf-8")

    file_count, total_bytes, files = get_dir_stats(sub)
    assert file_count == 2
    assert total_bytes > 0
    assert "state.json" in files
    assert "dummy.txt" in files


def test_analyze_run_dir_empty(tmp_path: Path):
    empty_run = tmp_path / "run_empty"
    empty_run.mkdir()
    now = time.time()
    res = analyze_run_dir(empty_run, now=now, keep_recent_sec=0.0)
    assert res["is_removable"] is True
    assert res["category"] == "empty"


def test_analyze_run_dir_recent_protection(tmp_path: Path):
    recent_run = tmp_path / "run_recent"
    recent_run.mkdir()
    (recent_run / "state.json").write_text("{}", encoding="utf-8")
    now = time.time()
    # keep_recent_sec = 3600s
    res = analyze_run_dir(recent_run, now=now, keep_recent_sec=3600.0)
    assert res["is_removable"] is False
    assert res["category"] == "recent_active"


def test_analyze_run_dir_system_queue(tmp_path: Path):
    queue_dir = tmp_path / "render_queue"
    queue_dir.mkdir()
    now = time.time() + 10000
    res = analyze_run_dir(queue_dir, now=now, keep_recent_sec=0.0)
    assert res["is_removable"] is False
    assert res["category"] == "system_queue"


def test_analyze_run_dir_state_only_test(tmp_path: Path):
    test_run = tmp_path / "run_test_nodes"
    test_run.mkdir()
    state_content = {
        "status": "failed",
        "node_states": {
            "node_idea": {},
            "node_video_gen": {}
        }
    }
    (test_run / "state.json").write_text(json.dumps(state_content), encoding="utf-8")
    now = time.time() + 10000
    res = analyze_run_dir(test_run, now=now, keep_recent_sec=0.0)
    assert res["is_removable"] is True
    assert res["category"] == "state_only_test"


def test_analyze_run_dir_media_run_protection(tmp_path: Path):
    media_run = tmp_path / "run_with_video"
    media_run.mkdir()
    (media_run / "video.mp4").write_bytes(b"0" * 1024)
    now = time.time() + 10000
    res = analyze_run_dir(media_run, now=now, keep_recent_sec=0.0, include_media=False)
    assert res["is_removable"] is False
    assert res["category"] == "media_run"

    # When include_media is True, it becomes removable
    res_removable = analyze_run_dir(media_run, now=now, keep_recent_sec=0.0, include_media=True)
    assert res_removable["is_removable"] is True
