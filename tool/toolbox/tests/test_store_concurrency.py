#!/usr/bin/env python3
"""
Stress test concurrency for append_index_record with 2 parallel processes writing 200 records.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Add toolbox_cli to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from toolbox_cli.store import read_index_records


def worker_task(worker_id: int, count: int, index_file: str):
    """Worker function executed in separate process."""
    from toolbox_cli.store import append_index_record

    for i in range(count):
        rec = {
            "id": f"worker_{worker_id}_rec_{i:04d}",
            "created_by_tool": "test_store_concurrency",
            "tool_version": "1.0.0",
            "source": f"test_source_{worker_id}_{i}",
            "license": "MIT",
            "worker": worker_id,
            "seq": i,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        append_index_record(index_file, rec)
        # Small jitter to interleave operations
        if i % 10 == 0:
            time.sleep(0.005)


def run_concurrency_test():
    test_dir = Path(__file__).parent / "_test_tmp"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_index = test_dir / "test_concurrency_index.jsonl"

    if test_index.exists():
        test_index.unlink()
    lock_file = Path(f"{test_index}.lock")
    if lock_file.exists():
        lock_file.unlink()

    print(f"Testing 2 parallel processes writing 200 records to {test_index}...")

    # Spawn 2 worker processes
    script_path = Path(__file__).resolve()
    cmd1 = [sys.executable, str(script_path), "--worker", "1", "--count", "100", "--index", str(test_index)]
    cmd2 = [sys.executable, str(script_path), "--worker", "2", "--count", "100", "--index", str(test_index)]

    p1 = subprocess.Popen(cmd1)
    p2 = subprocess.Popen(cmd2)

    ret1 = p1.wait()
    ret2 = p2.wait()

    assert ret1 == 0, f"Worker 1 failed with return code {ret1}"
    assert ret2 == 0, f"Worker 2 failed with return code {ret2}"

    # Verify results
    records = []
    corrupted_lines = 0
    with open(test_index, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                records.append(json.loads(line_str))
            except Exception as e:
                corrupted_lines += 1
                print(f"Line {idx} corrupted: {e}")

    ids = [r["id"] for r in records]
    unique_ids = set(ids)

    print("\n--- Concurrency Test Results ---")
    print(f"Total lines read: {len(records)}")
    print(f"Corrupted lines:  {corrupted_lines}")
    print(f"Unique record IDs:{len(unique_ids)}")

    # Clean up test artifacts
    if test_index.exists():
        test_index.unlink()
    if lock_file.exists():
        lock_file.unlink()
    if test_dir.exists():
        try:
            test_dir.rmdir()
        except Exception:
            pass

    assert corrupted_lines == 0, f"Found {corrupted_lines} corrupted lines!"
    assert len(records) == 200, f"Expected 200 records, got {len(records)}!"
    assert len(unique_ids) == 200, f"Found duplicate IDs! Unique: {len(unique_ids)}/200"

    print("TEST PASSED: 0 corrupted lines, 0 duplicate IDs, 200/200 records safely stored.\n")


if __name__ == "__main__":
    if "--worker" in sys.argv:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--worker", type=int, required=True)
        parser.add_argument("--count", type=int, required=True)
        parser.add_argument("--index", type=str, required=True)
        args = parser.parse_args()
        worker_task(args.worker, args.count, args.index)
    else:
        run_concurrency_test()
