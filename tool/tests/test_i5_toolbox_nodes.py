"""I5: node plugin Toolbox (core/nodes/plugins/toolbox.py).

- Đăng ký, cổng, tham số mặc định, danh mục hiển thị trong menu 'Thêm node'.
- Ánh xạ đầu ra công cụ -> Artifact (runner giả, không cần venv/weights).
- `run_tool`: gọi tiến trình con đúng hợp đồng, lỗi thật được báo (mã thoát 2/3, thiếu out.json).
- Chạy công cụ THẬT (scene-cut, handdraw) chỉ khi đặt SOCNHOTV_TOOLBOX_REAL=1: các công cụ ghi vào data/shared thật.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from socnhotv.core.contracts.types import Artifact, ArtifactKind, PortType
from socnhotv.core.nodes import registry as registry_mod
from socnhotv.core.nodes.plugins import toolbox as tb
from socnhotv.core.storage.project_store import ProjectStore

NODES = ["bg_remove", "word_captions", "scene_cut", "depth_layers", "handdraw", "voice_clone"]
# Các danh mục có khoá dịch trong messages/*.json ("categories.<tên>")
I18N_CATEGORIES = {"Input", "Identity", "Structure", "Intelligence", "Generation", "Audio", "Quality", "Composition", "Output"}
# Danh sách ẩn khỏi menu trong StudioCanvas.tsx (HIDDEN_NODE_TYPES)
HIDDEN_IN_MENU = {"source_video", "localize", "blueprint_analyze", "script_from_blueprint", "channel_insight"}


@pytest.fixture
def store(tmp_path):
    return ProjectStore("i5-test", repo_root=tmp_path)


def _png(path: Path, size=(64, 48)) -> Path:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", size, (200, 120, 40, 255)).save(path)
    return path


def _file(path: Path, data: bytes = b"x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _art(store, path: Path, kind: ArtifactKind) -> Artifact:
    from socnhotv.core.contracts.types import ArtifactProvenance

    prov = ArtifactProvenance(node_id="up", run_id="r0", provider="t", model="t", params={}, cost_usd=0.0, created_at="2026-01-01T00:00:00Z")
    return store.store_bytes(data=path.read_bytes(), ext=path.suffix.lstrip("."), kind=kind, provenance=prov)


class FakeRunner:
    """Giả `run_tool`: ghi lại lời gọi và trả out.json theo kịch bản."""

    def __init__(self, outputs):
        self.outputs, self.calls = outputs, []

    def __call__(self, tool_id, inputs, params, *, dry_run=False, project=None, timeout=None):
        self.calls.append({"tool": tool_id, "inputs": list(inputs), "params": params, "dry_run": dry_run})
        return {"ok": True, "outputs": [{"path": str(p), "kind": k, "sha256": ""} for k, p in self.outputs], "warnings": ["w1"] if dry_run is False else []}


def _run(node_type, store, runner, inputs=None, params=None, is_mock=False):
    return asyncio.run(tb.execute_toolbox_node(node_type, "n1", params or {}, inputs or {}, store, "run1", is_mock, runner=runner))


# --------------------------------------------------------------------------- đăng ký & menu
def test_all_six_nodes_registered_in_registry():
    for t in NODES:
        d = registry_mod.NodeRegistry.get(t)
        assert d is not None, f"{t} chưa đăng ký"
        assert d.description and d.display_name


def test_nodes_visible_in_add_node_menu():
    for t in NODES:
        d = registry_mod.NodeRegistry.get(t)
        assert t not in HIDDEN_IN_MENU
        assert d.category in I18N_CATEGORIES, f"{t}: danh mục '{d.category}' không có khoá dịch -> menu hiện sai"
        assert d.input_ports and d.output_ports


def test_node_tool_map_matches_manifests():
    assert set(tb.NODE_TOOL) == set(NODES)
    for t, tool_id in tb.NODE_TOOL.items():
        assert (tb.TOOLS_DIR / tool_id / "tool.json").exists(), f"{t} -> công cụ '{tool_id}' không có trong toolbox"
        assert tb.tool_available(tool_id)


def test_port_types():
    g = registry_mod.NodeRegistry.get
    assert [p.port_type for p in g("bg_remove").input_ports] == [PortType.IMAGE]
    assert {p.name: p.port_type for p in g("bg_remove").output_ports} == {"image": PortType.IMAGE, "mask": PortType.IMAGE}
    assert g("word_captions").input_ports[0].port_type == PortType.AUDIO
    assert g("word_captions").output_ports[0].port_type == PortType.CAPTIONS
    assert g("scene_cut").input_ports[0].port_type == PortType.VIDEO
    assert g("scene_cut").output_ports[0].port_type == PortType.SCENES
    assert [p.name for p in g("depth_layers").output_ports] == ["bg", "mid", "fg", "depth"]
    assert g("handdraw").output_ports[0].port_type == PortType.VIDEO
    assert g("voice_clone").output_ports[0].port_type == PortType.TEXT


def test_defaults_reasonable():
    g = registry_mod.NodeRegistry.get
    assert g("bg_remove").default_params["model"] == "u2net"  # weights Apache-2.0, không NC
    assert g("bg_remove").default_params["alpha_matting"] is False
    assert g("word_captions").default_params == {"model_size": "small", "language": "vi"}  # tiny kém tiếng Việt
    hd = g("handdraw").default_params
    assert hd["height"] > hd["width"], "handdraw mặc định phải dọc 9:16"
    assert abs(hd["width"] / hd["height"] - 9 / 16) < 0.01
    assert g("scene_cut").default_params["export_clips"] is False  # không tự xuất clip
    assert g("voice_clone").default_params["consent_note"] == ""  # buộc người dùng tự ghi
    for t in NODES:  # mọi khoá mặc định phải được executor hiểu
        assert g(t).default_params == tb.NODE_DEFAULTS[t]
    # mọi node đều chạy cục bộ: không đánh dấu mockable giả
    assert all(not g(t).mockable for t in NODES)


# --------------------------------------------------------------------------- ánh xạ đầu ra
def test_bg_remove_from_wired_image(store, tmp_path):
    src = _art(store, _png(tmp_path / "in.png"), ArtifactKind.IMAGE)
    cut, mask = _png(tmp_path / "o" / "cutout.png", (64, 48)), _png(tmp_path / "o" / "mask.png", (64, 48))
    fr = FakeRunner([("cutout", cut), ("mask", mask)])
    outputs, primary, cost = _run("bg_remove", store, fr, {"image": src})
    assert fr.calls[0]["tool"] == "bg-remove" and fr.calls[0]["inputs"] == [store.resolve_artifact_path(src)]
    assert fr.calls[0]["params"] == {"model": "u2net", "alpha_matting": False}
    assert outputs["image"].kind == ArtifactKind.IMAGE and outputs["mask"].kind == ArtifactKind.IMAGE
    assert (outputs["image"].meta.width, outputs["image"].meta.height) == (64, 48)
    assert primary is outputs["image"] and cost == 0.0
    assert store.resolve_artifact_path(outputs["image"]).exists()


def test_bg_remove_uses_character_dna_image_when_unwired(store, tmp_path):
    dna = _png(store.characters_dir / "bi" / "bi_01.png")
    _png(store.characters_dir / "bi" / "bi_02.png")
    cut = _png(tmp_path / "o" / "cutout.png")
    fr = FakeRunner([("cutout", cut)])
    outputs, _, _ = _run("bg_remove", store, fr, {}, {"characterId": "bi"})
    assert fr.calls[0]["inputs"] == [dna]
    assert "mask" not in outputs
    fr2 = FakeRunner([("cutout", cut)])
    _run("bg_remove", store, fr2, {}, {"characterId": "bi", "imageIndex": 1})
    assert fr2.calls[0]["inputs"][0].name == "bi_02.png"


def test_bg_remove_accepts_image_list_from_character_node(store, tmp_path):
    a = _art(store, _png(tmp_path / "a.png"), ArtifactKind.IMAGE)
    fr = FakeRunner([("cutout", _png(tmp_path / "c.png"))])
    _run("bg_remove", store, fr, {"image": [a]})
    assert fr.calls[0]["inputs"] == [store.resolve_artifact_path(a)]


def test_bg_remove_missing_input_is_clear_error(store, tmp_path):
    with pytest.raises(ValueError, match="thiếu ảnh đầu vào"):
        _run("bg_remove", store, FakeRunner([]))
    with pytest.raises(ValueError):  # nhân vật không có ảnh
        _run("bg_remove", store, FakeRunner([]), {}, {"characterId": "khong-co"})


def test_bg_remove_tool_without_cutout_is_error(store, tmp_path):
    src = _art(store, _png(tmp_path / "in.png"), ArtifactKind.IMAGE)
    with pytest.raises(tb.ToolboxError, match="cutout"):
        _run("bg_remove", store, FakeRunner([]), {"image": src})


def test_word_captions_outputs_srt_and_words(store, tmp_path):
    aud = _art(store, _file(tmp_path / "a.mp3", b"ID3fake"), ArtifactKind.AUDIO)
    srt = _file(tmp_path / "o" / "s.srt", b"1\n00:00:00,000 --> 00:00:01,000\nXin chao\n")
    wj = _file(tmp_path / "o" / "w.json", json.dumps({"language": "vi", "duration": 1.0, "segments": [
        {"words": [{"word": "Xin", "start": 0.0, "end": 0.3, "probability": 0.9}, {"word": "chao", "start": 0.3, "end": 0.8, "probability": 0.9}]}]}).encode())
    fr = FakeRunner([("subtitles_srt", srt), ("word_timings", wj)])
    outputs, primary, _ = _run("word_captions", store, fr, {"audio": aud})
    assert fr.calls[0]["tool"] == "stt-align"
    assert fr.calls[0]["params"] == {"model_size": "small", "language": "vi"}
    assert outputs["captions"].kind == ArtifactKind.CAPTIONS and primary is outputs["captions"]
    words = json.loads(outputs["words"])
    assert [w["word"] for w in words["words"]] == ["Xin", "chao"] and words["language"] == "vi"


def test_word_captions_requires_audio(store):
    with pytest.raises(ValueError, match="audio"):
        _run("word_captions", store, FakeRunner([]))


def test_scene_cut_maps_to_scene_dicts(store, tmp_path):
    vid = _art(store, _file(tmp_path / "v.mp4", b"fakevideo"), ArtifactKind.VIDEO)
    sj = _file(tmp_path / "o" / "scenes.json", json.dumps({"duration": 9.0, "scenes": [
        {"index": 1, "start": 0.0, "end": 3.0, "duration": 3.0},
        {"index": 2, "start": 3.0, "end": 9.0, "duration": 6.0, "clip": "/x/scene_002.mp4"}]}).encode())
    fr = FakeRunner([("scenes_json", sj)])
    outputs, primary, cost = _run("scene_cut", store, fr, {"video": vid}, {"threshold": 5.0})
    assert fr.calls[0]["params"]["threshold"] == 5.0 and fr.calls[0]["params"]["export_clips"] is False
    sc = outputs["scenes"]
    assert [s["sceneNumber"] for s in sc] == [1, 2] and sc[1]["durationSec"] == 6.0 and sc[1]["clip"].endswith("scene_002.mp4")
    assert "clip" not in sc[0] and "2 cảnh" in outputs["report"]
    assert primary is None and cost == 0.0


def test_depth_layers_four_images(store, tmp_path):
    src = _art(store, _png(tmp_path / "in.png"), ArtifactKind.IMAGE)
    o = {k: _png(tmp_path / "o" / f"{k}.png") for k in ("layer_bg", "layer_mid", "layer_fg", "depth")}
    fr = FakeRunner(list(o.items()))
    outputs, primary, _ = _run("depth_layers", store, fr, {"image": src})
    assert set(["bg", "mid", "fg", "depth"]) <= set(outputs)
    assert all(outputs[k].kind == ArtifactKind.IMAGE for k in ("bg", "mid", "fg", "depth"))
    assert primary is outputs["fg"]
    assert fr.calls[0]["params"] == {"fg_pct": 70, "mid_pct": 35, "feather": 3, "max_side": 1280}


def test_depth_layers_missing_layer_is_error(store, tmp_path):
    src = _art(store, _png(tmp_path / "in.png"), ArtifactKind.IMAGE)
    fr = FakeRunner([("layer_bg", _png(tmp_path / "bg.png"))])
    with pytest.raises(tb.ToolboxError, match="layer_mid"):
        _run("depth_layers", store, fr, {"image": src})


def test_handdraw_video_artifact(store, tmp_path):
    src = _art(store, _png(tmp_path / "sk.png"), ArtifactKind.IMAGE)
    fr = FakeRunner([("video", _file(tmp_path / "o" / "w.mp4", b"mp4data"))])
    outputs, primary, _ = _run("handdraw", store, fr, {"image": src}, {"duration_sec": 4})
    v = outputs["video"]
    assert v.kind == ArtifactKind.VIDEO and primary is v
    assert (v.meta.width, v.meta.height, v.meta.duration, v.meta.fps) == (540, 960, 4.0, 24.0)
    assert fr.calls[0]["params"]["duration_sec"] == 4 and fr.calls[0]["params"]["show_hand"] is True


def test_voice_clone_mock_is_dry_run(store, tmp_path):
    smp = _art(store, _file(tmp_path / "s.mp3", b"ID3"), ArtifactKind.AUDIO)
    fr = FakeRunner([])
    outputs, primary, _ = _run("voice_clone", store, fr, {"audio": smp}, {"name": "de-bong", "consent_note": "Mau cua chinh toi, dong y dung"}, is_mock=True)
    assert fr.calls[0]["dry_run"] is True and fr.calls[0]["tool"] == "voice-clone"
    assert outputs["voice_id"] == "de-bong" and primary is None and "mock" in outputs["report"]


def test_voice_clone_real_returns_voice_id_and_preview(store, tmp_path):
    smp = _art(store, _file(tmp_path / "s.mp3", b"ID3"), ArtifactKind.AUDIO)
    fr = FakeRunner([("voice_preview", _file(tmp_path / "o" / "p.mp3", b"ID3prev"))])
    outputs, primary, _ = _run("voice_clone", store, fr, {"audio": smp}, {"name": "de-bong", "consent_note": "Mau cua chinh toi, dong y dung"})
    assert fr.calls[0]["dry_run"] is False
    assert outputs["voice_id"] == "de-bong" and outputs["preview"].kind == ArtifactKind.AUDIO and primary is outputs["preview"]
    assert "text" not in fr.calls[0]["params"] and "display_name" not in fr.calls[0]["params"]  # tham số rỗng không gửi


def test_voice_clone_needs_name(store, tmp_path):
    smp = _art(store, _file(tmp_path / "s.mp3", b"ID3"), ArtifactKind.AUDIO)
    with pytest.raises(ValueError, match="params.name"):
        _run("voice_clone", store, FakeRunner([]), {"audio": smp})


def test_not_a_toolbox_node(store):
    with pytest.raises(KeyError):
        _run("image_gen", store, FakeRunner([]))


# --------------------------------------------------------------------------- run_tool (tiến trình con thật, công cụ giả)
@pytest.fixture
def fake_toolbox(tmp_path, monkeypatch):
    tools = tmp_path / "tb" / "tools"
    monkeypatch.setattr(tb, "TOOLBOX_DIR", tmp_path / "tb")
    monkeypatch.setattr(tb, "TOOLS_DIR", tools)

    def make(tool_id: str, body: str):
        d = tools / tool_id
        d.mkdir(parents=True)
        (d / "run.py").write_text(textwrap.dedent(body), encoding="utf-8")

    return make


HEAD = """
import argparse, json, sys
ap = argparse.ArgumentParser(); ap.add_argument('--in', dest='i'); ap.add_argument('--out', dest='o'); a = ap.parse_args()
cfg = json.load(open(a.i))
"""


def test_run_tool_ok_contract(fake_toolbox, tmp_path):
    fake_toolbox("echo", HEAD + "json.dump({'ok': True, 'outputs': [], 'warnings': [json.dumps(cfg)], 'error': None}, open(a.o, 'w')); print(a.o)")
    res = tb.run_tool("echo", [tmp_path / "x.png"], {"k": 1}, dry_run=True, project="p1")
    cfg = json.loads(res["warnings"][0])
    assert cfg == {"params": {"k": 1}, "inputs": [str(tmp_path / "x.png")], "project": "p1", "dry_run": True}


def test_run_tool_reports_bad_input_exit_3(fake_toolbox):
    fake_toolbox("bad", HEAD + "json.dump({'ok': False, 'error': {'code': 'NO_INPUT', 'message': 'thieu', 'fix_hint': 'noi cong'}}, open(a.o, 'w')); sys.exit(3)")
    with pytest.raises(tb.ToolboxError) as e:
        tb.run_tool("bad", [], {})
    assert e.value.exit_code == 3 and e.value.code == "NO_INPUT" and e.value.fix_hint == "noi cong"


def test_run_tool_crash_without_out_json(fake_toolbox):
    fake_toolbox("crash", "import sys\nprint('boom', file=sys.stderr)\nsys.exit(7)")
    with pytest.raises(tb.ToolboxError) as e:
        tb.run_tool("crash", [], {})
    assert e.value.code == "NO_OUT_JSON" and e.value.exit_code == 7 and "boom" in str(e.value)


def test_run_tool_timeout(fake_toolbox):
    fake_toolbox("slow", "import time\ntime.sleep(5)")
    with pytest.raises(tb.ToolboxError) as e:
        tb.run_tool("slow", [], {}, timeout=1)
    assert e.value.code == "TIMEOUT"


def test_run_tool_unknown_tool(fake_toolbox):
    with pytest.raises(tb.ToolboxError) as e:
        tb.run_tool("khong-co", [], {})
    assert e.value.code == "TOOL_NOT_FOUND" and e.value.exit_code == 2


def test_tool_python_prefers_own_venv(fake_toolbox, tmp_path):
    fake_toolbox("v", "pass")
    assert tb.tool_python("v") == sys.executable
    py = tb.TOOLS_DIR / "v" / ".venv" / "bin" / "python"
    py.parent.mkdir(parents=True)
    py.write_text("")
    assert tb.tool_python("v") == str(py)


# --------------------------------------------------------------------------- công cụ THẬT (tuỳ chọn)
REAL = os.environ.get("SOCNHOTV_TOOLBOX_REAL") == "1"


@pytest.mark.skipif(not REAL or not shutil.which("ffmpeg"), reason="đặt SOCNHOTV_TOOLBOX_REAL=1 và có ffmpeg (ghi vào data/shared thật)")
def test_real_scene_cut_three_colour_video(store, tmp_path):
    vid = tmp_path / "three.mp4"
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for c in ("red", "green", "blue"):
        cmd += ["-f", "lavfi", "-i", f"color=c={c}:s=320x180:r=30:d=2"]
    cmd += ["-filter_complex", "[0][1][2]concat=n=3:v=1:a=0[v]", "-map", "[v]", "-pix_fmt", "yuv420p", str(vid)]
    subprocess.run(cmd, check=True)
    art = _art(store, vid, ArtifactKind.VIDEO)
    outputs, _, _ = asyncio.run(tb.execute_toolbox_node("scene_cut", "n1", {}, {"video": art}, store, "r", False))
    assert [round(s["durationSec"]) for s in outputs["scenes"]] == [2, 2, 2]


@pytest.mark.skipif(not REAL or not shutil.which("ffmpeg"), reason="đặt SOCNHOTV_TOOLBOX_REAL=1 và có ffmpeg (ghi vào data/shared thật)")
def test_real_handdraw_makes_video(store, tmp_path):
    from PIL import Image, ImageDraw

    im = Image.new("RGB", (540, 960), "white")
    d = ImageDraw.Draw(im)
    d.ellipse((100, 200, 440, 540), outline="black", width=8)
    d.line((120, 700, 420, 760), fill="black", width=8)
    sk = tmp_path / "sketch.png"
    im.save(sk)
    art = _art(store, sk, ArtifactKind.IMAGE)
    outputs, _, _ = asyncio.run(tb.execute_toolbox_node("handdraw", "n1", {"duration_sec": 2}, {"image": art}, store, "r", False))
    assert store.resolve_artifact_path(outputs["video"]).stat().st_size > 1000
