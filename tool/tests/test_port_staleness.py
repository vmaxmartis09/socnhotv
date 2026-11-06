"""E5 bước 1–2: lỗi thời theo từng cổng ra + khung chức năng bật/tắt trong node."""
from __future__ import annotations

import asyncio
import time
import uuid

import pytest

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactProvenance,
    CapabilityDefinition,
    Edge,
    Graph,
    GraphRunRequest,
    NodeInstance,
    PortDefinition,
    PortType,
    RunMode,
)
from socnhotv.core.engine.graph_runner import GraphRunner, _port_signature
from socnhotv.core.engine.validator import validate_graph
from socnhotv.core.nodes.capabilities import CapabilityRuntime, register_capability, unregister_capability
from socnhotv.core.nodes.registry import NodeRegistry
from socnhotv.core.storage.project_store import ProjectStore

NOW = "2026-11-06T00:00:00Z"


def _art(art_id: str, run_id: str) -> Artifact:
    return Artifact(
        id=art_id,
        kind=ArtifactKind.IMAGE,
        uri=f"assets/{art_id}.png",
        mime="image/png",
        size=1,
        hash=art_id,
        provenance=ArtifactProvenance(
            node_id="n", run_id=run_id, provider="mock", model="m", params={"run": run_id}, cost_usd=0.0, created_at=NOW
        ),
    )


# ------------------------------------------------------------------ chữ ký cổng ra
def test_port_signature_ignores_provenance():
    assert _port_signature(_art("art_a", "r1")) == _port_signature(_art("art_a", "r2"))
    assert _port_signature([_art("art_a", "r1")]) != _port_signature([_art("art_b", "r1")])
    assert _port_signature({"x": 1}) == _port_signature({"x": 1})
    assert _port_signature("a") != _port_signature("b")


def test_changed_ports_and_children():
    runner = GraphRunner(ProjectStore("soc-nho-tv"))
    outs = {"text": "giống", "loud": "KHÁC"}
    prev = {"text": _port_signature("giống"), "loud": _port_signature("cũ")}
    assert GraphRunner._changed_ports(None, outs) is None
    assert GraphRunner._changed_ports(prev, outs) == {"loud"}

    g = Graph(
        id="g",
        project_id="soc-nho-tv",
        nodes=[NodeInstance(id=i, type="text") for i in ("a", "b", "c", "d")],
        edges=[
            Edge(id="e1", source_node_id="a", source_port="text", target_node_id="b", target_port="text"),
            Edge(id="e2", source_node_id="a", source_port="loud", target_node_id="c", target_port="text"),
            Edge(id="e3", source_node_id="a", source_port="khong_co", target_node_id="d", target_port="text"),
        ],
        updated_at=NOW,
    )
    # chỉ con nối cổng đổi + con nối cổng không có trong kết quả (cho chắc)
    assert runner._children_to_mark_stale(g, "a", {"loud"}, outs) == {"c", "d"}
    # chưa có lần trước -> đánh dấu tất cả như cũ
    assert runner._children_to_mark_stale(g, "a", None, outs) == {"b", "c", "d"}


# ------------------------------------------------------------------ khung chức năng (dùng chức năng thử "shout")
SHOUT = CapabilityDefinition(
    name="shout",
    display_name="Hét to",
    description="Chức năng thử: viết hoa nội dung + hậu tố",
    output_ports=[PortDefinition(name="loud", port_type=PortType.TEXT, description="Nội dung viết hoa")],
    default_params={"suffix": "!"},
)


class _ShoutRuntime(CapabilityRuntime):
    def __init__(self):
        self.calls = 0

    def cache_inputs(self, node, resolved_inputs, definition):
        return {"content": node.params.get("content")}

    def estimate_cost(self, node, params, runner, real_mode):
        return 0.5 if real_mode else 0.0

    async def run(self, runner, node, params, resolved_inputs, core_outputs, run_id, is_mock):
        self.calls += 1
        return {"loud": str(core_outputs.get("text", "")).upper() + str(params.get("suffix", ""))}, 0.0


@pytest.fixture
def shout():
    rt = _ShoutRuntime()
    register_capability("text", SHOUT, rt)
    try:
        yield rt
    finally:
        unregister_capability("text", "shout")


def test_effective_ports_follow_enabled_capability(shout):
    _, outs_off = NodeRegistry.effective_ports("text", {"content": "x"})
    _, outs_on = NodeRegistry.effective_ports("text", {"content": "x", "shout": {"enabled": True}})
    assert "loud" not in {p.name for p in outs_off}
    assert "loud" in {p.name for p in outs_on}
    # ghi đè _ports vẫn thắng
    _, outs_override = NodeRegistry.effective_ports(
        "text",
        {"shout": {"enabled": True}, "_ports": {"outputs": [{"name": "only", "portType": "text"}]}},
    )
    assert [p.name for p in outs_override] == ["only"]


def test_validator_capability_rules(shout):
    def graph(params):
        return Graph(
            id="g",
            project_id="soc-nho-tv",
            nodes=[NodeInstance(id="t", type="text", params=params), NodeInstance(id="s", type="script", params={"mode": "ai"})],
            edges=[Edge(id="e", source_node_id="t", source_port="loud", target_node_id="s", target_port="text")],
            updated_at=NOW,
        )

    off = validate_graph(graph({"content": "x"}))
    assert not off.is_valid
    assert any("Hét to" in e and "đang tắt" in e for e in off.errors)  # dây giữ nguyên, chỉ báo rõ

    on = validate_graph(graph({"content": "x", "shout": {"enabled": True}}))
    assert on.is_valid, on.errors

    # chức năng khai báo nhưng chưa có bộ chạy -> không cho bật
    register_capability("text", SHOUT.model_copy(update={"available": False}), shout)
    try:
        bad = validate_graph(graph({"content": "x", "shout": {"enabled": True}}))
        assert any("chưa sẵn sàng" in e for e in bad.errors)
    finally:
        register_capability("text", SHOUT, shout)


def test_capability_run_cache_and_per_port_stale(shout):
    """Đổi tham số chức năng: chỉ con nối cổng của chức năng bị lỗi thời; chạy lại y hệt thì dùng cache."""

    async def _t():
        runner = GraphRunner(ProjectStore("soc-nho-tv"))
        gid = f"test_e5_{uuid.uuid4().hex[:6]}"
        t = NodeInstance(id="t", type="text", params={"content": "chào bé", "shout": {"enabled": True}})
        s1 = NodeInstance(id="s1", type="script", params={"mode": "ai"})
        s2 = NodeInstance(id="s2", type="script", params={"mode": "ai"})
        g = Graph(
            id=gid,
            project_id="soc-nho-tv",
            nodes=[t, s1, s2],
            edges=[
                Edge(id="e1", source_node_id="t", source_port="text", target_node_id="s1", target_port="text"),
                Edge(id="e2", source_node_id="t", source_port="loud", target_node_id="s2", target_port="text"),
            ],
            updated_at=NOW,
        )
        first = await runner.run(g, GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.ALL))
        assert first.is_success, first.errors
        assert shout.calls == 1
        assert not s1.is_stale and not s2.is_stale

        single = GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.SINGLE_NODE, target_node_id="t")
        # chạy lại y hệt: chức năng lấy cache, không con nào lỗi thời
        same = await runner.run(g, single)
        assert same.is_success and shout.calls == 1
        assert same.stale_nodes == []
        assert not s1.is_stale and not s2.is_stale

        # đổi tham số chức năng: chỉ cổng 'loud' đổi -> chỉ s2 lỗi thời
        t.params = {**t.params, "shout": {"enabled": True, "suffix": "!!!"}}
        changed = await runner.run(g, single)
        assert changed.is_success and shout.calls == 2
        assert changed.stale_nodes == ["s2"]
        assert s2.is_stale is True and s1.is_stale is False

    asyncio.run(_t())


def test_capability_cost_added_to_estimate(shout):
    runner = GraphRunner(ProjectStore("soc-nho-tv"))
    g = Graph(
        id="g",
        project_id="soc-nho-tv",
        nodes=[NodeInstance(id="t", type="text", params={"content": "x", "shout": {"enabled": True}})],
        edges=[],
        updated_at=NOW,
    )
    base = runner.estimate_node_cost(g.nodes[0], real_mode=True)
    assert runner.estimate_graph_cost(g, ["t"], real_mode=True) == pytest.approx(base + 0.5)
    assert runner.estimate_graph_cost(g, ["t"], real_mode=False) == pytest.approx(
        runner.estimate_node_cost(g.nodes[0], real_mode=False)
    )
