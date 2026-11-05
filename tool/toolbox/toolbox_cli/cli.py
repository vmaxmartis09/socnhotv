#!/usr/bin/env python3
"""
Toolbox CLI (Pure Python Standard Library)
Management, diagnostic and execution runner for independent toolbox tools.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TOOLBOX_DIR = REPO_ROOT / "tool" / "toolbox"
TOOLS_DIR = TOOLBOX_DIR / "tools"
TEMPLATE_DIR = TOOLBOX_DIR / "_template"
SHARED_DIR = REPO_ROOT / "data" / "shared"
RUNS_LOG_PATH = SHARED_DIR / "toolbox" / "runs.jsonl"


def find_tool_manifest(tool_id: str) -> tuple[Path, dict]:
    """Locate tool directory and parse its tool.json."""
    tool_dir = TOOLS_DIR / tool_id
    if not tool_dir.exists():
        if tool_id == "_template" and TEMPLATE_DIR.exists():
            tool_dir = TEMPLATE_DIR
        else:
            raise FileNotFoundError(f"Tool '{tool_id}' not found in {TOOLS_DIR}")

    manifest_path = tool_dir / "tool.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest tool.json missing in {tool_dir}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    return tool_dir, manifest


def resolve_python_runtime(runtime_req: str = "python3.11", tool_dir: Path | None = None) -> tuple[str, bool]:
    """
    Resolve python executable.
    First check tool's local .venv.
    Then check Windows py launcher with requested version.
    Then fallback to current sys.executable.
    Returns (executable_path, is_venv).
    """
    if tool_dir:
        # Check Windows venv
        venv_py_win = tool_dir / ".venv" / "Scripts" / "python.exe"
        if venv_py_win.exists():
            return str(venv_py_win.resolve()), True
        # Check Unix venv
        venv_py_unix = tool_dir / ".venv" / "bin" / "python"
        if venv_py_unix.exists():
            return str(venv_py_unix.resolve()), True

    # Check system py launcher
    py_launcher = shutil.which("py")
    if py_launcher:
        ver_flag = "-3.11" if "3.11" in runtime_req else "-3.12" if "3.12" in runtime_req else ""
        if ver_flag:
            test_run = subprocess.run([py_launcher, ver_flag, "-c", "import sys; print(sys.executable)"],
                                      capture_output=True, text=True)
            if test_run.returncode == 0 and test_run.stdout.strip():
                return test_run.stdout.strip(), False

    # Fallback to sys.executable
    return sys.executable, False


def find_ffmpeg_bin() -> str | None:
    """Find ffmpeg in data/shared/models/ffmpeg-bin/ or on system PATH."""
    shared_ffmpeg = SHARED_DIR / "models" / "ffmpeg-bin" / "ffmpeg.exe"
    if shared_ffmpeg.exists():
        return str(shared_ffmpeg.resolve())

    shared_ffmpeg_unix = SHARED_DIR / "models" / "ffmpeg-bin" / "ffmpeg"
    if shared_ffmpeg_unix.exists():
        return str(shared_ffmpeg_unix.resolve())

    path_ffmpeg = shutil.which("ffmpeg")
    if path_ffmpeg:
        return path_ffmpeg

    return None


def cmd_list(args):
    """List all registered tools."""
    tools = []
    candidates = []
    if TEMPLATE_DIR.exists():
        candidates.append(("_template", TEMPLATE_DIR))
    if TOOLS_DIR.exists():
        for d in sorted(TOOLS_DIR.iterdir()):
            if d.is_dir() and (d / "tool.json").exists():
                candidates.append((d.name, d))

    print(f"{'TOOL ID':<16} {'NAME':<24} {'VERSION':<10} {'STATUS':<12} {'RUNTIME':<10} {'GPU':<6} {'FFMPEG':<8} {'COMMERCIAL'}")
    print("-" * 100)

    for tid, tdir in candidates:
        try:
            with open(tdir / "tool.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            ver = data.get("version", "0.0.0")
            name = data.get("name", tid)
            status = data.get("status", "unknown")
            runtime = data.get("runtime", "python3.11")
            gpu = "Yes" if data.get("requires_gpu") else "No"
            ff = "Yes" if data.get("requires_ffmpeg") else "No"
            lic = data.get("license", {})
            comm = "OK" if lic.get("commercial_ok") else "Non-Comm"
            print(f"{tid:<16} {name[:22]:<24} {ver:<10} {status:<12} {runtime:<10} {gpu:<6} {ff:<8} {comm}")
        except Exception as e:
            print(f"{tid:<16} [Error reading tool.json: {e}]")


def cmd_doctor(args):
    """Diagnose environment, runtimes, ffmpeg, GPU, disk, and tools."""
    print("=" * 60)
    print("           SOCNHOTV TOOLBOX DOCTOR REPORT           ")
    print("=" * 60)

    # 1. Python Environment
    print("\n[1] PYTHON RUNTIMES:")
    py311_exe, _ = resolve_python_runtime("python3.11")
    print(f"  - Python 3.11: {py311_exe}")
    py312_exe, _ = resolve_python_runtime("python3.12")
    print(f"  - Python 3.12: {py312_exe}")
    print(f"  - Current sys.executable: {sys.executable} ({sys.version.split()[0]})")

    # 2. FFmpeg
    print("\n[2] FFMPEG BINARY:")
    ffmpeg_bin = find_ffmpeg_bin()
    if ffmpeg_bin:
        ver_proc = subprocess.run([ffmpeg_bin, "-version"], capture_output=True, text=True)
        first_line = ver_proc.stdout.splitlines()[0] if ver_proc.stdout else "Available"
        print(f"  - Status: FOUND at {ffmpeg_bin}")
        print(f"  - Version: {first_line}")
    else:
        print("  - Status: MISSING (Neither in PATH nor in data/shared/models/ffmpeg-bin/)")
        print("  - Action required: Run T-08 bundle setup to download static ffmpeg CPU into data/shared/models/ffmpeg-bin/")

    # 3. GPU / Hardware
    print("\n[3] GPU / ACCELERATION:")
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        print(f"  - NVIDIA GPU: Available ({nvidia_smi})")
    else:
        print("  - NVIDIA GPU: None (nvidia-smi not found). CPU Execution Mode strictly enforced.")

    # 4. Disk Storage
    print("\n[4] STORAGE AVAILABILITY:")
    try:
        total, used, free = shutil.disk_usage(REPO_ROOT)
        free_gb = free // (2**30)
        total_gb = total // (2**30)
        print(f"  - Drive: {REPO_ROOT.drive or 'Workspace'}")
        print(f"  - Free space: {free_gb} GB / {total_gb} GB")
    except Exception as e:
        print(f"  - Cannot query disk usage: {e}")

    # 5. Shared Vaults
    print("\n[5] SHARED VAULTS:")
    for vault_name in ["voice_vault", "assets/cutouts", "models", "toolbox"]:
        vpath = SHARED_DIR / vault_name
        exists = vpath.exists()
        print(f"  - data/shared/{vault_name:<16}: {'EXISTS' if exists else 'NOT CREATED YET'}")

    # 6. Tools Health & Venvs
    print("\n[6] TOOLS & ENVIRONMENTS:")
    tools_found = []
    if TOOLS_DIR.exists():
        for d in sorted(TOOLS_DIR.iterdir()):
            if d.is_dir() and (d / "tool.json").exists():
                tools_found.append(d)

    if not tools_found:
        print("  - No tools installed in tool/toolbox/tools/ yet.")
    else:
        for tdir in tools_found:
            t_id = tdir.name
            with open(tdir / "tool.json", "r", encoding="utf-8") as f:
                t_manifest = json.load(f)
            t_name = t_manifest.get("name", t_id)
            t_runtime = t_manifest.get("runtime", "python3.11")
            venv_path = tdir / ".venv"
            venv_py, has_venv = resolve_python_runtime(t_runtime, tdir)
            status_flag = "READY" if has_venv else "NO VENV"
            print(f"  - [{t_id}] {t_name} ({t_manifest.get('status')}): {status_flag} -> {venv_py}")

    print("\n" + "=" * 60)


def cmd_add(args):
    """Create a new tool from _template and optionally setup its venv."""
    tool_id = args.tool_id
    target_dir = TOOLS_DIR / tool_id

    if target_dir.exists():
        print(f"Error: Tool '{tool_id}' already exists at {target_dir}")
        sys.exit(1)

    if not TEMPLATE_DIR.exists():
        print(f"Error: Template directory not found at {TEMPLATE_DIR}")
        sys.exit(1)

    print(f"Creating tool '{tool_id}' from _template...")
    shutil.copytree(TEMPLATE_DIR, target_dir, ignore=shutil.ignore_patterns(".venv", "*.tmp", "__pycache__"))

    # Update tool.json
    manifest_file = target_dir / "tool.json"
    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["id"] = tool_id
    data["name"] = args.name or tool_id.replace("-", " ").title()
    data["status"] = "planned"
    data["version"] = "0.1.0"

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Tool created at: {target_dir}")

    if args.setup_venv:
        print("Initializing isolated venv...")
        runtime = data.get("runtime", "python3.11")
        py_exe, _ = resolve_python_runtime(runtime)
        venv_dir = target_dir / ".venv"
        subprocess.run([py_exe, "-m", "venv", str(venv_dir)], check=True)
        print(f"Venv created at: {venv_dir}")

        req_file = target_dir / "requirements.txt"
        if req_file.exists():
            v_py, _ = resolve_python_runtime(runtime, target_dir)
            print("Installing dependencies from requirements.txt...")
            subprocess.run([v_py, "-m", "pip", "install", "-r", str(req_file)], check=True)

    print(f"Done. Manifest at {manifest_file}")


def cmd_run(args):
    """
    Execute a tool adhering to the execution contract:
    toolbox run <tool-id> --in in.json --out out.json
    """
    tool_id = args.tool_id
    in_path = Path(args.in_path).resolve()
    out_path = Path(args.out_path).resolve()

    start_ts = time.time()

    try:
        tool_dir, manifest = find_tool_manifest(tool_id)
    except FileNotFoundError as e:
        err_out = {
            "ok": False,
            "outputs": [],
            "store_records": [],
            "warnings": [],
            "error": {"code": "TOOL_NOT_FOUND", "message": str(e)},
            "elapsed_s": round(time.time() - start_ts, 4)
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(err_out, f, indent=2)
        print(str(out_path))
        sys.exit(2)

    entry_file = manifest.get("entry", "run.py")
    entry_path = tool_dir / entry_file

    if not entry_path.exists():
        err_out = {
            "ok": False,
            "outputs": [],
            "store_records": [],
            "warnings": [],
            "error": {"code": "ENTRY_POINT_MISSING", "message": f"Entry file {entry_file} missing in {tool_dir}"},
            "elapsed_s": round(time.time() - start_ts, 4)
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(err_out, f, indent=2)
        print(str(out_path))
        sys.exit(2)

    # Resolve runner executable
    runtime = manifest.get("runtime", "python3.11")
    py_exe, has_venv = resolve_python_runtime(runtime, tool_dir)

    # Check if tool requires specific venv and is not template
    if tool_id != "_template" and not has_venv and (tool_dir / "requirements.txt").exists():
        # Check if requirements are satisfied or warn
        pass

    cmd = [py_exe, str(entry_path), "--in", str(in_path), "--out", str(out_path)]

    # Subprocess execution
    proc = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start_ts

    # Record run in data/shared/toolbox/runs.jsonl
    try:
        RUNS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        log_entry = {
            "tool_id": tool_id,
            "tool_version": manifest.get("version"),
            "timestamp": datetime.now().isoformat(),
            "in": str(in_path),
            "out": str(out_path),
            "exit_code": proc.returncode,
            "elapsed_s": round(elapsed, 4)
        }
        with open(RUNS_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass

    # Print out_path to stdout as strictly contracted
    print(str(out_path))

    # Forward exit code
    sys.exit(proc.returncode)


def main():
    parser = argparse.ArgumentParser(description="SocNhoTV Toolbox CLI Runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = subparsers.add_parser("list", help="List registered tools")
    p_list.set_defaults(func=cmd_list)

    # doctor
    p_doc = subparsers.add_parser("doctor", help="Diagnose environment and dependencies")
    p_doc.set_defaults(func=cmd_doctor)

    # add
    p_add = subparsers.add_parser("add", help="Scaffold a new tool from _template")
    p_add.add_argument("tool_id", help="Unique identifier for the new tool (e.g. bg-remove)")
    p_add.add_argument("--name", help="Human readable name", default=None)
    p_add.add_argument("--setup-venv", action="store_true", help="Automatically create venv")
    p_add.set_defaults(func=cmd_add)

    # run
    p_run = subparsers.add_parser("run", help="Run a tool under contract")
    p_run.add_argument("tool_id", help="Tool ID to run")
    p_run.add_argument("--in", dest="in_path", required=True, help="Path to in.json")
    p_run.add_argument("--out", dest="out_path", required=True, help="Path to out.json")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
