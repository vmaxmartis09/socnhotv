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
    NodeDefinition,
    NodeInstance,
    NodeState,
    SSEEvent,
    SSEEventType,
)
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


class RunNodeRequest(BaseModel):
    node_id: str = Field(..., alias="nodeId")
    is_mock: bool = Field(True, alias="isMock")


@app.post("/projects/{project_id}/run")
async def run_single_node(project_id: str, req: RunNodeRequest):
    """Thực thi một node (chế độ mock mặc định cho Bước 1)."""
    store = ProjectStore(project_id)
    graph = store.get_graph()

    # Tìm node trong đồ thị
    target_node: Optional[NodeInstance] = None
    for n in graph.nodes:
        if n.id == req.node_id:
            target_node = n
            break

    if not target_node:
        raise HTTPException(status_code=404, detail=f"Node {req.node_id} not found in graph")

    run_id = f"run_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    store.create_run_session(run_id)

    # Báo trạng thái bắt đầu chạy qua SSE
    start_event = SSEEvent(
        event_type=SSEEventType.NODE_STATE,
        run_id=run_id,
        node_id=target_node.id,
        state=NodeState.RUNNING,
        progress=0.1,
        message=f"Bắt đầu thực thi node {target_node.type}...",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    broadcast_event(project_id, start_event)

    provider = MockProvider(store)
    artifact: Optional[Artifact] = None
    cost_usd = 0.0

    try:
        # Xử lý theo từng loại node
        if target_node.type == "image_gen":
            prompt = target_node.params.get("prompt", "A cute squirrel Bi")
            aspect = target_node.params.get("aspectRatio", "9:16")
            arts = await provider.generate_images(
                prompt=prompt, aspect_ratio=aspect, n=1, node_id=target_node.id, run_id=run_id
            )
            artifact = arts[0] if arts else None
        elif target_node.type == "video_gen":
            prompt = target_node.params.get("prompt", "Camera dolly zoom on Bi")
            aspect = target_node.params.get("aspectRatio", "9:16")
            duration = target_node.params.get("durationSec", 8.0)
            artifact = await provider.generate_video(
                prompt=prompt, duration_sec=duration, aspect_ratio=aspect, node_id=target_node.id, run_id=run_id
            )
        elif target_node.type == "voice_tts":
            text = target_node.params.get("text", "Chào các bạn, mình là Sóc Nhỏ Bi nè!")
            voice_id = target_node.params.get("voiceId", "soc-nho")
            tempo = target_node.params.get("tempo", 1.10)
            artifact = await provider.speak_voice(
                text=text, voice_id=voice_id, tempo=tempo, node_id=target_node.id, run_id=run_id
            )
        else:
            # Fallback mock artifact
            prompt = str(target_node.params)
            arts = await provider.generate_images(
                prompt=prompt, node_id=target_node.id, run_id=run_id
            )
            artifact = arts[0] if arts else None

        if not artifact:
            raise RuntimeError("Không sinh được artifact từ provider")

        # Ghi nhận Generation mới (Mục 11: mỗi lần chạy là 1 generation, không ghi đè)
        gen_id = f"gen_{uuid.uuid4().hex[:8]}"
        new_gen = Generation(
            id=gen_id,
            node_id=target_node.id,
            params=target_node.params,
            artifact_id=artifact.id,
            cost_usd=cost_usd,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            is_pinned=True,  # Mặc định ghim lần chạy mới nhất
        )

        # Unpin các generation cũ
        for g in target_node.generations:
            g.is_pinned = False

        target_node.generations.insert(0, new_gen)
        target_node.pinned_generation_id = gen_id
        target_node.state = NodeState.COMPLETED
        target_node.is_stale = False

        # Lưu đồ thị cập nhật
        store.save_graph(graph)

        # Ghi sổ chi phí
        store.record_cost_ledger(run_id, artifact.id, cost_usd, artifact.provenance.model)

        # Báo hoàn thành qua SSE
        done_event = SSEEvent(
            event_type=SSEEventType.NODE_STATE,
            run_id=run_id,
            node_id=target_node.id,
            state=NodeState.COMPLETED,
            progress=1.0,
            message="Thực thi thành công!",
            cost_usd=cost_usd,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        broadcast_event(project_id, done_event)

        return {
            "status": "success",
            "runId": run_id,
            "nodeId": target_node.id,
            "generation": new_gen.model_dump(by_alias=True),
            "artifact": artifact.model_dump(by_alias=True),
        }

    except Exception as e:
        target_node.state = NodeState.FAILED
        store.save_graph(graph)

        err_event = SSEEvent(
            event_type=SSEEventType.NODE_STATE,
            run_id=run_id,
            node_id=target_node.id,
            state=NodeState.FAILED,
            progress=0.0,
            message=f"Lỗi: {str(e)}",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        broadcast_event(project_id, err_event)
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
