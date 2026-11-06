"""Lặp theo cảnh (image_gen nối cổng 'scenes'), cổng nhiều dây, và chế độ 'Kịch bản tập' của node script.

Mục tiêu kèm theo: hành vi cũ không đổi khi không dùng tính năng mới.
"""
from __future__ import annotations

import asyncio
import json
import shutil
import time
from pathlib import Path

import pytest

from socnhotv.core.contracts.types import Edge, Graph, GraphRunRequest, NodeInstance, RunMode
from socnhotv.core.engine.graph_runner import GraphRunner, _name_tokens, _refs_for_scene
from socnhotv.core.engine.validator import validate_graph
from socnhotv.core.models_registry.registry import ModelRegistry
from socnhotv.core.nodes.registry import NodeRegistry
from socnhotv.core.providers.mock_provider import MockProvider
from socnhotv.core.storage.project_store import ProjectStore

REPO = Path(__file__).resolve().parents[2]
EP01 = REPO / "data/projects/soc-nho-tv/content/episodes/ep01-nui-lua-trong-bung-bi"
CHARS = REPO / "data/projects/soc-nho-tv/characters/studio_characters.json"
PID = "test-scene-batch"


@pytest.fixture(autouse=True)
def _registry():
    NodeRegistry.initialize_defaults()


@pytest.fixture()
def store(tmp_path: Path) -> ProjectStore:
    st = ProjectStore(PID, repo_root=tmp_path)
    if EP01.is_dir():
        dst = st.content_dir / "episodes" / EP01.name
        dst.mkdir(parents=True, exist_ok=True)
        for f in EP01.glob("KICH*.md"):
            shutil.copy2(f, dst / f.name)
    st.characters_dir.mkdir(parents=True, exist_ok=True)
    (st.characters_dir / "studio_characters.json").write_text(
        json.dumps(
            [
                {"id": "soc_nho", "name": "Sóc Nhỏ (Bi)"},
                {"id": "de_mun", "name": "Dê Mun (Em Út)"},
                {"id": "me_soc", "name": "Mẹ Sóc (Mẹ của Bi)"},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return st


def _graph(nodes, edges) -> Graph:
    return Graph(
        id="g", project_id=PID, nodes=nodes, edges=edges,
        updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


def _e(i, s, sp, t, tp) -> Edge:
    return Edge(id=i, source_node_id=s, source_port=sp, target_node_id=t, target_port=tp)


def _runner(store: ProjectStore) -> GraphRunner:
    return GraphRunner(store=store, model_registry=ModelRegistry(), provider=MockProvider(store=store))


# ---------------------------------------------------------------- khớp tên nhân vật

def test_name_tokens_strip_accents_and_height():
    assert _name_tokens("Sóc Bi (100cm)") == {"soc", "bi"}
    assert _name_tokens("Dê Mun") == {"de", "mun"}
    assert _name_tokens("Đức") == {"duc"}


class _Art:
    def __init__(self, uri, aliases):
        self.uri = uri
        self.provenance = type("P", (), {"params": {"characterAliases": aliases}})()


def test_refs_for_scene_picks_only_present_characters():
    bi = _Art("bi.png", ["soc nho", "Sóc Nhỏ", "Bi"])
    mun = _Art("mun.png", ["de mun", "Dê Mun", "Em Út"])
    me = _Art("me.png", ["me soc", "Mẹ Sóc", "Mẹ của Bi"])
    refs = [bi, mun, me]
    assert _refs_for_scene(refs, ["Sóc Bi (100cm)"]) == ["bi.png"]
    assert _refs_for_scene(refs, ["Sóc Bi (100cm)", "Dê Mun (85cm)"]) == ["bi.png", "mun.png"]
    assert _refs_for_scene(refs, ["Mẹ Sóc (145cm)"]) == ["me.png"]
    # Không ghi nhân vật / không khớp ai / ảnh chưa gắn nhân vật -> [] (nơi gọi dùng tất cả như cũ)
    assert _refs_for_scene(refs, []) == []
    assert _refs_for_scene(refs, ["Bác Voi"]) == []
    assert _refs_for_scene([_Art("x.png", [])], ["Sóc Bi"]) == []


# ---------------------------------------------------------------- cổng nhiều dây

def test_multi_edges_into_list_port_are_merged_not_overwritten(store):
    runner = _runner(store)
    node = NodeInstance(id="img", type="image_gen", params={})
    g = _graph(
        [NodeInstance(id="a", type="character"), NodeInstance(id="b", type="character"), node],
        [_e("e1", "a", "reference_images", "img", "references"), _e("e2", "b", "reference_images", "img", "references")],
    )
    outs = {"a": {"reference_images": ["A1", "A2"]}, "b": {"reference_images": ["B1"]}}
    res = runner._gather_node_inputs(node, g, outs)
    assert res["references"] == ["A1", "A2", "B1"]


def test_single_value_port_keeps_last_edge_wins(store):
    runner = _runner(store)
    node = NodeInstance(id="img", type="image_gen", params={})
    g = _graph(
        [NodeInstance(id="t1", type="text"), NodeInstance(id="t2", type="text"), node],
        [_e("e1", "t1", "text", "img", "prompt"), _e("e2", "t2", "text", "img", "prompt")],
    )
    res = runner._gather_node_inputs(node, g, {"t1": {"text": "một"}, "t2": {"text": "hai"}})
    assert res["prompt"] == "hai"


def test_single_edge_into_list_port_unchanged(store):
    runner = _runner(store)
    node = NodeInstance(id="r", type="hyperframes_render", params={})
    g = _graph([NodeInstance(id="s", type="scene"), node], [_e("e1", "s", "scenes", "r", "scenes")])
    res = runner._gather_node_inputs(node, g, {"s": {"scenes": [{"sceneNumber": 1}]}})
    assert res["scenes"] == [{"sceneNumber": 1}]


# ---------------------------------------------------------------- kịch bản tập

@pytest.mark.skipif(not EP01.is_dir(), reason="thiếu kịch bản Tập 1")
def test_episode_scenes_shot_and_scene_granularity(store):
    runner = _runner(store)
    shots, title = runner._episode_scenes(EP01.name, "shot")
    assert len(shots) == 30
    assert shots[0]["imagePrompt"] and shots[0]["characters"]
    scenes, _ = runner._episode_scenes(EP01.name, "scene")
    assert len(scenes) == 10
    assert abs(sum(s["durationSec"] for s in scenes) - 600) < 1
    assert "Dê Mun" in " ".join(scenes[0]["characters"])


# ---------------------------------------------------------------- chạy đồ thị đầu-cuối (mock)

@pytest.mark.skipif(not EP01.is_dir(), reason="thiếu kịch bản Tập 1")
def test_batch_image_gen_one_image_per_scene_end_to_end(store):
    nodes = [
        NodeInstance(id="sc", type="script", params={"mode": "episode", "episodeId": EP01.name, "granularity": "scene"}),
        NodeInstance(id="bi", type="character", params={"characterId": "soc_nho"}),
        NodeInstance(id="mun", type="character", params={"characterId": "de_mun"}),
        NodeInstance(id="me", type="character", params={"characterId": "me_soc"}),
        NodeInstance(id="kf", type="image_gen", params={"model": "mock-image", "aspectRatio": "16:9"}),
    ]
    edges = [
        _e("e1", "sc", "scenes", "kf", "scenes"),
        _e("e2", "bi", "reference_images", "kf", "references"),
        _e("e3", "mun", "reference_images", "kf", "references"),
        _e("e4", "me", "reference_images", "kf", "references"),
    ]
    g = _graph(nodes, edges)
    v = validate_graph(g)
    assert v.is_valid, v.errors
    assert not any("ý tưởng" in w for w in v.warnings)

    runner = _runner(store)
    captured = {}
    orig = runner._execute_node_handler

    async def spy(node, resolved_inputs, run_id, is_mock=True, all_node_outputs=None):
        out = await orig(node, resolved_inputs, run_id, is_mock=is_mock, all_node_outputs=all_node_outputs)
        captured[node.id] = (resolved_inputs, out[0])
        return out

    runner._execute_node_handler = spy  # type: ignore[assignment]
    summary = asyncio.run(runner.run(g, GraphRunRequest(project_id=PID, mode=RunMode.ALL, mock_mode=True)))
    assert summary.is_success, summary.errors

    _, kf_out = captured["kf"]
    assert len(kf_out["images"]) == 10
    assert len(kf_out["scenes"]) == 10
    for sc in kf_out["scenes"]:
        assert Path(sc["image"]).is_file()
        assert sc["imageUri"]
    # Đủ ảnh tham chiếu của cả 3 nhân vật (không bị dây sau ghi đè)
    kf_in, _ = captured["kf"]
    assert len(kf_in["references"]) == 6  # 3 nhân vật x 2 ảnh mock


def test_image_gen_without_scenes_behaves_as_before(store):
    g = _graph([NodeInstance(id="kf", type="image_gen", params={"prompt": "Bi vẫy tay", "n": 2})], [])
    runner = _runner(store)
    captured = {}
    orig = runner._execute_node_handler

    async def spy(node, resolved_inputs, run_id, is_mock=True, all_node_outputs=None):
        out = await orig(node, resolved_inputs, run_id, is_mock=is_mock, all_node_outputs=all_node_outputs)
        captured[node.id] = out[0]
        return out

    runner._execute_node_handler = spy  # type: ignore[assignment]
    summary = asyncio.run(runner.run(g, GraphRunRequest(project_id=PID, mode=RunMode.ALL, mock_mode=True)))
    assert summary.is_success
    assert len(captured["kf"]["images"]) == 2
    assert "scenes" not in captured["kf"]


@pytest.mark.skipif(not EP01.is_dir(), reason="thiếu kịch bản Tập 1")
def test_cost_estimate_multiplies_by_scene_count(store):
    nodes = [
        NodeInstance(id="sc", type="script", params={"mode": "episode", "episodeId": EP01.name, "granularity": "shot"}),
        NodeInstance(id="kf", type="image_gen", params={"model": "gemini-2.5-flash-image"}),
    ]
    g = _graph(nodes, [_e("e1", "sc", "scenes", "kf", "scenes")])
    runner = _runner(store)
    one = runner.estimate_node_cost(nodes[1], real_mode=True)
    total = runner.estimate_graph_cost(g, ["sc", "kf"], real_mode=True)
    assert one > 0
    assert abs(total - one * 30) < 1e-6


# ---------------------------------------------------------------- ảnh chụp cổng ra (cache đầy đủ)

@pytest.mark.skipif(not EP01.is_dir(), reason="thiếu kịch bản Tập 1")
def test_cached_upstream_keeps_structured_outputs_on_next_run(store):
    """Lần chạy 2 không chạy lại Kịch bản/Keyframe nhưng node sau vẫn nhận đủ danh sách cảnh."""
    nodes = [
        NodeInstance(id="sc", type="script", params={"mode": "episode", "episodeId": EP01.name, "granularity": "scene"}),
        NodeInstance(id="kf", type="image_gen", params={"model": "mock-image"}),
    ]
    g = _graph(nodes, [_e("e1", "sc", "scenes", "kf", "scenes")])
    runner = _runner(store)
    assert asyncio.run(runner.run(g, GraphRunRequest(project_id=PID, mode=RunMode.ALL, mock_mode=True))).is_success

    # Thêm node chuyển cảnh phía sau rồi chỉ chạy node đó
    g.nodes.append(NodeInstance(id="tr", type="transition", params={"style": "fade"}))
    g.edges.append(_e("e2", "kf", "scenes", "tr", "scenes"))
    runner2 = _runner(store)
    captured = {}
    orig = runner2._execute_node_handler

    async def spy(node, resolved_inputs, run_id, is_mock=True, all_node_outputs=None):
        out = await orig(node, resolved_inputs, run_id, is_mock=is_mock, all_node_outputs=all_node_outputs)
        captured[node.id] = (resolved_inputs, out[0])
        return out

    runner2._execute_node_handler = spy  # type: ignore[assignment]
    s2 = asyncio.run(
        runner2.run(g, GraphRunRequest(project_id=PID, mode=RunMode.SINGLE_NODE, target_node_id="tr", mock_mode=True))
    )
    assert s2.is_success, s2.errors
    assert set(captured) == {"tr"}  # không chạy lại node trên
    tr_in, tr_out = captured["tr"]
    assert len(tr_in["scenes"]) == 10
    assert all(sc.get("imageUri") for sc in tr_out["scenes"])


def test_snapshot_invalid_when_params_or_mode_change(store):
    from socnhotv.core.contracts.types import Artifact

    runner = _runner(store)
    node = NodeInstance(id="n1", type="image_gen", params={"prompt": "a"})
    art = asyncio.run(MockProvider(store=store).generate_images(prompt="x", node_id="n1", run_id="r", n=1))[0]
    art.provenance.params = {**(art.provenance.params or {}), "characterAliases": ["Bi"]}
    runner._save_outputs_snapshot("g", node, {"image": art, "scenes": [{"imageUri": art.uri}], "n": 3}, True)

    got = runner._load_outputs_snapshot("g", node, True)
    assert isinstance(got["image"], Artifact) and got["image"].uri == art.uri
    assert got["image"].provenance.params["characterAliases"] == ["Bi"]
    assert got["scenes"] == [{"imageUri": art.uri}] and got["n"] == 3
    assert runner._load_outputs_snapshot("g", node, False) is None  # khác chế độ mock/thật
    node.params["prompt"] = "b"
    assert runner._load_outputs_snapshot("g", node, True) is None  # đổi tham số
