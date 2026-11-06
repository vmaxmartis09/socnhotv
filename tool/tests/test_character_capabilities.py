"""E5 bước 3–4: hồ sơ nhân vật thật, tìm giọng trong kho, kịch bản xuất lời thoại có người nói."""
from __future__ import annotations

import json
from collections import Counter

import pytest

from socnhotv.core.contracts.types import (
    Edge,
    Graph,
    NodeInstance,
    PortType,
    is_port_compatible,
)
from socnhotv.core.engine.character_profile import match_speaker, resolve_voice_id
from socnhotv.core.engine.graph_runner import GraphRunner
from socnhotv.core.engine.validator import validate_graph
from socnhotv.core.storage.project_store import ProjectStore

NOW = "2026-11-06T00:00:00Z"
EP01 = "ep01-nui-lua-trong-bung-bi"


# ------------------------------------------------------------------ tìm giọng trong kho
@pytest.fixture
def vault(tmp_path):
    def mk(vid, status="ready", aliases=()):
        d = tmp_path / vid
        d.mkdir()
        (d / "voice.json").write_text(json.dumps({"id": vid, "status": status, "aliases": list(aliases)}), encoding="utf-8")

    mk("soc-nho", aliases=["soc_nho", "soc_nho_v1", "bi"])
    mk("mun", status="todo_clone", aliases=["voice-mun", "be-mun"])
    mk("vn-be-04")
    return tmp_path


def test_resolve_voice_id_variants(vault):
    assert resolve_voice_id("soc-nho", "soc_nho", [], vault)[:2] == ("soc-nho", "ready")
    assert resolve_voice_id("soc_nho_v1", "soc_nho", [], vault)[:2] == ("soc-nho", "ready")  # bỏ _v1, đổi _ -> -
    assert resolve_voice_id(None, "soc_nho", [], vault)[:2] == ("soc-nho", "ready")  # theo id nhân vật
    assert resolve_voice_id("vn-be-04", "de_mun", [], vault)[:2] == ("vn-be-04", "ready")


def test_resolve_voice_id_not_ready_or_missing_never_falls_back_to_soc_nho(vault):
    vid, status, msg = resolve_voice_id("de_mun_v1", "de_mun", ["Dê Mun", "Mun"], vault)  # qua bí danh 'mun'
    assert vid is None and status == "todo_clone" and "mun" in msg
    vid, status, msg = resolve_voice_id("me_soc_v1", "me_soc", ["Mẹ Sóc"], vault)
    assert vid is None and status == "missing" and "me_soc" in msg


def test_match_speaker():
    profiles = [
        {"id": "soc_nho", "name": "Sóc Nhỏ (Bi)"},
        {"id": "de_mun", "name": "Dê Mun (Em Út)"},
        {"id": "me_soc", "name": "Mẹ Sóc (Mẹ của Bi)"},
        {"id": "de_bong", "name": "Dê Bông (Anh Cả)"},
    ]
    assert match_speaker("Sóc Bi (100cm)", profiles) == "soc_nho"
    assert match_speaker("Dê Mun", profiles) == "de_mun"
    assert match_speaker("Mẹ Sóc (145cm)", profiles) == "me_soc"
    assert match_speaker("Người dẫn chuyện", profiles) is None
    assert match_speaker("", profiles) is None


# ------------------------------------------------------------------ node nhân vật & giọng
def test_character_info_reads_real_profile():
    r = GraphRunner(ProjectStore("soc-nho-tv"))
    bi = r._character_info("soc_nho")
    mun = r._character_info("de_mun")
    assert bi["profileFound"] and bi["heightCm"] == 100 and bi["scaleLock"] == "100cm"
    assert mun["profileFound"] and mun["heightCm"] == 85
    assert mun["name"].startswith("Dê Mun")
    # Mun không còn bị gán giọng Sóc Nhỏ
    assert mun["voiceId"] != "soc-nho"
    assert "Dê Mun" in mun["aliases"]
    ghost = r._character_info("khong_ton_tai_xyz")
    assert ghost["profileFound"] is False and ghost["voiceId"] is None and ghost["voiceMessage"]


def test_voice_for_tts_rules():
    r = GraphRunner(ProjectStore("soc-nho-tv"))

    def node(**params):
        return NodeInstance(id="v", type="voice_tts", params={"text": "x", "voiceId": "soc-nho", **params})

    mun = {"characterId": "de_mun", "voiceId": "vn-be-04", "voiceStatus": "ready", "defaultVoice": "vn-be-04"}
    # nối nhân vật + voiceId mặc định của node -> giọng nhân vật
    assert r._voice_for_tts(node(), {"character": mun, "voiceId": "soc-nho"}) == "vn-be-04"
    # chọn tay giọng khác mặc định -> giọng chọn tay thắng
    assert r._voice_for_tts(node(voiceId="vn-be-01"), {"character": mun, "voiceId": "vn-be-01"}) == "vn-be-01"
    # ép dùng giọng chọn tay kể cả là soc-nho
    assert r._voice_for_tts(node(voiceSource="manual"), {"character": mun}) == "soc-nho"
    # nhân vật chưa có giọng -> báo lỗi rõ, không đọc bằng giọng Sóc Nhỏ
    me = {"characterId": "me_soc", "voiceId": None, "voiceStatus": "missing", "voiceMessage": "Mẹ Sóc chưa có giọng"}
    with pytest.raises(ValueError, match="Mẹ Sóc chưa có giọng"):
        r._voice_for_tts(node(), {"character": me})
    # hồ sơ kiểu cũ (không có voiceStatus) -> giữ cách cũ
    assert r._voice_for_tts(node(), {"character": {"characterId": "x", "defaultVoice": "koala-voice"}}) == "koala-voice"
    # không nối nhân vật -> như cũ
    assert r._voice_for_tts(node(), {"voiceId": "soc-nho"}) == "soc-nho"


# ------------------------------------------------------------------ kịch bản xuất lời thoại
def test_episode_lines_tap1():
    r = GraphRunner(ProjectStore("soc-nho-tv"))
    lines = r._episode_lines(EP01)
    assert len(lines) == 30
    assert Counter(l["characterId"] for l in lines) == {"soc_nho": 19, "de_mun": 6, "me_soc": 5}
    assert not any(l["unmatched"] for l in lines)
    first = lines[0]
    assert first["shotId"] == "S01" and first["startSec"] == 0 and first["text"]
    assert [l["order"] for l in lines] == list(range(30))
    # mỗi cảnh 1 ảnh: sceneIndex trỏ vào danh sách cảnh (10 cảnh)
    by_scene = r._episode_lines(EP01, "scene")
    assert max(l["sceneIndex"] for l in by_scene) == 9


def test_lines_from_pasted_dialogue():
    r = GraphRunner(ProjectStore("soc-nho-tv"))
    lines = r._lines_from_scenes(
        [
            {"dialogue": "Sóc Bi: Chào các bạn!\nMẹ Sóc: Con ăn chậm thôi nhé."},
            {"dialogue": "Hôm nay trời đẹp quá.", "speaker": "Dê Mun"},
            {"dialogue": "Ông Kẹ Bí Ẩn: Hù!"},
        ]
    )
    assert [(l["speaker"], l["characterId"], l["sceneIndex"]) for l in lines] == [
        ("Sóc Bi", "soc_nho", 0),
        ("Mẹ Sóc", "me_soc", 0),
        ("Dê Mun", "de_mun", 1),
        ("Ông Kẹ Bí Ẩn", None, 2),
    ]
    assert lines[-1]["unmatched"] is True and lines[0]["unmatched"] is False


def test_dialogue_port_feeds_text_port():
    assert is_port_compatible(PortType.DIALOGUE, PortType.TEXT)
    assert not is_port_compatible(PortType.TEXT, PortType.DIALOGUE)
    r = GraphRunner(ProjectStore("soc-nho-tv"))
    g = Graph(
        id="g",
        project_id="soc-nho-tv",
        nodes=[
            NodeInstance(id="s", type="script", params={"mode": "episode", "episodeId": EP01}),
            NodeInstance(id="v", type="voice_tts", params={}),
        ],
        edges=[Edge(id="e", source_node_id="s", source_port="lines", target_node_id="v", target_port="text")],
        updated_at=NOW,
    )
    assert validate_graph(g).is_valid
    lines = [{"speaker": "Sóc Bi", "text": "Chào!"}, {"speaker": "", "text": "Kể chuyện."}]
    resolved = r._gather_node_inputs(g.nodes[1], g, {"s": {"lines": lines}})
    assert resolved["text"] == "Sóc Bi: Chào!\nKể chuyện."
