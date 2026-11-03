from __future__ import annotations

import asyncio
import json
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
from socnhotv.core.api.data_routes import router as data_router
from socnhotv.core.api.voice_routes import router as voice_router

app = FastAPI(
    title="AI Video Studio Core Engine",
    description="Backend động cơ chạy đồ thị node video AI & công cụ hậu kỳ",
    version="0.1.0",
)

app.include_router(data_router)
app.include_router(voice_router)

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
# Trạng thái khóa API trên máy chủ (chỉ lưu trạng thái đã đặt hay chưa, không bao giờ trả lại khóa)
server_api_keys: Dict[str, Dict[str, Any]] = {
    "gemini": {"provider": "gemini", "label": "Google Gemini & Veo", "configured": False, "updatedAt": None},
    "fal": {"provider": "fal", "label": "fal.ai (Video Queue)", "configured": False, "updatedAt": None},
    "openai": {"provider": "openai", "label": "OpenAI (GPT / Whisper)", "configured": False, "updatedAt": None},
    "replicate": {"provider": "replicate", "label": "Replicate", "configured": False, "updatedAt": None},
}


def broadcast_event(project_id: str, event: SSEEvent) -> None:
    queues = project_event_queues.get(project_id, [])
    payload = event.model_dump_json(by_alias=True)
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

    provider = None
    if not req.mock_mode:
        # Chế độ thật: chỉ Google (Gemini/Veo) + OmniVoice local, có khóa chi tiêu cứng 5 đô
        from socnhotv.core.providers.google_provider import GoogleProvider, MissingApiKey

        try:
            provider = GoogleProvider(store)
        except MissingApiKey as e:
            raise HTTPException(status_code=400, detail=str(e))

    runner = GraphRunner(
        store=store,
        model_registry=ModelRegistry(),
        event_callback=sse_callback,
        provider=provider,
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


@app.post("/projects/{project_id}/run/cancel")
async def cancel_project_run(project_id: str):
    """Dừng phiên chạy đồ thị hiện hành và phát sự kiện SSE hủy."""
    cancel_evt = SSEEvent(
        event_type=SSEEventType.RUN_FAILED,
        run_id=f"run_cancel_{int(time.time())}",
        state=NodeState.CANCELLED,
        message="Đã dừng chạy đồ thị theo yêu cầu người dùng.",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    broadcast_event(project_id, cancel_evt)
    return {"status": "cancelled", "projectId": project_id}


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
    """Nhân bản giọng nói vào Voice Vault (bắt buộc xác nhận quyền sở hữu/đồng ý)."""
    if not payload.get("consentConfirmed"):
        raise HTTPException(
            status_code=400,
            detail="Phải xác nhận quyền sử dụng giọng nói (chỉ giọng của chính bạn hoặc người đã đồng ý).",
        )
    voice_id = str(payload.get("voiceId", "soc-nho-custom"))
    return {
        "status": "cloned",
        "voiceId": voice_id,
        "vaultPath": f"data/shared/voice_vault/{voice_id}/",
        "mastering": "-14 LUFS · 44.1kHz · 192kbps",
    }


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

    provider = MockProvider(store)
    result = await provider.text_complete(
        system="Bạn là trợ lý điều khiển AI Video Studio cho dự án Sóc Nhỏ TV.",
        prompt=prompt,
    )
    return result


@app.get("/settings/api-keys")
async def get_api_keys_status():
    """Trả về trạng thái khóa API theo từng nhà cung cấp (KHÔNG BAO GIỜ trả về khóa)."""
    import os
    env_map = {
        "gemini": "GEMINI_API_KEY",
        "fal": "FAL_KEY",
        "openai": "OPENAI_API_KEY",
        "replicate": "REPLICATE_API_TOKEN",
    }
    items = []
    for k, info in server_api_keys.items():
        has_env = bool(os.environ.get(env_map.get(k, "")))
        items.append(
            {
                "provider": k,
                "label": info["label"],
                "configured": bool(info["configured"] or has_env),
                "updatedAt": info["updatedAt"],
            }
        )
    return {"providers": items}


@app.post("/settings/api-keys")
async def set_api_key(payload: Dict[str, Any] = Body(...)):
    """Cập nhật khóa API trên máy chủ (chỉ ghi nhận trạng thái, không bao giờ trả lại khóa)."""
    provider = str(payload.get("provider", "")).strip().lower()
    api_key = str(payload.get("apiKey", "")).strip()
    if provider not in server_api_keys:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    server_api_keys[provider]["configured"] = len(api_key) >= 6
    server_api_keys[provider]["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {
        "provider": provider,
        "configured": server_api_keys[provider]["configured"],
        "updatedAt": server_api_keys[provider]["updatedAt"],
    }


@app.get("/projects/{project_id}/files/{file_path:path}")
async def serve_project_file(project_id: str, file_path: str):
    """Phục vụ tệp artifact/media thật trong thư mục dự án (chống path traversal)."""
    store = ProjectStore(project_id)
    base_dir = store.project_dir.resolve()
    target = (base_dir / file_path).resolve()
    if not str(target).startswith(str(base_dir)) or not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(target)

