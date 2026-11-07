#!/usr/bin/env python3
"""Dựng / kiểm / duyệt hồ sơ nhất quán `characters/<id>/consistency.json` (G5, pha 1).

Quy trình (NGƯỜI DÙNG duyệt trước khi khoá):
  1) python scripts/characters/build_consistency.py --suggest soc_nho     # số đo từng ảnh ứng viên (không ghi gì)
  2) python scripts/characters/build_consistency.py --build               # ghi consistency.json, status = "proposed"
  3) python scripts/characters/build_consistency.py --sheet               # contact sheet để người dùng xem bằng mắt
  4) người dùng xác nhận ->  python scripts/characters/build_consistency.py --approve --by "<tên>"
  5) python scripts/characters/build_consistency.py --check               # kiểm hợp lệ (tệp tồn tại, SCALE_LOCK, vai trò)

Không có id thì làm cho 5 nhân vật Tập 1–2. Thêm --project <id> (mặc định soc-nho-tv).
Số đo (chiều cao, bảng màu HEX, tên, giọng) đọc từ SCALE_LOCK.md, <id>_profile.json, studio_characters.json.
Đề xuất ảnh theo vai trò nằm ở scripts/characters/g5_seeds.py (AI xem ảnh rồi đề xuất, người dùng quyết).
Chỉ dùng thư viện chuẩn + Pillow, không gọi model, chi phí $0.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tool" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from g5_seeds import DEFAULT_IDS, EXCLUDED_FROM_REFS, PART_EN, SEEDS  # noqa: E402
from socnhotv.core.engine import character_consistency as cc  # noqa: E402

_HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")


def characters_dir(project: str) -> Path:
    return ROOT / "data" / "projects" / project / "characters"


# ------------------------------------------------------------------ đọc nguồn số đo
def _read_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _studio_profile(cdir: Path, cid: str) -> Dict[str, Any]:
    raw = _read_json(cdir / "studio_characters.json")
    items = raw if isinstance(raw, list) else raw.get("characters", [])
    for c in items:
        if c.get("id") == cid:
            return c
    raise SystemExit(f"studio_characters.json không có nhân vật {cid}")


def _palette_from_profile(colors: Dict[str, Any]) -> Dict[str, Any]:
    pal: Dict[str, Any] = {}
    for part, val in colors.items():
        if part == "swatches" or not isinstance(val, str):
            continue
        hexes = [h.upper() for h in _HEX.findall(val)]
        if not hexes:
            continue
        uniq: List[str] = []
        for h in hexes:
            if h not in uniq:
                uniq.append(h)
        pal[part] = {"hex": uniq, "en": PART_EN.get(part, part.replace("_", " ")), "note": re.sub(r"\s+", " ", val).strip()}
    return pal


def build_one(cdir: Path, cid: str, scale: Dict[str, float]) -> Dict[str, Any]:
    if cid not in SEEDS:
        raise SystemExit(f"Chưa có seed cho {cid} (g5_seeds.py)")
    seed = SEEDS[cid]
    prof_path = cdir / cid / f"{cid}_profile.json"
    prof = _read_json(prof_path)
    studio = _studio_profile(cdir, cid)

    height = float(studio.get("heightCm") or prof.get("height_cm"))
    if cid in scale and float(scale[cid]) != height:
        raise SystemExit(f"{cid}: heightCm {height} lệch SCALE_LOCK.md {scale[cid]} - sửa nguồn trước")
    ratio = float(studio.get("scaleRatio") or prof.get("scale_ratio") or round(height / scale.get("soc_nho", 100.0), 2))
    age = re.search(r"[\d.]+", str(prof.get("age", "")))

    refs: Dict[str, Any] = {}
    for role, val in seed["refs"].items():
        if role == "expressions":
            refs["expressions"] = {k: {"file": f, "note": n} for k, (f, n) in val.items()}
        else:
            f, n = val
            refs[role] = {"file": f, "note": n}

    return {
        "schemaVersion": cc.SCHEMA_VERSION,
        "id": cid,
        "status": "proposed",
        "proposedBy": "ai-g5",
        "proposedAt": dt.date.today().isoformat(),
        "approvedBy": None,
        "approvedAt": None,
        "identity": {
            "name": studio.get("name") or prof.get("name"),
            "promptName": seed["promptName"],
            "aliases": seed["aliases"],
            "species": prof.get("species"),
            "speciesEn": seed["speciesEn"],
            "ageYears": float(age.group(0)) if age else None,
            "role": studio.get("role"),
            "heightCm": height,
            "scaleRatio": ratio,
            "weightKg": prof.get("weight_kg"),
            "headBodyRatio": prof.get("head_body_ratio"),
            "headBodyRatioEn": seed["headBodyRatioEn"],
            "scaleNote": (prof.get("body") or {}).get("scale_note") or prof.get("scale_note"),
            "relativeHeights": {
                other: round(height / h, 2) for other, h in sorted(scale.items()) if other != cid and h
            },
        },
        "locked": {
            "palette": _palette_from_profile(prof.get("colors") or {}),
            "swatches": [s.upper() for s in (prof.get("colors") or {}).get("swatches", [])],
            "features": seed["features"],
            "defaultOutfit": seed["defaultOutfit"],
            "promptLock": studio.get("promptLock") or prof.get("prompt_lock"),
        },
        "forbidden": seed["forbidden"],
        "references": refs,
        "gaps": seed.get("gaps", []),
        "excludedFromRefs": list(EXCLUDED_FROM_REFS),
        "voice": {
            "voiceId": studio.get("voiceId") or prof.get("voice_id"),
            "note": prof.get("voice_description"),
            "defaultTempo": studio.get("defaultTempo"),
        },
        "scoring": {"threshold": 0.7, "maxRegenerations": 2},
    }


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ gợi ý (số đo ảnh)
def analyze_image(path: Path) -> Dict[str, Any]:
    """Số đo rẻ để xếp hạng ứng viên: tỉ lệ khung bị nhân vật chiếm, độ đối xứng, độ đơn giản của nền."""
    from PIL import Image, ImageChops, ImageStat

    im = Image.open(path).convert("RGBA")
    w, h = im.size
    alpha = im.getchannel("A")
    lo, _hi = alpha.getextrema()
    if lo < 250:  # PNG cắt nền: dùng kênh alpha
        mask = alpha.point(lambda v: 255 if v > 32 else 0)
    else:  # nền đặc: so với màu viền
        rgb = im.convert("RGB")
        border = [rgb.getpixel((x, y)) for x in range(0, w, max(1, w // 16)) for y in (0, h - 1)]
        border += [rgb.getpixel((x, y)) for y in range(0, h, max(1, h // 16)) for x in (0, w - 1)]
        med = tuple(sorted(c[i] for c in border)[len(border) // 2] for i in range(3))
        diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, med)).convert("L")
        mask = diff.point(lambda v: 255 if v > 28 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return {"fill": 0.0, "symmetry": 0.0, "bgStd": 0.0, "bbox": None}
    x0, y0, x1, y1 = bbox
    crop = mask.crop(bbox)
    mir = crop.transpose(Image.FLIP_LEFT_RIGHT)
    sym = 1.0 - ImageStat.Stat(ImageChops.difference(crop, mir)).mean[0] / 255.0
    bg = Image.composite(Image.new("L", mask.size, 0), im.convert("L"), mask)  # chỉ pixel nền
    border_std = ImageStat.Stat(im.convert("L").crop((0, 0, w, max(2, h // 12)))).stddev[0]
    return {
        "fill": round((y1 - y0) / h, 3),
        "symmetry": round(sym, 3),
        "bgStd": round(border_std, 2),
        "bbox": [x0, y0, x1, y1],
    }


def cmd_suggest(cdir: Path, cid: str) -> None:
    files = sorted(p for p in (cdir / cid).glob(f"{cid}_*.png") if not any(p.name.endswith(s) for s in EXCLUDED_FROM_REFS))
    print(f"\n== {cid}: {len(files)} ảnh ứng viên (fill = chiều cao nhân vật / khung; sym = độ đối xứng, cao ~ chính diện)")
    for p in files:
        m = analyze_image(p)
        close = "có vẻ cận mặt" if m["fill"] >= 0.9 else "-"
        print(f"  {p.name:28s} fill={m['fill']:.2f} sym={m['symmetry']:.2f} nền_std={m['bgStd']:5.1f}  {close}")
    print("  (đã đo thử: chỉ nhận ra ảnh cận mặt (fill>=0.9); KHÔNG phân biệt được toàn thân/trung cảnh hay chính diện/lưng/nghiêng. Vai trò do con mắt người/AI xem contact sheet, ghi ở g5_seeds.py)")


# ------------------------------------------------------------------ contact sheet
def _thumb(path: Path, size: Tuple[int, int]):
    from PIL import Image

    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (236, 236, 236, 255))
    bg.alpha_composite(im)
    bg = bg.convert("RGB")
    bg.thumbnail(size)
    canvas = Image.new("RGB", size, (236, 236, 236))
    canvas.paste(bg, ((size[0] - bg.width) // 2, (size[1] - bg.height) // 2))
    return canvas


def _font(size: int):
    """Font có dấu tiếng Việt (font mặc định của PIL không có). Không tìm được thì dùng mặc định."""
    from PIL import ImageFont

    for f in (
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            continue
    return ImageFont.load_default()


def cmd_sheet(cdir: Path, ids: List[str], out_dir: Path) -> List[Path]:
    from PIL import Image, ImageDraw

    f12, f14 = _font(12), _font(14)

    out_dir.mkdir(parents=True, exist_ok=True)
    outs: List[Path] = []
    cell = (320, 200)
    head, foot = 26, 30
    for cid in ids:
        data = cc.load_consistency(cdir, cid)
        if not data:
            print(f"{cid}: chưa có consistency.json (chạy --build trước)")
            continue
        items = cc.iter_reference_files(data)
        # gộp vai trò dùng chung 1 tệp để người xem thấy rõ ảnh nào đóng nhiều vai
        by_file: Dict[str, List[str]] = {}
        for role, f in items:
            by_file.setdefault(f, []).append(role)
        gaps = [g.get("role", "") for g in data.get("gaps", [])]
        cols = 4
        rows = (len(by_file) + cols - 1) // cols
        W, H = cols * cell[0], head + rows * (cell[1] + foot) + 22
        sheet = Image.new("RGB", (W, H), (255, 255, 255))
        d = ImageDraw.Draw(sheet)
        pal = " ".join(h for spec in data["locked"]["palette"].values() for h in spec["hex"][:1])
        d.text((6, 4), f"{cid} | {data['identity']['name']} | {data['identity']['heightCm']:g}cm | status={data['status']} | {len(by_file)} ảnh", fill=(0, 0, 0), font=f14)
        for i, (f, roles) in enumerate(by_file.items()):
            x, y = (i % cols) * cell[0], head + (i // cols) * (cell[1] + foot)
            sheet.paste(_thumb(cdir / cid / f, cell), (x, y))
            d.rectangle([x, y + cell[1], x + cell[0], y + cell[1] + foot], fill=(30, 30, 30))
            d.text((x + 4, y + cell[1] + 2), f, fill=(255, 255, 255), font=f12)
            d.text((x + 4, y + cell[1] + 15), ", ".join(roles)[:52], fill=(255, 214, 90), font=f12)
        y = H - 18
        d.text((6, y), "thiếu: " + (", ".join(gaps) if gaps else "không") + f"   | màu khoá: {pal}"[:150], fill=(150, 0, 0), font=f12)
        p = out_dir / f"{cid}.jpg"
        sheet.save(p, quality=88)
        outs.append(p)
    # một tờ tổng
    if outs:
        ims = [Image.open(p) for p in outs]
        W = max(i.width for i in ims)
        H = sum(i.height for i in ims)
        all_sheet = Image.new("RGB", (W, H), (255, 255, 255))
        y = 0
        for i in ims:
            all_sheet.paste(i, (0, y))
            y += i.height
        pa = out_dir / "ALL.jpg"
        all_sheet.save(pa, quality=85)
        outs.append(pa)
    return outs


# ------------------------------------------------------------------ duyệt / kiểm
def cmd_approve(cdir: Path, cid: str, by: str) -> None:
    data = cc.load_consistency(cdir, cid)
    if not data:
        raise SystemExit(f"{cid}: chưa có consistency.json")
    rep = cc.validate_consistency(data, cdir, cc.parse_scale_lock(cdir / "SCALE_LOCK.md"))
    if rep["errors"]:
        raise SystemExit(f"{cid}: còn lỗi, không duyệt: {rep['errors']}")
    data["status"] = "approved"
    data["approvedBy"] = by
    data["approvedAt"] = dt.date.today().isoformat()
    write_json(cc.consistency_path(cdir, cid), data)
    print(f"{cid}: đã duyệt bởi {by}")


def cmd_check(cdir: Path, ids: List[str]) -> int:
    scale = cc.parse_scale_lock(cdir / "SCALE_LOCK.md")
    bad = 0
    for cid in ids:
        data = cc.load_consistency(cdir, cid)
        if not data:
            print(f"[THIẾU] {cid}: không có consistency.json")
            bad += 1
            continue
        rep = cc.validate_consistency(data, cdir, scale)
        n = cc.distinct_reference_count(data)
        flag = "LỖI" if rep["errors"] else "ok"
        print(f"[{flag}] {cid}: status={data.get('status')} ảnh_khác_nhau={n} errors={rep['errors']} warnings={rep['warnings']}")
        bad += 1 if rep["errors"] else 0
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="id nhân vật (mặc định: 5 nhân vật Tập 1–2)")
    ap.add_argument("--project", default="soc-nho-tv")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--suggest", action="store_true", help="in số đo từng ảnh ứng viên, không ghi gì")
    g.add_argument("--build", action="store_true", help="ghi consistency.json (status=proposed)")
    g.add_argument("--sheet", action="store_true", help="dựng contact sheet để người dùng duyệt bằng mắt")
    g.add_argument("--approve", action="store_true", help="khoá hồ sơ sau khi người dùng xác nhận (cần --by)")
    g.add_argument("--check", action="store_true", help="kiểm hợp lệ")
    ap.add_argument("--by", default="", help="tên người duyệt (bắt buộc với --approve)")
    ap.add_argument("--out", default="", help="thư mục ra cho --sheet (mặc định characters/consistency_review)")
    ap.add_argument("--force", action="store_true", help="--build ghi đè cả hồ sơ đã approved")
    a = ap.parse_args()

    cdir = characters_dir(a.project)
    ids = a.ids or DEFAULT_IDS
    scale = cc.parse_scale_lock(cdir / "SCALE_LOCK.md")

    if a.suggest:
        for cid in ids:
            cmd_suggest(cdir, cid)
        return 0
    if a.sheet:
        outs = cmd_sheet(cdir, ids, Path(a.out) if a.out else cdir / "consistency_review")
        for p in outs:
            print(p)
        return 0
    if a.approve:
        if not a.by.strip():
            raise SystemExit("--approve cần --by '<tên người duyệt>'")
        for cid in ids:
            cmd_approve(cdir, cid, a.by.strip())
        return 0
    if a.check:
        return 1 if cmd_check(cdir, ids) else 0
    # mặc định = --build
    for cid in ids:
        cur = cc.load_consistency(cdir, cid)
        if cur and cur.get("status") == "approved" and not a.force:
            print(f"{cid}: đã approved, bỏ qua (dùng --force để ghi đè)")
            continue
        data = build_one(cdir, cid, scale)
        write_json(cc.consistency_path(cdir, cid), data)
        rep = cc.validate_consistency(data, cdir, scale)
        print(f"{cid}: ghi {cc.consistency_path(cdir, cid).relative_to(ROOT)} | ảnh khác nhau={cc.distinct_reference_count(data)} | {rep}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
