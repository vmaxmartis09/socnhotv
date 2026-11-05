#!/usr/bin/env python3
"""
Shared Vault Storage Utilities
Atomic file writing, cross-platform file-locked index.jsonl append, and content hashing.
"""
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

IS_WIN = sys.platform == "win32"
if IS_WIN:
    import msvcrt
else:
    import fcntl


def compute_sha256(data: bytes | Path | str) -> str:
    """Compute full sha256 of bytes or file content."""
    h = hashlib.sha256()
    if isinstance(data, (bytes, bytearray)):
        h.update(data)
    else:
        path = Path(data)
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
    return h.hexdigest()


def compute_sha8(data: bytes | Path | str) -> str:
    """Compute 8-character prefix sha of bytes or file content."""
    return compute_sha256(data)[:8]


def atomic_write(target_path: Path | str, content: bytes | str) -> Path:
    """Write content to .tmp file and atomic replace to destination."""
    target = Path(target_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = target.with_suffix(f"{target.suffix}.tmp_{os.getpid()}_{time.time_ns()}")

    mode = "wb" if isinstance(content, (bytes, bytearray)) else "w"
    encoding = None if isinstance(content, (bytes, bytearray)) else "utf-8"

    with open(tmp_file, mode, encoding=encoding) as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())

    # Windows os.replace is atomic on modern NTFS/Python 3.3+
    os.replace(tmp_file, target)
    return target


class FileLock:
    """Cross-platform advisory file lock using a companion .lock file."""
    def __init__(self, target_file: Path | str, timeout: float = 10.0, retry_interval: float = 0.05):
        self.lock_path = Path(f"{target_file}.lock").resolve()
        self.timeout = timeout
        self.retry_interval = retry_interval
        self._fd = None

    def __enter__(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        start = time.time()

        while True:
            try:
                # Open lock file for read/write
                self._fd = open(self.lock_path, "a+b")
                # Ensure at least 1 byte exists to lock
                if self.lock_path.stat().st_size == 0:
                    self._fd.write(b"\0")
                    self._fd.flush()

                self._fd.seek(0)
                if IS_WIN:
                    msvcrt.locking(self._fd.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except (OSError, IOError):
                if self._fd:
                    try:
                        self._fd.close()
                    except Exception:
                        pass
                    self._fd = None

                if time.time() - start > self.timeout:
                    raise TimeoutError(f"Could not acquire lock on {self.lock_path} within {self.timeout}s")
                time.sleep(self.retry_interval)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._fd:
            try:
                self._fd.seek(0)
                if IS_WIN:
                    msvcrt.locking(self._fd.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            finally:
                self._fd.close()
                self._fd = None


def append_index_record(index_path: Path | str, record: dict, timeout: float = 10.0) -> None:
    """Append a validated JSON record to index.jsonl under lock."""
    index_file = Path(index_path).resolve()
    index_file.parent.mkdir(parents=True, exist_ok=True)

    # Ensure mandatory fields
    if "created_at" not in record:
        record["created_at"] = datetime.now().isoformat()

    line = json.dumps(record, ensure_ascii=False) + "\n"

    with FileLock(index_file, timeout=timeout):
        with open(index_file, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()


def read_index_records(index_path: Path | str) -> list[dict]:
    """Read all valid JSON records from index.jsonl."""
    index_file = Path(index_path).resolve()
    if not index_file.exists():
        return []

    records = []
    with open(index_file, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                records.append(json.loads(line_str))
    return records
