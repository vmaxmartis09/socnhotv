#!/usr/bin/env python3
"""
Runner kit: khung chung cho tool Toolbox, đúng hợp đồng chạy (T0_TOOLBOX_PROMPT.md §2.3).

Tool chỉ viết `process(inputs, params, ctx)` và trả về (outputs, store_records, warnings);
kit lo đọc --in, ghi --out (atomic), mã thoát (0 ok · 2 thiếu phụ thuộc/model · 3 đầu vào sai · 1 lỗi khác).

Lỗi thật thì báo lỗi thật: không tạo file giả.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

KIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = KIT_DIR.parents[2]
SHARED_DIR = REPO_ROOT / "data" / "shared"
FFMPEG_DIR = SHARED_DIR / "models" / "ffmpeg-bin"

if str(KIT_DIR) not in sys.path:
    sys.path.insert(0, str(KIT_DIR))
from store import append_index_record, atomic_write, compute_sha256, compute_sha8  # noqa: E402,F401

# ffmpeg dùng chung của Toolbox (không sửa PATH hệ thống, chỉ tiến trình này)
if FFMPEG_DIR.exists():
    os.environ["PATH"] = str(FFMPEG_DIR.resolve()) + os.pathsep + os.environ.get("PATH", "")


class ToolError(Exception):
    """Lỗi có mã và gợi ý sửa; `exit_code` theo hợp đồng."""

    def __init__(self, code: str, message: str, fix_hint: str | None = None, exit_code: int = 1):
        super().__init__(message)
        self.code, self.message, self.fix_hint, self.exit_code = code, message, fix_hint, exit_code


class MissingDependency(ToolError):
    def __init__(self, message: str, fix_hint: str | None = None):
        super().__init__("MISSING_DEPENDENCY", message, fix_hint, 2)


class BadInput(ToolError):
    def __init__(self, message: str, code: str = "BAD_INPUT"):
        super().__init__(code, message, None, 3)


def out_file(path: Path, kind: str) -> dict:
    return {"path": str(Path(path).resolve()), "kind": kind, "sha256": compute_sha256(Path(path))}


def store_record(rec_id: str, tool: str, version: str, source: str, license_: str, files: dict, metadata: dict, index: Path | None = None) -> dict:
    rec = {
        "id": rec_id,
        "created_by_tool": tool,
        "tool_version": version,
        "source": source,
        "license": license_,
        "created_at": datetime.now().isoformat(),
        "files": {k: str(Path(v).resolve()) for k, v in files.items()},
        "metadata": metadata,
    }
    if index:
        rec["_index"] = str(index)  # kit sẽ append vào index.jsonl rồi bỏ khóa này
    return rec


def _write(path: Path, data: dict) -> None:
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2))


def run_tool(process: Callable[[list[Path], dict, dict], tuple[list[dict], list[dict], list[str]]], *, needs_input: bool = True) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", required=True)
    ap.add_argument("--out", dest="out_path", required=True)
    args = ap.parse_args()
    out_path = Path(args.out_path)
    t0 = time.time()

    def fail(code: str, msg: str, hint: str | None, exit_code: int):
        _write(out_path, {
            "ok": False, "outputs": [], "store_records": [], "warnings": [],
            "error": {"code": code, "message": msg, **({"fix_hint": hint} if hint else {})},
            "elapsed_s": round(time.time() - t0, 4),
        })
        print(str(out_path.resolve()))
        sys.exit(exit_code)

    try:
        in_data = json.loads(Path(args.in_path).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        fail("INVALID_JSON_INPUT", f"Không đọc được file đầu vào: {e}", None, 3)

    params: dict[str, Any] = in_data.get("params", {}) or {}
    raw_inputs = in_data.get("inputs", []) or []
    if needs_input and not raw_inputs:
        fail("NO_INPUT", "Cần ít nhất một đường dẫn đầu vào", None, 3)
    inputs = []
    for p in raw_inputs:
        pp = Path(p)
        if not pp.exists():
            fail("INPUT_NOT_FOUND", f"Không thấy file: {p}", None, 3)
        inputs.append(pp)

    ctx = {"dry_run": bool(in_data.get("dry_run")), "project": in_data.get("project"), "t0": t0}
    try:
        outputs, records, warnings = process(inputs, params, ctx)
    except ToolError as e:
        fail(e.code, e.message, e.fix_hint, e.exit_code)
    except Exception as e:  # noqa: BLE001
        fail("TOOL_FAILED", f"{type(e).__name__}: {e}", traceback.format_exc().strip().splitlines()[-1], 1)

    for r in records:
        idx = r.pop("_index", None)
        if idx:
            append_index_record(Path(idx), r)
    _write(out_path, {
        "ok": True, "outputs": outputs, "store_records": records, "warnings": warnings,
        "error": None, "elapsed_s": round(time.time() - t0, 4),
    })
    print(str(out_path.resolve()))
    sys.exit(0)
