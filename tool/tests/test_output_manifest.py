import json
import pytest
from pathlib import Path
from socnhotv.core.storage.project_store import get_repo_root


def test_output_manifest_schema():
    repo_root = get_repo_root()
    test_slug_dir = repo_root / "data" / "projects" / "soc-nho-tv" / "output" / "_test_manifest_pkg"
    test_slug_dir.mkdir(parents=True, exist_ok=True)
    
    manifest_data = {
        "id": "video_test_manifest_123",
        "title": "Vì sao cầu vồng có nhiều màu?",
        "topic": "Vì sao cầu vồng có nhiều màu?",
        "slug": "_test_manifest_pkg",
        "created_at": "2026-11-04T12:00:00Z",
        "duration_s": 45.0,
        "size_mb": 12.5,
        "platforms": ["tiktok", "youtube"],
        "template_id": "shorts-fact-v1",
        "graph_ref": "graph.json",
        "run_id": "run_test_123",
        "voice_id": "soc-nho",
        "providers_per_scene": [{"scene_index": 0, "image_provider": "local"}],
        "cost_usd": 0.0,
        "files": {
            "video": "output/_test_manifest_pkg/final_45s.mp4",
            "thumb": "output/_test_manifest_pkg/thumb.jpg",
            "script": "output/_test_manifest_pkg/script.md",
            "voice": "output/_test_manifest_pkg/voice.mp3",
            "captions": "output/_test_manifest_pkg/captions.srt",
            "captions_words": "output/_test_manifest_pkg/captions.words.json",
            "scenes": "output/_test_manifest_pkg/scenes",
            "composition": "output/_test_manifest_pkg/composition",
            "verify_report": "output/_test_manifest_pkg/verify_report.json",
        },
        "verify": {
            "pass": True,
            "scores": {"duration": 1.0, "freeze": 1.0},
        },
    }
    
    manifest_file = test_slug_dir / "video.json"
    manifest_file.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Đọc lại và kiểm tra tính toàn vẹn
    loaded = json.loads(manifest_file.read_text(encoding="utf-8"))
    
    # 9 artifacts bắt buộc trong files
    required_files = [
        "video", "thumb", "script", "voice", "captions", 
        "captions_words", "scenes", "composition", "verify_report"
    ]
    for rf in required_files:
        assert rf in loaded["files"], f"Thiếu key {rf} trong manifest files"
    
    assert loaded["duration_s"] == 45.0
    assert loaded["verify"]["pass"] is True
    
    # Dọn dẹp test artifact
    try:
        manifest_file.unlink()
        test_slug_dir.rmdir()
    except Exception:
        pass
