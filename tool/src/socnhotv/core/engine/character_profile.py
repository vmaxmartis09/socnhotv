"""Hồ sơ nhân vật cho bộ chạy đồ thị.

- Đọc hồ sơ thật trong characters/studio_characters.json của dự án (tên, chiều cao, promptLock, voiceId...).
- Tìm giọng trong kho (data/shared/voice_vault hoặc characters/<id>/voice) từ voiceId của nhân vật.
  Không tìm thấy thì trả None kèm lý do, KHÔNG âm thầm dùng giọng Sóc Nhỏ.
- Ghép tên người nói trong kịch bản ("Sóc Bi (100cm)", "Dê Mun", "Mẹ Sóc") với nhân vật của dự án.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


def name_tokens(name: str) -> Set[str]:
    """Chuẩn hoá tên thành tập từ: bỏ '(100cm)', bỏ dấu tiếng Việt, chữ thường."""
    s = re.sub(r"\([^)]*\)", " ", str(name or "")).replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()
    return {t for t in re.split(r"[^a-z0-9]+", s) if t}


def _slug(name: str) -> str:
    s = str(name or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


# ------------------------------------------------------------------ hồ sơ
def load_profiles(characters_dir: Path) -> List[Dict[str, Any]]:
    f = Path(characters_dir) / "studio_characters.json"
    try:
        if f.is_file():
            raw = json.loads(f.read_text(encoding="utf-8"))
            items = raw if isinstance(raw, list) else (raw.get("characters") or [])
            return [c for c in items if isinstance(c, dict) and c.get("id")]
    except Exception:
        pass
    return []


def load_profile(characters_dir: Path, char_id: str) -> Optional[Dict[str, Any]]:
    for c in load_profiles(characters_dir):
        if c.get("id") == char_id:
            return c
    return None


def character_aliases(char_id: str, profile: Optional[Dict[str, Any]]) -> List[str]:
    """Các tên gọi của nhân vật: id, tên bỏ phần trong ngoặc, từng phần trong ngoặc, aliases khai báo."""
    names: List[str] = [char_id.replace("_", " ").replace("-", " ")]
    if profile:
        nm = str(profile.get("name") or "")
        if nm:
            names.append(re.sub(r"\s*\([^)]*\)", "", nm).strip())
            names.extend(x.strip() for x in re.findall(r"\(([^)]*)\)", nm))
        names.extend(str(a) for a in (profile.get("aliases") or []) if a)
    seen: List[str] = []
    for n in names:
        n = n.strip()
        if n and n not in seen:
            seen.append(n)
    return seen


# ------------------------------------------------------------------ ảnh DNA tham chiếu
_NOT_REFERENCE = re.compile(r"(dna_sheet|sheet|turnaround|back|_old|cutout)", re.IGNORECASE)


def dna_reference_files(characters_dir: Path, char_id: str, profile: Optional[Dict[str, Any]] = None,
                        limit: int = 3) -> List[Path]:
    """Ảnh DNA dùng làm tham chiếu khi sinh ảnh (tốt nhất trước).

    1. `dnaReferences` trong hồ sơ (tên tệp trong characters/<id>/, do người/AI đã xem và chọn).
    2. Không có: mọi *.png trong thư mục nhân vật trừ bảng DNA / quay lưng / cutout, ưu tiên `_02` (chính diện
       đứng thẳng) rồi `_01`, rồi theo tên. Trước đây bộ chạy lấy 4 ảnh đầu theo tên -> dính ảnh quay lưng `_04`.
    """
    d = Path(characters_dir) / char_id
    if not d.is_dir():
        return []
    prof = profile if profile is not None else load_profile(characters_dir, char_id)
    out: List[Path] = []
    for name in (prof or {}).get("dnaReferences") or []:
        p = d / Path(str(name)).name
        if p.is_file() and p not in out:
            out.append(p)
    if not out:
        pngs = [p for p in sorted(d.glob("*.png")) if not _NOT_REFERENCE.search(p.stem)]

        def rank(p: Path) -> Tuple[int, str]:
            m = re.search(r"_(\d+)$", p.stem)
            n = int(m.group(1)) if m else 99
            return ({2: 0, 1: 1}.get(n, 2), p.name)

        out = sorted(pngs, key=rank)
    return out[: max(1, limit)]


# ------------------------------------------------------------------ giọng
def _read_voice_meta(d: Path) -> Dict[str, Any]:
    f = d / "voice.json"
    try:
        if f.is_file():
            data = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def resolve_voice_id(
    voice_id: Optional[str],
    char_id: str,
    aliases: List[str],
    vault_dir: Path,
    project_characters_dir: Optional[Path] = None,
) -> Tuple[Optional[str], str, str]:
    """Tìm id giọng dùng được trong kho cho nhân vật.

    Trả (voiceId | None, trạng thái, thông báo). Trạng thái: "ready" | "todo_clone" | ... | "missing".
    Thứ tự thử: voiceId khai báo, voiceId bỏ hậu tố _v1, đổi '_' <-> '-', id nhân vật, rồi tra
    `aliases` trong voice.json của từng giọng trong kho.
    """
    vault_dir = Path(vault_dir)
    cands: List[str] = []

    def add(x: Optional[str]) -> None:
        x = str(x or "").strip()
        if not x:
            return
        for v in (x, re.sub(r"[_-]v\d+$", "", x)):
            for w in (v, v.replace("_", "-"), v.replace("-", "_")):
                if w and w not in cands:
                    cands.append(w)

    add(voice_id)
    add(char_id)

    def status_of(vid: str) -> Optional[Tuple[str, str]]:
        if project_characters_dir is not None and (Path(project_characters_dir) / vid / "voice").is_dir():
            return vid, "ready"
        d = vault_dir / vid
        if d.is_dir():
            meta = _read_voice_meta(d)
            return str(meta.get("id") or vid), str(meta.get("status") or "ready")
        return None

    for c in cands:
        hit = status_of(c)
        if hit:
            return _verdict(hit[0], hit[1], char_id)

    # Tra bí danh trong kho: voiceId/id nhân vật/tên gọi nhân vật (dạng slug)
    keys = {c.lower() for c in cands} | {_slug(a) for a in aliases if a}
    keys |= {f"voice-{k}" for k in list(keys)} | {f"be-{k}" for k in list(keys)}
    if vault_dir.is_dir():
        for d in sorted(p for p in vault_dir.iterdir() if p.is_dir()):
            meta = _read_voice_meta(d)
            vault_aliases = {str(a).lower() for a in (meta.get("aliases") or [])}
            if keys & vault_aliases:
                return _verdict(str(meta.get("id") or d.name), str(meta.get("status") or "ready"), char_id)

    shown = voice_id or "(chưa khai báo)"
    return None, "missing", f"Nhân vật '{char_id}' chưa có giọng trong kho (voiceId {shown}). Chọn 1 giọng có sẵn hoặc clone giọng mới."


def _verdict(vid: str, status: str, char_id: str) -> Tuple[Optional[str], str, str]:
    if status == "ready":
        return vid, status, ""
    return None, status, (
        f"Giọng '{vid}' của nhân vật '{char_id}' chưa dùng được (trạng thái {status}: chưa có mẫu giọng). "
        "Cấp mẫu để clone hoặc chọn 1 giọng có sẵn."
    )


# ------------------------------------------------------------------ ghép người nói
def match_speaker(speaker: str, profiles: List[Dict[str, Any]]) -> Optional[str]:
    """Ghép tên người nói trong kịch bản với id nhân vật. Chọn bí danh khớp nhiều từ nhất; hoà thì bỏ (không đoán)."""
    sp = name_tokens(speaker)
    if not sp:
        return None
    best: Optional[str] = None
    best_score = 0
    tie = False
    for p in profiles:
        cid = str(p.get("id"))
        score = 0
        for a in character_aliases(cid, p):
            at = name_tokens(a)
            # Bí danh phải nằm trọn trong tên người nói VÀ phủ ít nhất nửa số từ của tên
            # ("Sóc Bi" khớp "Bi", nhưng "Ông Kẹ Bí Ẩn" không khớp "Bi")
            if at and at <= sp and len(at) * 2 >= len(sp):
                s = len(at) * 10 + (5 if at == sp else 0)
                score = max(score, s)
        if score > best_score:
            best, best_score, tie = cid, score, False
        elif score and score == best_score:
            tie = True
    return None if tie else best
