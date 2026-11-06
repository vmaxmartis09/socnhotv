#!/usr/bin/env python3
"""Nghiệm thu 1 tập theo "Định nghĩa Done" (ai/plans/2026-11-roadmap/session-G-hai-tap-dau/README.md, mục 5).

Tự động đo:
  1. ffprobe   : 1920×1080, h264 + aac, thời lượng 600 ± 15 s
  2. âm lượng  : volumedetect mean_volume > -30 dB, loudness tích phân -14 ± 1 LUFS (ebur128)
  3. keyframe  : ≥ 30 ảnh khác nhau (sha256 nội dung tệp thật), không ảnh nào provenance.provider = "mock"
  4. giọng     : mỗi câu thoại của tập có clip, provenance OmniVoice, đúng voiceId của nhân vật
                 (đối chiếu characters/studio_characters.json), clip không im lặng, và NGHE LẠI bằng
                 faster-whisper (trên máy): không chèn câu mẫu của giọng, lời giống kịch bản ≥ 0.5
  5. snapshot  : runs/_node_outputs/<graph>/<image_gen>.json có "mock": false
Báo cáo thêm (không tự chấm ĐẠT được):
  6. contact sheet 12 khung output/<ep>/contact_sheet.jpg (tự tạo nếu chưa có) — CHỜ NGƯỜI DÙNG xác nhận
     (đạt khi có output/<ep>/user_confirm.json {"approved": true, "by": ..., "at": ...})
  7. tua trong Studio: request Range tới Core trả 206; đếm ảnh chụp shots/G*_*.png
  8. Mức B: shot có clip thật (scenes[].video từ video_gen hoặc content/episodes/<ep>/clips/<shot>.mp4)

Dùng:
  .venv/bin/python scripts/video/verify_episode.py ep01-nui-lua-trong-bung-bi
  .venv/bin/python scripts/video/verify_episode.py ep02-mun-so-bong-toi --video data/projects/soc-nho-tv/output/x/y.mp4
  thêm: --project <id>  --graph graph_<id>  --core http://127.0.0.1:8000  --level B  --allow-mock-images (mốc M1)
Kết quả: in bảng ĐẠT/KHÔNG ĐẠT, ghi output/<ep>/verify_episode.json (+ tóm tắt vào video.json nếu có).
Mã thoát 0 khi mục 1–5 ĐẠT (và mục 8 nếu --level B), ngược lại 1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
PASS, FAIL, WAIT, INFO = "ĐẠT", "KHÔNG ĐẠT", "CHỜ NGƯỜI DÙNG", "THÔNG TIN"


def _exe(name: str) -> str:
    p = shutil.which(name)
    if p:
        return p
    if name == "ffmpeg":
        try:
            import imageio_ffmpeg

            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass
    return name


FFMPEG, FFPROBE = _exe("ffmpeg"), _exe("ffprobe")


def run(cmd: List[str], timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ahash(p: Path) -> Optional[str]:
    """Băm cảm nhận 8×8 để báo ảnh gần trùng (chỉ thông tin)."""
    try:
        from PIL import Image

        im = Image.open(p).convert("L").resize((8, 8))
        px = list(im.tobytes())
        avg = sum(px) / len(px)
        return "".join("1" if v > avg else "0" for v in px)
    except Exception:
        return None


def mean_volume(path: Path, extra: Optional[List[str]] = None) -> Optional[float]:
    r = run([FFMPEG, "-hide_banner", "-nostats", "-i", str(path), *(extra or []), "-af", "volumedetect", "-vn", "-f", "null", "-"])
    m = re.search(r"mean_volume:\s*(-?[\d.]+|-inf) dB", r.stderr)
    if not m:
        return None
    return float("-inf") if m.group(1) == "-inf" else float(m.group(1))


def integrated_lufs(path: Path) -> Optional[float]:
    r = run([FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=framelog=quiet", "-f", "null", "-"])
    tail = r.stderr[r.stderr.rfind("Summary:"):] if "Summary:" in r.stderr else r.stderr
    m = re.search(r"I:\s*(-?[\d.]+) LUFS", tail)
    return float(m.group(1)) if m else None


def load_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def art_of(x: Any) -> Optional[Dict[str, Any]]:
    if isinstance(x, dict):
        if "$artifact" in x and isinstance(x["$artifact"], dict):
            return x["$artifact"]
        if "uri" in x and "provenance" in x:
            return x
    return None


class Report:
    def __init__(self) -> None:
        self.items: List[Dict[str, Any]] = []

    def add(self, no: str, name: str, status: str, detail: str, data: Any = None) -> None:
        self.items.append({"no": no, "name": name, "status": status, "detail": detail, "data": data})

    def status(self, no: str) -> Optional[str]:
        for it in self.items:
            if it["no"] == no:
                return it["status"]
        return None


# ----------------------------------------------------------------------------- tìm dữ liệu
def find_video(project_dir: Path, ep: str, explicit: Optional[str]) -> Optional[Path]:
    if explicit:
        p = Path(explicit)
        return p if p.is_absolute() else (ROOT / p)
    cand = project_dir / "output" / ep / f"{ep}.mp4"
    if cand.is_file():
        return cand
    # thư mục trùng tên do chạy lại (ep-2, ep-3 ...) hoặc video.json trỏ tới tệp <ep>.mp4 — lấy bản mới nhất
    hits = []
    for vj in (project_dir / "output").glob("*/video.json"):
        try:
            rel = (load_json(vj).get("files") or {}).get("video") or ""
        except Exception:
            continue
        if rel.endswith(f"{ep}.mp4") and (project_dir / rel).is_file():
            hits.append(project_dir / rel)
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def episode_lines(project_dir: Path, ep: str) -> List[Dict[str, Any]]:
    sj = project_dir / "content" / "episodes" / ep / "script.json"
    data = load_json(sj)
    out = []
    for sc in data.get("scenes", []):
        for sh in sc.get("shots", []):
            t = str(sh.get("dialogue") or "").strip()
            if t:
                out.append({"shotId": sh["id"], "characterId": sh.get("speakerId"), "text": t, "priority": sh.get("priority")})
    return out


def studio_voices(project_dir: Path) -> Dict[str, str]:
    p = project_dir / "characters" / "studio_characters.json"
    d = load_json(p)
    items = d.get("characters", d) if isinstance(d, dict) else d
    return {c["id"]: c.get("voiceId") for c in items if isinstance(c, dict) and c.get("id")}


def node_ids(project_dir: Path) -> Dict[str, List[str]]:
    g = load_json(project_dir / "graph.json")
    by: Dict[str, List[str]] = {}
    for n in g.get("nodes", []):
        by.setdefault(n["type"], []).append(n["id"])
    return by


def snap(snap_dir: Path, node_id: str) -> Optional[Dict[str, Any]]:
    p = snap_dir / f"{node_id}.json"
    return load_json(p) if p.is_file() else None


# ----------------------------------------------------------------------------- kiểm từng mục
def check_probe(rep: Report, video: Path) -> Dict[str, Any]:
    r = run([FFPROBE, "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate:format=duration,size",
             "-of", "json", str(video)])
    info = json.loads(r.stdout or "{}")
    v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), {})
    dur = float((info.get("format") or {}).get("duration") or 0)
    ok = v.get("width") == 1920 and v.get("height") == 1080 and v.get("codec_name") == "h264" and a.get("codec_name") == "aac" and abs(dur - 600) <= 15
    detail = (f"{v.get('width')}×{v.get('height')} {v.get('codec_name')} {v.get('r_frame_rate')} + {a.get('codec_name') or 'KHÔNG CÓ AUDIO'}"
              f" · {dur:.1f}s · {int((info.get('format') or {}).get('size') or 0) / 1e6:.0f} MB")
    rep.add("1", "ffprobe 1920×1080 h264+aac 600±15s", PASS if ok else FAIL, detail, {"video": v, "audio": a, "durationSec": dur})
    return {"duration": dur}


def check_loudness(rep: Report, video: Path) -> None:
    mv = mean_volume(video)
    lufs = integrated_lufs(video)
    ok = mv is not None and mv > -30 and lufs is not None and abs(lufs - (-14.0)) <= 1.0
    rep.add("2", "âm lượng mean > -30 dB, -14 ± 1 LUFS", PASS if ok else FAIL,
            f"mean_volume={mv} dB · integrated={lufs} LUFS", {"meanVolumeDb": mv, "lufs": lufs})


def check_keyframes(rep: Report, project_dir: Path, snap_dir: Path, img_nodes: List[str], allow_mock: bool) -> None:
    images: List[Dict[str, Any]] = []
    flags: Dict[str, Any] = {}
    for nid in img_nodes:
        s = snap(snap_dir, nid)
        if not s:
            continue
        flags[nid] = s.get("mock")
        for x in (s.get("outputs") or {}).get("images") or []:
            a = art_of(x)
            if a:
                images.append(a)
    if not images:
        rep.add("3", "≥30 keyframe khác nhau, không mock", FAIL, f"không tìm thấy ảnh trong snapshot {img_nodes}")
        rep.add("5", "snapshot image_gen mock=false", FAIL, f"không có snapshot cho {img_nodes}")
        return
    shas, missing, mock_n, providers, ah = set(), 0, 0, {}, set()
    for a in images:
        f = project_dir / a["uri"]
        prov = (a.get("provenance") or {}).get("provider") or "?"
        providers[prov] = providers.get(prov, 0) + 1
        if prov == "mock" or str((a.get("provenance") or {}).get("model") or "").startswith("mock"):
            mock_n += 1
        if f.is_file():
            shas.add(sha256_file(f))
            h = ahash(f)
            if h:
                ah.add(h)
        else:
            missing += 1
    ok = len(shas) >= 30 and mock_n == 0 and missing == 0
    st = PASS if ok else (INFO if allow_mock else FAIL)
    rep.add("3", "≥30 keyframe khác nhau, không mock", st,
            f"{len(images)} ảnh · {len(shas)} sha256 khác nhau · {len(ah)} aHash khác nhau · mock={mock_n} · thiếu tệp={missing} · nguồn={providers}"
            + (" (mốc M1: cho phép ảnh mock)" if allow_mock and not ok else ""),
            {"images": len(images), "distinctSha": len(shas), "distinctAhash": len(ah), "mock": mock_n, "providers": providers})
    all_real = all(v is False for v in flags.values())
    st5 = PASS if all_real else (INFO if allow_mock else FAIL)
    rep.add("5", "snapshot image_gen mock=false", st5, f"{flags}", flags)


# ----------------------------------------------------------------------------- nghe lại nội dung giọng (Whisper)
class Listener:
    """Nhận dạng lời bằng faster-whisper chạy trên máy ($0) để bắt lỗi nội dung mà volumedetect không thấy:
    OmniVoice chèn câu mẫu (reference_transcript) vào đầu câu khi transcript mẫu không khớp lát âm mẫu."""

    def __init__(self, model: str = "small") -> None:
        self.ok = False
        self.reason = ""
        try:
            from faster_whisper import WhisperModel

            self.m = WhisperModel(model, device="cpu", compute_type="int8", local_files_only=True)
            self.ok = True
        except Exception as e:  # thiếu thư viện / chưa tải model
            self.reason = f"không nghe lại được ({e.__class__.__name__}: {str(e)[:80]})"

    @staticmethod
    def words(s: str) -> List[str]:
        return re.sub(r"[^\w\s]", " ", str(s or "").lower()).split()

    def hear(self, path: Path) -> str:
        import numpy as np

        pcm = subprocess.run([FFMPEG, "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                             capture_output=True, timeout=120).stdout
        segs, _ = self.m.transcribe(np.frombuffer(pcm, np.float32), language="vi", beam_size=5)
        return " ".join(x.text.strip() for x in segs)

    def judge(self, text: str, heard: str, ref_text: str) -> Dict[str, Any]:
        import difflib

        a, b, r = self.words(text), self.words(heard), self.words(ref_text)
        ratio = difflib.SequenceMatcher(None, a, b).ratio()
        a3 = {tuple(a[i:i + 3]) for i in range(len(a) - 2)}
        leak = [" ".join(r[i:i + 3]) for i in range(len(r) - 2)
                if tuple(r[i:i + 3]) not in a3 and " ".join(r[i:i + 3]) in " ".join(b)]
        return {"similarity": round(ratio, 2), "leak": leak[:3], "heard": heard[:200]}


def voice_ref_text(vid: str) -> str:
    f = ROOT / "data" / "shared" / "voice_vault" / str(vid) / "reference_transcript.txt"
    return f.read_text(encoding="utf-8").strip() if f.is_file() else ""


def check_voices(rep: Report, project_dir: Path, snap_dir: Path, nodes: Dict[str, List[str]], ep: str, listen: bool = True) -> None:
    want = episode_lines(project_dir, ep)
    voices = studio_voices(project_dir)
    clips: List[Dict[str, Any]] = []
    src = []
    for nid in nodes.get("cast", []) + nodes.get("character", []):
        s = snap(snap_dir, nid)
        if s:
            v = (s.get("outputs") or {}).get("voice")
            if isinstance(v, list):
                clips += v
                src.append(nid)
    by_text = {}
    for c in clips:
        by_text.setdefault(str(c.get("text") or "").strip(), c)
    rows, bad = [], []
    ear = Listener() if listen else None
    for ln in want:
        c = by_text.get(ln["text"])
        row = {"shotId": ln["shotId"], "characterId": ln["characterId"], "expectVoice": voices.get(ln["characterId"] or "")}
        if not c:
            row["status"] = "thiếu clip"
            bad.append(row)
            rows.append(row)
            continue
        a = art_of(c.get("audio")) or {}
        prov = a.get("provenance") or {}
        row.update(voiceId=c.get("voiceId"), provider=prov.get("provider"), provVoice=(prov.get("params") or {}).get("voiceId"), uri=a.get("uri"))
        f = project_dir / str(a.get("uri") or "")
        row["meanVolumeDb"] = mean_volume(f) if f.is_file() else None
        problems = []
        if prov.get("provider") != "omnivoice":
            problems.append(f"provider={prov.get('provider')}")
        if row["expectVoice"] and (row["voiceId"] != row["expectVoice"] or (row["provVoice"] and row["provVoice"] != row["expectVoice"])):
            problems.append(f"giọng {row['voiceId']}≠{row['expectVoice']}")
        if not f.is_file():
            problems.append("thiếu tệp")
        elif row["meanVolumeDb"] is None or row["meanVolumeDb"] < -40:
            problems.append(f"im lặng? {row['meanVolumeDb']} dB")
        elif ear and ear.ok:
            j = ear.judge(ln["text"], ear.hear(f), voice_ref_text(row["voiceId"]))
            row["asr"] = j
            if j["leak"]:
                problems.append(f"chèn câu mẫu '{j['leak'][0]}'")
            elif j["similarity"] < 0.5:
                problems.append(f"lời khác kịch bản (giống {j['similarity']})")
        row["status"] = "ok" if not problems else "; ".join(problems)
        if problems:
            bad.append(row)
        rows.append(row)
    ok = bool(want) and not bad
    detail = f"{len(want) - len(bad)}/{len(want)} câu đúng (nguồn: {', '.join(src) or 'không có snapshot giọng'})"
    if ear is not None:
        sims = [r["asr"]["similarity"] for r in rows if r.get("asr")]
        detail += (f" · nghe lại Whisper: {len(sims)} câu, giống TB {sum(sims) / len(sims):.2f}" if sims
                   else f" · {ear.reason or 'chưa nghe lại câu nào'}")
    if bad:
        detail += " · lỗi: " + "; ".join(f"{r['shotId']}({r['status']})" for r in bad[:6]) + (" …" if len(bad) > 6 else "")
    rep.add("4", "giọng OmniVoice đúng voiceId từng câu", PASS if ok else FAIL, detail, rows)


def check_episode_match(rep: Report, project_dir: Path, snap_dir: Path, nodes: Dict[str, List[str]], ep: str) -> bool:
    """Snapshot hiện tại có đúng là của tập này không (snapshot chỉ giữ lần chạy mới nhất của mỗi node)."""
    want = {ln["text"] for ln in episode_lines(project_dir, ep)}
    got = set()
    for nid in nodes.get("script", []):
        s = snap(snap_dir, nid)
        for ln in ((s or {}).get("outputs") or {}).get("lines") or []:
            got.add(str(ln.get("text") or "").strip())
    match = len(want & got) / max(1, len(want))
    rep.add("0", "snapshot flow thuộc đúng tập", PASS if match >= 0.9 else FAIL,
            f"{match:.0%} câu thoại trong snapshot node Kịch bản khớp {ep}", {"match": match})
    return match >= 0.9


def contact_sheet(rep: Report, project_dir: Path, ep: str, video: Path, duration: float) -> None:
    out_dir = project_dir / "output" / ep
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet = out_dir / "contact_sheet.jpg"
    made = False
    if not sheet.is_file() or sheet.stat().st_mtime < video.stat().st_mtime:
        tmp = out_dir / ".cs_frames"
        tmp.mkdir(exist_ok=True)
        dur = duration or 600
        for i in range(12):
            t = dur * (i + 0.5) / 12
            run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                 "-vf", "scale=640:-2", str(tmp / f"f{i:02d}.jpg")], timeout=120)
        r = run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(tmp / "f%02d.jpg"), "-vf", "tile=4x3:padding=6:margin=6",
                 "-frames:v", "1", str(sheet)], timeout=120)
        shutil.rmtree(tmp, ignore_errors=True)
        made = r.returncode == 0
    confirm = out_dir / "user_confirm.json"
    approved = False
    if confirm.is_file():
        try:
            c = load_json(confirm)
            approved = bool(c.get("approved")) and Path(str(c.get("video") or video)).name == video.name
        except Exception:
            approved = False
    rel = sheet.relative_to(ROOT) if sheet.is_file() else "—"
    rep.add("6", "contact sheet 12 khung + người dùng duyệt DNA/tỉ lệ", PASS if approved else WAIT,
            f"{rel}{' (vừa tạo)' if made else ''} · " + ("người dùng đã xác nhận" if approved else "chưa có xác nhận của người dùng"),
            {"sheet": str(rel), "approved": approved})


def check_range(rep: Report, project: str, project_dir: Path, video: Path, core: str) -> None:
    rel = video.relative_to(project_dir).as_posix()
    url = f"{core.rstrip('/')}/projects/{project}/files/{rel}"
    size = video.stat().st_size
    start = max(0, int(size * 0.9))
    code, crange = None, None
    try:
        req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{start + 1023}"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            code, crange = resp.status, resp.headers.get("content-range")
    except Exception as e:
        crange = f"lỗi: {e}"
    shots = sorted(p.name for p in (project_dir / "shots").glob("G*_*.png"))
    ok = code == 206
    rep.add("7", "tua được: Range → 206 (+ ảnh chụp Studio)", PASS if ok else FAIL,
            f"{url} → {code} {crange} · ảnh chụp G*: {len(shots)}", {"url": url, "status": code, "shots": shots[-10:]})


def check_level_b(rep: Report, project_dir: Path, snap_dir: Path, nodes: Dict[str, List[str]], ep: str, required: bool) -> None:
    clips: Dict[str, str] = {}
    for nid in nodes.get("video_gen", []):
        s = snap(snap_dir, nid)
        for sc in ((s or {}).get("outputs") or {}).get("scenes") or []:
            v = sc.get("video") if isinstance(sc, dict) else None
            a = art_of(v)
            sid = sc.get("shotId") or sc.get("id")
            if a and sid:
                prov = a.get("provenance") or {}
                if prov.get("provider") != "mock":
                    clips[str(sid)] = f"{prov.get('provider')}/{prov.get('model')}"
            elif isinstance(v, str) and v and sid:
                clips[str(sid)] = f"tệp {v}"
    for f in sorted((project_dir / "content" / "episodes" / ep / "clips").glob("*.mp4")):
        clips.setdefault(f.stem, "làm tay (clips/)")
    n = len(clips)
    st = (PASS if n >= 5 else FAIL) if required else INFO
    rep.add("8", "Mức B: ≥5 shot có clip thật", st, f"{n} shot: " + ", ".join(f"{k}→{v}" for k, v in sorted(clips.items())) if clips else "0 shot có clip", clips)


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("episode")
    ap.add_argument("--project", default="soc-nho-tv")
    ap.add_argument("--graph", default=None, help="thư mục snapshot runs/_node_outputs/<graph> (mặc định graph_<project>)")
    ap.add_argument("--video", default=None)
    ap.add_argument("--core", default="http://127.0.0.1:8000")
    ap.add_argument("--level", default="A", choices=["A", "B"])
    ap.add_argument("--allow-mock-images", action="store_true", help="mốc M1: mục 3 & 5 chỉ báo, không chấm trượt")
    ap.add_argument("--json", default=None, help="ghi thêm báo cáo JSON ra tệp này")
    ap.add_argument("--no-listen", action="store_true", help="bỏ bước nghe lại lời thoại bằng Whisper (mục 4)")
    a = ap.parse_args()

    ep = a.episode
    project_dir = ROOT / "data" / "projects" / a.project
    snap_dir = project_dir / "runs" / "_node_outputs" / (a.graph or f"graph_{a.project}")
    rep = Report()
    t0 = time.time()

    video = find_video(project_dir, ep, a.video)
    nodes = node_ids(project_dir)
    if not video or not video.is_file():
        rep.add("1", "ffprobe 1920×1080 h264+aac 600±15s", FAIL, f"không tìm thấy video của {ep} (output/{ep}/{ep}.mp4)")
        dur = 0.0
    else:
        dur = check_probe(rep, video)["duration"]
        check_loudness(rep, video)
    same_ep = check_episode_match(rep, project_dir, snap_dir, nodes, ep)
    if same_ep:
        check_keyframes(rep, project_dir, snap_dir, nodes.get("image_gen", []), a.allow_mock_images)
        check_voices(rep, project_dir, snap_dir, nodes, ep, listen=not a.no_listen)
    else:
        for no, name in (("3", "≥30 keyframe khác nhau, không mock"), ("4", "giọng OmniVoice đúng voiceId từng câu"), ("5", "snapshot image_gen mock=false")):
            rep.add(no, name, FAIL, "snapshot flow hiện tại là của tập khác → chạy lại flow cho tập này rồi kiểm")
    if video and video.is_file():
        contact_sheet(rep, project_dir, ep, video, dur)
        check_range(rep, a.project, project_dir, video, a.core)
    check_level_b(rep, project_dir, snap_dir, nodes, ep, a.level == "B")

    core_ok = all(rep.status(n) in (PASS, INFO) for n in ("1", "2", "3", "4", "5")) and rep.status("0") == PASS
    if a.allow_mock_images:
        core_ok = core_ok and all(rep.status(n) == PASS for n in ("1", "2", "4"))
    if a.level == "B":
        core_ok = core_ok and rep.status("8") == PASS
    verdict = "ĐẠT mục 1–5" if core_ok else "CHƯA ĐẠT"
    if core_ok and rep.status("6") != PASS:
        verdict += " · CHỜ người dùng duyệt contact sheet (mục 6) — CHƯA được báo 'xong'"

    order = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8}
    rep.items.sort(key=lambda it: order.get(it["no"], 99))
    print(f"\nNGHIỆM THU {ep}  ·  video: {video.relative_to(ROOT) if video else '—'}  ·  mức {a.level}" + ("  ·  (M1: cho phép ảnh mock)" if a.allow_mock_images else ""))
    print("-" * 110)
    for it in rep.items:
        print(f" {it['no']:>2}  {it['status']:<15} {it['name']:<44} {it['detail']}")
    print("-" * 110)
    print(f" KẾT LUẬN: {verdict}   ({time.time() - t0:.0f}s)\n")

    result = {
        "episodeId": ep, "project": a.project, "video": str(video.relative_to(ROOT)) if video else None, "level": a.level,
        "allowMockImages": a.allow_mock_images, "verdict": verdict, "pass1to5": core_ok,
        "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "items": rep.items,
    }
    out_dir = project_dir / "output" / ep
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "verify_episode.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.json:
        Path(a.json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if video:
        vj = video.parent / "video.json"
        if vj.is_file():
            try:
                m = load_json(vj)
                m["episodeVerify"] = {
                    "verdict": verdict, "pass1to5": core_ok, "checkedAt": result["checkedAt"],
                    "items": {it["no"]: it["status"] for it in rep.items},
                }
                vj.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass
    return 0 if core_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
