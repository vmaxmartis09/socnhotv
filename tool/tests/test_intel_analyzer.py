from __future__ import annotations

import json
from pathlib import Path
from socnhotv.intelligence.analyzer import analyze_video, infer_beat_role
from socnhotv.sources.models import SourceItem
from socnhotv.workspace import project_path


def test_infer_beat_role():
    assert infer_beat_role(0, 5, 0.5, 30.0, "Cả nhà ơi xem này") == "hook"
    assert infer_beat_role(4, 5, 27.0, 30.0, "Bấm vào giỏ hàng ngay nhé") == "cta"
    assert infer_beat_role(1, 5, 5.0, 30.0, "Rất nhiều người gặp vấn đề này") == "problem"
    assert infer_beat_role(2, 5, 12.0, 30.0, "Dùng thử tính năng này") == "demo"
    assert infer_beat_role(3, 5, 22.0, 30.0, "Giá ưu đãi hôm nay") == "offer"


def test_analyze_video_pacing_and_template():
    # Setup test source with 3 scenes
    sid = "intel_test_source_01"
    sdir = project_path("soc-nho-tv", "raw", sid)
    sdir.mkdir(parents=True, exist_ok=True)

    s = SourceItem(
        id=sid,
        project_id="soc-nho-tv",
        platform="tiktok",
        url="https://tiktok.com/@test/1",
        duration_s=20.0,
    )
    with open(sdir / "meta.json", "w", encoding="utf-8") as f:
        f.write(s.model_dump_json())

    scenes = [
        {"scene_idx": 1, "start_s": 0.0, "end_s": 3.0},
        {"scene_idx": 2, "start_s": 3.0, "end_s": 10.0},
        {"scene_idx": 3, "start_s": 10.0, "end_s": 20.0},
    ]
    with open(sdir / "scenes.json", "w", encoding="utf-8") as f:
        json.dump(scenes, f)

    transcript = [
        {"start": 0.0, "end": 3.0, "text": "Đừng bỏ qua sản phẩm này"},
        {"start": 3.0, "end": 10.0, "text": "Dùng thử thấy rất tiện"},
        {"start": 10.0, "end": 20.0, "text": "Mua ngay tại giỏ hàng"},
    ]
    with open(sdir / "transcript.vi.json", "w", encoding="utf-8") as f:
        json.dump(transcript, f)

    bp = analyze_video("soc-nho-tv", sid)

    assert bp.id == f"bp_{sid}"
    assert bp.duration_s == 20.0
    assert len(bp.beats) == 3
    assert bp.beats[0].role == "hook"
    assert bp.beats[-1].role == "cta"
    # Pacing: cuts per 10s -> (2 cuts / 20s) * 10 = 1.0
    assert bp.pacing_cuts_per_10s == 1.0
    assert bp.suggested_template_id in ["koc-review-v1", "tiktok-sales-v1", "affiliate-compare-v1"]
