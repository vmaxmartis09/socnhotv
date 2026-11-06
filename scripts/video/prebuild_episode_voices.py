#!/usr/bin/env python3
"""Dựng sẵn giọng THẬT (OmniVoice, $0, chạy trên máy) cho mọi câu thoại của 1 hay nhiều tập,
ghi thẳng vào cache giọng từng câu của bộ chạy (runs/_voice_lines/<key>.json).

Khi flow Studio chạy node Dàn diễn viên (cast) với chức năng Nói, mỗi câu tra cache theo khoá
line_cache_key(voiceId, text, tempo, mock=False) -> trúng cache thì không đọc lại (mốc M1 chạy nhanh).
Script này dùng đúng các hàm của GraphRunner (_episode_lines, _character_info, _voice_line_cache_*,
_synthesize_line) nên khoá cache luôn khớp với lúc chạy flow.

Dùng:
  .venv/bin/python scripts/video/prebuild_episode_voices.py ep01-nui-lua-trong-bung-bi ep02-mun-so-bong-toi
  .venv/bin/python scripts/video/prebuild_episode_voices.py ep01-nui-lua-trong-bung-bi --dry-run
  thêm --project <id>, --concurrency 2, --json report.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tool" / "src"))

from socnhotv.core.engine.graph_runner import GraphRunner  # noqa: E402
from socnhotv.core.storage.project_store import ProjectStore  # noqa: E402

FFMPEG = "ffmpeg"


def mean_volume_db(path: Path) -> float | None:
    try:
        from socnhotv.core.adapters.hyperframes_adapter import FFMPEG_EXE

        exe = FFMPEG_EXE or FFMPEG
    except Exception:
        exe = FFMPEG
    try:
        r = subprocess.run(
            [exe, "-hide_banner", "-nostats", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True, timeout=60,
        )
        for ln in r.stderr.splitlines():
            if "mean_volume:" in ln:
                return float(ln.split("mean_volume:")[1].split("dB")[0].strip())
    except Exception:
        return None
    return None


async def prebuild(project: str, episodes: list[str], concurrency: int, dry_run: bool) -> dict:
    store = ProjectStore(project)
    runner = GraphRunner(store)
    report: dict = {"project": project, "episodes": {}, "startedAt": time.strftime("%Y-%m-%dT%H:%M:%S")}
    sem = asyncio.Semaphore(max(1, concurrency))
    t_all = time.time()

    for ep in episodes:
        lines = runner._episode_lines(ep, "shot")
        infos: dict[str, dict] = {}
        rows: list[dict] = []

        async def one(ln: dict) -> None:
            cid = ln.get("characterId")
            text = str(ln.get("text") or "").strip()
            row = {"lineId": ln.get("id"), "shotId": ln.get("shotId"), "characterId": cid, "text": text}
            if not cid:
                row["status"] = "LỖI: câu chưa ghép được nhân vật (speaker=%s)" % ln.get("speaker")
                rows.append(row)
                return
            info = infos.get(cid) or runner._character_info(cid)
            infos[cid] = info
            vid = info.get("voiceId")
            tempo = float(info.get("defaultTempo") or 1.10)  # giống SpeakCapability khi params.tempo trống
            row.update(voiceId=vid, tempo=tempo)
            if not vid:
                row["status"] = "LỖI: nhân vật chưa có giọng (" + str(info.get("voiceMessage") or "") + ")"
                rows.append(row)
                return
            art = runner._voice_line_cache_get(vid, text, tempo, False)
            if art is not None:
                row.update(status="cache", uri=art.uri, provider=art.provenance.provider,
                           durationSec=getattr(art.meta, "duration", None) if art.meta else None)
                rows.append(row)
                return
            if dry_run:
                row["status"] = "thiếu"
                rows.append(row)
                return
            async with sem:
                t0 = time.time()
                try:
                    art = await runner._synthesize_line(text, vid, tempo, "prebuild_voice", f"prebuild_{ep}", False)
                    runner._voice_line_cache_put(vid, text, tempo, False, art)
                    row.update(status="mới", uri=art.uri, provider=art.provenance.provider,
                               durationSec=getattr(art.meta, "duration", None) if art.meta else None,
                               seconds=round(time.time() - t0, 1))
                except Exception as e:  # ghi lỗi, đi tiếp câu khác
                    row.update(status=f"LỖI: {e}", seconds=round(time.time() - t0, 1))
            rows.append(row)
            print(f"[{ep}] {row.get('shotId')} {cid} {vid}: {row['status']} {row.get('seconds', '')}", flush=True)

        t_ep = time.time()
        await asyncio.gather(*(one(ln) for ln in lines))
        rows.sort(key=lambda r: str(r.get("lineId")))
        for r in rows:
            if r.get("uri"):
                r["meanVolumeDb"] = mean_volume_db(store.project_dir / r["uri"])
        report["episodes"][ep] = {
            "lines": len(lines),
            "ok": sum(1 for r in rows if r.get("status") in ("cache", "mới")),
            "new": sum(1 for r in rows if r.get("status") == "mới"),
            "seconds": round(time.time() - t_ep, 1),
            "voices": {cid: i.get("voiceId") for cid, i in infos.items()},
            "rows": rows,
        }
    report["totalSeconds"] = round(time.time() - t_all, 1)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("episodes", nargs="+")
    ap.add_argument("--project", default="soc-nho-tv")
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true", help="Chỉ đếm câu đã có / còn thiếu trong cache")
    ap.add_argument("--json", default=None, help="Ghi báo cáo JSON ra tệp này")
    a = ap.parse_args()
    rep = asyncio.run(prebuild(a.project, a.episodes, a.concurrency, a.dry_run))
    bad = 0
    for ep, e in rep["episodes"].items():
        silent = [r for r in e["rows"] if r.get("meanVolumeDb") is not None and r["meanVolumeDb"] < -40]
        errs = [r for r in e["rows"] if str(r.get("status", "")).startswith(("LỖI", "thiếu"))]
        bad += len(errs) + len(silent)
        print(f"\n== {ep}: {e['ok']}/{e['lines']} câu có giọng thật (mới {e['new']}) · {e['seconds']}s · giọng {e['voices']}")
        for r in errs:
            print(f"   {r.get('shotId')} {r.get('characterId')}: {r['status']}")
        for r in silent:
            print(f"   {r.get('shotId')} IM LẶNG? mean_volume={r['meanVolumeDb']} dB")
    print(f"\nTổng thời gian: {rep['totalSeconds']}s")
    if a.json:
        Path(a.json).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
