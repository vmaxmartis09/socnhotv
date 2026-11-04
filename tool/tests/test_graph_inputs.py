import pytest
import asyncio
from socnhotv.core.contracts.types import Graph, NodeInstance, Edge, GraphRunRequest, RunMode
from socnhotv.core.engine.graph_runner import GraphRunner
from socnhotv.core.engine.validator import validate_graph
from socnhotv.core.providers.mock_provider import MockProvider
from socnhotv.core.storage.project_store import ProjectStore


def test_validator_with_script_paste_mode():
    # 1. Script paste mode with empty rawScript -> should warn
    node_script_empty = NodeInstance(
        id="s1",
        type="script",
        params={"mode": "paste", "rawScript": ""}
    )
    graph1 = Graph(
        id="g1",
        project_id="soc-nho-tv",
        nodes=[node_script_empty],
        edges=[],
        updated_at="2026-11-04T00:00:00Z"
    )
    val1 = validate_graph(graph1)
    assert any("rawScript rỗng" in w for w in val1.warnings)

    # 2. Script paste mode with content -> valid, no rawScript warning
    node_script_ok = NodeInstance(
        id="s2",
        type="script",
        params={
            "mode": "paste",
            "rawScript": "Cảnh 1: Khởi hành\nBi: Chào các bạn nhỏ!\n\nCảnh 2: Khám phá\nBi: Đẹp quá!"
        }
    )
    graph2 = Graph(
        id="g2",
        project_id="soc-nho-tv",
        nodes=[node_script_ok],
        edges=[],
        updated_at="2026-11-04T00:00:00Z"
    )
    val2 = validate_graph(graph2)
    assert not any("rawScript rỗng" in w for w in val2.warnings)


@pytest.mark.anyio
async def test_graph_runner_script_paste_mode():
    store = ProjectStore("soc-nho-tv")
    provider = MockProvider(store=store)
    runner = GraphRunner(store=store, provider=provider)

    raw_script_text = """
Cảnh 1: Bữa sáng ngọt ngào
(Sóc Bi cầm chiếc kẹo mút)
Sóc Nhỏ: Chào các bạn, mình là Sóc Bi! Hôm nay mình sẽ ăn thật nhiều kẹo!

Cảnh 2: Lời khuyên của bạn Koala
Bác sĩ Koala: Bi ơi, ăn xong nhớ chải răng nhé!
Sóc Nhỏ: Bi nhớ rồi ạ!
"""

    node_script = NodeInstance(
        id="node_script",
        type="script",
        params={
            "mode": "paste",
            "rawScript": raw_script_text,
            "targetSceneCount": 2,
            "targetDurationSec": 15,
        }
    )

    node_voice = NodeInstance(
        id="node_voice",
        type="voice_tts",
        params={"voiceId": "soc-nho"}
    )

    edge = Edge(
        id="e1",
        source_node_id="node_script",
        source_port="dialogue",
        target_node_id="node_voice",
        target_port="text"
    )

    graph = Graph(
        id="g_paste_test",
        project_id="soc-nho-tv",
        nodes=[node_script, node_voice],
        edges=[edge],
        updated_at="2026-11-04T00:00:00Z"
    )

    req = GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.ALL)
    summary = await runner.run(graph, req)
    assert summary.is_success is True
    assert "node_script" in summary.executed_nodes
    assert "node_voice" in summary.executed_nodes
    assert summary.total_cost_usd == 0.0


def test_api_run_graph_mock_script_paste_mode():
    """Test API FastAPI chạy đồ thị mock có script.mode='paste'."""
    from fastapi.testclient import TestClient
    from socnhotv.core.api.app import app

    client = TestClient(app)

    raw_script = """
Cảnh 1: Khởi động ngày mới
Sóc Nhỏ: Chào buổi sáng cả nhà!
(Bi nhảy chân sáo)

Cảnh 2: Khám phá rừng xanh
Bi: Hôm nay trời thật trong xanh!
"""

    graph_payload = {
        "id": "graph_api_paste_test",
        "projectId": "soc-nho-tv",
        "nodes": [
            {
                "id": "node_text_in",
                "type": "text",
                "params": {"content": "Chuyến phiêu lưu của Bi"},
                "inputs": {},
            },
            {
                "id": "node_script_paste",
                "type": "script",
                "params": {
                    "mode": "paste",
                    "rawScript": raw_script,
                    "targetSceneCount": 2,
                    "targetDurationSec": 10,
                },
                "inputs": {},
            },
            {
                "id": "node_voice_out",
                "type": "voice_tts",
                "params": {"voiceId": "soc-nho"},
                "inputs": {},
            },
            {
                "id": "node_render_out",
                "type": "hyperframes_render",
                "params": {"templateId": "default_cartoon", "platform": "tiktok"},
                "inputs": {},
            },
            {
                "id": "node_export_out",
                "type": "export",
                "params": {"outputFileName": "api_test_paste.mp4", "platforms": ["tiktok"]},
                "inputs": {},
            },
        ],
        "edges": [
            {
                "id": "e_s_v",
                "sourceNodeId": "node_script_paste",
                "sourcePort": "dialogue",
                "targetNodeId": "node_voice_out",
                "targetPort": "text",
            },
            {
                "id": "e_s_r",
                "sourceNodeId": "node_script_paste",
                "sourcePort": "scenes",
                "targetNodeId": "node_render_out",
                "targetPort": "scenes",
            },
            {
                "id": "e_v_r",
                "sourceNodeId": "node_voice_out",
                "sourcePort": "audio",
                "targetNodeId": "node_render_out",
                "targetPort": "audio",
            },
            {
                "id": "e_r_exp",
                "sourceNodeId": "node_render_out",
                "sourcePort": "video",
                "targetNodeId": "node_export_out",
                "targetPort": "video",
            },
        ],
        "updatedAt": "2026-11-04T00:00:00Z",
    }

    # 1. Chạy đồ thị ở chế độ mock qua API (truyền graph trực tiếp)
    res_run = client.post(
        "/projects/soc-nho-tv/run",
        json={"mode": "force_all", "mockMode": True, "graph": graph_payload},
    )
    assert res_run.status_code == 200
    data = res_run.json()
    assert data["isSuccess"] is True
    assert "node_script_paste" in data["executedNodes"]
    assert "node_voice_out" in data["executedNodes"]
    assert "node_render_out" in data["executedNodes"]
    assert "node_export_out" in data["executedNodes"]
    assert data["totalCostUsd"] == 0.0
