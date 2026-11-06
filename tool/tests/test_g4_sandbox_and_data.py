"""G4: test chạy trong sandbox, chọn ảnh DNA tham chiếu, script_to_scenes mang priority, verify_episode."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REAL_ROOT = Path(__file__).resolve().parents[2]


def test_repo_root_is_sandbox_not_real_repo(sandbox_root):
    from socnhotv.core.storage.project_store import ProjectStore, get_repo_root
    from socnhotv.workspace import data_root, project_path, repo_root

    if sandbox_root is None:
        pytest.skip("SOCNHOTV_TEST_REAL_DATA=1")
    assert repo_root() == sandbox_root and get_repo_root() == sandbox_root
    assert data_root() == sandbox_root / "data"
    assert project_path("soc-nho-tv").resolve().is_relative_to(sandbox_root.resolve())
    store = ProjectStore("soc-nho-tv")
    assert store.runs_dir.resolve().is_relative_to(sandbox_root.resolve())
    assert not store.runs_dir.resolve().is_relative_to((REAL_ROOT / "data").resolve())
    # runs/ của sandbox bắt đầu rỗng, không có .env (không dùng key thật)
    assert not (sandbox_root / ".env").exists()


def test_sandbox_write_does_not_touch_real_data(sandbox_root):
    if sandbox_root is None:
        pytest.skip("SOCNHOTV_TEST_REAL_DATA=1")
    from socnhotv.core.storage.project_store import ProjectStore

    store = ProjectStore("soc-nho-tv")
    g = store.get_graph_path()
    real_g = REAL_ROOT / "data" / "projects" / "soc-nho-tv" / "graph.json"
    before = real_g.read_bytes() if real_g.exists() else None
    g.write_text('{"probe": true}', encoding="utf-8")
    after = real_g.read_bytes() if real_g.exists() else None
    assert before == after
    assert not (REAL_ROOT / "data" / "projects" / "soc-nho-tv" / "runs" / "g4_probe").exists()
    (store.runs_dir / "g4_probe").mkdir()
    assert not (REAL_ROOT / "data" / "projects" / "soc-nho-tv" / "runs" / "g4_probe").exists()


def _mk_char(tmp_path: Path, cid: str, names: list[str], profile: dict | None = None) -> Path:
    chars = tmp_path / "characters"
    (chars / cid).mkdir(parents=True)
    for n in names:
        (chars / cid / n).write_bytes(b"\x89PNG fake")
    (chars / "studio_characters.json").write_text(
        json.dumps({"characters": [{"id": cid, **(profile or {})}]}), encoding="utf-8"
    )
    return chars


def test_dna_reference_files_prefers_profile_list(tmp_path):
    from socnhotv.core.engine.character_profile import dna_reference_files

    chars = _mk_char(tmp_path, "bi", ["bi_01.png", "bi_02.png", "bi_04.png", "bi_11.png"], {"dnaReferences": ["bi_11.png", "bi_01.png", "missing.png"]})
    assert [p.name for p in dna_reference_files(chars, "bi")] == ["bi_11.png", "bi_01.png"]


def test_dna_reference_files_heuristic_skips_sheet_and_orders_front_first(tmp_path):
    from socnhotv.core.engine.character_profile import dna_reference_files

    chars = _mk_char(tmp_path, "mun", ["mun_01.png", "mun_02.png", "mun_03.png", "mun_04.png", "mun_dna_sheet.png"])
    got = [p.name for p in dna_reference_files(chars, "mun")]
    assert got == ["mun_02.png", "mun_01.png", "mun_03.png"]
    assert "mun_dna_sheet.png" not in got


def test_real_profiles_have_dna_references_for_episode_cast():
    from socnhotv.core.engine.character_profile import dna_reference_files, load_profile

    chars = REAL_ROOT / "data" / "projects" / "soc-nho-tv" / "characters"
    if not (chars / "studio_characters.json").is_file():
        pytest.skip("không có dữ liệu dự án")
    for cid in ("soc_nho", "de_mun", "me_soc", "de_bong", "ong_de_rau_bac"):
        prof = load_profile(chars, cid)
        assert prof and prof.get("dnaReferences"), cid
        files = dna_reference_files(chars, cid, prof)
        assert 1 <= len(files) <= 3 and all(f.is_file() for f in files), cid


def test_script_to_scenes_carries_priority_and_timing():
    from socnhotv.core.engine.episode_script import script_to_scenes

    data = {"scenes": [{"index": 1, "title": "Mở đầu", "shots": [{
        "id": "S01", "sceneIndex": 1, "startSec": 0, "endSec": 20, "durationSec": 20.0, "imagePrompt": "i", "videoPrompt": "v",
        "dialogue": "Chào", "speaker": "Bi", "characters": ["Bi"], "shotSize": "WS", "camera": "push-in", "sfx": "", "bgm": "",
        "priority": 1, "clipDurationSec": 5, "action": "[0-7s] vẫy tay",
    }]}]}
    sc = script_to_scenes(data)[0]
    assert sc["priority"] == 1 and sc["sceneIndex"] == 1 and sc["startSec"] == 0 and sc["endSec"] == 20
    assert sc["clipDurationSec"] == 5 and sc["action"].startswith("[0-7s]")


@pytest.mark.parametrize("ep", ["ep01-nui-lua-trong-bung-bi", "ep02-mun-so-bong-toi"])
def test_episode_scripts_locked_with_priorities_and_real_clip_length(ep):
    sj = REAL_ROOT / "data" / "projects" / "soc-nho-tv" / "content" / "episodes" / ep / "script.json"
    if not sj.is_file():
        pytest.skip("không có kịch bản")
    d = json.loads(sj.read_text(encoding="utf-8"))
    shots = [s for sc in d["scenes"] for s in sc["shots"]]
    assert d.get("locked") is True and len(shots) == 30
    assert sum(1 for s in shots if s.get("priority") == 1) >= 5
    assert not any("8-second" in s["videoPrompt"] for s in shots)
    assert not any("cm)" in s["dialogue"] for s in shots), "lời thoại không được đọc cả chiều cao '(85cm)'"


def _load_verify():
    p = REAL_ROOT / "scripts" / "video" / "verify_episode.py"
    spec = importlib.util.spec_from_file_location("verify_episode", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_verify_episode_detects_silent_mock_video(tmp_path):
    ve = _load_verify()
    ffmpeg = ve.FFMPEG
    v = tmp_path / "silent.mp4"
    r = subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=320x180:d=2",
                        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "2", "-c:v", "libx264", "-c:a", "aac", str(v)],
                       capture_output=True)
    if r.returncode != 0:
        pytest.skip("ffmpeg không tạo được video thử")
    rep = ve.Report()
    ve.check_probe(rep, v)
    ve.check_loudness(rep, v)
    assert rep.status("1") == ve.FAIL  # 320×180, 2 giây
    assert rep.status("2") == ve.FAIL  # im lặng


def test_verify_episode_keyframes_and_mock_flag(tmp_path):
    ve = _load_verify()
    proj = tmp_path / "proj"
    (proj / "assets").mkdir(parents=True)
    snap_dir = proj / "runs" / "_node_outputs" / "g"
    snap_dir.mkdir(parents=True)
    imgs = []
    for i in range(30):
        f = proj / "assets" / f"{i}.png"
        f.write_bytes(f"img{i}".encode())
        imgs.append({"$artifact": {"uri": f"assets/{i}.png", "provenance": {"provider": "pollinations", "model": "flux"}}})
    (snap_dir / "kf.json").write_text(json.dumps({"mock": False, "outputs": {"images": imgs}}), encoding="utf-8")
    rep = ve.Report()
    ve.check_keyframes(rep, proj, snap_dir, ["kf"], allow_mock=False)
    assert rep.status("3") == ve.PASS and rep.status("5") == ve.PASS

    imgs[0]["$artifact"]["provenance"]["provider"] = "mock"
    (snap_dir / "kf.json").write_text(json.dumps({"mock": True, "outputs": {"images": imgs}}), encoding="utf-8")
    rep = ve.Report()
    ve.check_keyframes(rep, proj, snap_dir, ["kf"], allow_mock=False)
    assert rep.status("3") == ve.FAIL and rep.status("5") == ve.FAIL


def test_shot_pack_zip_has_priority_shots_prompts_and_readme():
    import io
    import zipfile

    from fastapi.testclient import TestClient

    from socnhotv.core.api.app import app

    client = TestClient(app)
    r = client.get("/data/projects/soc-nho-tv/episodes/ep01-nui-lua-trong-bung-bi/shot-pack")
    if r.status_code == 404:
        pytest.skip("không có kịch bản tập 1")
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = set(z.namelist())
    assert "README.txt" in names and "manifest.json" in names
    man = json.loads(z.read("manifest.json"))
    ids = [s["shotId"] for s in man["shots"]]
    assert len(ids) >= 5 and all(s["priority"] == 1 for s in man["shots"])
    for sid in ids:
        assert f"{sid}.txt" in names
        assert any(n.startswith(sid + ".") and not n.endswith(".txt") for n in names), f"thiếu ảnh {sid}"
    txt = z.read(f"{ids[0]}.txt").decode()
    assert "5-second" in txt and "clips" in z.read("README.txt").decode()

    r2 = client.get("/data/projects/soc-nho-tv/episodes/ep01-nui-lua-trong-bung-bi/shot-pack?shots=S02,S03")
    assert sorted(json.loads(zipfile.ZipFile(io.BytesIO(r2.content)).read("manifest.json"))["shots"][0]["shotId"] for _ in [0]) == ["S02"]
    assert client.get("/data/projects/soc-nho-tv/episodes/ep01-nui-lua-trong-bung-bi/shot-pack?shots=../x").status_code == 400


def test_verify_listener_flags_reference_transcript_leak():
    ve = _load_verify()
    ear = ve.Listener.__new__(ve.Listener)  # không nạp Whisper, chỉ thử phần chấm
    ref = "Bên là bảo thức năm nay mình tảm tuổi Mình sọt chiến hiểu học đã đi điểm"
    text = "Anh Bi ơi! Mun mang quả bóng vải sang chơi với anh Bi nè!"
    bad = ear.judge(text, "Xọc chiến hiểu học đã đi ơi! Mun mang quả bóng vải sang chơi với anh Bi nè!", ref)
    assert bad["leak"], bad
    good = ear.judge(text, "Anh Bi ơi, muốn mang quả bóng vải sang chơi với anh Bi nè", ref)
    assert not good["leak"] and good["similarity"] >= 0.7
