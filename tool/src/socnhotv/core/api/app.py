from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
    Generation,
    Graph,
    GraphRunRequest,
    GraphRunSummary,
    GraphValidationResult,
    NodeDefinition,
    NodeInstance,
    NodeState,
    RunMode,
    SSEEvent,
    SSEEventType,
)
from socnhotv.core.engine.graph_runner import (
    BudgetExceededError,
    GraphExecutionError,
    GraphRunner,
)
from socnhotv.core.engine.validator import validate_graph
from socnhotv.core.models_registry.registry import ModelRegistry, ModelSpec
from socnhotv.core.nodes.registry import NodeRegistry
from socnhotv.core.providers.mock_provider import MockProvider
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root

app = FastAPI(
    title="AI Video Studio Core Engine",
    description="Backend động cơ chạy đồ thị node video AI & công cụ hậu kỳ",
    version="0.1.0",
)

# Cho phép Next.js và các client gọi từ localhost:3000 / localhost:3100
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Quản lý hàng đợi SSE sự kiện theo project_id
project_event_queues: Dict[str, List[asyncio.Queue]] = {}


def broadcast_event(project_id: str, event: SSEEvent) -> None:
    queues = project_event_queues.get(project_id, [])
    payload = event.model_dump_json(by_alias=True)
    for q in queues:
        q.put_nowait(payload)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Video Studio Core",
        "repo_root": str(get_repo_root()),
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@app.get("/models", response_model=List[ModelSpec])
async def list_models(kind: Optional[str] = None):
    registry = ModelRegistry.get_instance()
    if kind:
        return registry.list_by_kind(kind)
    return registry.list_all()


@app.get("/node-types", response_model=List[NodeDefinition])
async def list_node_types():
    return NodeRegistry.list_all()


@app.get("/projects")
async def list_projects():
    """Đọc danh sách các dự án từ data/workspace.json."""
    repo_root = get_repo_root()
    workspace_file = repo_root / "data" / "workspace.json"
    if not workspace_file.exists():
        return {"activeProject": "soc-nho-tv", "projects": []}

    with open(workspace_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@app.get("/projects/{project_id}/graph", response_model=Graph)
async def get_project_graph(project_id: str):
    store = ProjectStore(project_id)
    return store.get_graph()


@app.post("/projects/{project_id}/graph")
async def update_project_graph(project_id: str, graph: Graph):
    store = ProjectStore(project_id)
    store.save_graph(graph)
    return {"status": "success", "updatedAt": graph.updated_at}


@app.get("/projects/{project_id}/artifacts/{artifact_id}")
async def get_artifact(project_id: str, artifact_id: str):
    store = ProjectStore(project_id)
    artifact = store.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@app.post("/projects/{project_id}/graph/validate", response_model=GraphValidationResult)
async def validate_project_graph(project_id: str, graph: Optional[Graph] = None):
    """Kiểm tra toàn diện tính hợp lệ của đồ thị node: chu trình, kiểu cổng, required inputs."""
    if graph is None:
        store = ProjectStore(project_id)
        graph = store.get_graph()
    return validate_graph(graph)


@app.post("/projects/{project_id}/run", response_model=GraphRunSummary)
async def run_graph(project_id: str, payload: Dict[str, Any] = Body(...)):
    """Thực thi đồ thị node thông qua GraphRunner:
    Hỗ trợ chế độ chạy linh hoạt:
    - ALL: Chạy toàn bộ (bỏ qua các node đã ghim hợp lệ không stale).
    - FORCE_ALL: Chạy lại toàn bộ đồ thị.
    - SINGLE_NODE: Chạy 1 node cụ thể (targetNodeId).
    - DOWNSTREAM: Chạy 1 node và toàn bộ các node con cháu (descendants).
    """
    store = ProjectStore(project_id)
    if "graph" in payload and payload["graph"]:
        graph = Graph.model_validate(payload["graph"])
    else:
        graph = store.get_graph()

    # Hỗ trợ backward compatibility với request cũ dạng {"nodeId": "...", "isMock": true}
    target_node_id = payload.get("targetNodeId") or payload.get("nodeId")
    mode_str = payload.get("mode")
    if not mode_str and target_node_id:
        mode = RunMode.SINGLE_NODE
    elif mode_str:
        mode = RunMode(mode_str)
    else:
        mode = RunMode.ALL

    req = GraphRunRequest(
        project_id=project_id,
        graph_id=payload.get("graphId") or graph.id,
        mode=mode,
        target_node_id=target_node_id,
        spending_limit_usd=payload.get("spendingLimitUsd"),
        mock_mode=payload.get("mockMode", True),
        max_retries=int(payload.get("maxRetries", 3)),
        concurrency_limit=int(payload.get("concurrencyLimit", 2)),
    )

    def sse_callback(event: SSEEvent):
        broadcast_event(project_id, event)

    runner = GraphRunner(
        store=store,
        model_registry=ModelRegistry(),
        event_callback=sse_callback,
    )

    try:
        summary = await runner.run(graph, req)
        return summary
    except (BudgetExceededError, GraphExecutionError) as be:
        raise HTTPException(status_code=400, detail=str(be))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/projects/{project_id}/events")
async def sse_events(project_id: str):
    """Server-Sent Events streaming cho giao diện Next.js."""

    async def event_generator() -> AsyncGenerator[str, None]:
        q = asyncio.Queue()
        if project_id not in project_event_queues:
            project_event_queues[project_id] = []
        project_event_queues[project_id].append(q)

        try:
            # Gửi ping kết nối ban đầu
            yield f"data: {json.dumps({'type': 'connected', 'projectId': project_id})}\n\n"

            while True:
                data = await q.get()
                yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if project_id in project_event_queues and q in project_event_queues[project_id]:
                project_event_queues[project_id].remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
