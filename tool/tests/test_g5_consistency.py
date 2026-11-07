"""G5 pha 1: consistency.json, refs_for_shot, build_prompt_block.

- Test đơn vị dùng thư mục tạm (tmp_path) với ảnh nhỏ tự tạo.
- Test dữ liệu thật đọc characters/ qua sandbox của conftest (tệp json được COPY, ảnh symlink, không ghi ngược).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from socnhotv.core.engine import character_consistency as cc
from socnhotv.workspace import paths

FIVE = ["soc_nho", "de_mun", "me_soc", "de_bong", "ong_de_rau_bac"]


# ----------------------------------------------------------------------------- dữ liệu giả
def _char(cid: str, name: str, height: float, ratio: float, refs: dict, aliases=None) -> dict:
    return {
        "id": cid,
        "identity": {"name": name, "promptName": cid, "aliases": aliases or [], "heightCm": height, "scaleRatio": ratio},
        "locked": {
            "palette": {"fur": {"hex": ["#D96B27"], "en": "fur"}},
            "features": [{"vi": "đuôi", "en": "fluffy tail"}],
            "defaultOutfit": {"vi": "áo vàng", "en": "yellow t-shirt"},
        },
        "forbidden": [{"vi": "béo", "en": "chubby"}, {"vi": "đuôi ngắn", "en": "short tail"}],
        "references": refs,
    }


def _refs(*roles: str, expr: dict | None = None) -> dict:
    out = {r: {"file": f"{r}.png"} for r in roles}
    if expr:
        out["expressions"] = {k: {"file": f"expr_{k}.png"} for k in expr}
    return out


@pytest.fixture()
def chars() -> dict:
    full = ("front", "three_quarter", "profile", "back", "full_body", "closeup", "action")
    return {
        "bi": _char("bi", "Sóc Nhỏ (Bi)", 100, 1.0, _refs(*full, expr={"happy": 1, "sad": 1, "surprised": 1}), ["Sóc Bi", "Bi"]),
        "mun": _char("mun", "Dê Mun", 85, 0.85, _refs("front", "full_body", "closeup", expr={"happy": 1}), ["Mun"]),
        "me": _char("me", "Mẹ Sóc", 145, 1.45, _refs("front", "full_body"), ["Mẹ Sóc"]),
    }


def _shot(**kw) -> dict:
    base = {"id": "S01", "shotSize": "MS", "camera": "eye-level, 35mm, static", "characters": ["Sóc Bi (100cm)"], "expression": ""}
    base.update(kw)
    return base


# ----------------------------------------------------------------------------- ghép tên
def test_match_character_by_alias(chars):
    assert cc.match_character("Sóc Bi (100cm)", chars) == "bi"
    assert cc.match_character("Dê Mun (85cm)", chars) == "mun"
    assert cc.match_character("Mẹ Sóc (145cm)", chars) == "me"
    assert cc.match_character("Bác Voi (180cm)", chars) is None


def test_match_character_me_soc_not_confused_with_bi(chars):
    # "Mẹ Sóc" có chữ "Sóc" nhưng không được rơi vào Bi
    assert cc.match_character("Mẹ Sóc", chars) == "me"
    assert cc.match_character("Sóc Bi", chars) == "bi"


# ----------------------------------------------------------------------------- phân tích shot
def test_expression_parsing_multi_character():
    shot = _shot(expression="Sóc Bi (vui): cười rộng | Dê Mun (buồn): môi trề | Mẹ Sóc (ngạc nhiên): mắt mở to")
    got = cc.expressions_by_character(shot)
    assert got == {"Sóc Bi": "happy", "Dê Mun": "sad", "Mẹ Sóc": "surprised"}


def test_camera_view_keywords():
    assert cc.camera_view("eye-level, 35mm, lateral-pan") == "profile"
    assert cc.camera_view("eye-level, 50mm, push-in") is None
    assert cc.camera_view("low, 35mm, dutch-angle") == "three_quarter"
    assert cc.camera_view("over-the-shoulder, 50mm") == "back"


# ----------------------------------------------------------------------------- chọn ảnh theo shot
def test_wide_shot_prefers_full_body(chars):
    plan = cc.plan_refs_for_shot(_shot(shotSize="WS"), chars, max_references=1)
    assert [(r["characterId"], r["role"]) for r in plan["refs"]] == [("bi", "full_body")]


def test_closeup_uses_expression_then_closeup(chars):
    plan = cc.plan_refs_for_shot(_shot(shotSize="CU", expression="Sóc Bi (buồn): cúi đầu"), chars, max_references=2)
    roles = [r["role"] for r in plan["refs"]]
    assert roles[0] == "expression:sad" and "closeup" in roles


def test_closeup_without_expression_ref_falls_back_to_closeup(chars):
    shot = _shot(shotSize="CU", characters=["Mẹ Sóc (145cm)"], expression="Mẹ Sóc (vui): cười")
    plan = cc.plan_refs_for_shot(shot, chars, max_references=1)
    assert plan["refs"][0]["role"] in ("front",)  # mẹ không có closeup/biểu cảm trong dữ liệu giả


def test_lateral_camera_picks_profile(chars):
    plan = cc.plan_refs_for_shot(_shot(shotSize="WS", camera="eye-level, 35mm, lateral-pan"), chars, max_references=1)
    assert plan["refs"][0]["role"] == "profile"


def test_motion_shot_uses_action_ref(chars):
    plan = cc.plan_refs_for_shot(_shot(shotSize="WS", action="Bi chạy theo bạn"), chars, max_references=1)
    assert plan["refs"][0]["role"] == "action"


def test_respects_max_references_and_never_exceeds(chars):
    shot = _shot(shotSize="MS", characters=["Sóc Bi (100cm)", "Dê Mun (85cm)", "Mẹ Sóc (145cm)"], speaker="Dê Mun (85cm)")
    for n in (0, 1, 2, 3, 5, 8):
        plan = cc.plan_refs_for_shot(shot, chars, max_references=n)
        assert len(plan["refs"]) <= n
        files = [r["path"] for r in plan["refs"]]
        assert len(files) == len(set(files)), "không trả trùng ảnh"


def test_budget_smaller_than_cast_prefers_speaker(chars):
    shot = _shot(characters=["Sóc Bi (100cm)", "Dê Mun (85cm)", "Mẹ Sóc (145cm)"], speaker="Mẹ Sóc (145cm)")
    plan = cc.plan_refs_for_shot(shot, chars, max_references=2)
    assert [r["characterId"] for r in plan["refs"]] == ["me", "bi"]
    assert [d["characterId"] for d in plan["dropped"]] == ["mun"]


def test_budget_zero_means_no_refs(chars):
    plan = cc.plan_refs_for_shot(_shot(), chars, max_references=0)
    assert plan["refs"] == []


def test_deterministic_same_input_same_output(chars):
    shot = _shot(shotSize="MCU", characters=["Sóc Bi (100cm)", "Dê Mun (85cm)"], expression="Sóc Bi (vui): x | Dê Mun (vui): y")
    runs = [cc.refs_for_shot(shot, chars, max_references=3) for _ in range(5)]
    assert all(r == runs[0] for r in runs)
    # đảo thứ tự khoá trong dict nhân vật không đổi kết quả
    rev = dict(reversed(list(chars.items())))
    assert cc.refs_for_shot(shot, rev, max_references=3) == runs[0]


def test_unmatched_character_reported_not_crashing(chars):
    plan = cc.plan_refs_for_shot(_shot(characters=["Bác Voi (180cm)"]), chars, max_references=3)
    assert plan["refs"] == [] and plan["unmatched"] == ["Bác Voi (180cm)"]


def test_paths_are_absolute_when_characters_dir_given(chars, tmp_path):
    out = cc.refs_for_shot(_shot(shotSize="WS"), chars, max_references=1, characters_dir=tmp_path)
    assert out == [str(tmp_path / "bi" / "full_body.png")]


# ----------------------------------------------------------------------------- khối prompt
def test_prompt_block_contains_locked_and_forbidden(chars):
    blk = cc.build_prompt_block(chars, order=["bi", "mun"])
    assert "#D96B27" in blk["prompt"] and "fluffy tail" in blk["prompt"] and "yellow t-shirt" in blk["prompt"]
    assert blk["negativePrompt"] == "chubby, short tail"  # bỏ trùng, giữ thứ tự
    assert blk["characterIds"] == ["bi", "mun"]


def test_prompt_block_scale_lock_orders_by_height(chars):
    blk = cc.build_prompt_block(chars, order=["bi", "mun", "me"])
    s = blk["scaleLock"]
    assert s.index("me 145cm") < s.index("bi 100cm") < s.index("mun 85cm")
    assert cc.build_prompt_block(chars, order=["bi"])["scaleLock"] == ""


# ----------------------------------------------------------------------------- validate
def test_validate_catches_missing_files_and_scale_mismatch(chars, tmp_path):
    d = chars["bi"]
    rep = cc.validate_consistency(d, tmp_path, scale_lock={"bi": 105})
    assert any("SCALE_LOCK" in e for e in rep["errors"])
    assert any("không tồn tại" in e for e in rep["errors"])
    (tmp_path / "bi").mkdir()
    for _, f in cc.iter_reference_files(d):
        Image.new("RGB", (4, 4)).save(tmp_path / "bi" / f)
    rep2 = cc.validate_consistency(d, tmp_path, scale_lock={"bi": 100})
    assert rep2["errors"] == []


def test_validate_requires_front_and_full_body():
    d = _char("x", "X", 100, 1.0, _refs("front"))
    assert any("full_body" in e for e in cc.validate_consistency(d)["errors"])


def test_parse_scale_lock_reads_real_table():
    md = paths.project_path("soc-nho-tv", "characters", "SCALE_LOCK.md")
    got = cc.parse_scale_lock(md)
    assert got["soc_nho"] == 100 and got["koala"] == 150 and got["de_mun"] == 85 and len(got) == 10


# ----------------------------------------------------------------------------- dữ liệu thật
@pytest.fixture(scope="module")
def real_dir() -> Path:
    return paths.project_path("soc-nho-tv", "characters")


@pytest.fixture(scope="module")
def real_chars(real_dir):
    return cc.load_all_consistency(real_dir)


def test_five_characters_have_consistency_json(real_chars):
    assert set(FIVE) <= set(real_chars)


@pytest.mark.parametrize("cid", FIVE)
def test_real_consistency_valid_and_complete(cid, real_chars, real_dir):
    data = real_chars[cid]
    rep = cc.validate_consistency(data, real_dir, cc.parse_scale_lock(real_dir / "SCALE_LOCK.md"))
    assert rep["errors"] == [], rep
    assert cc.distinct_reference_count(data) >= cc.TARGET_REF_COUNT
    assert data["status"] in ("proposed", "approved")
    # chiều cao khớp studio_characters.json
    studio = {c["id"]: c for c in json.loads((real_dir / "studio_characters.json").read_text(encoding="utf-8"))["characters"]}
    assert data["identity"]["heightCm"] == studio[cid]["heightCm"]
    assert data["voice"]["voiceId"] == studio[cid]["voiceId"]
    # ảnh bảng DNA (có chữ) không được lọt vào ảnh tham chiếu
    assert all("dna_sheet" not in f for _, f in cc.iter_reference_files(data))


def _episode_shots(ep: str) -> list:
    script = json.loads(paths.project_path("soc-nho-tv", "content", "episodes", ep, "script.json").read_text(encoding="utf-8"))
    return [s for sc in script["scenes"] for s in sc["shots"]]


@pytest.mark.parametrize("max_refs", [1, 2, 3, 4])
def test_refs_for_all_60_shots_ep01_ep02(real_chars, real_dir, max_refs):
    shots = _episode_shots("ep01-nui-lua-trong-bung-bi") + _episode_shots("ep02-mun-so-bong-toi")
    assert len(shots) == 60
    for s in shots:
        plan = cc.plan_refs_for_shot(s, real_chars, max_references=max_refs, characters_dir=real_dir)
        assert plan["unmatched"] == [], (s["id"], plan["unmatched"])
        assert 1 <= len(plan["refs"]) <= max_refs, (s["id"], len(plan["refs"]))
        for r in plan["refs"]:
            assert Path(r["path"]).is_file(), r
        again = cc.plan_refs_for_shot(s, real_chars, max_references=max_refs, characters_dir=real_dir)
        assert again == plan  # tất định
        blk = cc.build_prompt_block(real_chars, order=[r["characterId"] for r in plan["refs"]])
        assert blk["prompt"] and blk["negativePrompt"]


def test_every_character_in_shot_gets_a_ref_when_budget_allows(real_chars, real_dir):
    for ep in ("ep01-nui-lua-trong-bung-bi", "ep02-mun-so-bong-toi"):
        for s in _episode_shots(ep):
            n = len(s["characters"])
            plan = cc.plan_refs_for_shot(s, real_chars, max_references=max(3, n), characters_dir=real_dir)
            assert len({r["characterId"] for r in plan["refs"]}) == n, s["id"]


def test_real_ref_images_are_readable(real_chars, real_dir):
    for cid, data in real_chars.items():
        for _, f in cc.iter_reference_files(data):
            with Image.open(real_dir / cid / f) as im:
                im.verify()
