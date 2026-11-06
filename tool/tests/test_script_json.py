"""script.json: kịch bản đã biên dịch, đầy đủ thuộc tính, có id nhân vật tường minh."""
from __future__ import annotations

import json
from pathlib import Path

from socnhotv.core.engine.character_profile import load_profiles
from socnhotv.core.engine.episode_script import SCRIPT_JSON, compile_script, load_script

REPO = Path(__file__).resolve().parents[2]
PROJ = REPO / "data" / "projects" / "soc-nho-tv"
EP = "ep02-mun-so-bong-toi"


def _ep_dir(tmp_path):
    src = PROJ / "content" / "episodes" / EP
    d = tmp_path / EP
    d.mkdir()
    for f in src.glob("KICH*.md"):
        (d / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    return d


def test_compile_keeps_all_properties_and_adds_explicit_ids():
    profiles = load_profiles(PROJ / "characters")
    md = next((PROJ / "content" / "episodes" / EP).glob("KICH*.md")).read_text(encoding="utf-8")
    data = compile_script(md, EP, profiles, "KICH.md")
    # giữ đủ thuộc tính của kịch bản
    for key in ("title", "durationSec", "lesson", "mantra", "environmentPromptLock", "scenes", "characters", "cast"):
        assert key in data
    shot = data["scenes"][0]["shots"][0]
    for key in ("imagePrompt", "videoPrompt", "action", "expression", "startSec", "dialogue", "speaker"):
        assert key in shot
    assert "promptLock" in data["characters"][0] and "voiceDirection" in data["characters"][0]
    # id tường minh
    assert data["castIds"] == ["de_mun", "de_bong", "ong_de_rau_bac"]
    assert [c["id"] for c in data["cast"]] == data["castIds"]
    assert all(sh["speakerId"] in data["castIds"] for sc in data["scenes"] for sh in sc["shots"] if sh["dialogue"])
    assert data["unmatched"] == []
    assert data["source"]["sha"] and data["schemaVersion"] == 1


def test_load_prefers_json_regenerates_on_md_change_and_respects_lock(tmp_path):
    profiles = load_profiles(PROJ / "characters")
    d = _ep_dir(tmp_path)
    first = load_script(d, EP, profiles)  # chưa có json -> biên dịch + ghi
    sj = d / SCRIPT_JSON
    assert sj.is_file() and first["castIds"]

    # sửa tay script.json nhưng chưa khoá, .md không đổi -> vẫn dùng json (sha khớp)
    cur = json.loads(sj.read_text(encoding="utf-8"))
    cur["title"] = "Sửa tay"
    sj.write_text(json.dumps(cur, ensure_ascii=False), encoding="utf-8")
    assert load_script(d, EP, profiles)["title"] == "Sửa tay"

    # .md đổi, chưa khoá -> biên dịch lại, ghi đè
    md_file = next(d.glob("KICH*.md"))
    md_file.write_text(md_file.read_text(encoding="utf-8") + "\n\n<!-- đổi -->\n", encoding="utf-8")
    assert load_script(d, EP, profiles)["title"] != "Sửa tay"

    # khoá -> .md đổi cũng không ghi đè
    cur = json.loads(sj.read_text(encoding="utf-8"))
    cur["title"], cur["locked"] = "Đã khoá", True
    sj.write_text(json.dumps(cur, ensure_ascii=False), encoding="utf-8")
    md_file.write_text(md_file.read_text(encoding="utf-8") + "\nthêm\n", encoding="utf-8")
    assert load_script(d, EP, profiles)["title"] == "Đã khoá"
