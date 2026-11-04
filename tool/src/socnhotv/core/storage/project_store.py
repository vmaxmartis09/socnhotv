from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
    Graph,
)


def get_repo_root() -> Path:
    """Tìm thư mục gốc của repository socnhotv (chứa data/ và tool/)."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "data" / "workspace.json").exists() or (parent / "tool" / "src").exists():
            return parent
    return current.parents[4]


class ProjectStore:
    """Quản lý kho tệp và dữ liệu của một project trong data/projects/<project_id>/."""

    def __init__(self, project_id: str, repo_root: Optional[Path] = None):
        self.project_id = project_id
        self.repo_root = repo_root or get_repo_root()
        self.project_dir = self.repo_root / "data" / "projects" / project_id

        # Các thư mục con bên trong project
        self.assets_dir = self.project_dir / "assets"
        self.runs_dir = self.project_dir / "runs"
        self.outputs_dir = self.project_dir / "output"
        self.characters_dir = self.project_dir / "characters"
        self.content_dir = self.project_dir / "content"

        self._ensure_dirs()

    @property
    def output_dir(self) -> Path:
        return self.outputs_dir

    def _ensure_dirs(self) -> None:
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def get_graph_path(self) -> Path:
        return self.project_dir / "graph.json"

    def get_graph(self) -> Graph:
        graph_path = self.get_graph_path()
        if not graph_path.exists():
            # Khởi tạo đồ thị mặc định rỗng
            return Graph(
                id=f"graph_{self.project_id}",
                project_id=self.project_id,
                name=f"Graph for {self.project_id}",
                nodes=[],
                edges=[],
                updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )

        with open(graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Graph(**data)

    def save_graph(self, graph: Graph) -> None:
        graph.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        graph_path = self.get_graph_path()
        with open(graph_path, "w", encoding="utf-8") as f:
            json.dump(graph.model_dump(by_alias=True), f, indent=2, ensure_ascii=False)

    def store_bytes(
        self,
        data: bytes,
        ext: str,
        kind: ArtifactKind,
        provenance: ArtifactProvenance,
        meta: Optional[ArtifactMeta] = None,
        mime: Optional[str] = None,
    ) -> Artifact:
        """Lưu trữ dữ liệu nhị phân vào kho assets/ theo mã băm sha256 (Deduplication)."""
        sha256_hash = hashlib.sha256(data).hexdigest()
        clean_ext = ext.lstrip(".").lower()
        file_name = f"{sha256_hash}.{clean_ext}"
        target_path = self.assets_dir / file_name

        if not target_path.exists():
            with open(target_path, "wb") as f:
                f.write(data)

        # Mime type suy luận nếu chưa có
        if not mime:
            if clean_ext in ["png", "jpg", "jpeg", "webp"]:
                mime = f"image/{clean_ext}"
            elif clean_ext in ["mp4", "webm", "mov"]:
                mime = f"video/{clean_ext}"
            elif clean_ext in ["mp3", "wav", "m4a"]:
                mime = f"audio/{clean_ext}"
            elif clean_ext in ["json"]:
                mime = "application/json"
            else:
                mime = "application/octet-stream"

        relative_uri = f"assets/{file_name}"
        artifact_id = f"art_{sha256_hash[:12]}"

        artifact = Artifact(
            id=artifact_id,
            kind=kind,
            uri=relative_uri,
            mime=mime,
            size=len(data),
            hash=f"sha256:{sha256_hash}",
            meta=meta or ArtifactMeta(),
            provenance=provenance,
        )

        # Lưu metadata json kèm theo
        meta_json_path = self.assets_dir / f"{sha256_hash}.meta.json"
        with open(meta_json_path, "w", encoding="utf-8") as f:
            json.dump(artifact.model_dump(by_alias=True), f, indent=2, ensure_ascii=False)

        return artifact

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Tìm artifact theo ID (art_<hash_prefix>) hoặc file sha256."""
        for meta_file in self.assets_dir.glob("*.meta.json"):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("id") == artifact_id or meta_file.name.startswith(artifact_id):
                    return Artifact(**data)
            except Exception:
                continue
        return None

    def resolve_artifact_path(self, artifact: Artifact) -> Path:
        """Trả về đường dẫn tuyệt đối an toàn tới file artifact trên đĩa."""
        return self.project_dir / artifact.uri

    def create_run_session(self, run_id: str) -> Path:
        """Tạo thư mục cho một phiên chạy trong runs/<run_id>/."""
        session_dir = self.runs_dir / run_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def log_run_event(self, run_id: str, event_data: Dict[str, Any]) -> None:
        """Ghi nhận sự kiện vào nhật ký phiên chạy."""
        session_dir = self.runs_dir / run_id
        if not session_dir.exists():
            session_dir.mkdir(parents=True, exist_ok=True)

        events_file = session_dir / "events.jsonl"
        with open(events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_data, ensure_ascii=False) + "\n")

    def record_cost_ledger(
        self,
        run_id: str,
        artifact_id: Optional[str] = None,
        cost_usd: float = 0.0,
        model: str = "",
        node_id: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> None:
        """Ghi sổ chi phí thực tế vào runs/<run_id>/ledger.json."""
        session_dir = self.runs_dir / run_id
        session_dir.mkdir(parents=True, exist_ok=True)
        ledger_path = session_dir / "ledger.json"
        ledger_data = {"runId": run_id, "totalCostUsd": 0.0, "entries": []}

        if ledger_path.exists():
            try:
                with open(ledger_path, "r", encoding="utf-8") as f:
                    ledger_data = json.load(f)
            except Exception:
                pass

        ledger_data["entries"].append(
            {
                "artifactId": artifact_id or node_id or "unknown",
                "nodeId": node_id,
                "provider": provider or "local",
                "costUsd": cost_usd,
                "model": model,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        ledger_data["totalCostUsd"] = round(
            sum(e["costUsd"] for e in ledger_data["entries"]), 4
        )

        with open(ledger_path, "w", encoding="utf-8") as f:
            json.dump(ledger_data, f, indent=2, ensure_ascii=False)
