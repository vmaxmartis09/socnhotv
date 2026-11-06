"""Cấu hình chung cho bộ test — chạy trong một repo SANDBOX tạm, không ghi vào data/ thật.

Vấn đề cũ (status/THUC_TRANG_2026-11-06.md, N8): nhiều test gọi ProjectStore("soc-nho-tv") hoặc
workspace.paths.project_path(...) và ghi thẳng vào data/projects/soc-nho-tv/{runs,assets,output}
-> runs/ thật phình lên hàng trăm thư mục rác, graph.json của người dùng bị ghi đè.

Cách làm (G4):
- Ngay khi conftest được nạp (trước khi bất kỳ module test nào import socnhotv), dựng một repo
  sandbox trong thư mục tạm:
    <sandbox>/data/         bản sao data/ thật:
                              * macOS/APFS: sandbox đặt CẠNH repo (cùng ổ) và chép bằng clonefile
                                (`cp -c`): tức thì, không tốn dung lượng, copy-on-write -> test ghi
                                gì cũng chỉ ghi vào bản sao.
                              * nơi khác (không clone được): tệp văn bản/tệp nhỏ COPY, tệp nhị phân
                                lớn symlink (chỉ đọc).
                              * runs/, output/, shots/ của mọi dự án -> rỗng
    <sandbox>/tool, scripts, .venv, ai, integrations -> symlink về repo thật (code, không phải dữ liệu)
    KHÔNG có .env -> test không bao giờ dùng key thật / gọi nguồn trả phí.
- Vá 2 hàm tìm gốc repo (socnhotv.workspace.paths.repo_root và
  socnhotv.core.storage.project_store.get_repo_root) để trả về sandbox.
- Cuối phiên: so sánh data/projects/*/runs thật trước/sau. Nếu có thư mục mới -> in cảnh báo
  ĐỎ trong báo cáo pytest (để phát hiện test nào còn lách được sandbox). Không tự xoá gì.

Biến môi trường:
- SOCNHOTV_TEST_KEEP_SANDBOX=1  giữ lại sandbox sau phiên test để soi.
- SOCNHOTV_TEST_REAL_DATA=1     tắt sandbox (chạy trên dữ liệu thật như cũ — chỉ dùng khi biết mình làm gì).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REAL_ROOT = Path(__file__).resolve().parents[2]
REAL_DATA = REAL_ROOT / "data"

# Tệp được COPY (sửa trong sandbox không ảnh hưởng thật). Còn lại: copy nếu nhỏ, symlink nếu lớn.
_TEXT_EXT = {
    ".json", ".jsonl", ".md", ".yaml", ".yml", ".txt", ".csv", ".srt", ".vtt", ".ass",
    ".html", ".css", ".js", ".toml", ".ini", ".cfg", ".xml", ".svg", ".py", ".log",
}
_SMALL_BYTES = 256 * 1024
# Thư mục con của mỗi dự án luôn để RỖNG trong sandbox (đầu ra của bộ chạy / chụp màn hình).
_EMPTY_PROJECT_DIRS = {"runs", "output", "shots"}
_CODE_LINKS = ("tool", "scripts", ".venv", "ai", "integrations")


def _mirror_tree(src: Path, dst: Path, *, skip_dirs: set[str] | None = None) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    try:
        entries = list(os.scandir(src))
    except OSError:
        return
    for e in entries:
        s = Path(e.path)
        d = dst / e.name
        try:
            if e.is_dir(follow_symlinks=True):
                if skip_dirs and e.name in skip_dirs:
                    d.mkdir(parents=True, exist_ok=True)
                    continue
                _mirror_tree(s, d)
            elif e.is_file(follow_symlinks=True):
                size = e.stat(follow_symlinks=True).st_size
                if s.suffix.lower() in _TEXT_EXT or size <= _SMALL_BYTES:
                    shutil.copy2(s, d)
                else:
                    os.symlink(s.resolve(), d)
        except OSError:
            continue


def _clone(src: Path, dst: Path) -> bool:
    """APFS clonefile (cp -c): chép tức thì, copy-on-write -> test ghi vào bản sao không chạm bản thật."""
    if sys.platform != "darwin":
        return False
    try:
        r = subprocess.run(["cp", "-cR", str(src), str(dst)], capture_output=True, timeout=120)
        return r.returncode == 0
    except Exception:
        return False


def _sandbox_parent() -> Path | None:
    """Thư mục chứa sandbox CÙNG ổ với repo (để clone được). None -> dùng thư mục tạm của hệ thống."""
    parent = REAL_ROOT.parent
    try:
        probe = Path(tempfile.mkdtemp(prefix=".socnhotv-test-probe-", dir=parent))
        probe.rmdir()
        return parent
    except OSError:
        return None


def _drop_stale_sandboxes(parent: Path, max_age_sec: float = 6 * 3600) -> None:
    """Sandbox sót lại từ phiên test bị ngắt giữa chừng (chỉ thư mục do conftest này tạo)."""
    import time as _t

    for p in parent.glob(".socnhotv-test-*"):
        try:
            if p.is_dir() and not p.is_symlink() and _t.time() - p.stat().st_mtime > max_age_sec:
                shutil.rmtree(p, ignore_errors=True)
        except OSError:
            pass


def _build_sandbox() -> Path:
    parent = _sandbox_parent()
    if parent:
        _drop_stale_sandboxes(parent)
    root = Path(tempfile.mkdtemp(prefix=".socnhotv-test-" if parent else "socnhotv-test-", dir=parent))
    data = root / "data"
    data.mkdir()
    for e in os.scandir(REAL_DATA):
        s = Path(e.path)
        if e.name == "projects" and e.is_dir():
            projects = data / "projects"
            projects.mkdir()
            for pe in os.scandir(s):
                if not pe.is_dir():
                    continue
                dst = projects / pe.name
                dst.mkdir()
                for ce in os.scandir(pe.path):
                    cs, cd = Path(ce.path), dst / ce.name
                    if ce.is_dir() and ce.name in _EMPTY_PROJECT_DIRS:
                        cd.mkdir()
                    elif parent and _clone(cs, cd):
                        continue
                    elif ce.is_dir():
                        _mirror_tree(cs, cd)
                    elif ce.is_file():
                        shutil.copy2(cs, cd)
        elif parent and _clone(s, data / e.name):
            continue
        elif e.is_dir():
            _mirror_tree(s, data / e.name)
        elif e.is_file():
            shutil.copy2(s, data / e.name)
    for name in _CODE_LINKS:
        src = REAL_ROOT / name
        if src.exists():
            os.symlink(src, root / name)
    return root


def _real_run_entries() -> set[Path]:
    out: set[Path] = set()
    projects = REAL_DATA / "projects"
    if projects.is_dir():
        for p in projects.iterdir():
            if p.is_dir():
                out.add(p)  # phát hiện cả dự án mới do test tạo (vd. test-step5)
                runs = p / "runs"
                if runs.is_dir():
                    out.update(runs.iterdir())
                    nodes = runs / "_node_outputs"
                    if nodes.is_dir():
                        out.update(nodes.rglob("*.json"))
    return out


_USE_SANDBOX = os.environ.get("SOCNHOTV_TEST_REAL_DATA") != "1"
SANDBOX_ROOT: Path | None = None
_REAL_BEFORE: set[Path] = set()

if _USE_SANDBOX:
    _REAL_BEFORE = _real_run_entries()
    SANDBOX_ROOT = _build_sandbox()
    os.environ["SOCNHOTV_TEST_SANDBOX"] = str(SANDBOX_ROOT)
    # Các test khởi chạy tiến trình con (voice_studio.py ...) vẫn đọc .env từ repo thật nếu tự tìm;
    # tắt key nguồn trả phí trong tiến trình test cho chắc.
    for _k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "FAL_KEY", "REPLICATE_API_TOKEN"):
        os.environ.pop(_k, None)

    _src = REAL_ROOT / "tool" / "src"
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
    import socnhotv.workspace.paths as _ws_paths  # noqa: E402
    import socnhotv.core.storage.project_store as _ps  # noqa: E402

    import socnhotv.workspace as _ws_pkg  # noqa: E402
    import socnhotv.core.storage as _st_pkg  # noqa: E402

    def _sandbox_repo_root() -> Path:
        return SANDBOX_ROOT  # type: ignore[return-value]

    # Vá cả hàm gốc lẫn bản re-export ở __init__ của package (from socnhotv.workspace import repo_root)
    _ws_paths.repo_root = _sandbox_repo_root  # type: ignore[assignment]
    _ws_pkg.repo_root = _sandbox_repo_root  # type: ignore[assignment]
    _ps.get_repo_root = _sandbox_repo_root  # type: ignore[assignment]
    _st_pkg.get_repo_root = _sandbox_repo_root  # type: ignore[assignment]


@pytest.fixture(scope="session")
def sandbox_root() -> Path | None:
    """Gốc repo sandbox của phiên test (None nếu chạy SOCNHOTV_TEST_REAL_DATA=1)."""
    return SANDBOX_ROOT


def _leaks() -> list[Path]:
    if not _USE_SANDBOX:
        return []
    return sorted(_real_run_entries() - _REAL_BEFORE)


def pytest_terminal_summary(terminalreporter, exitstatus, config):  # noqa: D401
    if not _USE_SANDBOX:
        terminalreporter.write_line("SOCNHOTV: chạy trên DỮ LIỆU THẬT (SOCNHOTV_TEST_REAL_DATA=1)", yellow=True)
        return
    leaks = _leaks()
    terminalreporter.write_line(f"SOCNHOTV sandbox: {SANDBOX_ROOT}")
    if leaks:
        terminalreporter.write_line(
            f"CẢNH BÁO: {len(leaks)} mục mới xuất hiện trong data/projects thật (test lách sandbox):",
            red=True,
            bold=True,
        )
        for p in leaks[:30]:
            terminalreporter.write_line(f"  {p.relative_to(REAL_ROOT)}", red=True)
    else:
        terminalreporter.write_line("SOCNHOTV: không có mục mới trong data/projects/*/runs thật.", green=True)


def pytest_unconfigure(config):
    if SANDBOX_ROOT and os.environ.get("SOCNHOTV_TEST_KEEP_SANDBOX") != "1":
        shutil.rmtree(SANDBOX_ROOT, ignore_errors=True)
