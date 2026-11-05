#!/usr/bin/env python3
"""
Toolbox Tool Template Runner
Adheres strictly to the Toolbox Execution Contract (T0_TOOLBOX_PROMPT.md §2.3)
"""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path


def calculate_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def write_atomic_json(filepath: str, data: dict):
    target = Path(filepath)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, target)


def main():
    parser = argparse.ArgumentParser(description="Toolbox Template Runner")
    parser.add_argument("--in", dest="in_path", required=True, help="Input JSON file path")
    parser.add_argument("--out", dest="out_path", required=True, help="Output JSON file path")
    args = parser.parse_args()

    start_time = time.time()
    in_file = Path(args.in_path)

    if not in_file.exists():
        err_out = {
            "ok": False,
            "outputs": [],
            "store_records": [],
            "warnings": [],
            "error": {
                "code": "INPUT_FILE_NOT_FOUND",
                "message": f"Input file not found at {args.in_path}"
            },
            "elapsed_s": time.time() - start_time
        }
        write_atomic_json(args.out_path, err_out)
        print(os.path.abspath(args.out_path))
        sys.exit(3)

    try:
        with open(in_file, "r", encoding="utf-8") as f:
            in_data = json.load(f)
    except Exception as e:
        err_out = {
            "ok": False,
            "outputs": [],
            "store_records": [],
            "warnings": [],
            "error": {
                "code": "INVALID_JSON_INPUT",
                "message": f"Cannot parse input JSON: {str(e)}"
            },
            "elapsed_s": time.time() - start_time
        }
        write_atomic_json(args.out_path, err_out)
        print(os.path.abspath(args.out_path))
        sys.exit(3)

    inputs = in_data.get("inputs", [])
    params = in_data.get("params", {})
    dry_run = in_data.get("dry_run", False)

    outputs = []
    store_records = []
    warnings = []

    # Echo behavior for the template: inspect inputs or echo params
    for inp in inputs:
        inp_path = Path(inp)
        if not inp_path.exists():
            err_out = {
                "ok": False,
                "outputs": [],
                "store_records": [],
                "warnings": warnings,
                "error": {
                    "code": "INPUT_PATH_MISSING",
                    "message": f"Input path does not exist: {inp}"
                },
                "elapsed_s": time.time() - start_time
            }
            write_atomic_json(args.out_path, err_out)
            print(os.path.abspath(args.out_path))
            sys.exit(3)

        outputs.append({
            "path": str(inp_path.resolve()),
            "kind": "echo_result",
            "sha256": calculate_sha256(str(inp_path)) if inp_path.is_file() else "directory"
        })

    elapsed = time.time() - start_time
    out_data = {
        "ok": True,
        "outputs": outputs,
        "store_records": store_records,
        "warnings": warnings,
        "error": None,
        "elapsed_s": round(elapsed, 4)
    }

    write_atomic_json(args.out_path, out_data)
    print(os.path.abspath(args.out_path))
    sys.exit(0)


if __name__ == "__main__":
    main()
