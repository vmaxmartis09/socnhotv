#!/usr/bin/env python3
"""Mỗi nhân vật đọc câu cửa miệng của mình bằng giọng đã gán -> voice_vault/<voice>/<id>_catchphrase.mp3, gán làm sampleAudioUrl."""
import json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
CH = ROOT / "data/projects/soc-nho-tv/characters"
reg = json.loads((CH / "studio_characters.json").read_text(encoding="utf-8"))
for c in reg["characters"]:
    cid, voice = c["id"], c["voiceId"]
    doc = (CH / cid / "persona.md")
    txt = doc.read_text(encoding="utf-8") if doc.exists() else ""
    m = re.search(r"Câu cửa miệng\*\*:\s*\n\s*-\s*\*\"?(.+?)\"?\*\s*\n", txt)
    if not m:
        print("thiếu câu cửa miệng:", cid); continue
    line = m.group(1).strip().strip('"')
    out = ROOT / f"data/shared/voice_vault/{voice}/{cid}_catchphrase.mp3"
    if not out.exists():
        r = subprocess.run([sys.executable, str(ROOT / "scripts/voice/voice_studio.py"), "speak", "--voice", voice, "--script", line, "--output", str(out)], cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0 or not out.exists():
            print("LỖI", cid, r.stderr[-200:]); continue
    url = f"/data/voices/{voice}/{out.name}"
    c["sampleAudioUrl"] = url; c["sampleText"] = line
    sj = CH / cid / "studio.json"
    if sj.exists():
        s = json.loads(sj.read_text(encoding="utf-8")); s["sampleAudioUrl"] = url; s["sampleText"] = line
        sj.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK", cid, voice, "|", line)
(CH / "studio_characters.json").write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
