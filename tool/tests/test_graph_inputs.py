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
