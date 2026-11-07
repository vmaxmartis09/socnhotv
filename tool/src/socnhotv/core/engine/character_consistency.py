"""G5: hồ sơ nhân vật có cấu trúc + chọn ảnh tham chiếu theo shot + khối prompt khoá.

Dữ liệu: data/projects/<id>/characters/<charId>/consistency.json (schema xem status/G5.md).
Module này CHỈ ĐỌC dữ liệu đó. Không gọi provider, không tốn tiền (pha 1).

Hàm chính (G3 / runner gọi):
- load_consistency / load_all_consistency
- validate_consistency            kiểm tệp ảnh tồn tại, chiều cao khớp SCALE_LOCK.md, đủ vai trò tối thiểu
- plan_refs_for_shot / refs_for_shot   chọn ảnh tham chiếu cho 1 shot (tất định)
- build_prompt_block              khối prompt + negativePrompt khoá màu/trang phục/đặc điểm/điều cấm/tỉ lệ

Pha 2 (chấm điểm, sinh lại) sẽ thêm vào cùng tệp này.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from socnhotv.core.engine.character_profile import name_tokens

SCHEMA_VERSION = 1
DEFAULT_MAX_REFERENCES = 3  # khi không biết model: đủ 1 neo nhận diện + 1 góc + 1 toàn thân

# Vai trò ảnh tham chiếu. front + full_body là bắt buộc; còn lại có thì tốt.
REQUIRED_ROLES = ("front", "full_body")
VIEW_ROLES = ("front", "three_quarter", "profile", "back", "full_body", "closeup", "action")
CANONICAL_EXPRESSIONS = ("happy", "sad", "surprised", "angry", "curious", "proud", "scared")
TARGET_REF_COUNT = 5  # "Done khi": mỗi nhân vật >= 5 ảnh tham chiếu khác nhau

# --- cỡ cảnh -> nhóm ---------------------------------------------------------
_FULL_SIZES = {"ELS", "EWS", "XWS", "VWS", "WS", "LS", "FS"}
_FACE_SIZES = {"CU", "ECU", "XCU", "BCU", "MCU"}
# còn lại (MS, MWS, OTS, ...) = trung cảnh

# --- biểu cảm tiếng Việt / Anh -> khoá chuẩn ----------------------------------
_EXPR_ALIASES: Dict[str, Tuple[str, ...]] = {
    "happy": ("vui", "cười", "hạnh phúc", "happy", "joy", "smile", "laugh", "phấn khích", "hào hứng", "excited"),
    "sad": ("buồn", "khóc", "lo lắng", "lo âu", "sad", "cry", "worried", "ngại"),
    "surprised": ("ngạc nhiên", "bất ngờ", "ngỡ ngàng", "surprise", "surprised", "shock"),
    "angry": ("giận", "tức", "bực", "angry", "mad"),
    "curious": ("tò mò", "curious", "thắc mắc", "suy nghĩ", "bối rối"),
    "proud": ("tự hào", "proud", "hãnh diện", "tự tin"),
    "scared": ("sợ", "hoảng", "scared", "afraid", "lo sợ"),
}
# gần nghĩa khi thiếu ảnh đúng biểu cảm: thử lần lượt
_EXPR_FALLBACK: Dict[str, Tuple[str, ...]] = {
    "scared": ("sad", "surprised"),
    "sad": ("scared",),
    "surprised": ("scared",),
    "angry": (),
    "curious": ("happy",),
    "proud": ("happy",),
    "happy": (),
}

_MOTION_WORDS = ("chạy", "nhảy", "bước đi", "đi bộ", "chạy lon ton", "running", "jump", "walk", "dash", "chạy theo")

CharactersArg = Union[Mapping[str, Mapping[str, Any]], Sequence[Mapping[str, Any]]]


# =============================================================================
# Đọc dữ liệu
# =============================================================================
def consistency_path(characters_dir: Path, char_id: str) -> Path:
    return Path(characters_dir) / char_id / "consistency.json"


def load_consistency(characters_dir: Path, char_id: str) -> Optional[Dict[str, Any]]:
    f = consistency_path(characters_dir, char_id)
    try:
        if f.is_file():
            data = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("id", char_id)
                return data
    except Exception:
        pass
    return None


def load_all_consistency(characters_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Mọi nhân vật có consistency.json trong thư mục characters (khoá theo id, thứ tự tên thư mục)."""
    out: Dict[str, Dict[str, Any]] = {}
    root = Path(characters_dir)
    if not root.is_dir():
        return out
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        data = load_consistency(root, d.name)
        if data:
            out[str(data.get("id") or d.name)] = data
    return out


def _as_map(characters: CharactersArg) -> Dict[str, Mapping[str, Any]]:
    if isinstance(characters, Mapping):
        return {str(k): v for k, v in characters.items()}
    return {str(c.get("id")): c for c in characters if isinstance(c, Mapping) and c.get("id")}


# =============================================================================
# SCALE_LOCK.md
# =============================================================================
def parse_scale_lock(md_path: Path) -> Dict[str, float]:
    """{charId: heightCm} đọc từ bảng trong SCALE_LOCK.md (hàng có `id` và **NNN cm**)."""
    out: Dict[str, float] = {}
    try:
        text = Path(md_path).read_text(encoding="utf-8")
    except Exception:
        return out
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        idm = re.search(r"`([a-z][a-z0-9_]+)`", line)
        hm = re.search(r"\*\*\s*(\d+(?:\.\d+)?)\s*cm\s*\*\*", line)
        if idm and hm:
            out[idm.group(1)] = float(hm.group(1))
    return out


# =============================================================================
# Kiểm hợp lệ
# =============================================================================
def _ref_file(entry: Any) -> Optional[str]:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, Mapping):
        f = entry.get("file")
        return str(f) if f else None
    return None


def iter_reference_files(data: Mapping[str, Any]) -> List[Tuple[str, str]]:
    """[(vai trò, tệp)] gồm cả expressions dạng 'expression:happy'. Thứ tự cố định."""
    refs = data.get("references") or {}
    out: List[Tuple[str, str]] = []
    for role in VIEW_ROLES:
        f = _ref_file(refs.get(role))
        if f:
            out.append((role, f))
    exprs = refs.get("expressions") or {}
    if isinstance(exprs, Mapping):
        for name in sorted(exprs):
            f = _ref_file(exprs[name])
            if f:
                out.append((f"expression:{name}", f))
    return out


def distinct_reference_count(data: Mapping[str, Any]) -> int:
    return len({f for _, f in iter_reference_files(data)})


def validate_consistency(
    data: Mapping[str, Any],
    characters_dir: Optional[Path] = None,
    scale_lock: Optional[Mapping[str, float]] = None,
) -> Dict[str, List[str]]:
    """Trả {"errors": [...], "warnings": [...]}. errors rỗng = dùng được."""
    errors: List[str] = []
    warnings: List[str] = []
    cid = str(data.get("id") or "")
    if not cid:
        errors.append("thiếu id")
    ident = data.get("identity") or {}
    if not ident.get("heightCm"):
        errors.append("identity.heightCm trống")
    if scale_lock and cid in scale_lock and ident.get("heightCm") is not None:
        if float(ident["heightCm"]) != float(scale_lock[cid]):
            errors.append(f"heightCm {ident['heightCm']} lệch SCALE_LOCK.md ({scale_lock[cid]})")
    locked = data.get("locked") or {}
    if not (locked.get("palette") or {}):
        errors.append("locked.palette trống")
    if not (data.get("forbidden") or []):
        warnings.append("forbidden trống")

    refs = data.get("references") or {}
    for role in REQUIRED_ROLES:
        if not _ref_file(refs.get(role)):
            errors.append(f"thiếu ảnh tham chiếu bắt buộc: {role}")
    n = distinct_reference_count(data)
    if n < TARGET_REF_COUNT:
        warnings.append(f"chỉ có {n} ảnh tham chiếu khác nhau (mục tiêu >= {TARGET_REF_COUNT})")
    if characters_dir is not None:
        base = Path(characters_dir) / cid
        for role, f in iter_reference_files(data):
            if not (base / f).is_file():
                errors.append(f"ảnh {role} không tồn tại: {cid}/{f}")
    return {"errors": errors, "warnings": warnings}


# =============================================================================
# Phân tích shot
# =============================================================================
def canonical_expression(text: str) -> Optional[str]:
    """'vui', 'Sóc Bi (ngạc nhiên): ...' -> khoá chuẩn. Không nhận ra -> None."""
    low = str(text or "").lower()
    for key, words in _EXPR_ALIASES.items():
        if any(w in low for w in words):
            return key
    return None


def expressions_by_character(shot: Mapping[str, Any]) -> Dict[str, str]:
    """Từ trường expression của shot: 'Sóc Bi (vui): ... | Dê Mun (buồn): ...' -> {tên người: khoá biểu cảm}.

    Cũng chấp nhận expression là dict/list. Khoá trả về là tên đúng như trong shot (chưa ghép id).
    """
    raw = shot.get("expression")
    out: Dict[str, str] = {}
    if isinstance(raw, Mapping):
        for k, v in raw.items():
            e = canonical_expression(str(v))
            if e:
                out[str(k)] = e
        return out
    parts: Iterable[str]
    if isinstance(raw, (list, tuple)):
        parts = [str(x) for x in raw]
    else:
        parts = str(raw or "").split("|")
    for p in parts:
        m = re.match(r"\s*([^():]+?)\s*(?:\(([^)]*)\))?\s*:", p.strip())
        if not m:
            continue
        who = m.group(1).strip()
        # "Sóc Bi (vui)" => nhãn trong ngoặc; nếu ngoặc là "100cm" thì bỏ qua
        label = m.group(2) or ""
        e = canonical_expression(label)
        if e:
            out[who] = e
    return out


def camera_view(camera: Any) -> Optional[str]:
    """Góc nhìn nhân vật gợi ý từ chuỗi camera: profile | back | three_quarter | None (chính diện).

    Quy ước (heuristic, ghi trong status/G5.md): từ khoá rõ ràng thắng; 'lateral' (lia/dolly ngang)
    => profile; góc cao/thấp hoặc dutch => three_quarter (không bao giờ chính diện phẳng).
    """
    low = str(camera or "").lower()
    if re.search(r"\b(back|rear|behind)\b|từ phía sau|from behind|over-the-shoulder|\bots\b", low):
        return "back"
    if re.search(r"profile|side[- ]view|\bside\b|lateral|tracking|nhìn ngang|góc ngang", low):
        return "profile"
    if re.search(r"3/4|three[- ]?quarter|ba phần tư|dutch|\bhigh\b|\blow\b", low):
        return "three_quarter"
    return None


def _shot_group(shot_size: Any) -> str:
    s = str(shot_size or "").strip().upper()
    if s in _FULL_SIZES:
        return "full"
    if s in _FACE_SIZES:
        return "face"
    return "mid"


def _is_motion(shot: Mapping[str, Any]) -> bool:
    text = f"{shot.get('action') or ''} {shot.get('camera') or ''}".lower()
    return any(w in text for w in _MOTION_WORDS)


# =============================================================================
# Ghép tên người trong shot với hồ sơ
# =============================================================================
def _aliases_of(data: Mapping[str, Any]) -> List[str]:
    ident = data.get("identity") or {}
    names = [str(data.get("id") or "").replace("_", " "), str(ident.get("name") or "")]
    names += [str(a) for a in (ident.get("aliases") or [])]
    out: List[str] = []
    for n in names:
        n = re.sub(r"\s*\([^)]*\)", "", n).strip()
        if n and n not in out:
            out.append(n)
    # phần trong ngoặc của name ("Sóc Nhỏ (Bi)" -> "Bi")
    out += [x.strip() for x in re.findall(r"\(([^)]*)\)", str(ident.get("name") or "")) if x.strip() and not re.search(r"\d", x)]
    return out


def match_character(name: str, characters: CharactersArg) -> Optional[str]:
    """Tên trong shot ('Sóc Bi (100cm)') -> id nhân vật. Khớp chính xác ưu tiên hơn khớp tập con."""
    cmap = _as_map(characters)
    nt = name_tokens(name)
    if not nt:
        return None
    best: Optional[Tuple[int, int, str]] = None
    for cid, data in cmap.items():
        for al in _aliases_of(data):
            at = name_tokens(al)
            if not at or not at <= nt:
                continue
            score = (1 if at == nt else 0, len(at), cid)
            if best is None or score[:2] > best[:2] or (score[:2] == best[:2] and cid < best[2]):
                best = (score[0], score[1], cid)
    return best[2] if best else None


# =============================================================================
# Chọn ảnh tham chiếu theo shot
# =============================================================================
def max_references_for_model(model_key: Optional[str]) -> Optional[int]:
    """max_references của model trong sổ models.yaml (G1). Không biết model -> None."""
    if not model_key:
        return None
    try:
        from socnhotv.core.models_registry.registry import ModelRegistry

        spec = ModelRegistry.get_instance().get(model_key)
        if spec is None:
            return None
        return int(spec.max_references) if spec.supports_reference else 0
    except Exception:
        return None


def _role_ref(data: Mapping[str, Any], role: str) -> Optional[str]:
    refs = data.get("references") or {}
    if role.startswith("expression:"):
        exprs = refs.get("expressions") or {}
        return _ref_file(exprs.get(role.split(":", 1)[1])) if isinstance(exprs, Mapping) else None
    return _ref_file(refs.get(role))


def _expression_role(data: Mapping[str, Any], emo: Optional[str]) -> Optional[str]:
    if not emo:
        return None
    exprs = (data.get("references") or {}).get("expressions") or {}
    if not isinstance(exprs, Mapping):
        return None
    for cand in (emo,) + _EXPR_FALLBACK.get(emo, ()):
        if _ref_file(exprs.get(cand)):
            return f"expression:{cand}"
    return None


def _role_priority(data: Mapping[str, Any], shot: Mapping[str, Any], emo: Optional[str]) -> List[Tuple[str, str]]:
    """[(vai trò, lý do)] theo thứ tự ưu tiên cho 1 nhân vật trong 1 shot. Tất định."""
    group = _shot_group(shot.get("shotSize"))
    view = camera_view(shot.get("camera"))
    expr_role = _expression_role(data, emo)
    order: List[Tuple[str, str]] = []

    def add(role: Optional[str], why: str) -> None:
        if role and _role_ref(data, role) and role not in [r for r, _ in order]:
            order.append((role, why))

    view_role = view if view in ("profile", "back", "three_quarter") else None
    if group == "full":
        add(view_role, f"camera '{view}' -> góc {view}")
        add("action" if _is_motion(shot) else None, "shot có chuyển động")
        add("full_body", "cỡ cảnh toàn -> toàn thân")
        add("three_quarter" if view is None else None, "bổ sung dáng 3/4")
    elif group == "face":
        add(view_role, f"camera '{view}' -> góc {view}")
        add(expr_role, f"cận mặt, biểu cảm {emo}")
        add("closeup", "cận mặt -> ảnh mặt")
        add("front", "cận mặt -> chính diện")
    else:  # mid
        add(view_role, f"camera '{view}' -> góc {view}")
        add("action" if _is_motion(shot) else None, "shot có chuyển động")
        add(expr_role, f"trung cảnh, biểu cảm {emo}")
        add("three_quarter" if view is None and group == "mid" and expr_role is None else None, "trung cảnh -> 3/4")
        add("front", "trung cảnh -> chính diện")
    # neo nhận diện + dáng người/trang phục luôn ở cuối danh sách (cắt theo ngân sách)
    add("front", "neo nhận diện (chính diện)")
    add("full_body", "neo tỉ lệ + trang phục")
    add("closeup", "bổ sung chi tiết mặt")
    return order


def plan_refs_for_shot(
    shot: Mapping[str, Any],
    characters: CharactersArg,
    *,
    max_references: Optional[int] = None,
    model: Optional[str] = None,
    characters_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Kế hoạch ảnh tham chiếu cho 1 shot: {"refs": [{characterId, role, file, path, reason}], "dropped": [...], "maxReferences": n}.

    - max_references: ưu tiên tham số; không có thì lấy từ `model` (sổ models.yaml); không có nữa thì 3.
      0 nghĩa là model không nhận ảnh tham chiếu -> refs rỗng.
    - Nhân vật nói (speaker) và nhân vật đầu danh sách được ưu tiên khi ngân sách ít hơn số nhân vật.
    - Tất định: cùng shot + cùng dữ liệu luôn ra cùng danh sách, cùng thứ tự.
    """
    cmap = _as_map(characters)
    budget = max_references
    if budget is None:
        budget = max_references_for_model(model)
    if budget is None:
        budget = DEFAULT_MAX_REFERENCES
    budget = max(0, int(budget))

    names = [str(n) for n in (shot.get("characters") or []) if str(n).strip()]
    ids: List[str] = []
    for n in names:
        cid = match_character(n, cmap)
        if cid and cid not in ids:
            ids.append(cid)
    speaker_id = match_character(str(shot.get("speaker") or ""), cmap) if shot.get("speaker") else None
    if speaker_id and speaker_id in ids:  # người nói lên đầu, còn lại giữ thứ tự xuất hiện
        ids = [speaker_id] + [i for i in ids if i != speaker_id]

    emo_by_name = expressions_by_character(shot)
    emo_by_id: Dict[str, str] = {}
    for who, e in emo_by_name.items():
        cid = match_character(who, cmap)
        if cid and cid not in emo_by_id:
            emo_by_id[cid] = e

    result: Dict[str, Any] = {"refs": [], "dropped": [], "maxReferences": budget, "unmatched": []}
    result["unmatched"] = [n for n in names if match_character(n, cmap) is None]
    if budget == 0 or not ids:
        result["dropped"] = [{"characterId": i, "reason": "model không nhận ảnh tham chiếu"} for i in ids] if budget == 0 else []
        return result

    kept = ids[:budget]
    result["dropped"] = [{"characterId": i, "reason": "vượt max_references"} for i in ids[budget:]]
    base_each, extra = divmod(budget, len(kept))
    for idx, cid in enumerate(kept):
        quota = base_each + (1 if idx < extra else 0)
        data = cmap[cid]
        prio = _role_priority(data, shot, emo_by_id.get(cid))
        taken = 0
        seen_files: set = set()
        for role, why in prio:
            if taken >= quota:
                break
            f = _role_ref(data, role)
            if not f or f in seen_files:
                continue
            seen_files.add(f)
            rel = f"{cid}/{f}"
            result["refs"].append(
                {
                    "characterId": cid,
                    "role": role,
                    "file": f,
                    "path": str(Path(characters_dir) / rel) if characters_dir is not None else rel,
                    "reason": why,
                }
            )
            taken += 1
    return result


def refs_for_shot(
    shot: Mapping[str, Any],
    characters: CharactersArg,
    *,
    max_references: Optional[int] = None,
    model: Optional[str] = None,
    characters_dir: Optional[Path] = None,
) -> List[str]:
    """Danh sách đường dẫn ảnh tham chiếu ngắn gọn cho 1 shot (xem plan_refs_for_shot)."""
    plan = plan_refs_for_shot(
        shot, characters, max_references=max_references, model=model, characters_dir=characters_dir
    )
    return [r["path"] for r in plan["refs"]]


# =============================================================================
# Khối prompt khoá
# =============================================================================
def _palette_text(palette: Mapping[str, Any]) -> str:
    parts: List[str] = []
    for part, spec in palette.items():
        hexes = spec.get("hex") if isinstance(spec, Mapping) else spec
        if isinstance(hexes, str):
            hexes = [hexes]
        if not hexes:
            continue
        label = (spec.get("en") if isinstance(spec, Mapping) else None) or part.replace("_", " ")
        parts.append(f"{label} {'/'.join(hexes)}")
    return ", ".join(parts)


def _en(item: Any) -> str:
    if isinstance(item, Mapping):
        return str(item.get("en") or "").strip()
    return str(item or "").strip()


def build_prompt_block(characters: CharactersArg, *, order: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Khối prompt khoá cho các nhân vật có mặt trong shot.

    Trả {"prompt": str, "negativePrompt": str, "scaleLock": str, "characterIds": [...]}.
    - prompt: mỗi nhân vật 1 đoạn (tên, chiều cao, bảng màu HEX, đặc điểm, trang phục mặc định).
    - negativePrompt: gộp `forbidden[].en` của mọi nhân vật (bỏ trùng, giữ thứ tự).
    - scaleLock: chỉ khi >= 2 nhân vật, sắp theo chiều cao giảm dần, lấy từ identity.heightCm.
    """
    cmap = _as_map(characters)
    ids = list(order) if order else list(cmap)
    ids = [i for i in ids if i in cmap]
    paras: List[str] = []
    neg: List[str] = []
    for cid in ids:
        d = cmap[cid]
        ident = d.get("identity") or {}
        locked = d.get("locked") or {}
        pname = ident.get("promptName") or ident.get("name") or cid
        species_en = str(ident.get("speciesEn") or "").strip()
        bits = [f"{pname} ({species_en})" if species_en else str(pname)]
        if ident.get("heightCm"):
            ratio = f" ({float(ident['scaleRatio']):.2f}x)" if ident.get("scaleRatio") else ""
            bits.append(f"exact height {ident['heightCm']:g}cm{ratio}")
        if ident.get("headBodyRatioEn"):
            bits.append(f"head-to-body ratio {ident['headBodyRatioEn']}")
        pal = _palette_text(locked.get("palette") or {})
        if pal:
            bits.append(f"locked colors: {pal}")
        feats = [_en(f) for f in (locked.get("features") or []) if _en(f)]
        if feats:
            bits.append("always: " + "; ".join(feats))
        outfit = _en(locked.get("defaultOutfit"))
        if outfit:
            bits.append(f"default outfit: {outfit}")
        paras.append(", ".join(bits))
        for f in d.get("forbidden") or []:
            e = _en(f)
            if e and e not in neg:
                neg.append(e)

    scale = ""
    if len(ids) >= 2:
        ranked = sorted(
            ((cmap[i].get("identity") or {}) for i in ids),
            key=lambda x: (-float(x.get("heightCm") or 0), str(x.get("promptName") or "")),
        )
        chain = " > ".join(
            f"{x.get('promptName') or x.get('name')} {x['heightCm']:g}cm ({float(x.get('scaleRatio') or 0):.2f}x)"
            if x.get("scaleRatio")
            else f"{x.get('promptName') or x.get('name')} {x['heightCm']:g}cm"
            for x in ranked
            if x.get("heightCm")
        )
        scale = f"Strict Scale Lock: {chain}."
    prompt = " | ".join(paras)
    if scale:
        prompt = f"{prompt} {scale}" if prompt else scale
    return {
        "prompt": prompt,
        "negativePrompt": ", ".join(neg),
        "scaleLock": scale,
        "characterIds": ids,
    }
