#!/usr/bin/env python3
"""
voice-clone (T-06): nhân bản giọng vào kho `data/shared/voice_vault/<name>/` bằng OmniVoice sẵn có của dự án
(gọi `scripts/voice/voice_studio.py clone`, không sửa). Sau khi clone: ghi `voice.json`, thêm bản ghi vào
`voice_vault/index.jsonl`, và (mặc định) đọc thử một câu để kiểm tra giọng.

params:
  name          (bắt buộc) mã giọng, dạng slug: chữ thường, số, gạch ngang (vd "de-bong")
  display_name  (tuỳ chọn) tên hiển thị
  consent_note  (bắt buộc, >= 10 ký tự) mẫu giọng của ai và đã được đồng ý dùng làm gì
  dialect       north|south|central (mặc định "south")
  text          transcript khớp mẫu (bỏ trống: Whisper tự chép)
  duration      độ dài lát mẫu, 3.5–6.0s (mặc định 4.5)
  verify        true/false: đọc thử 1 câu sau khi clone (mặc định true)
  verify_text   câu đọc thử
  python        đường dẫn python có OmniVoice (mặc định: <repo>/.venv)

Không clone nếu: thiếu consent_note, mã giọng đã tồn tại (không ghi đè), hoặc không có file mẫu.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_DIR.parents[1] / "toolbox_cli"))
from kit import (  # noqa: E402
    REPO_ROOT, SHARED_DIR, BadInput, MissingDependency, ToolError, atomic_write, out_file, run_tool, store_record,
)

VERSION = "1.0.0"
VAULT = SHARED_DIR / "voice_vault"
STUDIO = REPO_ROOT / "scripts" / "voice" / "voice_studio.py"
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")
DEFAULT_VERIFY = "Xin chào các bạn, mình là giọng mới trong kho giọng của Sóc Nhỏ TV."


def _python(params) -> str:
    cand = [params.get("python")] if params.get("python") else []
    cand += [REPO_ROOT / ".venv" / "Scripts" / "python.exe", REPO_ROOT / ".venv" / "bin" / "python"]
    for c in cand:
        if c and Path(c).exists():
            return str(c)
    raise MissingDependency("Không thấy python của dự án có OmniVoice", "Tạo .venv ở gốc repo (uv sync) hoặc truyền params.python")


def _run(cmd, timeout):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(REPO_ROOT), timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise ToolError("OMNIVOICE_TIMEOUT", f"OmniVoice quá thời gian chờ ({timeout}s)") from e


def process(inputs, params, ctx):
    name = str(params.get("name", "")).strip()
    consent = str(params.get("consent_note", "")).strip()
    if not SLUG.match(name):
        raise BadInput("params.name phải là slug: chữ thường, số, gạch ngang, 2–41 ký tự", "BAD_NAME")
    if len(consent) < 10:
        raise BadInput("Bắt buộc có params.consent_note (>= 10 ký tự): mẫu giọng của ai và đã được đồng ý dùng làm gì", "CONSENT_REQUIRED")
    sample = inputs[0]
    if sample.suffix.lower() not in AUDIO_EXT:
        raise BadInput(f"Định dạng {sample.suffix} không phải âm thanh được hỗ trợ")
    dest = VAULT / name
    if dest.exists():
        raise BadInput(f"Giọng '{name}' đã có trong kho; không ghi đè. Chọn mã khác.", "VOICE_EXISTS")
    if not STUDIO.exists():
        raise MissingDependency(f"Không thấy {STUDIO}", "Thiếu scripts/voice/voice_studio.py của dự án")
    if ctx["dry_run"]:
        return [], [], [f"dry_run: sẽ clone '{name}' từ {sample.name}"]

    py = _python(params)
    dialect = params.get("dialect", "south")
    cmd = [py, str(STUDIO), "clone", "--input", str(sample), "--name", name, "--dialect", dialect,
           "--duration", str(params.get("duration", 4.5))]
    if params.get("text"):
        cmd += ["--text", str(params["text"])]
    r = _run(cmd, 900)
    if r.returncode != 0 or not dest.exists():
        tail = " | ".join((r.stderr or r.stdout).strip().splitlines()[-3:])
        raise ToolError("CLONE_FAILED", f"OmniVoice clone lỗi (mã {r.returncode}): {tail or 'không có chi tiết'}",
                        "Kiểm tra mẫu giọng (3.5–6s, sạch, một người nói) và checkpoint OmniVoice")

    samples = sorted(p.name for p in dest.iterdir() if p.suffix.lower() in AUDIO_EXT and not p.stem.startswith("preview"))
    outputs, warnings = [], []
    preview_path = None
    if params.get("verify", True):
        preview_path = dest / "preview_verify.mp3"
        text = str(params.get("verify_text") or DEFAULT_VERIFY)
        rv = _run([py, str(STUDIO), "speak", "--voice", name, "--script", text, "--output", str(preview_path), "--tempo", "1.0"], 600)
        if rv.returncode != 0 or not preview_path.exists() or preview_path.stat().st_size == 0:
            warnings.append("Clone xong nhưng đọc thử thất bại: " + " | ".join((rv.stderr or "").strip().splitlines()[-2:]))
            preview_path = None
        else:
            outputs.append(out_file(preview_path, "voice_preview"))

    voice_json = {
        "id": name,
        "display_name": params.get("display_name") or name,
        "aliases": [],
        "engine": "omnivoice",
        "lang": "vi",
        "dialect": dialect,
        "sample_paths": samples,
        "loudness": -14.0,
        "status": "ready",
        "consent_note": consent,
        "created_at": datetime.now().isoformat(),
        "cloned_from": sample.name,
    }
    vj = dest / "voice.json"
    atomic_write(vj, json.dumps(voice_json, ensure_ascii=False, indent=2))
    outputs.insert(0, out_file(vj, "voice_json"))
    for s in samples:
        outputs.append(out_file(dest / s, "voice_sample"))

    rec = store_record(
        name, "voice-clone", VERSION, f"voice_vault/{name}", "SocNhoTV Internal (OmniVoice, Apache-2.0)",
        {"voice_json": vj, **({"preview": preview_path} if preview_path else {})},
        {"display_name": voice_json["display_name"], "aliases": [], "engine": "omnivoice", "lang": "vi",
         "status": "ready", "loudness": -14.0, "consent_note": consent, "verified_by_speaking": bool(preview_path)},
        index=VAULT / "index.jsonl",
    )
    rec["files"]["samples"] = samples
    return outputs, [rec], warnings


if __name__ == "__main__":
    run_tool(process)
