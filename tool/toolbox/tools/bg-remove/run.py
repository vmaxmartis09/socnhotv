#!/usr/bin/env python3
"""
Background Removal Tool Runner (T-05)
Wraps rembg to produce RGBA cutout.png and mask.png stored in data/shared/assets/cutouts/<sha8>/
"""
import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Paths
TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parents[3]
CUTOUTS_VAULT_DIR = REPO_ROOT / "data" / "shared" / "assets" / "cutouts"
INDEX_PATH = CUTOUTS_VAULT_DIR / "index.jsonl"

# Add toolbox_cli to sys.path for store utilities
TOOLBOX_CLI_DIR = REPO_ROOT / "tool" / "toolbox" / "toolbox_cli"
if str(TOOLBOX_CLI_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLBOX_CLI_DIR))

try:
    from store import append_index_record, atomic_write, compute_sha8, compute_sha256
except ImportError:
    # Fallback minimal store utilities if store import fails
    def compute_sha256(filepath: Path) -> str:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def compute_sha8(filepath: Path) -> str:
        return compute_sha256(filepath)[:8]

    def atomic_write(target_path: Path, content: bytes) -> Path:
        target = Path(target_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(f".tmp_{os.getpid()}")
        with open(tmp, "wb") as f:
            f.write(content)
        os.replace(tmp, target)
        return target

    def append_index_record(idx_path: Path, record: dict) -> None:
        idx_path.parent.mkdir(parents=True, exist_ok=True)
        with open(idx_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def process_image(input_path: Path, params: dict) -> tuple[Path, Path, Path, dict]:
    """Execute rembg separation and save artifacts into data/shared/assets/cutouts/<sha8>/"""
    from PIL import Image
    from rembg import new_session, remove

    if not input_path.exists():
        raise FileNotFoundError(f"Input image not found: {input_path}")

    # Read original bytes to compute content sha8
    with open(input_path, "rb") as f:
        img_bytes = f.read()

    h = hashlib.sha256(img_bytes)
    full_sha = h.hexdigest()
    sha8 = full_sha[:8]

    target_dir = CUTOUTS_VAULT_DIR / sha8
    target_dir.mkdir(parents=True, exist_ok=True)

    cutout_path = target_dir / "cutout.png"
    mask_path = target_dir / "mask.png"
    source_json_path = target_dir / "source.json"

    model_name = params.get("model", "u2net")
    alpha_matting = params.get("alpha_matting", False)
    session = new_session(model_name)

    # 1. Generate Cutout (RGBA)
    with Image.open(input_path) as orig_img:
        width, height = orig_img.size
        cutout_img = remove(orig_img, session=session, alpha_matting=alpha_matting)
        # Ensure RGBA
        if cutout_img.mode != "RGBA":
            cutout_img = cutout_img.convert("RGBA")

        # Save cutout atomically
        tmp_cutout = target_dir / "cutout.tmp.png"
        cutout_img.save(tmp_cutout, format="PNG")
        os.replace(tmp_cutout, cutout_path)

        # 2. Extract and Save Mask (Grayscale)
        alpha_channel = cutout_img.split()[3]
        tmp_mask = target_dir / "mask.tmp.png"
        alpha_channel.save(tmp_mask, format="PNG")
        os.replace(tmp_mask, mask_path)

    # 3. Save source metadata
    source_meta = {
        "sha8": sha8,
        "full_sha256": full_sha,
        "original_file": str(input_path.resolve()),
        "original_filename": input_path.name,
        "width": width,
        "height": height,
        "model": model_name,
        "processed_at": datetime.now().isoformat()
    }
    tmp_source = target_dir / "source.tmp.json"
    with open(tmp_source, "w", encoding="utf-8") as f:
        json.dump(source_meta, f, ensure_ascii=False, indent=2)
    os.replace(tmp_source, source_json_path)

    # 4. Create and append store record
    store_record = {
        "id": sha8,
        "created_by_tool": "bg-remove",
        "tool_version": "1.0.0",
        "source": str(input_path.resolve()),
        "license": "Internal Project Asset",
        "created_at": datetime.now().isoformat(),
        "files": {
            "cutout": str(cutout_path.resolve()),
            "mask": str(mask_path.resolve()),
            "source_json": str(source_json_path.resolve())
        },
        "metadata": {
            "width": width,
            "height": height,
            "model": model_name,
            "sha256": full_sha
        }
    }
    append_index_record(INDEX_PATH, store_record)

    return cutout_path, mask_path, source_json_path, store_record


def main():
    parser = argparse.ArgumentParser(description="Background Removal Runner")
    parser.add_argument("--in", dest="in_path", required=True)
    parser.add_argument("--out", dest="out_path", required=True)
    args = parser.parse_args()

    start_time = time.time()
    out_file = Path(args.out_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    in_file = Path(args.in_path)
    if not in_file.exists():
        err_out = {
            "ok": False,
            "outputs": [],
            "store_records": [],
            "warnings": [],
            "error": {"code": "INPUT_FILE_NOT_FOUND", "message": f"Input config {args.in_path} missing"},
            "elapsed_s": round(time.time() - start_time, 4)
        }
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(err_out, f, indent=2)
        print(str(out_file))
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
            "error": {"code": "INVALID_JSON_INPUT", "message": str(e)},
            "elapsed_s": round(time.time() - start_time, 4)
        }
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(err_out, f, indent=2)
        print(str(out_file))
        sys.exit(3)

    inputs = in_data.get("inputs", [])
    if not inputs:
        err_out = {
            "ok": False,
            "outputs": [],
            "store_records": [],
            "warnings": [],
            "error": {"code": "NO_INPUT_IMAGE_PROVIDED", "message": "At least one input image must be specified"},
            "elapsed_s": round(time.time() - start_time, 4)
        }
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(err_out, f, indent=2)
        print(str(out_file))
        sys.exit(3)

    params = in_data.get("params", {})
    outputs = []
    store_records = []
    warnings = []

    for inp in inputs:
        inp_path = Path(inp)
        if not inp_path.exists():
            err_out = {
                "ok": False,
                "outputs": [],
                "store_records": [],
                "warnings": warnings,
                "error": {"code": "INPUT_IMAGE_NOT_FOUND", "message": f"File does not exist: {inp}"},
                "elapsed_s": round(time.time() - start_time, 4)
            }
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(err_out, f, indent=2)
            print(str(out_file))
            sys.exit(3)

        try:
            cutout_p, mask_p, src_p, rec = process_image(inp_path, params)
            outputs.append({
                "path": str(cutout_p.resolve()),
                "kind": "cutout",
                "sha256": compute_sha256(cutout_p)
            })
            outputs.append({
                "path": str(mask_p.resolve()),
                "kind": "mask",
                "sha256": compute_sha256(mask_p)
            })
            store_records.append(rec)
        except Exception as e:
            err_out = {
                "ok": False,
                "outputs": outputs,
                "store_records": store_records,
                "warnings": warnings,
                "error": {
                    "code": "BACKGROUND_REMOVAL_FAILED",
                    "message": str(e),
                    "fix_hint": "Check model weights download or onnxruntime CPU compatibility."
                },
                "elapsed_s": round(time.time() - start_time, 4)
            }
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(err_out, f, indent=2)
            print(str(out_file))
            sys.exit(1)

    out_data = {
        "ok": True,
        "outputs": outputs,
        "store_records": store_records,
        "warnings": warnings,
        "error": None,
        "elapsed_s": round(time.time() - start_time, 4)
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)

    print(str(out_file))
    sys.exit(0)


if __name__ == "__main__":
    main()
