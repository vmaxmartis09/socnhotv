#!/usr/bin/env python3
"""
Speech-to-Text & Word Alignment Runner (T-07)
Uses faster-whisper (CTranslate2 CPU int8) to extract accurate word-level timestamps (for karaoke/subtitles).
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
AUDIO_VAULT_DIR = REPO_ROOT / "data" / "shared" / "assets" / "audio"
INDEX_PATH = AUDIO_VAULT_DIR / "index.jsonl"
SHARED_FFMPEG_DIR = REPO_ROOT / "data" / "shared" / "models" / "ffmpeg-bin"

# Prepend shared ffmpeg-bin to PATH in current process for subprocesses/libs
if SHARED_FFMPEG_DIR.exists():
    os.environ["PATH"] = str(SHARED_FFMPEG_DIR.resolve()) + os.pathsep + os.environ.get("PATH", "")

# Add toolbox_cli to sys.path
TOOLBOX_CLI_DIR = REPO_ROOT / "tool" / "toolbox" / "toolbox_cli"
if str(TOOLBOX_CLI_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLBOX_CLI_DIR))

try:
    from store import append_index_record, atomic_write, compute_sha8, compute_sha256
except ImportError:
    def compute_sha256(filepath: Path) -> str:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def compute_sha8(filepath: Path) -> str:
        return compute_sha256(filepath)[:8]

    def atomic_write(target_path: Path, content: str | bytes) -> Path:
        target = Path(target_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(f".tmp_{os.getpid()}")
        mode = "wb" if isinstance(content, (bytes, bytearray)) else "w"
        encoding = None if isinstance(content, (bytes, bytearray)) else "utf-8"
        with open(tmp, mode, encoding=encoding) as f:
            f.write(content)
        os.replace(tmp, target)
        return target

    def append_index_record(idx_path: Path, record: dict) -> None:
        idx_path.parent.mkdir(parents=True, exist_ok=True)
        with open(idx_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def format_srt_timestamp(seconds: float) -> str:
    """Format float seconds to SRT time string (HH:MM:SS,mmm)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def process_audio(audio_path: Path, params: dict) -> tuple[Path, Path, Path, dict]:
    """Transcribe audio and generate word timings and SRT."""
    from faster_whisper import WhisperModel

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Compute content hash
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    h = hashlib.sha256(audio_bytes)
    full_sha = h.hexdigest()
    sha8 = full_sha[:8]

    target_dir = AUDIO_VAULT_DIR / sha8
    target_dir.mkdir(parents=True, exist_ok=True)

    timings_json_path = target_dir / "timings.json"
    srt_path = target_dir / "subtitles.srt"
    source_json_path = target_dir / "source.json"

    # Settings
    model_size = params.get("model_size", "small")
    language = params.get("language", "vi")
    compute_type = params.get("compute_type", "int8")

    # Load faster-whisper model
    model = WhisperModel(model_size, device="cpu", compute_type=compute_type)

    # Transcribe with word timestamps
    segments, info = model.transcribe(
        str(audio_path.resolve()),
        language=language,
        word_timestamps=True,
        beam_size=5,
        vad_filter=True
    )

    all_segments = []
    full_text_parts = []
    srt_lines = []
    srt_idx = 1

    for seg in segments:
        words = []
        if seg.words:
            for w in seg.words:
                words.append({
                    "word": w.word.strip(),
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "probability": round(w.probability, 3)
                })

        seg_text = seg.text.strip()
        full_text_parts.append(seg_text)

        all_segments.append({
            "id": seg.id,
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg_text,
            "words": words
        })

        # Build SRT entry
        start_srt = format_srt_timestamp(seg.start)
        end_srt = format_srt_timestamp(seg.end)
        srt_lines.append(f"{srt_idx}\n{start_srt} --> {end_srt}\n{seg_text}\n")
        srt_idx += 1

    full_text = " ".join(full_text_parts)

    timings_payload = {
        "text": full_text,
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration": round(info.duration, 3),
        "model": model_size,
        "segments": all_segments
    }

    # Save timings.json atomically
    atomic_write(timings_json_path, json.dumps(timings_payload, ensure_ascii=False, indent=2))

    # Save subtitles.srt atomically
    atomic_write(srt_path, "\n".join(srt_lines))

    # Save source metadata
    source_meta = {
        "sha8": sha8,
        "full_sha256": full_sha,
        "original_file": str(audio_path.resolve()),
        "original_filename": audio_path.name,
        "duration": round(info.duration, 3),
        "model": model_size,
        "processed_at": datetime.now().isoformat()
    }
    atomic_write(source_json_path, json.dumps(source_meta, ensure_ascii=False, indent=2))

    # Append to store index
    store_record = {
        "id": sha8,
        "created_by_tool": "stt-align",
        "tool_version": "1.0.0",
        "source": str(audio_path.resolve()),
        "license": "Apache-2.0",
        "created_at": datetime.now().isoformat(),
        "files": {
            "timings": str(timings_json_path.resolve()),
            "subtitles": str(srt_path.resolve()),
            "source_json": str(source_json_path.resolve())
        },
        "metadata": {
            "duration": round(info.duration, 3),
            "language": info.language,
            "text_preview": full_text[:100],
            "word_count": sum(len(s["words"]) for s in all_segments)
        }
    }
    append_index_record(INDEX_PATH, store_record)

    return timings_json_path, srt_path, source_json_path, store_record


def main():
    parser = argparse.ArgumentParser(description="STT & Word Alignment Runner")
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
            "error": {"code": "NO_INPUT_AUDIO_PROVIDED", "message": "At least one input audio path must be provided"},
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
                "error": {"code": "INPUT_AUDIO_NOT_FOUND", "message": f"File does not exist: {inp}"},
                "elapsed_s": round(time.time() - start_time, 4)
            }
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(err_out, f, indent=2)
            print(str(out_file))
            sys.exit(3)

        try:
            timings_p, srt_p, src_p, rec = process_audio(inp_path, params)
            outputs.append({
                "path": str(timings_p.resolve()),
                "kind": "word_timings",
                "sha256": compute_sha256(timings_p)
            })
            outputs.append({
                "path": str(srt_p.resolve()),
                "kind": "subtitles_srt",
                "sha256": compute_sha256(srt_p)
            })
            store_records.append(rec)
        except Exception as e:
            err_out = {
                "ok": False,
                "outputs": outputs,
                "store_records": store_records,
                "warnings": warnings,
                "error": {
                    "code": "STT_ALIGN_FAILED",
                    "message": str(e),
                    "fix_hint": "Check faster-whisper small model download or ffmpeg installation."
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
