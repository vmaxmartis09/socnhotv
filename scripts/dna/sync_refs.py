#!/usr/bin/env python3
"""Đồng bộ ảnh DNA (characters/<id>/dna/*.png) vào referenceImages của studio_characters.json (+ studio.json từng nhân vật). Bỏ ảnh trùng nội dung."""
import hashlib, json, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2] / "data/projects/soc-nho-tv/characters"
reg = ROOT / "studio_characters.json"
data = json.loads(reg.read_text(encoding="utf-8"))
changed = False
for c in data["characters"]:
    cid = c["id"]
    seen, imgs = set(), []
    for p in sorted((ROOT / cid / "dna").glob(f"{cid}_*.png")):
        h = hashlib.md5(p.read_bytes()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        dst = ROOT / cid / p.name  # dashboard (data_routes) chỉ liệt kê ảnh ở thư mục gốc của nhân vật
        if not dst.exists():
            shutil.copy2(p, dst)
        imgs.append(f"/data/projects/soc-nho-tv/files/characters/{cid}/{p.name}")
    cuts = [f"/data/projects/soc-nho-tv/files/characters/{cid}/cutout/{p.name}" for p in sorted((ROOT / cid / "cutout").glob("*.png"))]
    if cuts and c.get("cutoutImages") != cuts:
        c["cutoutImages"] = cuts; changed = True
    pj = ROOT / cid / f"{cid}_profile.json"
    if cuts and pj.exists():
        pr = json.loads(pj.read_text(encoding="utf-8"))
        if pr.get("cutout_images") != [f"characters/{cid}/cutout/{Path(u).name}" for u in cuts]:
            pr["cutout_images"] = [f"characters/{cid}/cutout/{Path(u).name}" for u in cuts]
            pj.write_text(json.dumps(pr, ensure_ascii=False, indent=2), encoding="utf-8")
    if cid == "soc_nho" or not imgs:
        continue
    sheet = f"/data/projects/soc-nho-tv/files/characters/{cid}/{cid}_dna_sheet.png"
    new = imgs + ([sheet] if (ROOT / cid / f"{cid}_dna_sheet.png").exists() else [])
    if c.get("referenceImages") != new:
        c["referenceImages"] = new
        changed = True
        sj = ROOT / cid / "studio.json"
        if sj.exists():
            s = json.loads(sj.read_text(encoding="utf-8")); s["referenceImages"] = new
            sj.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
if changed:
    reg.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("updated")
