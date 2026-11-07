"""I4 — node template_render chạy thật trong graph (không còn nhánh mock 'Generic execution')."""
from __future__ import annotations

import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from socnhotv.core.api.app import app
from socnhotv.core.nodes.registry import NodeRegistry
from socnhotv.video.hyperframes_engine import FFMPEG_EXE, find_hyperframes_bin

pytestmark = pytest.mark.skipif(not (find_hyperframes_bin() and shutil.which("ffprobe")), reason="cần hyperframes + ffprobe")


def _graph(with_audio: bool):
    n = lambda i, t, p: {"id": i, "type": t, "position": {"x": 0, "y": 0}, "params": p}  # noqa: E731
    e = lambda i, s, sp, t, tp: {"id": i, "sourceNodeId": s, "sourcePort": sp, "targetNodeId": t, "targetPort": tp}  # noqa: E731
    return {
        "id": "g_i4_node", "projectId": "soc-nho-tv", "updatedAt": "2026-11-07T00:00:00Z",
        "nodes": [
            n("t", "text", {"content": "Bạn có biết không"}),
            n("v", "voice_tts", {"voiceId": "soc-nho"}),
            n("r", "template_render", {"template_id": "shorts-fact-v1", "platforms": ["tiktok"],
                                       "slot_mapping": {"fact_question": "CÂU HỎI", "fact_statement": "Sự thật"}}),
            n("x", "platform_export", {"target_platforms": ["tiktok"]}),
        ],
        "edges": [e("e1", "t", "text", "v", "text")]
        + ([e("e2", "v", "audio", "r", "audio")] if with_audio else [])
        + [e("e3", "r", "video", "x", "video")],
    }


def test_template_render_outputs_real_mp4_not_mock_image():
    NodeRegistry.initialize_defaults()
    c = TestClient(app)
    r = c.post("/projects/soc-nho-tv/run", json={"graph": _graph(True), "mode": "force_all", "mockMode": True})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["isSuccess"], body
    import json
    import conftest

    snap = json.loads((conftest.SANDBOX_ROOT / "data/projects/soc-nho-tv/runs/_node_outputs/g_i4_node/r.json").read_text())
    art = snap["outputs"]["video"]["$artifact"]
    assert art["kind"] == "video" and art["uri"].endswith(".mp4"), art
    assert art["provenance"]["provider"] == "local" and art["meta"]["width"] == 1080
    assert (conftest.SANDBOX_ROOT / "data/projects/soc-nho-tv" / art["uri"]).stat().st_size > 20_000


def test_unknown_template_fails_loudly():
    NodeRegistry.initialize_defaults()
    g = _graph(False)
    g["nodes"][2]["params"]["template_id"] = "khong-ton-tai-v9"
    r = TestClient(app).post("/projects/soc-nho-tv/run", json={"graph": g, "mode": "force_all", "mockMode": True})
    body = r.json()
    assert r.status_code != 200 or not body.get("isSuccess"), body
