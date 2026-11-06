"""E5 bước 5–6: chức năng Nói của node Nhân vật + bộ dựng nhận giọng nhiều nhân vật."""
from __future__ import annotations

import asyncio
import uuid
from collections import Counter

import pytest

from socnhotv.core.contracts.types import (
    Edge,
    Graph,
    GraphRunRequest,
    NodeInstance,
    RunMode,
)
from socnhotv.core.engine.dialogue_voice import (
    build_timeline,
    lines_for_character,
    timeline_to_srt,
)
from socnhotv.core.engine.graph_runner import GraphRunner
from socnhotv.core.engine.validator import validate_graph
from socnhotv.core.nodes.registry import NodeRegistry
from socnhotv.core.storage.project_store import ProjectStore

NOW = "2026-11-06T00:00:00Z"
EP01 = "ep01-nui-lua-trong-bung-bi"


class _A:  # artifact giả cho build_timeline
    def __init__(self, i):
        self.uri = f"assets/x{i}.wav"


def _clip(order, scene, dur, cid="soc_nho", speaker="Sóc Bi", text="câu"):
    return {"lineId": f"L{order}", "order": order, "sceneIndex": scene, "durationSec": dur,
            "characterId": cid, "speaker": speaker, "text": f"{text} {order}", "audio": _A(order)}


# ------------------------------------------------------------------ đơn vị
def test_lines_for_character():
    lines = [
        {"text": "a", "characterId": "soc_nho", "speaker": "Sóc Bi"},
        {"text": "b", "characterId": "de_mun", "speaker": "Dê Mun"},
        {"text": "c", "characterId": None, "speaker": "Bi"},  # chưa ghép -> khớp bí danh
        {"text": "d", "characterId": None, "speaker": "Ông Kẹ Bí Ẩn"},
        {"text": "", "characterId": "soc_nho"},
    ]
    got = [l["text"] for l in lines_for_character(lines, "soc_nho", ["soc nho", "Sóc Nhỏ", "Bi"])]
    assert got == ["a", "c"]


def test_build_timeline_orders_lines_without_overlap_and_extends_scene():
    scenes = [{"durationSec": 5.0}, {"durationSec": 2.0}]
    # 2 nhân vật nói cùng cảnh 0, đưa vào lộn thứ tự -> phải xếp theo 'order', nối tiếp, không chồng
    clips = [_clip(1, 0, 2.0, "de_mun", "Dê Mun"), _clip(0, 0, 1.5), _clip(2, 1, 4.0)]
    tl, sc, total = build_timeline(scenes, clips, gap_sec=0.5, lead_sec=0.3, tail_sec=0.6)
    assert [t["lineId"] for t in tl] == ["L0", "L1", "L2"]
    assert tl[0]["audioStartSec"] == 0.3 and tl[0]["audioEndSec"] == 1.8
    assert tl[1]["audioStartSec"] == 2.3  # sau câu trước + gap
    for a, b in zip(tl, tl[1:]):
        assert b["audioStartSec"] >= a["audioEndSec"]
    assert sc[0]["durationSec"] == 5.0  # giữ độ dài kịch bản (thoại vừa)
    assert sc[1]["startSec"] == 5.0
    assert sc[1]["durationSec"] == pytest.approx(0.3 + 4.0 + 0.6)  # thoại dài hơn -> kéo dài cảnh
    assert total == pytest.approx(5.0 + 4.9)


def test_build_timeline_voice_timing_and_orphans():
    scenes = [{"durationSec": 20.0}]
    clips = [_clip(0, 0, 1.0), _clip(1, None, 2.0)]
    tl, sc, total = build_timeline(scenes, clips, gap_sec=0.35, timing="voice")
    assert sc[0]["startSec"] == 0.0
    assert total < 10  # timing=voice: không giữ 20s của kịch bản
    assert tl[1]["audioStartSec"] >= tl[0]["audioEndSec"]
    srt = timeline_to_srt(tl)
    assert srt.startswith("1\n00:00:00,300 --> 00:00:01,300\nSóc Bi: câu 0")


def test_speak_capability_ports_and_validation():
    _, outs = NodeRegistry.effective_ports("character", {"characterId": "soc_nho", "speak": {"enabled": True}})
    ins, _ = NodeRegistry.effective_ports("character", {"characterId": "soc_nho", "speak": {"enabled": True}})
    assert "voice" in {p.name for p in outs} and "lines" in {p.name for p in ins}
    g = Graph(
        id="g", project_id="soc-nho-tv",
        nodes=[
            NodeInstance(id="s", type="script", params={"mode": "episode", "episodeId": EP01}),
            NodeInstance(id="c", type="character", params={"characterId": "soc_nho", "speak": {"enabled": True}}),
            NodeInstance(id="r", type="hyperframes_render", params={}),
        ],
        edges=[
            Edge(id="e1", source_node_id="s", source_port="lines", target_node_id="c", target_port="lines"),
            Edge(id="e2", source_node_id="c", source_port="voice", target_node_id="r", target_port="voice_clips"),
        ],
        updated_at=NOW,
    )
    res = validate_graph(g)
    assert res.is_valid, res.errors


# ------------------------------------------------------------------ chạy thật trên Tập 1 (mock)
def _ep_graph(gid, speak_extra=None):
    speak = {"enabled": True, **(speak_extra or {})}
    nodes = [NodeInstance(id="s", type="script", params={"mode": "episode", "episodeId": EP01, "granularity": "shot"})]
    edges = []
    for cid in ("soc_nho", "de_mun", "me_soc"):
        nodes.append(NodeInstance(id=f"c_{cid}", type="character", params={"characterId": cid, "speak": dict(speak)}))
        edges.append(Edge(id=f"e_{cid}", source_node_id="s", source_port="lines", target_node_id=f"c_{cid}", target_port="lines"))
    return Graph(id=gid, project_id="soc-nho-tv", nodes=nodes, edges=edges, updated_at=NOW)


def test_three_characters_speak_own_lines_with_line_cache(monkeypatch):
    async def _t():
        store = ProjectStore("soc-nho-tv")
        runner = GraphRunner(store)
        calls = []
        orig = runner._synthesize_line

        async def counting(text, voice_id, tempo, node_id, run_id, is_mock):
            calls.append((voice_id, text))
            return await orig(text, voice_id, tempo, node_id, run_id, is_mock)

        monkeypatch.setattr(runner, "_synthesize_line", counting)
        # tốc độ đọc ngẫu nhiên -> khoá cache từng câu mới, không đụng cache của lần chạy khác
        tempo = 1.0 + (uuid.uuid4().int % 1000) / 10000
        g = _ep_graph(f"test_e5_speak_{uuid.uuid4().hex[:6]}", {"tempo": tempo})
        s = await runner.run(g, GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.ALL, mock_mode=True))
        assert s.is_success, s.errors
        assert len(calls) == 30
        assert Counter(v for v, _ in calls) == {"soc-nho": 19, "vn-be-04": 6, "vn-nam-nu-01": 5}

        outs = {n.id: runner._load_outputs_snapshot(g.id, n, True) for n in g.nodes}
        bi = outs["c_soc_nho"]["voice"]
        assert len(bi) == 19 and all(c["characterId"] == "soc_nho" and c["durationSec"] > 0 for c in bi)
        assert len(outs["c_de_mun"]["voice"]) == 6 and len(outs["c_me_soc"]["voice"]) == 5

        # Đổi 1 câu của Mun trong kịch bản giả -> chỉ đọc lại 1 câu (cache từng câu)
        calls.clear()
        lines = runner._episode_lines(EP01)
        mun_idx = next(i for i, l in enumerate(lines) if l["characterId"] == "de_mun")
        lines[mun_idx] = {**lines[mun_idx], "text": lines[mun_idx]["text"] + " (sửa)"}
        mun = next(n for n in g.nodes if n.id == "c_de_mun")
        core = {"character": runner._character_info("de_mun")}
        out, _ = await runner._run_capabilities(g.id, mun, {"lines": lines}, core, "run_test", True)
        assert len(out["voice"]) == 6
        assert len(calls) == 1 and calls[0][1].endswith("(sửa)")

    asyncio.run(_t())


def test_render_dialogue_mixes_all_characters():
    async def _t():
        store = ProjectStore("soc-nho-tv")
        runner = GraphRunner(store)
        g = _ep_graph(f"test_e5_mix_{uuid.uuid4().hex[:6]}")
        s = await runner.run(g, GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.ALL, mock_mode=True))
        assert s.is_success, s.errors
        outs = {n.id: runner._load_outputs_snapshot(g.id, n, True) for n in g.nodes}
        clips = outs["c_soc_nho"]["voice"] + outs["c_de_mun"]["voice"] + outs["c_me_soc"]["voice"]
        scenes = outs["s"]["scenes"]
        render = NodeInstance(id="r", type="hyperframes_render", params={"timing": "voice"})
        new_scenes, voice_art, srt_art, tl = runner._render_dialogue(render, scenes, clips, "run_test_mix")
        assert len(tl) == 30 and len(new_scenes) == len(scenes) == 30
        assert [t["order"] for t in tl] == sorted(t["order"] for t in tl)
        for a, b in zip(tl, tl[1:]):
            assert b["audioStartSec"] >= a["audioEndSec"] - 1e-6
        total = voice_art.meta.duration
        assert total == pytest.approx(sum(sc["durationSec"] for sc in new_scenes), abs=0.05)
        from socnhotv.video.hyperframes_engine import HyperFramesEngine

        measured = HyperFramesEngine().get_audio_duration(store.project_dir / voice_art.uri)
        assert measured == pytest.approx(total, abs=0.3)
        srt = (store.project_dir / srt_art.uri).read_text(encoding="utf-8")
        assert srt.count(" --> ") == 30 and "Dê Mun:" in srt and "Mẹ Sóc:" in srt

    asyncio.run(_t())


# ------------------------------------------------------------------ cổng kiểm định chặn dựng video (E5)
def _gate_graph(gid, dialogue, block):
    return Graph(
        id=gid,
        project_id="soc-nho-tv",
        nodes=[
            NodeInstance(id="s", type="script", params={"mode": "paste", "rawScript": dialogue, "targetSceneCount": 2}),
            NodeInstance(id="q", type="quality_check", params={"blockOnFail": block}),
            NodeInstance(id="r", type="hyperframes_render", params={"aspectRatio": "16:9"}),
        ],
        edges=[
            Edge(id="e1", source_node_id="s", source_port="scenes", target_node_id="q", target_port="scenes"),
            Edge(id="e2", source_node_id="q", source_port="pass_fail", target_node_id="r", target_port="gate"),
        ],
        updated_at=NOW,
    )


def test_quality_gate_blocks_render_on_policy_violation():
    async def _t():
        runner = GraphRunner(ProjectStore("soc-nho-tv"))
        g = _gate_graph(f"test_gate_{uuid.uuid4().hex[:6]}", "Sóc Bi: Mình sẽ đánh nhau và đổ máu!", True)
        s = await runner.run(g, GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.ALL, mock_mode=True, max_retries=1))
        assert "q" in s.failed_nodes and "KHÔNG ĐẠT" in s.errors["q"]
        assert "r" not in s.executed_nodes  # không tốn công dựng video

    asyncio.run(_t())


def test_quality_gate_default_does_not_block_and_clean_script_passes():
    async def _t():
        runner = GraphRunner(ProjectStore("soc-nho-tv"))
        # không bật blockOnFail: giữ hành vi cũ (chỉ báo cáo)
        g = _gate_graph(f"test_gate_{uuid.uuid4().hex[:6]}", "Sóc Bi: Mình sẽ đánh nhau và đổ máu!", False)
        s = await runner.run(g, GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.ALL, mock_mode=True, max_retries=1))
        assert "q" in s.executed_nodes
        # kịch bản sạch + bật chặn: vẫn qua
        g2 = _gate_graph(f"test_gate_{uuid.uuid4().hex[:6]}", "Sóc Bi: Chào các bạn nhỏ, hôm nay mình xếp tháp gỗ.", True)
        s2 = await runner.run(g2, GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.ALL, mock_mode=True, max_retries=1))
        assert "q" in s2.executed_nodes and "q" not in s2.failed_nodes  # kịch bản sạch: cổng mở

    asyncio.run(_t())
