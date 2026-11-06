#!/usr/bin/env python3
"""Script dọn dẹp thư mục runs/ của các dự án SocNhoTV.

Chức năng:
- Quét và phân loại thư mục trong data/projects/<project-id>/runs/
- Bảo vệ tuyệt đối các tệp/thư mục nhạy cảm: .gitkeep, spend.json, hàng đợi runtime (events, render_queue, _node_outputs, _voice_lines)
- Bảo vệ các run gần đây (mặc định trong vòng 2 giờ qua)
- Phân loại rác:
  + Thư mục rỗng (0 tệp)
  + Rác test cũ (chỉ có state.json, không có artifacts/media, id node test)
  + Run test đặc biệt (run_hf_test, run_test_mix, hf_smoke, run_hf_test_clean)
  + Run media cũ (chỉ dọn khi có cờ --include-media)
- Hỗ trợ --dry-run (mặc định), --trash (chuyển vào Thùng rác macOS, an toàn khôi phục) hoặc --delete (xoá hẳn)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Các mục bảo vệ cứng — TUYỆT ĐỐI KHÔNG XOÁ MẶC ĐỊNH
HARD_PROTECTED_FILES = {".gitkeep", "spend.json"}
SYSTEM_QUEUE_DIRS = {"events", "render_queue", "_node_outputs", "_voice_lines"}
SPECIAL_TEST_NAMES = {"run_hf_test", "run_test_mix", "hf_smoke", "run_hf_test_clean"}

# Node ID phổ biến trong các bộ test tự động
TEST_NODE_PREFIXES = (
    "node_idea",
    "node_video_gen",
    "node_retry",
    "node_faulty",
    "test_",
    "mock_",
    "s1",
    "s2",
    "c_de_mun",
    "c_de_bong",
)


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_dir_stats(path: Path) -> tuple[int, int, list[str]]:
    """Trả về (số tệp, tổng bytes, danh sách tệp con tương đối)."""
    file_count = 0
    total_bytes = 0
    files = []
    try:
        for root, _, filenames in os.walk(path):
            for f in filenames:
                fp = Path(root) / f
                try:
                    size = fp.stat().st_size
                    total_bytes += size
                    file_count += 1
                    files.append(str(fp.relative_to(path)))
                except OSError:
                    pass
    except OSError:
        pass
    return file_count, total_bytes, files


def analyze_run_dir(
    path: Path,
    now: float,
    keep_recent_sec: float,
    include_media: bool = False,
) -> dict[str, Any]:
    name = path.name
    mtime = path.stat().st_mtime
    age_hours = (now - mtime) / 3600.0
    file_count, total_bytes, files = get_dir_stats(path)
    size_mb = total_bytes / (1024.0 * 1024.0)

    # 1. Hệ thống / Hàng đợi
    if name in SYSTEM_QUEUE_DIRS:
        return {
            "path": path,
            "name": name,
            "category": "system_queue",
            "is_removable": False,
            "reason": "Hàng đợi / cache runtime của hệ thống",
            "file_count": file_count,
            "size_mb": size_mb,
            "age_hours": age_hours,
        }

    # 2. Vừa chạy gần đây
    if (now - mtime) < keep_recent_sec:
        return {
            "path": path,
            "name": name,
            "category": "recent_active",
            "is_removable": False,
            "reason": f"Mới tạo/sửa đổi ({age_hours:.1f}h trước < ngưỡng bảo vệ)",
            "file_count": file_count,
            "size_mb": size_mb,
            "age_hours": age_hours,
        }

    # 3. Thư mục rỗng
    if file_count == 0:
        return {
            "path": path,
            "name": name,
            "category": "empty",
            "is_removable": True,
            "reason": "Thư mục rỗng (0 tệp)",
            "file_count": 0,
            "size_mb": 0.0,
            "age_hours": age_hours,
        }

    # 4. Tên test đặc biệt
    if name in SPECIAL_TEST_NAMES:
        return {
            "path": path,
            "name": name,
            "category": "special_test",
            "is_removable": True,
            "reason": "Thư mục chạy test cũ (named test run)",
            "file_count": file_count,
            "size_mb": size_mb,
            "age_hours": age_hours,
        }

    # 5. Phân tích state.json
    state_file = path / "state.json"
    has_media = any(f.endswith((".mp4", ".mov", ".webm", ".wav", ".mp3")) for f in files)

    if file_count == 1 and state_file.exists():
        # Chỉ có state.json
        try:
            state_data = json.loads(state_file.read_text(encoding="utf-8"))
            node_states = state_data.get("node_states", {})
            node_ids = list(node_states.keys())
            status = state_data.get("status", "unknown")
            is_test_nodes = all(
                any(nid.startswith(prefix) for prefix in TEST_NODE_PREFIXES)
                for nid in node_ids
            ) if node_ids else True

            if is_test_nodes or status in ("failed", "cancelled") or len(node_ids) == 0:
                return {
                    "path": path,
                    "name": name,
                    "category": "state_only_test",
                    "is_removable": True,
                    "reason": f"Chỉ có state.json (status={status}, nodes={len(node_ids)})",
                    "file_count": 1,
                    "size_mb": size_mb,
                    "age_hours": age_hours,
                }
        except Exception:
            return {
                "path": path,
                "name": name,
                "category": "corrupt_state",
                "is_removable": True,
                "reason": "Chỉ có state.json bị lỗi định dạng",
                "file_count": 1,
                "size_mb": size_mb,
                "age_hours": age_hours,
            }

    # 6. Run có chứa Media
    if has_media or size_mb >= 1.0:
        return {
            "path": path,
            "name": name,
            "category": "media_run",
            "is_removable": include_media,
            "reason": f"Run chứa media/artifacts ({size_mb:.1f} MB, {file_count} tệp)"
            + (" (chỉ xoá khi bật --include-media)" if not include_media else ""),
            "file_count": file_count,
            "size_mb": size_mb,
            "age_hours": age_hours,
        }

    # 7. Còn lại: run nhỏ không chứa media
    return {
        "path": path,
        "name": name,
        "category": "other_run",
        "is_removable": True,
        "reason": f"Run cũ không chứa media ({file_count} tệp, {size_mb:.2f} MB)",
        "file_count": file_count,
        "size_mb": size_mb,
        "age_hours": age_hours,
    }


def send_to_trash(path: Path) -> bool:
    """Chuyển thư mục vào Thùng rác macOS (khôi phục được)."""
    if sys.platform == "darwin":
        try:
            cmd = ["osascript", "-e", f'tell application "Finder" to delete POSIX file "{path.resolve()}"']
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                return True
        except Exception:
            pass
    # Fallback ~/.Trash
    trash_dir = Path.home() / ".Trash"
    if trash_dir.exists():
        try:
            target = trash_dir / f"{path.name}_{int(time.time())}"
            shutil.move(str(path), str(target))
            return True
        except Exception:
            pass
    return False


def run_cleanup(
    project_id: str,
    dry_run: bool = True,
    action: str = "dry-run",
    keep_recent_hours: float = 2.0,
    include_media: bool = False,
    clean_queues: bool = False,
) -> dict[str, Any]:
    repo_root = get_repo_root()
    runs_dir = repo_root / "data" / "projects" / project_id / "runs"

    if not runs_dir.exists():
        print(f"[-] Thư mục không tồn tại: {runs_dir}")
        return {"error": "runs_dir_not_found"}

    now = time.time()
    keep_recent_sec = keep_recent_hours * 3600.0

    entries = sorted(os.scandir(runs_dir), key=lambda e: e.name)
    analyzed_items = []
    protected_files = []

    for entry in entries:
        if entry.is_file():
            protected_files.append(entry.name)
            continue
        if entry.is_dir():
            p = Path(entry.path)
            stat = analyze_run_dir(p, now, keep_recent_sec, include_media=include_media)
            if stat["name"] in SYSTEM_QUEUE_DIRS and clean_queues:
                stat["is_removable"] = True
                stat["reason"] = "Hàng đợi được yêu cầu làm sạch bằng cờ --clean-queues"
            analyzed_items.append(stat)

    candidates = [item for item in analyzed_items if item["is_removable"]]
    kept = [item for item in analyzed_items if not item["is_removable"]]

    total_runs_count = len(analyzed_items)
    total_runs_size_mb = sum(item["size_mb"] for item in analyzed_items)
    cand_count = len(candidates)
    cand_size_mb = sum(item["size_mb"] for item in candidates)

    print("\n" + "=" * 70)
    print(f" BÁO CÁO DỌN DẸP RUNS: Dự án '{project_id}'")
    print(f" Thư mục: {runs_dir}")
    print(f" Chế độ: {action.upper()}" + (" (KHÔNG thay đổi dữ liệu)" if dry_run else " (THỰC THI THẬT)"))
    print("=" * 70)
    print(f"[*] Tổng số thư mục runs hiện tại: {total_runs_count} ({total_runs_size_mb:.2f} MB)")
    print(f"[*] Tệp gốc được bảo vệ ({len(protected_files)}): {', '.join(protected_files)}")
    print(f"[*] Số thư mục đề xuất dọn: {cand_count} ({cand_size_mb:.2f} MB)")
    print(f"[*] Số thư mục giữ lại: {len(kept)} ({total_runs_size_mb - cand_size_mb:.2f} MB)")
    print("-" * 70)

    # Phân loại đề xuất
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for c in candidates:
        by_cat.setdefault(c["category"], []).append(c)

    for cat, items in by_cat.items():
        cat_size = sum(x["size_mb"] for x in items)
        print(f"  + [{cat}] {len(items)} mục ({cat_size:.2f} MB): ví dụ {items[0]['name']}")

    if candidates:
        print("\nDanh sách chi tiết 10 mục đề xuất dọn đầu tiên:")
        for c in candidates[:10]:
            print(f"  - {c['name']:<25} | {c['size_mb']:>7.2f} MB | {c['file_count']:>3} tệp | {c['reason']}")
        if len(candidates) > 10:
            print(f"  ... và {len(candidates) - 10} mục khác.")

    executed_count = 0
    executed_size_mb = 0.0
    failed_items = []

    if not dry_run and candidates:
        print(f"\n[!] Bắt đầu thực thi '{action}' trên {len(candidates)} thư mục...")
        for c in candidates:
            p = c["path"]
            try:
                if action == "trash":
                    ok = send_to_trash(p)
                    if ok:
                        executed_count += 1
                        executed_size_mb += c["size_mb"]
                    else:
                        failed_items.append((c["name"], "Không thể đưa vào thùng rác"))
                elif action == "delete":
                    shutil.rmtree(p)
                    executed_count += 1
                    executed_size_mb += c["size_mb"]
            except Exception as ex:
                failed_items.append((c["name"], str(ex)))

        print(f"[✓] Đã xử lý thành công: {executed_count}/{len(candidates)} mục ({executed_size_mb:.2f} MB)")
        if failed_items:
            print(f"[!] Thất bại {len(failed_items)} mục: {failed_items[:3]}")

    print("=" * 70)
    if dry_run:
        print("LƯU Ý: Đây là chế độ DRY-RUN. Để thực thi thật:")
        print(f"  Chuyển vào Thùng rác (khuyên dùng): python scripts/maintenance/clean_runs.py --project {project_id} --trash")
        print(f"  Xoá vĩnh viễn:                     python scripts/maintenance/clean_runs.py --project {project_id} --delete")
    print("=" * 70 + "\n")

    return {
        "project_id": project_id,
        "runs_dir": str(runs_dir),
        "total_before_count": total_runs_count,
        "total_before_size_mb": total_runs_size_mb,
        "candidates_count": cand_count,
        "candidates_size_mb": cand_size_mb,
        "kept_count": len(kept),
        "kept_size_mb": total_runs_size_mb - cand_size_mb,
        "executed_count": executed_count,
        "action": action,
        "dry_run": dry_run,
        "candidates": [
            {
                "name": c["name"],
                "category": c["category"],
                "size_mb": c["size_mb"],
                "file_count": c["file_count"],
                "reason": c["reason"],
            }
            for c in candidates
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Dọn dẹp rác thư mục runs/ của SocNhoTV")
    parser.add_argument("--project", default="soc-nho-tv", help="ID dự án (mặc định: soc-nho-tv)")
    parser.add_argument("--all-projects", action="store_true", help="Quét toàn bộ dự án trong data/projects/")
    parser.add_argument("--dry-run", action="store_true", help="Chạy thử nghiệm không sửa đổi gì (mặc định)")
    parser.add_argument("--trash", action="store_true", help="Chuyển thư mục vào Thùng rác macOS (an toàn, khôi phục được)")
    parser.add_argument("--delete", action="store_true", help="Xoá vĩnh viễn các thư mục rác")
    parser.add_argument("--keep-recent-hours", type=float, default=2.0, help="Số giờ bảo vệ các run vừa tạo (mặc định: 2.0h)")
    parser.add_argument("--include-media", action="store_true", help="Bao gồm cả các run chứa video/media cũ")
    parser.add_argument("--clean-queues", action="store_true", help="Làm sạch cả các hàng đợi runtime (events, render_queue)")
    parser.add_argument("--json", action="store_true", help="Xuất kết quả dưới dạng JSON")

    args = parser.parse_args()

    # Mặc định an toàn: nếu không có --trash hay --delete thì ép về dry-run
    if not args.trash and not args.delete:
        dry_run = True
        action = "dry-run"
    elif args.trash:
        dry_run = args.dry_run
        action = "trash" if not args.dry_run else "dry-run (trash simulated)"
    else:
        dry_run = args.dry_run
        action = "delete" if not args.dry_run else "dry-run (delete simulated)"

    repo_root = get_repo_root()
    projects_dir = repo_root / "data" / "projects"

    projects = []
    if args.all_projects:
        if projects_dir.exists():
            projects = [p.name for p in projects_dir.iterdir() if p.is_dir()]
    else:
        projects = [args.project]

    results = []
    for pid in projects:
        res = run_cleanup(
            project_id=pid,
            dry_run=dry_run,
            action=action,
            keep_recent_hours=args.keep_recent_hours,
            include_media=args.include_media,
            clean_queues=args.clean_queues,
        )
        results.append(res)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
