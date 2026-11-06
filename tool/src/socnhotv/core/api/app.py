from __future__ import annotations

import asyncio
import json
from pathlib import Path
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
    Generation,
    Graph,
    GraphCostEstimateResponse,
    GraphRunRequest,
    GraphRunSummary,
    GraphValidationResult,
    NodeDefinition,
    NodeInstance,
    NodeState,
    RunMode,
    RunPolicy,
    SSEEvent,
    SSEEventType,
)
from socnhotv.core.engine.graph_runner import (
    BudgetExceededError,
    GraphExecutionError,
    GraphRunner,
)
from socnhotv.core.engine.run_manager import RunManager
from socnhotv.core.engine.validator import validate_graph
from socnhotv.core.models_registry.registry import ModelRegistry, ModelSpec
from socnhotv.core.nodes.registry import NodeRegistry
from socnhotv.core.providers import (
    FalProvider,
    GoogleProvider,
    KeyVault,
    MissingApiKey,
    MockProvider,
    ProviderError,
    ProviderRouter,
    ReplicateProvider,
    SpendCapExceeded,
    SpendGuard,
    redact_secrets,
)
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root
from socnhotv.core.api.data_routes import router as data_router
from socnhotv.core.api.voice_routes import router as voice_router, execute_voice_clone

app = FastAPI(
    title="AI Video Studio Core Engine",
    description="Backend động cơ chạy đồ thị node video AI & công cụ hậu kỳ",
    version="0.1.0",
)

app.include_router(data_router)
app.include_router(voice_router)
from socnhotv.core.api.routes import include_all
include_all(app)

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
# Quản lý tín hiệu hủy thực sự (cancel_event) cho các phiên chạy đang diễn ra theo project_id
active_run_cancel_events: Dict[str, List[asyncio.Event]] = {}


def get_key_vault() -> KeyVault:
    """Trả về KeyVault phía máy chủ (cho phép override trong kiểm thử)."""
    return KeyVault()


def _parse_run_request(project_id: str, graph: Graph, payload: Dict[str, Any]) -> GraphRunRequest:
    target_node_id = payload.get("targetNodeId") or payload.get("nodeId")
    mode_str = payload.get("mode")
    if not mode_str and target_node_id:
        mode = RunMode.SINGLE_NODE
    elif mode_str:
        mode = RunMode(mode_str)
    else:
        mode = RunMode.ALL

    confirm_paid_run = bool(
        payload.get("confirmPaidRun") or payload.get("confirm_paid_run") or payload.get("confirmed", False)
    )
    run_policy_raw = payload.get("runPolicy") or payload.get("run_policy")
    run_policy = None
    if run_policy_raw:
        if isinstance(run_policy_raw, dict):
            run_policy = RunPolicy.model_validate(run_policy_raw)
        elif isinstance(run_policy_raw, RunPolicy):
            run_policy = run_policy_raw

    mock_mode_raw = payload.get("mockMode")
    mock_mode = bool(mock_mode_raw) if mock_mode_raw is not None else True

    return GraphRunRequest(
        project_id=project_id,
        graph_id=payload.get("graphId") or graph.id,
        mode=mode,
        target_node_id=target_node_id,
        spending_limit_usd=payload.get("spendingLimitUsd"),
        mock_mode=mock_mode,
        run_policy=run_policy,
        confirm_paid_run=confirm_paid_run,
        source=str(payload.get("source", "api")),
        max_retries=int(payload.get("maxRetries", 3)),
        concurrency_limit=int(payload.get("concurrencyLimit", 2)),
    )


def broadcast_event(project_id: str, event: SSEEvent) -> None:
    if event.message:
        event.message = redact_secrets(event.message)
    try:
        rm = RunManager.get_instance()
        if event.node_id and event.state:
            state_str = event.state.value if hasattr(event.state, "value") else str(event.state)
            rm.update_node_progress(
                project_id=project_id,
                run_id=event.run_id,
                node_id=event.node_id,
                state=state_str,
                progress=event.progress or 0.0,
                message=event.message,
                cost_usd=event.cost_usd or 0.0,
            )
    except Exception:
        pass

    ev_dict = event.model_dump(by_alias=True)
    if "state" in ev_dict and ev_dict["state"]:
        state_val = ev_dict["state"]
        if hasattr(state_val, "value"):
            state_val = state_val.value
        ev_dict["status"] = state_val
    if "progress" in ev_dict and ev_dict["progress"] is not None:
        ev_dict["progressPct"] = round(float(ev_dict["progress"]) * 100, 1)

    payload = json.dumps(ev_dict)
    queues = project_event_queues.get(project_id, [])
    for q in queues:
        q.put_nowait(payload)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "AI Video Studio Core",
        "repo_root": str(get_repo_root()),
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


class ModelItemResponse(ModelSpec):
    available: bool = True


@app.get("/models", response_model=List[ModelItemResponse])
async def list_models(kind: Optional[str] = None, provider: Optional[str] = None):
    registry = ModelRegistry.get_instance()
    vault = get_key_vault()
    if provider:
        items = registry.list_by_provider(provider)
        items = [m for m in items if m.kind == kind] if kind else items
    elif kind:
        items = registry.list_by_kind(kind)
    else:
        items = registry.list_all()

    out: List[ModelItemResponse] = []
    for m in items:
        pname = m.provider
        tier = getattr(m, "tier", "paid")
        is_avail = False
        if tier in ("free", "local") or pname in ("mock", "local"):
            is_avail = True
        elif pname == "pollinations":
            is_avail = True
        elif pname in ("google", "gemini"):
            is_avail = vault.has_valid_key("gemini")
        elif pname == "fal":
            is_avail = vault.has_valid_key("fal")
        elif pname == "replicate":
            is_avail = vault.has_valid_key("replicate")
        elif pname == "cloudflare":
            is_avail = vault.has_valid_key("cloudflare")
        else:
            is_avail = vault.has_valid_key(pname)

        d = m.model_dump(by_alias=True)
        d["available"] = is_avail
        out.append(ModelItemResponse.model_validate(d))
    return out


@app.get("/providers")
async def list_providers():
    """Trả về danh sách Provider adapter, khả năng hỗ trợ, tier, needs_key và trạng thái cấu hình (không trả khóa)."""
    vault = get_key_vault()
    registry = ModelRegistry.get_instance()
    dummy_store = ProjectStore("soc-nho-tv")
    dummy_key = "inspection_only_dummy_key_123456"

    mock_caps = MockProvider(dummy_store).capabilities()
    google_caps = GoogleProvider(dummy_store, key=dummy_key).capabilities()
    fal_caps = FalProvider(dummy_store, key=dummy_key).capabilities()
    rep_caps = ReplicateProvider(dummy_store, key=dummy_key).capabilities()

    caps_map = {
        "mock": mock_caps,
        "google": google_caps,
        "fal": fal_caps,
        "replicate": rep_caps,
        "pollinations": {"image": True, "video": False, "supports_reference": True},
        "cloudflare": {"image": True, "video": False, "supports_reference": False},
        "local": {"image": True, "video": False, "supports_reference": False},
    }

    try:
        from socnhotv.core.providers.factories import PROVIDER_META
    except ImportError:
        PROVIDER_META = {}

    providers_list = []
    ordered_ids = ["mock", "local", "cloudflare", "pollinations", "google", "fal", "replicate"]
    for pid in ordered_ids:
        meta = PROVIDER_META.get(pid, {})
        tier = meta.get("tier", "paid" if pid in ("google", "fal", "replicate") else "free")
        needs_key = meta.get("needs_key", pid in ("google", "fal", "replicate", "cloudflare"))
        label = meta.get("label", pid)
        quota_note = meta.get("quota_note", "")

        vault_name = "gemini" if pid in ("google", "gemini") else pid
        if not needs_key:
            configured = True
        else:
            configured = vault.has_valid_key(vault_name)

        models = [m.model_id for m in registry.list_by_provider(pid)]

        providers_list.append({
            "id": pid,
            "label": label,
            "tier": tier,
            "needs_key": bool(needs_key),
            "configured": configured,
            "quota_note": quota_note,
            "capabilities": caps_map.get(pid, {}),
            "models": models,
        })

    return {"providers": providers_list}


@app.get("/node-types", response_model=List[NodeDefinition])
async def list_node_types():
    return NodeRegistry.list_all()


def _custom_types_file(scope: str, project_id: Optional[str]) -> Path:
    root = get_repo_root() / "data"
    if scope == "shared":
        return root / "shared" / "custom_node_types.json"
    if not project_id:
        raise HTTPException(status_code=400, detail="Thiếu projectId cho loại node theo dự án.")
    return root / "projects" / project_id / "custom_node_types.json"


def _read_custom_types(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


@app.get("/custom-node-types")
async def list_custom_node_types(projectId: Optional[str] = Query(default=None)):
    """Loại node tuỳ biến: gộp dùng chung (shared) + theo dự án."""
    out: List[Dict[str, Any]] = []
    for d in _read_custom_types(_custom_types_file("shared", None)):
        out.append({**d, "scope": "shared"})
    if projectId:
        for d in _read_custom_types(_custom_types_file("project", projectId)):
            out.append({**d, "scope": "project"})
    return out


@app.post("/custom-node-types")
async def save_custom_node_type(
    definition: NodeDefinition,
    scope: str = Query(default="project"),
    projectId: Optional[str] = Query(default=None),
):
    """Lưu (thêm/ghi đè theo typeName) một loại node tuỳ biến — biến thể của node gốc."""
    if scope not in ("project", "shared"):
        raise HTTPException(status_code=400, detail="scope phải là 'project' hoặc 'shared'.")
    if not definition.base_type or NodeRegistry.get(definition.base_type) is None:
        raise HTTPException(status_code=400, detail="Loại node tuỳ biến phải có baseType hợp lệ.")
    path = _custom_types_file(scope, projectId)
    items = [d for d in _read_custom_types(path) if d.get("typeName") != definition.type_name]
    items.append(definition.model_dump(by_alias=True, mode="json", exclude={"scope"}))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "success", "typeName": definition.type_name, "scope": scope}


@app.delete("/custom-node-types/{type_name}")
async def delete_custom_node_type(
    type_name: str,
    scope: str = Query(default="project"),
    projectId: Optional[str] = Query(default=None),
):
    path = _custom_types_file(scope, projectId)
    items = _read_custom_types(path)
    kept = [d for d in items if d.get("typeName") != type_name]
    if len(kept) == len(items):
        raise HTTPException(status_code=404, detail="Không tìm thấy loại node.")
    path.write_text(json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "success"}


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


@app.post("/graph/validate", response_model=GraphValidationResult)
async def validate_direct_graph(graph: Graph):
    """Kiểm tra tính hợp lệ của đồ thị trực tiếp (POST /graph/validate)."""
    return validate_graph(graph)


@app.post("/projects/{project_id}/graph/validate", response_model=GraphValidationResult)
async def validate_project_graph(project_id: str, graph: Optional[Graph] = None):
    """Kiểm tra toàn diện tính hợp lệ của đồ thị node: chu trình, kiểu cổng, required inputs."""
    if graph is None:
        store = ProjectStore(project_id)
        graph = store.get_graph()
    return validate_graph(graph)


@app.get("/projects/{project_id}/spend")
async def get_project_spend_status(project_id: str, source: str = Query("api")):
    """Xem trạng thái trần chi tiêu dự án, trần 24 giờ và trần MCP/Agent."""
    store = ProjectStore(project_id)
    guard = SpendGuard(store.runs_dir)
    return guard.preview(0.0, source=source)


@app.post("/projects/{project_id}/estimate", response_model=GraphCostEstimateResponse)
async def estimate_project_run(project_id: str, payload: Dict[str, Any] = Body(default_factory=dict)):
    """Ước tính chi tiết từng node sẽ chạy, tổng chi phí USD, khóa API thiếu và trạng thái trần chi tiêu."""
    store = ProjectStore(project_id)
    if "graph" in payload and payload["graph"]:
        graph = Graph.model_validate(payload["graph"])
    else:
        graph = store.get_graph()

    req = _parse_run_request(project_id, graph, payload)
    runner = GraphRunner(store=store, model_registry=ModelRegistry())
    try:
        return runner.plan_execution(
            graph,
            req,
            vault=get_key_vault(),
            guard=SpendGuard(store.runs_dir),
        )
    except GraphExecutionError as ge:
        raise HTTPException(status_code=400, detail=redact_secrets(str(ge)))


@app.post("/projects/{project_id}/run", response_model=GraphRunSummary)
async def run_graph(project_id: str, payload: Dict[str, Any] = Body(...)):
    """Thực thi đồ thị node thông qua GraphRunner:
    Hỗ trợ chế độ chạy linh hoạt:
    - ALL: Chạy toàn bộ (bỏ qua các node đã ghim hợp lệ không stale).
    - FORCE_ALL: Chạy lại toàn bộ đồ thị.
    - SINGLE_NODE: Chạy 1 node cụ thể (targetNodeId).
    - DOWNSTREAM: Chạy 1 node và toàn bộ các node con cháu (descendants).
    Ở chế độ thật (mockMode=False) có phát sinh chi phí, yêu cầu confirmPaidRun=True.
    """
    store = ProjectStore(project_id)
    if "graph" in payload and payload["graph"]:
        graph = Graph.model_validate(payload["graph"])
    else:
        graph = store.get_graph()

    req = _parse_run_request(project_id, graph, payload)
    vault = get_key_vault()
    guard = SpendGuard(store.runs_dir)

    def sse_callback(event: SSEEvent):
        broadcast_event(project_id, event)

    # Kiểm tra trước chi phí & khóa API khi chạy chế độ thật trên đồ thị hợp lệ
    policy = req.resolve_run_policy()
    is_all_mock = (
        policy.image == "mock"
        and policy.video in ("mock", "off")
        and policy.text == "mock"
        and policy.voice == "mock"
    )
    if not is_all_mock and validate_graph(graph).is_valid:
        planner = GraphRunner(store=store, model_registry=ModelRegistry())
        try:
            plan = planner.plan_execution(graph, req, vault=vault, guard=guard)
        except GraphExecutionError as ge:
            raise HTTPException(status_code=400, detail=redact_secrets(str(ge)))

        if plan.missing_api_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Thiếu khóa API hợp lệ cho provider: {', '.join(plan.missing_api_keys)}",
            )
        if not plan.spend_status.get("canProceed", True):
            raise HTTPException(
                status_code=400,
                detail=str(plan.spend_status.get("reason") or "Vượt trần chi tiêu cho phép."),
            )
        if plan.total_estimated_cost_usd > 0 and not req.confirm_paid_run:
            return JSONResponse(
                status_code=409,
                content={
                    "detail": "Cần xác nhận chi phí trước khi gọi model trả phí (truyền confirmPaidRun=true).",
                    "estimate": plan.model_dump(by_alias=True),
                },
            )

    cancel_event = asyncio.Event()
    active_run_cancel_events.setdefault(project_id, []).append(cancel_event)

    import inspect
    router_kwargs: Dict[str, Any] = {
        "store": store,
        "guard": guard,
        "vault": vault,
        "mock_mode": req.mock_mode,
        "fallback_to_mock": False,
        "source": req.source,
    }
    sig = inspect.signature(ProviderRouter)
    if "run_policy" in sig.parameters or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
        router_kwargs["run_policy"] = policy

    provider = ProviderRouter(**router_kwargs)

    runner = GraphRunner(
        store=store,
        model_registry=ModelRegistry(),
        event_callback=sse_callback,
        provider=provider,
        cancel_event=cancel_event,
    )

    try:
        summary = await runner.run(graph, req)
        return summary
    except (BudgetExceededError, GraphExecutionError, MissingApiKey, SpendCapExceeded) as be:
        raise HTTPException(status_code=400, detail=redact_secrets(str(be)))
    except ProviderError as pe:
        raise HTTPException(status_code=400, detail=redact_secrets(str(pe)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=redact_secrets(str(e)))
    finally:
        ev_list = active_run_cancel_events.get(project_id, [])
        if cancel_event in ev_list:
            ev_list.remove(cancel_event)


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


@app.post("/projects/{project_id}/run/cancel")
async def cancel_project_run(project_id: str):
    """Kích hoạt cancel_event thực sự dừng các tác vụ đang chạy và phát sự kiện SSE hủy."""
    signalled = 0
    for ev in list(active_run_cancel_events.get(project_id, [])):
        ev.set()
        signalled += 1

    RunManager.get_instance().cancel_run(project_id)

    cancel_evt = SSEEvent(
        event_type=SSEEventType.RUN_FAILED,
        run_id=f"run_cancel_{int(time.time())}",
        state=NodeState.CANCELLED,
        message="Đã dừng chạy đồ thị theo yêu cầu người dùng.",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    broadcast_event(project_id, cancel_evt)
    return {"status": "cancelled", "projectId": project_id, "signalledRuns": signalled}


@app.get("/projects/{project_id}/runs")
async def list_project_runs(project_id: str, limit: int = 20):
    """Danh sách các phiên chạy của dự án."""
    return RunManager.get_instance().list_runs(project_id, limit=limit)


@app.get("/projects/{project_id}/runs/active")
async def get_active_project_run(project_id: str):
    """Phiên chạy đang chạy của dự án (nếu có) để frontend khôi phục trạng thái."""
    active = RunManager.get_instance().get_active_run(project_id)
    if not active:
        return JSONResponse(status_code=204, content=None)
    return active


@app.delete("/projects/{project_id}/runs/{run_id}")
async def delete_project_run(project_id: str, run_id: str):
    """Xoá một phiên chạy khỏi danh sách job (đang chạy thì dừng trước). Không xoá file output."""
    if not RunManager.get_instance().delete_run(project_id, run_id):
        raise HTTPException(status_code=404, detail=f"Không tìm thấy phiên chạy {run_id}")
    return {"status": "deleted", "runId": run_id}


@app.get("/projects/{project_id}/runs/{run_id}")
async def get_project_run(project_id: str, run_id: str):
    """Chi tiết 1 phiên chạy theo ID."""
    state = RunManager.get_instance().get_run_state_from_disk(project_id, run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy phiên chạy {run_id}")
    return state


@app.get("/projects/{project_id}/outputs")
async def list_project_outputs(project_id: str):
    """Danh sách các thành phẩm video trong thư mục data/projects/{project_id}/output/."""
    return RunManager.get_instance().list_outputs(project_id)


def _default_studio_characters(project_id: str) -> List[Dict[str, Any]]:
    return [
        {
            "id": "soc_nho",
            "projectId": project_id,
            "name": "Sóc Nhỏ (Bi)",
            "role": "main",
            "description": "Bé sóc đỏ 3-4 tuổi thân hình thon gọn, nhanh nhẹn, mặc áo phông vàng cổ tròn, quần short đen, giày thể thao tối màu, đuôi xù lớn.",
            "heightCm": 100,
            "scaleRatio": 1.0,
            "voiceId": "soc-nho",
            "defaultTempo": 1.10,
            "sampleAudioUrl": "/demo/voice/soc-nho_sample.mp3",
            "promptLock": "Bé sóc nam, 3-4 tuổi, cao ~100cm nặng ~15kg, thân hình THON GỌN, ốm khỏe, nhanh nhẹn như trẻ hay chạy nhảy, KHÔNG béo, bụng phẳng, thân nhỏ gọn, tay chân ngắn thon, đầu to vừa phải khoảng 1/4 thân, lông nâu đỏ cam, mắt đen tròn to, má hồng nhẹ, hai răng cửa, đuôi xù lớn, áo phông vàng vừa người, quần short đen, giày thể thao tối màu, 3D Pixar, ánh sáng studio mềm, nền trơn sáng",
            "referenceImages": [
                "/demo/characters/soc_nho_01.png",
                "/demo/characters/soc_nho_02.png",
                "/demo/characters/soc_nho_03.png",
                "/demo/characters/soc_nho_04.png",
            ],
            "referenceLibrary": [
                {
                    "id": "ref_sn_01",
                    "url": "/demo/characters/soc_nho_01.png",
                    "angle": "Chính diện vẫy tay (Master DNA)",
                    "isPrimary": True,
                    "sourceType": "master_dna",
                    "model": "gemini-2.5-flash-image",
                    "prompt": "assets/soc_nho/soc_nho_01.png — Chính diện chuẩn tỉ lệ 100cm",
                    "createdAt": "2026-11-01T17:30:00Z",
                },
                {
                    "id": "ref_sn_02",
                    "url": "/demo/characters/soc_nho_02.png",
                    "angle": "Góc nghiêng 3/4 trái",
                    "isPrimary": False,
                    "sourceType": "master_dna",
                    "model": "gemini-2.5-flash-image",
                    "prompt": "assets/soc_nho/soc_nho_02.png — Góc 3/4 trái giữ đuôi xù lớn",
                    "createdAt": "2026-11-01T17:30:30Z",
                },
                {
                    "id": "ref_sn_03",
                    "url": "/demo/characters/soc_nho_03.png",
                    "angle": "Góc nghiêng 3/4 phải",
                    "isPrimary": False,
                    "sourceType": "master_dna",
                    "model": "gemini-2.5-flash-image",
                    "prompt": "assets/soc_nho/soc_nho_03.png — Góc 3/4 phải cười tươi lộ 2 răng cửa",
                    "createdAt": "2026-11-01T17:31:00Z",
                },
                {
                    "id": "ref_sn_04",
                    "url": "/demo/characters/soc_nho_04.png",
                    "angle": "Nhìn từ sau (đuôi xù cong)",
                    "isPrimary": False,
                    "sourceType": "master_dna",
                    "model": "gemini-2.5-flash-image",
                    "prompt": "assets/soc_nho/soc_nho_04.png — Nhìn từ sau kiểm tra đuôi xù nâu đỏ",
                    "createdAt": "2026-11-01T17:31:30Z",
                },
            ],
            "generatedClips": [
                {
                    "id": "clip_sn_ep1_s1",
                    "url": "/demo/videos/canh_01.mp4",
                    "thumbnailUrl": "/demo/scenes/canh_01.jpg",
                    "episodeId": "ep_01_kham_rang",
                    "episodeTitle": "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
                    "sceneIndex": 1,
                    "sceneTitle": "Cảnh 1: Bi ở nhà cây mắt sáng rực nhìn kệ kẹo",
                    "durationSec": 8.0,
                    "model": "google-veo-2",
                    "createdAt": "2026-11-01T22:41:00Z",
                }
            ],
            "appearances": [
                {
                    "episodeId": "ep_01_kham_rang",
                    "episodeTitle": "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
                    "scenes": [
                        "Cảnh 1: Nhà cây & kệ kẹo",
                        "Cảnh 2: Ăn kẹo quên đánh răng",
                        "Cảnh 3: Sáng dậy ôm má đau răng",
                        "Cảnh 4: Khám răng cùng Bác sĩ Koala",
                        "Cảnh 5: Học chải răng đúng cách",
                        "Cảnh 6: Răng trắng sáng bóng",
                    ],
                }
            ],
            "memory": {
                "personality": "Nhanh nhẹn, lanh lợi, thân thiện, tinh nghịch, tò mò, hay quên đánh răng buổi tối",
                "catchphrases": [
                    "Oa, nhiều kẹo quá! Hôm nay Bi sẽ ăn thật nhiều luôn!",
                    "Cảm ơn bác sĩ! Từ nay Bi sẽ chăm sóc răng thật tốt!",
                ],
                "habits": [
                    "Thích ăn hạt dẻ và kẹo ngọt",
                    "Luôn vẫy cái đuôi xù lớn khi hào hứng",
                ],
                "pastEventsSummary": [
                    "Tập 1 (Sóc Nhỏ và Chiếc Răng Sâu): Ăn nhiều kẹo quên đánh răng nên bị sâu răng, được Bác sĩ Koala chữa và dạy đánh răng sáng tối.",
                ],
            },
        },
        {
            "id": "koala",
            "projectId": project_id,
            "name": "Bác sĩ Koala (Gấu Túi)",
            "role": "supporting",
            "description": "Bác sĩ nha khoa gấu túi lớn tuổi hiền từ, lông xám mềm, đeo kính tròn gọng vàng, mặc áo blouse trắng có huy hiệu chữ thập xanh lá.",
            "heightCm": 150,
            "scaleRatio": 1.5,
            "voiceId": "voice-koala",
            "defaultTempo": 1.00,
            "sampleAudioUrl": "/demo/voice/canh_01.mp3",
            "promptLock": "a gentle elderly koala doctor, about 150cm tall (1.5x the height of Bi the squirrel), soft gray fur, large round black nose, fluffy round ears, kind small eyes behind round gold glasses, wearing a clean white doctor coat with a green cross badge, a head mirror on his forehead, a stethoscope around his neck, 3D Pixar-style soft render, soft studio lighting, plain light gray background",
            "referenceImages": ["/demo/scenes/canh_04.jpg", "/demo/scenes/canh_05.jpg"],
            "referenceLibrary": [
                {
                    "id": "ref_kl_01",
                    "url": "/demo/scenes/canh_04.jpg",
                    "angle": "Khám răng cho Sóc Bi (Tỉ lệ 150cm : 100cm)",
                    "isPrimary": True,
                    "sourceType": "generated",
                    "model": "gemini-2.5-flash-image",
                    "prompt": "Bác sĩ Koala 150cm soi gương khám răng cho Sóc Bi 100cm tại phòng khám rừng xanh",
                    "createdAt": "2026-11-01T22:37:00Z",
                },
                {
                    "id": "ref_kl_02",
                    "url": "/demo/scenes/canh_05.jpg",
                    "angle": "Hướng dẫn cầm bàn chải mẫu",
                    "isPrimary": False,
                    "sourceType": "generated",
                    "model": "gemini-2.5-flash-image",
                    "prompt": "Bác sĩ Koala cầm bàn chải lớn hướng dẫn Bi đánh răng xoay tròn",
                    "createdAt": "2026-11-01T22:38:00Z",
                },
            ],
            "generatedClips": [],
            "appearances": [
                {
                    "episodeId": "ep_01_kham_rang",
                    "episodeTitle": "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu",
                    "scenes": [
                        "Cảnh 4: Khám răng cho Sóc Bi tại phòng khám gốc cây",
                        "Cảnh 5: Dạy Sóc Bi đánh răng xoay tròn sáng và tối",
                    ],
                }
            ],
            "memory": {
                "personality": "Hiền hậu, kiên nhẫn, ấm áp, dạy dỗ nhẹ nhàng",
                "catchphrases": [
                    "Cháu bị sâu răng rồi. Do ăn quá nhiều kẹo ngọt đấy.",
                    "Hãy đánh răng sáng và tối, ăn ít kẹo, uống nhiều nước nhé.",
                ],
                "habits": [
                    "Luôn đeo kính tròn gọng vàng và ống nghe quanh cổ",
                    "Dùng mô hình răng khổng lồ để hướng dẫn các bạn nhỏ",
                ],
                "pastEventsSummary": [
                    "Tập 1 (Sóc Nhỏ và Chiếc Răng Sâu): Khám và chữa chiếc răng sâu cho Sóc Bi, tặng Bi bàn chải mới.",
                ],
            },
        },
    ]


@app.get("/projects/{project_id}/characters")
async def list_project_characters(project_id: str):
    """Đọc danh sách hồ sơ nhân vật đầy đủ từ data/projects/<id>/characters/."""
    store = ProjectStore(project_id)
    studio_chars_file = store.characters_dir / "studio_characters.json"
    if studio_chars_file.exists():
        try:
            with open(studio_chars_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    chars = _default_studio_characters(project_id)
    store.characters_dir.mkdir(parents=True, exist_ok=True)
    with open(studio_chars_file, "w", encoding="utf-8") as f:
        json.dump(chars, f, indent=2, ensure_ascii=False)
    return chars


@app.post("/projects/{project_id}/characters")
async def save_project_character(project_id: str, character: Dict[str, Any] = Body(...)):
    """Lưu hoặc cập nhật hồ sơ nhân vật mở rộng vào data/projects/<id>/characters/."""
    store = ProjectStore(project_id)
    store.characters_dir.mkdir(parents=True, exist_ok=True)
    studio_chars_file = store.characters_dir / "studio_characters.json"
    chars = _default_studio_characters(project_id)
    if studio_chars_file.exists():
        try:
            with open(studio_chars_file, "r", encoding="utf-8") as f:
                chars = json.load(f)
        except Exception:
            pass

    char_id = character.get("id")
    if not char_id:
        raise HTTPException(status_code=400, detail="Missing character id")

    idx = next((i for i, c in enumerate(chars) if c.get("id") == char_id), -1)
    if idx >= 0:
        chars[idx] = character
    else:
        chars.append(character)

    with open(studio_chars_file, "w", encoding="utf-8") as f:
        json.dump(chars, f, indent=2, ensure_ascii=False)

    # Đồng bộ vào thư mục con của nhân vật
    char_subdir = store.characters_dir / char_id
    char_subdir.mkdir(parents=True, exist_ok=True)
    with open(char_subdir / "studio_profile.json", "w", encoding="utf-8") as f:
        json.dump(character, f, indent=2, ensure_ascii=False)

    return {"status": "saved", "character": character}


@app.delete("/projects/{project_id}/characters/{char_id}")
async def delete_project_character(project_id: str, char_id: str):
    store = ProjectStore(project_id)
    studio_chars_file = store.characters_dir / "studio_characters.json"
    if not studio_chars_file.exists():
        return {"status": "deleted", "id": char_id}
    with open(studio_chars_file, "r", encoding="utf-8") as f:
        chars = json.load(f)
    chars = [c for c in chars if c.get("id") != char_id]
    with open(studio_chars_file, "w", encoding="utf-8") as f:
        json.dump(chars, f, indent=2, ensure_ascii=False)
    return {"status": "deleted", "id": char_id}


@app.post("/projects/{project_id}/voice/preview")
async def preview_character_voice(project_id: str, payload: Dict[str, Any] = Body(...)):
    """Đọc thử một câu qua OmniVoice (hoặc MockProvider khi ở chế độ chạy thử)."""
    store = ProjectStore(project_id)
    text = str(payload.get("text", "Chào các bạn nhỏ, mình là Sóc Nhỏ Bi nè!"))
    voice_id = str(payload.get("voiceId", "soc-nho"))
    tempo = float(payload.get("tempo", 1.10))
    mock_mode = bool(payload.get("mockMode", True))

    provider = MockProvider(store)
    art = await provider.speak_voice(
        text=text,
        voice_id=voice_id,
        tempo=tempo,
        node_id="voice_preview",
        run_id="preview",
    )
    return {
        "status": "ok",
        "voiceId": voice_id,
        "tempo": tempo,
        "text": text,
        "mockMode": mock_mode,
        "audioUrl": "/demo/voice/soc-nho_sample.mp3" if voice_id == "soc-nho" else "/demo/voice/canh_01.mp3",
        "artifact": art.model_dump(by_alias=True),
    }


@app.post("/projects/{project_id}/voice/clone")
async def clone_character_voice(project_id: str, payload: Dict[str, Any] = Body(...)):
    """Nhân bản giọng nói thật cho nhân vật thuộc dự án cụ thể."""
    return await execute_voice_clone(payload, project_id=project_id)


@app.get("/projects/{project_id}/publishing")
async def get_project_publishing(project_id: str):
    """Đọc danh sách kênh và lịch đăng tuần của dự án."""
    store = ProjectStore(project_id)
    pub_dir = store.project_dir / "publishing"
    pub_dir.mkdir(parents=True, exist_ok=True)
    sched_file = pub_dir / "schedule.json"
    if sched_file.exists():
        try:
            with open(sched_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    default_pub = {
        "channels": [
            {
                "id": "chan_yt_1",
                "name": "Sóc Nhỏ TV Official",
                "platform": "youtube",
                "connected": True,
                "defaultHashtags": ["#SocNhoTV", "#HoatHinh3D", "#ThieuNhi"],
                "defaultPublishHours": "19:00",
                "requireManualApproval": True,
            },
            {
                "id": "chan_tt_1",
                "name": "@socnhotv.official",
                "platform": "tiktok",
                "connected": True,
                "defaultHashtags": ["#socnhotv", "#cartoon3d", "#learnontiktok"],
                "defaultPublishHours": "20:00",
                "requireManualApproval": True,
            },
        ],
        "posts": [
            {
                "id": "post_ep1_yt",
                "projectId": project_id,
                "episodeId": "ep_01_kham_rang",
                "title": "Tập 1: Sóc Nhỏ và Chiếc Răng Sâu (16:9)",
                "channelId": "chan_yt_1",
                "platform": "youtube",
                "scheduledDate": "2026-11-05",
                "scheduledTime": "19:00",
                "aspectRatio": "16:9",
                "status": "pending_approval",
                "videoUri": "content/episodes/soc-nho-sau-rang/soc_bi_kham_rang_16x9_long_tieng_nhe.mp4",
            },
            {
                "id": "post_ep1_tt",
                "projectId": project_id,
                "episodeId": "ep_01_kham_rang",
                "title": "Tập 1: Sóc Bi Đau Răng Vì Ăn Kẹo (Shorts 9:16)",
                "channelId": "chan_tt_1",
                "platform": "tiktok",
                "scheduledDate": "2026-11-05",
                "scheduledTime": "20:00",
                "aspectRatio": "9:16",
                "status": "draft",
                "videoUri": "content/episodes/soc-nho-sau-rang/scenes/canh_01.mp4",
            },
        ],
    }
    with open(sched_file, "w", encoding="utf-8") as f:
        json.dump(default_pub, f, indent=2, ensure_ascii=False)
    return default_pub


@app.post("/projects/{project_id}/publishing")
async def save_project_publishing(project_id: str, payload: Dict[str, Any] = Body(...)):
    store = ProjectStore(project_id)
    pub_dir = store.project_dir / "publishing"
    pub_dir.mkdir(parents=True, exist_ok=True)
    sched_file = pub_dir / "schedule.json"
    with open(sched_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return {"status": "saved"}


@app.post("/projects/{project_id}/chat")
async def studio_chat_command(project_id: str, payload: Dict[str, Any] = Body(...)):
    """Xử lý lệnh chat điều khiển Studio thông qua Provider.text_complete (hoặc trợ lý quy tắc ở chế độ thử)."""
    store = ProjectStore(project_id)
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Empty prompt")

    mock_mode = bool(payload.get("mockMode", True))
    vault = get_key_vault()
    if not mock_mode and vault.has_valid_key("gemini"):
        try:
            key = vault.require_key("gemini")
            provider = GoogleProvider(store, guard=SpendGuard(store.runs_dir), key=key)
            return await provider.text_complete(
                system="Bạn là trợ lý điều khiển AI Video Studio cho dự án Sóc Nhỏ TV.",
                prompt=prompt,
            )
        except (ProviderError, MissingApiKey) as pe:
            raise HTTPException(status_code=400, detail=redact_secrets(str(pe)))

    provider_mock = MockProvider(store)
    result = await provider_mock.text_complete(
        system="Bạn là trợ lý điều khiển AI Video Studio cho dự án Sóc Nhỏ TV.",
        prompt=prompt,
    )
    return result


@app.post("/projects/{project_id}/ai/script")
async def ai_script_alias(project_id: str, payload: Dict[str, Any] = Body(...)):
    """Viết nháp kịch bản từ ý tưởng (alias từ /data/projects/{project_id}/ai/script)."""
    from socnhotv.core.api.data_routes import ai_generate_script
    return await ai_generate_script(project_id, payload)


@app.post("/projects/{project_id}/library/upload")
async def upload_library_alias(project_id: str, payload: Dict[str, Any] = Body(...)):
    """Tải ảnh/video lên kho thư viện (alias từ /data/projects/{project_id}/library/upload)."""
    from socnhotv.core.api.data_routes import upload_library_file
    return await upload_library_file(project_id, payload)



@app.get("/settings/api-keys")
async def get_api_keys_status():
    """Trả về trạng thái khóa API theo từng nhà cung cấp (KHÔNG BAO GIỜ trả về khóa)."""
    vault = get_key_vault()
    return {"providers": vault.list_status()}


@app.post("/settings/api-keys")
async def set_api_key(payload: Dict[str, Any] = Body(...)):
    """Cập nhật hoặc kiểm tra khóa API trên máy chủ (KHÔNG BAO GIỜ trả lại khóa trong phản hồi)."""
    provider = str(payload.get("provider", "")).strip().lower()
    api_key = str(payload.get("apiKey", ""))
    verify_live = bool(payload.get("verifyLive", False))

    vault = get_key_vault()
    try:
        if verify_live and api_key.strip():
            await vault.verify_key_live(provider, api_key=api_key)
        status = vault.set_key(provider, api_key)
        if verify_live and status.get("configured"):
            status["verifiedLive"] = True
        return status
    except (MissingApiKey, ProviderError) as err:
        raise HTTPException(status_code=400, detail=redact_secrets(str(err)))


@app.post("/settings/api-keys/verify")
async def verify_api_key(payload: Dict[str, Any] = Body(...)):
    """Kiểm tra trực tiếp khóa API có hoạt động không (gọi endpoint miễn phí $0)."""
    provider = str(payload.get("provider", "")).strip().lower()
    api_key = str(payload.get("apiKey", ""))
    vault = get_key_vault()
    try:
        res = await vault.verify_key_live(provider, api_key=api_key if api_key else None)
        return {"provider": provider, "valid": True, "detail": res}
    except (MissingApiKey, ProviderError) as err:
        return JSONResponse(
            status_code=400,
            content={"provider": provider, "valid": False, "detail": redact_secrets(str(err))},
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"provider": provider, "valid": False, "detail": redact_secrets(str(e))},
        )


@app.get("/projects/{project_id}/files/{file_path:path}")
async def serve_project_file(project_id: str, file_path: str):
    """Phục vụ tệp artifact/media thật trong thư mục dự án (chống path traversal)."""
    store = ProjectStore(project_id)
    base_dir = store.project_dir.resolve()
    target = (base_dir / file_path).resolve()
    if not str(target).startswith(str(base_dir)) or not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(target)

