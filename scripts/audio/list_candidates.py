#!/usr/bin/env python3
"""I7: liệt kê ứng viên nhạc/SFX có giấy phép CC0/CC BY từ Openverse (KHÔNG tải tệp).
Dùng: python3 scripts/audio/list_candidates.py out.json
Ẩn danh: 20 truy vấn/phút, 200/ngày -> nghỉ giữa các truy vấn."""
import json, sys, time, urllib.parse, urllib.request

API = "https://api.openverse.org/v1/audio/"
SFX_Q = {
 "footsteps": ["footsteps", "footsteps grass", "footsteps wood floor", "running footsteps", "tiptoe"],
 "door": ["door open", "door close", "door creak", "door knock", "wooden door"],
 "animal": ["squirrel", "koala", "bird chirp", "cat meow", "dog bark", "frog ribbit", "owl hoot", "rooster", "duck quack", "cow moo"],
 "nature": ["wind", "rain", "forest ambience", "water splash", "leaves rustle", "thunder"],
 "cartoon": ["whoosh", "pop", "boing", "slide whistle", "magic sparkle", "cartoon bounce", "ding", "success chime", "fail", "giggle", "applause", "bell"],
 "house": ["clock tick", "click", "button", "pour water", "munch eating", "cough", "sneeze", "yawn", "typing", "camera shutter", "heartbeat"],
}
MUSIC_Q = ["happy children", "playful ukulele", "cheerful kids", "lullaby", "storytelling calm", "whimsical", "acoustic happy", "cartoon music", "xylophone", "bouncy fun", "adventure light", "piano gentle"]

def search(q, n, extra=None):
    p = {"q": q, "license": "cc0,by", "page_size": n}
    if extra: p.update(extra)
    url = API + "?" + urllib.parse.urlencode(p)
    for _ in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "socnhotv-i7"}), timeout=30) as r:
                return json.load(r)["results"]
        except Exception as e:
            err = e; time.sleep(8)
    print("FAIL", q, err, file=sys.stderr); return []

def slim(r, q, kind, cat):
    return {"id": r["id"], "kind": kind, "category": cat, "query": q, "title": r["title"], "creator": r["creator"],
            "license": r["license"], "license_version": r.get("license_version"), "license_url": r["license_url"],
            "source": r.get("source"), "landing_url": r["foreign_landing_url"], "download_url": r["url"],
            "duration_s": round((r.get("duration") or 0)/1000, 1), "filesize": r.get("filesize"), "filetype": r.get("filetype"),
            "attribution": r.get("attribution")}

out, seen = [], set()
def add(rs, q, kind, cat, keep, maxdur):
    c = 0
    for r in rs:
        d = (r.get("duration") or 0) / 1000
        if r["id"] in seen or r["license"] not in ("cc0", "by") or not (r.get("url")): continue
        if kind == "sfx" and (d == 0 or d > maxdur): continue
        if kind == "music" and (d < 45 or d > 300): continue
        seen.add(r["id"]); out.append(slim(r, q, kind, cat)); c += 1
        if c >= keep: break

for cat, qs in SFX_Q.items():
    for q in qs:
        add(search(q, 20), q, "sfx", cat, 2, 12); time.sleep(3.2)
for q in MUSIC_Q:
    add(search(q, 20, {"category": "music"}), q, "music", "bgm", 4, 300); time.sleep(3.2)
json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
print(len(out), "candidates;", sum(1 for x in out if x["kind"]=="sfx"), "sfx;", sum(1 for x in out if x["kind"]=="music"), "music")
