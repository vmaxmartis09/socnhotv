from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from socnhotv.core.contracts.types import Graph, GraphRunRequest, NodeState, SSEEvent, SSEEventType
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root

logger = logging.getLogger("socnhotv.core.run_manager")


class RunManager:
    """Quản lý trạng thái thực thi phiên chạy (Runs) đồ thị:
    - Lưu vết trạng thái vào data/projects/<id>/runs/<run_id>/state.json
    - Theo dõi tiến độ thời gian thực, node hiện tại, phần trăm tổng
    - Khôi phục trạng thái khi người dùng tải lại trang giữa chừng
    - Quét danh sách thành phẩm video từ data/projects/<id>/output/
    """

    _instance: Optional["RunManager"] = None

    def __init__(self):
        self._active_runs: Dict[str, Dict[str, Any]] = {}  # project_id -> run_dict
        self._cancel_events: Dict[str, asyncio.Event] = {}  # project_id -> cancel_event
        self.repo_root = get_repo_root()

    @classmethod
    def get_instance(cls) -> "RunManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_project_runs_dir(self, project_id: str) -> Path:
        return self.repo_root / "data" / "projects" / project_id / "runs"

    def _get_project_output_dir(self, project_id: str) -> Path:
        return self.repo_root / "data" / "projects" / project_id / "output"

    def start_run(
        self,
        project_id: str,
        run_id: str,
        graph: Graph,
        req: GraphRunRequest,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> Dict[str, Any]:
        """Bắt đầu phiên chạy mới, khởi tạo state.json."""
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        now_ts = time.time()

        nodes_info = [
            {
                "id": n.id,
                "type": n.type,
                "name": n.params.get("title") or n.id,
                "state": "pending",
                "progressPct": 0,
                "error": None,
            }
            for n in graph.nodes
        ]

        run_state = {
            "runId": run_id,
            "id": run_id,
            "projectId": project_id,
            "status": "running",
            "mode": req.mode.value if hasattr(req.mode, "value") else str(req.mode),
            "stage": "Bắt đầu",
            "currentNodeId": None,
            "progress": 0.05,
            "progressPct": 5,
            "startedAtTs": now_ts,
            "createdAt": now_iso,
            "updatedAt": now_iso,
            "elapsedSec": 0.0,
            "actualCostUsd": 0.0,
            "costUsd": 0.0,
            "nodes": nodes_info,
            "totalNodes": len(nodes_info),
            "completedNodes": 0,
            "output": None,
            "error": None,
        }

        self._active_runs[project_id] = run_state
        if cancel_event:
            self._cancel_events[project_id] = cancel_event

        self.persist_run_state(project_id, run_id, run_state)
        return run_state

    def update_node_progress(
        self,
        project_id: str,
        run_id: str,
        node_id: str,
        state: str,
        progress: float = 0.0,
        message: Optional[str] = None,
        cost_usd: float = 0.0,
    ) -> None:
        """Cập nhật tiến trình của 1 node trong phiên chạy."""
        run_state = self._active_runs.get(project_id)
        if not run_state or run_state.get("runId") != run_id:
            # Khôi phục từ disk nếu cần
            run_state = self.get_run_state_from_disk(project_id, run_id)
            if not run_state:
                return
            self._active_runs[project_id] = run_state

        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        run_state["updatedAt"] = now_iso
        start_ts = run_state.get("startedAtTs", time.time())
        run_state["elapsedSec"] = round(time.time() - start_ts, 1)
        run_state["currentNodeId"] = node_id

        # Cập nhật danh sách nodes
        completed_count = 0
        current_node_type = "node"
        for n in run_state.get("nodes", []):
            if n["id"] == node_id:
                current_node_type = n.get("type", "node")
                n["state"] = state
                n["progressPct"] = round(progress * 100)
                if state == "failed":
                    n["error"] = message
            if n.get("state") in ("completed", "succeeded"):
                completed_count += 1

        run_state["completedNodes"] = completed_count
        total_nodes = max(1, len(run_state.get("nodes", [])))
        
        # Tính % tổng tiến độ
        base_progress = completed_count / total_nodes
        node_partial = (progress / total_nodes) if state == "running" else 0.0
        overall_progress = min(0.99, max(0.05, base_progress + node_partial))
        run_state["progress"] = round(overall_progress, 3)
        run_state["progressPct"] = round(overall_progress * 100)

        # Cập nhật tên công đoạn nhân văn
        stage_names = {
            "text": "Khởi tạo ý tưởng",
            "script": "Biên kịch phân cảnh",
            "character": "Nạp hồ sơ nhân vật",
            "voice_tts": "Đọc thoại Sóc Nhỏ (OmniVoice)",
            "captions": "Tạo phụ đề Karaoke",
            "image": "Chuẩn bị hình ảnh",
            "image_gen": "Tạo ảnh AI",
            "scene": "Đóng gói phân cảnh",
            "hyperframes_render": "Dựng video HyperFrames",
            "export": "Xuất & Đóng gói sản phẩm",
        }
        human_stage = stage_names.get(current_node_type, f"Xử lý {current_node_type}")
        if message:
            run_state["stage"] = f"{human_stage} · {message}"
        else:
            run_state["stage"] = human_stage

        if cost_usd > 0:
            run_state["actualCostUsd"] = round(run_state.get("actualCostUsd", 0.0) + cost_usd, 4)
            run_state["costUsd"] = run_state["actualCostUsd"]

        self.persist_run_state(project_id, run_id, run_state)

    def complete_run(
        self,
        project_id: str,
        run_id: str,
        is_success: bool,
        output_info: Optional[Dict[str, Any]] = None,
        error_msg: Optional[str] = None,
    ) -> None:
        """Đánh dấu phiên chạy hoàn tất hoặc thất bại."""
        run_state = self._active_runs.get(project_id)
        if not run_state or run_state.get("runId") != run_id:
            run_state = self.get_run_state_from_disk(project_id, run_id) or {}

        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        start_ts = run_state.get("startedAtTs", time.time())
        run_state["elapsedSec"] = round(time.time() - start_ts, 1)
        run_state["status"] = "completed" if is_success else "failed"
        run_state["progress"] = 1.0 if is_success else run_state.get("progress", 0.0)
        run_state["progressPct"] = 100 if is_success else run_state.get("progressPct", 0)
        run_state["updatedAt"] = now_iso
        run_state["completedAt"] = now_iso
        run_state["stage"] = "Hoàn tất xuất sắc" if is_success else f"Thất bại: {error_msg}"
        if output_info:
            run_state["output"] = output_info
            run_state["outputs"] = output_info
        if error_msg:
            run_state["error"] = error_msg

        self.persist_run_state(project_id, run_id, run_state)
        # Giữ lại trong _active_runs một thời gian ngắn hoặc xoá active
        if project_id in self._active_runs and self._active_runs[project_id].get("runId") == run_id:
            # Chuyển trạng thái hoàn thành để UI đọc được
            self._active_runs[project_id] = run_state

    def cancel_run(self, project_id: str) -> bool:
        """Kích hoạt hủy phiên chạy đang chạy."""
        event = self._cancel_events.get(project_id)
        if event:
            event.set()
        run_state = self._active_runs.get(project_id)
        if run_state:
            run_state["status"] = "cancelled"
            run_state["stage"] = "Đã dừng chạy theo yêu cầu người dùng"
            run_state["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            run_id = run_state.get("runId", "")
            if run_id:
                self.persist_run_state(project_id, run_id, run_state)
            return True
        return False

    def get_active_run(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Lấy phiên chạy đang active của project (nếu có)."""
        run = self._active_runs.get(project_id)
        if run and run.get("status") == "running":
            # Cập nhật elapsedSec tính tới hiện tại
            start_ts = run.get("startedAtTs", time.time())
            run["elapsedSec"] = round(time.time() - start_ts, 1)
            return run

        # Kiểm tra disk xem có run nào chưa kết thúc không
        runs_dir = self._get_project_runs_dir(project_id)
        if runs_dir.exists():
            for state_file in sorted(runs_dir.glob("*/state.json"), key=os.path.getmtime, reverse=True)[:5]:
                try:
                    data = json.loads(state_file.read_text(encoding="utf-8"))
                    if data.get("status") == "running":
                        # Nếu quá 30 phút không update thì coi như failed/stale
                        mtime = state_file.stat().st_mtime
                        if time.time() - mtime < 1800:
                            self._active_runs[project_id] = data
                            return data
                except Exception:
                    continue
        return None

    def list_runs(self, project_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Liệt kê các phiên chạy của dự án."""
        runs: List[Dict[str, Any]] = []
        active = self.get_active_run(project_id)
        if active:
            runs.append(active)

        seen_ids = {active["runId"]} if active else set()

        runs_dir = self._get_project_runs_dir(project_id)
        if runs_dir.exists():
            state_files = sorted(runs_dir.glob("*/state.json"), key=os.path.getmtime, reverse=True)
            for sf in state_files:
                if len(runs) >= limit:
                    break
                try:
                    data = json.loads(sf.read_text(encoding="utf-8"))
                    rid = data.get("runId") or sf.parent.name
                    if rid in seen_ids:
                        continue
                    seen_ids.add(rid)
                    runs.append(data)
                except Exception:
                    continue
        return runs

    def get_run_state_from_disk(self, project_id: str, run_id: str) -> Optional[Dict[str, Any]]:
        state_file = self._get_project_runs_dir(project_id) / run_id / "state.json"
        if state_file.exists():
            try:
                return json.loads(state_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return None

    def persist_run_state(self, project_id: str, run_id: str, state: Dict[str, Any]) -> None:
        try:
            run_dir = self._get_project_runs_dir(project_id) / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            state_file = run_dir / "state.json"
            # Lưu an toàn atomic
            tmp_file = run_dir / "state.json.tmp"
            tmp_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp_file.replace(state_file)
        except Exception as e:
            logger.warning(f"Lỗi lưu state.json phiên {run_id}: {e}")

    def list_outputs(self, project_id: str) -> List[Dict[str, Any]]:
        """Quét toàn bộ video thành phẩm trong data/projects/<id>/output/."""
        output_dir = self._get_project_output_dir(project_id)
        results: List[Dict[str, Any]] = []
        seen_slugs = set()

        if not output_dir.exists():
            return results

        # 1. Tìm các thư mục output/<slug>/video.json (theo chuẩn Mục 2B-C)
        for manifest_path in sorted(output_dir.glob("*/video.json"), key=os.path.getmtime, reverse=True):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                slug = manifest_path.parent.name
                seen_slugs.add(slug)
                manifest["slug"] = slug
                manifest["folder_rel"] = f"output/{slug}"
                results.append(manifest)
            except Exception:
                continue

        # 2. Tìm các file mp4 lẻ trong output/*.mp4 (cho các video cũ nếu có)
        for mp4 in sorted(output_dir.glob("*.mp4"), key=os.path.getmtime, reverse=True):
            stem = mp4.stem
            if stem in seen_slugs:
                continue
            seen_slugs.add(stem)
            st = mp4.stat()
            results.append({
                "id": f"out_{stem}",
                "title": stem.replace("_", " ").replace("-", " ").title(),
                "topic": stem,
                "slug": stem,
                "folder_rel": f"output/{mp4.name}",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
                "duration_s": 0.0,
                "size_mb": round(st.st_size / (1024 * 1024), 2),
                "platforms": ["tiktok", "youtube"],
                "files": {
                    "video": f"output/{mp4.name}",
                },
                "verify": {"pass": True, "scores": {}},
            })

        return results
