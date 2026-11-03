from __future__ import annotations

import asyncio
import inspect
import json as _json
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from socnhotv.core.adapters.caption_adapter import CaptionAdapter
from socnhotv.core.adapters.hyperframes_adapter import HyperFramesAdapter
from socnhotv.core.adapters.voice_adapter import VoiceAdapter
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
    NodeCostEstimate,
    NodeInstance,
    NodeState,
    PortType,
    RunMode,
    SSEEvent,
    SSEEventType,
)
from socnhotv.core.engine.validator import validate_graph
from socnhotv.core.models_registry.registry import ModelRegistry
from socnhotv.core.nodes.registry import NodeRegistry
from socnhotv.core.providers.errors import ProviderError, redact_secrets
from socnhotv.core.providers.key_vault import KeyVault
from socnhotv.core.providers.mock_provider import MockProvider
from socnhotv.core.providers.router import resolve_provider_for_model
from socnhotv.core.providers.spend_guard import SpendGuard
from socnhotv.core.storage.project_store import ProjectStore


class BudgetExceededError(Exception):
    """Ngoại lệ khi chi phí ước tính vượt quá trần ngân sách cho phép."""
    pass


class GraphExecutionError(Exception):
    """Lỗi khi thực thi đồ thị node."""
    pass


def _extract_uris(val: Any) -> List[str]:
    """Trích xuất danh sách đường dẫn tương đối (URI) từ Artifact hoặc danh sách Artifact/str."""
    if not val:
        return []
    if isinstance(val, Artifact):
        return [val.uri]
    if isinstance(val, str):
        return [val]
    if isinstance(val, list):
        out: List[str] = []
        for item in val:
            if isinstance(item, Artifact):
                out.append(item.uri)
            elif isinstance(item, str) and item:
                out.append(item)
        return out
    return []


def _filter_kwargs(fn: Any, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Chỉ truyền các tham số mà hàm provider hỗ trợ (hoặc truyền hết nếu có **kwargs)."""
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return kwargs
    for p in sig.parameters.values():
        if p.kind == inspect.Parameter.VAR_KEYWORD:
            return kwargs
    return {k: v for k, v in kwargs.items() if k in sig.parameters}


class GraphRunner:
    """Bộ chạy đồ thị node (Execution Engine):
    - Kiểm tra tính hợp lệ đồ thị (DAG, không vòng lặp, tương thích cổng).
    - Hỗ trợ 4 chế độ chạy: ALL, FORCE_ALL, SINGLE_NODE, DOWNSTREAM.
    - Lập kế hoạch & ước tính chi phí chi tiết trước khi chạy (plan_execution).
    - Kiểm tra trần chi phí (spending limit) trước khi chạy.
    - Xử lý lỗi từng cảnh / từng node độc lập (Fault Isolation).
    - Tự động thử lại có lùi thời gian cho lỗi tạm thời, dừng ngay với lỗi xác thực/chặn nội dung/sai tham số.
    - Cập nhật Generation, Ghim kết quả và đánh dấu Stale chuẩn hợp đồng.
    - Phát sự kiện SSE thời gian thực (đã che khóa API) và ghi sổ chi phí (Cost Ledger).
    """

    def __init__(
        self,
        store: ProjectStore,
        model_registry: Optional[ModelRegistry] = None,
        provider: Optional[Any] = None,
        event_callback: Optional[Callable[[SSEEvent], None]] = None,
        cancel_event: Optional[asyncio.Event] = None,
    ):
        self.store = store
        self.model_registry = model_registry or ModelRegistry()
        self.provider = provider or MockProvider(store)
        self.event_callback = event_callback
        self.cancel_event = cancel_event

    def _emit_event(self, event: SSEEvent) -> None:
        if event.message:
            event.message = redact_secrets(event.message)
        if self.event_callback:
            try:
                self.event_callback(event)
            except Exception:
                pass

    def _find_descendants(self, graph: Graph, start_node_id: str) -> Set[str]:
        """Tìm toàn bộ các node con, cháu (hậu duệ) đi ra từ một node."""
        descendants: Set[str] = set()
        queue = [start_node_id]

        outgoing: Dict[str, List[str]] = {}
        for edge in graph.edges:
            outgoing.setdefault(edge.source_node_id, []).append(edge.target_node_id)
        for node in graph.nodes:
            for _, val in node.inputs.items():
                if isinstance(val, dict) and "nodeId" in val:
                    outgoing.setdefault(val["nodeId"], []).append(node.id)

        while queue:
            current = queue.pop(0)
            for child in outgoing.get(current, []):
                if child not in descendants:
                    descendants.add(child)
                    queue.append(child)

        return descendants

    def _find_direct_children(self, graph: Graph, node_id: str) -> Set[str]:
        """Tìm các node con trực tiếp của một node."""
        children: Set[str] = set()
        for edge in graph.edges:
            if edge.source_node_id == node_id:
                children.add(edge.target_node_id)
        for n in graph.nodes:
            for _, val in n.inputs.items():
                if isinstance(val, dict) and val.get("nodeId") == node_id:
                    children.add(n.id)
        return children

    def _find_direct_parents(self, graph: Graph, node_id: str) -> Set[str]:
        """Tìm các node cha trực tiếp mà node_id phụ thuộc vào."""
        parents: Set[str] = set()
        for edge in graph.edges:
            if edge.target_node_id == node_id:
                parents.add(edge.source_node_id)
        target_node = next((n for n in graph.nodes if n.id == node_id), None)
        if target_node:
            for _, val in target_node.inputs.items():
                if isinstance(val, dict) and "nodeId" in val:
                    parents.add(val["nodeId"])
        return parents

    def _effective_model_for_node(self, node: NodeInstance, real_mode: bool = False) -> Tuple[str, str]:
        """Xác định (model_key, provider) thực tế sẽ dùng cho một node."""
        raw_model = str(node.params.get("model", "")).strip()

        if node.type in ("image_gen", "image_edit"):
            if not raw_model or (real_mode and raw_model.startswith("mock")):
                model_key = "gemini-2.5-flash-image" if real_mode else (raw_model or "mock-image")
            else:
                model_key = raw_model
            prov = resolve_provider_for_model(model_key, default_provider="google" if real_mode else "mock")
            return model_key, prov

        if node.type == "video_gen":
            if not raw_model or (real_mode and raw_model.startswith("mock")):
                model_key = "google-veo-2" if real_mode else (raw_model or "mock-video")
            else:
                model_key = raw_model
            prov = resolve_provider_for_model(model_key, default_provider="google" if real_mode else "mock")
            return model_key, prov

        if node.type == "voice_tts":
            model_key = raw_model or ("local-omnivoice" if real_mode else "mock-voice")
            return model_key, "local_tool" if real_mode else "mock"

        if node.type in ("vision_analyze", "quality_check", "script"):
            if real_mode and raw_model and not raw_model.startswith("mock"):
                return raw_model, resolve_provider_for_model(raw_model, default_provider="google")
            if real_mode and node.type in ("vision_analyze", "quality_check"):
                return "gemini-2.5-flash", "google"
            return raw_model or "local", "local"

        return raw_model or "local", "local_tool"

    def estimate_node_cost(self, node: NodeInstance, real_mode: bool = False) -> float:
        """Ước tính chi phí USD cho một node dựa trên sổ model."""
        node_def = NodeRegistry.get(node.type)
        if not node_def:
            return 0.0

        model_id, _ = self._effective_model_for_node(node, real_mode=real_mode)

        if node.type in ("image_gen", "image_edit"):
            n = int(node.params.get("n", 1))
            return self.model_registry.estimate_cost(model_id, num_images=n)
        if node.type == "video_gen":
            duration = float(node.params.get("durationSec", 8.0))
            return self.model_registry.estimate_cost(model_id, duration_sec=duration)
        if node.type == "voice_tts":
            text = str(node.params.get("text", ""))
            return self.model_registry.estimate_cost(model_id, text_length=len(text))
        if real_mode and node.type in ("vision_analyze", "quality_check"):
            return self.model_registry.estimate_cost(model_id, num_images=1)

        return 0.0

    def estimate_graph_cost(
        self,
        graph: Graph,
        node_ids_to_run: List[str],
        real_mode: bool = False,
    ) -> float:
        """Tính tổng chi phí USD ước tính của toàn bộ các node sẽ chạy."""
        total = 0.0
        node_map = {n.id: n for n in graph.nodes}
        for nid in node_ids_to_run:
            if nid in node_map:
                total += self.estimate_node_cost(node_map[nid], real_mode=real_mode)
        return round(total, 6)

    def select_nodes_to_execute(self, graph: Graph, topo_order: List[str], req: GraphRunRequest) -> List[str]:
        """Xác định chính xác những node sẽ thực sự chạy theo RunMode và quy tắc Mục 11."""
        node_map = {n.id: n for n in graph.nodes}
        if req.mode == RunMode.FORCE_ALL:
            return list(topo_order)
        if req.mode == RunMode.SINGLE_NODE:
            if not req.target_node_id or req.target_node_id not in node_map:
                raise GraphExecutionError(f"Target node '{req.target_node_id}' không tồn tại trong đồ thị.")
            return [req.target_node_id]
        if req.mode == RunMode.DOWNSTREAM:
            if not req.target_node_id or req.target_node_id not in node_map:
                raise GraphExecutionError(f"Target node '{req.target_node_id}' không tồn tại trong đồ thị.")
            descendants = self._find_descendants(graph, req.target_node_id)
            descendants.add(req.target_node_id)
            return [nid for nid in topo_order if nid in descendants]

        # RunMode.ALL: bỏ qua node đã có generation được ghim hợp lệ & không bị stale
        selected: List[str] = []
        for nid in topo_order:
            n = node_map[nid]
            has_valid_pin = bool(
                n.pinned_generation_id and any(g.id == n.pinned_generation_id for g in n.generations)
            )
            if n.state != NodeState.COMPLETED or n.is_stale or not has_valid_pin:
                selected.append(nid)
        return selected

    def plan_execution(
        self,
        graph: Graph,
        req: GraphRunRequest,
        vault: Optional[KeyVault] = None,
        guard: Optional[SpendGuard] = None,
    ) -> GraphCostEstimateResponse:
        """Lập bảng ước tính chi phí, trạng thái trần chi tiêu và kiểm tra khóa API trước khi chạy."""
        validation = validate_graph(graph)
        if not validation.is_valid:
            raise GraphExecutionError("Đồ thị không hợp lệ: " + "; ".join(validation.errors))

        topo = validation.topological_order
        to_run = self.select_nodes_to_execute(graph, topo, req)
        skipped = [nid for nid in topo if nid not in to_run]
        node_map = {n.id: n for n in graph.nodes}

        real_mode = not req.mock_mode
        kv = vault or KeyVault(persist_local=False)
        sg = guard or SpendGuard(self.store.runs_dir)

        estimates: List[NodeCostEstimate] = []
        missing_providers: Set[str] = set()
        total_real_cost = 0.0

        for nid in to_run:
            node = node_map[nid]
            if req.mock_mode:
                model_key, _ = self._effective_model_for_node(node, real_mode=False)
                estimates.append(
                    NodeCostEstimate(
                        node_id=nid,
                        node_type=node.type,
                        model=model_key,
                        provider="mock",
                        estimated_cost_usd=0.0,
                    )
                )
            else:
                model_key, prov = self._effective_model_for_node(node, real_mode=True)
                cost = self.estimate_node_cost(node, real_mode=True)
                total_real_cost += cost
                estimates.append(
                    NodeCostEstimate(
                        node_id=nid,
                        node_type=node.type,
                        model=model_key,
                        provider=prov,
                        estimated_cost_usd=cost,
                    )
                )
                if prov in ("google", "gemini") and not kv.has_valid_key("gemini"):
                    missing_providers.add("gemini")
                elif prov == "fal" and not kv.has_valid_key("fal"):
                    missing_providers.add("fal")
                elif prov == "replicate" and not kv.has_valid_key("replicate"):
                    missing_providers.add("replicate")

        total_real_cost = round(total_real_cost, 4)
        spend_status = sg.preview(total_real_cost, source=req.source)
        if req.spending_limit_usd is not None and total_real_cost > req.spending_limit_usd + 1e-9:
            spend_status["canProceed"] = False
            spend_status["reason"] = (
                f"Chi phí ước tính ${total_real_cost:.4f} vượt trần mỗi lần chạy ${req.spending_limit_usd:.4f}."
            )

        return GraphCostEstimateResponse(
            project_id=req.project_id,
            mode=req.mode,
            mock_mode=req.mock_mode,
            nodes_to_execute=estimates,
            skipped_nodes=skipped,
            total_estimated_cost_usd=total_real_cost,
            requires_confirmation=bool(real_mode and total_real_cost > 0),
            missing_api_keys=sorted(missing_providers),
            spend_status=spend_status,
        )

    def _gather_node_inputs(
        self,
        node: NodeInstance,
        graph: Graph,
        node_outputs: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Thu thập dữ liệu đầu vào cho node từ params, inputs và kết quả các node cha."""
        resolved: Dict[str, Any] = dict(node.params)

        for edge in graph.edges:
            if edge.target_node_id == node.id:
                src_out = node_outputs.get(edge.source_node_id, {})
                if edge.source_port in src_out:
                    val = src_out[edge.source_port]
                    tgt_def = NodeRegistry.get(node.type)
                    if tgt_def:
                        tgt_port_def = next((p for p in tgt_def.input_ports if p.name == edge.target_port), None)
                        if tgt_port_def and tgt_port_def.port_type == PortType.IMAGE_LIST and not isinstance(val, list):
                            val = [val]
                    resolved[edge.target_port] = val

        for port_name, in_ref in node.inputs.items():
            if isinstance(in_ref, dict) and "nodeId" in in_ref:
                src_id = in_ref["nodeId"]
                src_port = in_ref.get("outputPort", "")
                src_out = node_outputs.get(src_id, {})
                if src_port in src_out:
                    resolved[port_name] = src_out[src_port]
            elif in_ref is not None and port_name not in resolved:
                resolved[port_name] = in_ref

        return resolved

    def _is_real_provider(self) -> bool:
        pname_fn = getattr(self.provider, "provider_name", None)
        if callable(pname_fn):
            return pname_fn() != "mock"
        return False

    async def _execute_node_handler(
        self,
        node: NodeInstance,
        resolved_inputs: Dict[str, Any],
        run_id: str,
        is_mock: bool = True,
    ) -> Tuple[Dict[str, Any], Optional[Artifact], float]:
        """Thực thi logic sinh sản phẩm của một Node cụ thể."""
        outputs: Dict[str, Any] = {}
        primary_artifact: Optional[Artifact] = None
        cost_usd = 0.0 if is_mock else self.estimate_node_cost(node, real_mode=True)

        node_type = node.type

        if node_type == "text":
            content = str(resolved_inputs.get("content", ""))
            outputs["text"] = content
            provenance = ArtifactProvenance(
                node_id=node.id,
                run_id=run_id,
                provider="local",
                model="text",
                params={"content": content},
                cost_usd=0.0,
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            primary_artifact = self.store.store_bytes(
                data=content.encode("utf-8"),
                ext="txt",
                kind=ArtifactKind.TEXT,
                provenance=provenance,
            )
            outputs["artifact"] = primary_artifact

        elif node_type == "character":
            char_id = str(resolved_inputs.get("characterId", "soc_nho"))
            char_info = {
                "characterId": char_id,
                "name": "Sóc Nhỏ (Bi)" if char_id == "soc_nho" else char_id,
                "scaleLock": "100cm",
                "defaultVoice": "soc-nho",
            }
            outputs["character"] = char_info
            # Nếu có sẵn ảnh DNA nhân vật trong thư mục dự án, nạp trực tiếp không tốn phí gọi API!
            char_dir = self.store.characters_dir / char_id
            local_pngs = sorted(char_dir.glob("*.png")) if char_dir.exists() else []
            if local_pngs and not is_mock:
                ref_arts: List[Artifact] = []
                for p in local_pngs[:4]:
                    prov = ArtifactProvenance(
                        node_id=node.id,
                        run_id=run_id,
                        provider="local",
                        model="master_dna",
                        params={"characterId": char_id, "file": p.name},
                        cost_usd=0.0,
                        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    )
                    ref_arts.append(
                        self.store.store_bytes(
                            data=p.read_bytes(),
                            ext=p.suffix.lstrip(".") or "png",
                            kind=ArtifactKind.IMAGE,
                            provenance=prov,
                        )
                    )
            else:
                ref_arts = await MockProvider(self.store).generate_images(
                    prompt=f"Master DNA character panel for {char_id}",
                    node_id=node.id,
                    run_id=run_id,
                    n=2,
                )
            outputs["reference_images"] = ref_arts
            primary_artifact = ref_arts[0] if ref_arts else None
            cost_usd = 0.0

        elif node_type == "image":
            uri = str(resolved_inputs.get("uri", ""))
            local_cand = (self.store.project_dir / uri.lstrip("/")) if uri else None
            if local_cand and local_cand.exists() and local_cand.is_file():
                prov = ArtifactProvenance(
                    node_id=node.id,
                    run_id=run_id,
                    provider="local",
                    model="upload",
                    params={"uri": uri},
                    cost_usd=0.0,
                    created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
                primary_artifact = self.store.store_bytes(
                    data=local_cand.read_bytes(),
                    ext=local_cand.suffix.lstrip(".") or "png",
                    kind=ArtifactKind.IMAGE,
                    provenance=prov,
                )
            else:
                arts = await MockProvider(self.store).generate_images(
                    prompt=f"Uploaded image reference: {uri or 'default image'}",
                    node_id=node.id,
                    run_id=run_id,
                    n=1,
                )
                primary_artifact = arts[0]
            outputs["image"] = primary_artifact

        elif node_type == "script":
            text_in = str(resolved_inputs.get("text", "Sóc Nhỏ và Chiếc Răng Sâu"))
            target_count = int(resolved_inputs.get("targetSceneCount", 6))
            scenes: List[Dict[str, Any]] = []
            prov_name = "mock"
            model_used = "script-planner-v1"
            actual_script_cost = 0.0

            if not is_mock and self._is_real_provider() and hasattr(self.provider, "text_complete"):
                schema = {
                    "type": "OBJECT",
                    "properties": {
                        "scenes": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "sceneNumber": {"type": "INTEGER"},
                                    "title": {"type": "STRING"},
                                    "imagePrompt": {"type": "STRING"},
                                    "videoPrompt": {"type": "STRING"},
                                    "dialogue": {"type": "STRING"},
                                    "durationSec": {"type": "NUMBER"},
                                },
                                "required": ["sceneNumber", "imagePrompt", "videoPrompt", "dialogue", "durationSec"],
                            },
                        }
                    },
                    "required": ["scenes"],
                }
                tc_res = await self.provider.text_complete(
                    system=(
                        "Bạn là biên kịch hoạt hình 3D Sóc Nhỏ TV. Hãy tách cốt truyện thành danh sách cảnh "
                        "(tuân thủ tỉ lệ Sóc Nhỏ Bi 100cm, Koala 150cm)."
                    ),
                    prompt=f"Tách thành {target_count} cảnh JSON cho ý tưởng: {text_in}",
                    schema=schema,
                )
                if isinstance(tc_res.get("scenes"), list) and tc_res["scenes"]:
                    scenes = tc_res["scenes"]
                    prov_name = str(tc_res.get("provider", "google"))
                    model_used = str(tc_res.get("model", "gemini-2.5-flash"))
                    actual_script_cost = float(tc_res.get("costUsd", 0.0))

            if not scenes:
                scenes = [
                    {
                        "sceneNumber": 1,
                        "title": "Cảnh 1: Kệ kẹo nhà cây",
                        "imagePrompt": "Sóc Bi ở nhà cây, kệ đầy hũ kẹo, mắt sáng rực, 3D Pixar 100cm",
                        "videoPrompt": "Camera dolly chậm vào Sóc Bi đang nhảy lên vui sướng",
                        "dialogue": "Oa, nhiều kẹo quá! Hôm nay Bi sẽ ăn thật nhiều luôn!",
                        "durationSec": 7.0,
                    },
                    {
                        "sceneNumber": 2,
                        "title": "Cảnh 2: Quên đánh răng",
                        "imagePrompt": "Bi ăn kẹo liên tục trên sàn gỗ nhà cây, vỏ kẹo chất đống rồi ngủ quên",
                        "videoPrompt": "Camera pan nhẹ qua đống vỏ kẹo, Bi ngáp ngủ",
                        "dialogue": "Bi ăn kẹo cả ngày, tối đến lại quên đánh răng rồi đi ngủ.",
                        "durationSec": 8.0,
                    },
                    {
                        "sceneNumber": 3,
                        "title": "Cảnh 3: Sáng dậy đau răng",
                        "imagePrompt": "Bi ôm má nhăn mặt vì đau răng trong nắng sớm nhà cây",
                        "videoPrompt": "Camera push-in cận mặt Bi ôm má mếu máo",
                        "dialogue": "Ôi đau quá! Sáng nay răng của Bi đau lắm!",
                        "durationSec": 7.0,
                    },
                    {
                        "sceneNumber": 4,
                        "title": "Cảnh 4: Khám Bác sĩ Koala",
                        "imagePrompt": "Bác sĩ Koala (150cm) khám răng cho Sóc Bi (100cm) tại phòng khám rừng xanh",
                        "videoPrompt": "Bác sĩ Koala cầm gương nha khoa soi nhẹ nhàng và gật đầu",
                        "dialogue": "Bác sĩ Koala bảo Bi bị sâu răng vì ăn quá nhiều kẹo ngọt.",
                        "durationSec": 8.0,
                    },
                    {
                        "sceneNumber": 5,
                        "title": "Cảnh 5: Học chải răng đúng cách",
                        "imagePrompt": "Bác sĩ Koala cầm bàn chải lớn hướng dẫn Sóc Bi đánh răng xoay tròn",
                        "videoPrompt": "Bi làm theo bác sĩ Koala, cả hai cùng mỉm cười",
                        "dialogue": "Bác sĩ dạy Bi đánh răng sáng tối, ăn ít kẹo, uống nhiều nước.",
                        "durationSec": 8.0,
                    },
                    {
                        "sceneNumber": 6,
                        "title": "Cảnh 6: Răng trắng sáng bóng",
                        "imagePrompt": "Sóc Bi cười tươi răng trắng sáng trước cửa nhà cây, kệ đầy táo và cà rốt",
                        "videoPrompt": "Camera pull-back chậm, Bi vẫy tay chào khán giả",
                        "dialogue": "Cảm ơn bác sĩ! Từ nay Bi sẽ chăm sóc răng thật tốt!",
                        "durationSec": 7.0,
                    },
                ]

            outputs["scenes"] = scenes
            outputs["prompt"] = scenes[0].get("imagePrompt", "")
            outputs["dialogue"] = scenes[0].get("dialogue", "")
            cost_usd = actual_script_cost
            provenance = ArtifactProvenance(
                node_id=node.id,
                run_id=run_id,
                provider=prov_name,
                model=model_used,
                params={"targetSceneCount": len(scenes), "sourceText": text_in[:120]},
                cost_usd=actual_script_cost,
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            primary_artifact = self.store.store_bytes(
                data=_json.dumps({"title": text_in, "scenes": scenes}, ensure_ascii=False, indent=2).encode("utf-8"),
                ext="json",
                kind=ArtifactKind.TEXT,
                provenance=provenance,
            )
            outputs["artifact"] = primary_artifact

        elif node_type == "image_gen":
            prompt = str(resolved_inputs.get("prompt", "Sóc Nhỏ Bi đang khám phá khu rừng diệu kỳ"))
            aspect = str(resolved_inputs.get("aspectRatio", "9:16"))
            resolution = str(resolved_inputs.get("resolution", "1080p"))
            n = int(resolved_inputs.get("n", 1))
            seed = resolved_inputs.get("seed")
            refs = _extract_uris(resolved_inputs.get("references"))
            model_param = resolved_inputs.get("model")

            gen_fn = self.provider.generate_images
            call_args = _filter_kwargs(
                gen_fn,
                {
                    "prompt": prompt,
                    "references": refs or None,
                    "aspect_ratio": aspect,
                    "resolution": resolution,
                    "n": n,
                    "seed": int(seed) if seed is not None else None,
                    "node_id": node.id,
                    "run_id": run_id,
                    "model": model_param,
                },
            )
            arts = await gen_fn(**call_args)
            outputs["images"] = arts
            outputs["image"] = arts[0] if arts else None
            primary_artifact = arts[0] if arts else None
            if arts:
                cost_usd = round(sum(a.provenance.cost_usd for a in arts), 6)

        elif node_type == "image_edit":
            img_in = resolved_inputs.get("image")
            img_uri = img_in.uri if isinstance(img_in, Artifact) else str(img_in or "")
            prompt = str(resolved_inputs.get("prompt", "Chỉnh sửa ảnh sắc nét, giữ nguyên nhận diện nhân vật"))
            aspect = str(resolved_inputs.get("aspectRatio", "9:16"))
            refs = _extract_uris(resolved_inputs.get("references"))
            model_param = resolved_inputs.get("model")

            if hasattr(self.provider, "edit_image"):
                edit_fn = self.provider.edit_image
                art = await edit_fn(
                    **_filter_kwargs(
                        edit_fn,
                        {
                            "image_uri": img_uri,
                            "prompt": prompt,
                            "references": refs or None,
                            "aspect_ratio": aspect,
                            "node_id": node.id,
                            "run_id": run_id,
                            "model": model_param,
                        },
                    )
                )
            else:
                gen_fn = self.provider.generate_images
                arts = await gen_fn(
                    **_filter_kwargs(
                        gen_fn,
                        {
                            "prompt": prompt,
                            "references": ([img_uri] if img_uri else []) + refs,
                            "aspect_ratio": aspect,
                            "n": 1,
                            "node_id": node.id,
                            "run_id": run_id,
                        },
                    )
                )
                art = arts[0]
            outputs["image"] = art
            primary_artifact = art
            cost_usd = art.provenance.cost_usd

        elif node_type == "video_gen":
            prompt = str(resolved_inputs.get("prompt", "Camera dolly zoom theo bước chân Sóc Nhỏ Bi"))
            aspect = str(resolved_inputs.get("aspectRatio", "9:16"))
            duration = float(resolved_inputs.get("durationSec", 8.0))
            has_audio = bool(resolved_inputs.get("hasAudio", False))
            model_param = resolved_inputs.get("model")
            first_frame_art = resolved_inputs.get("first_frame") or resolved_inputs.get("image")
            first_frame_uri = (
                first_frame_art.uri
                if isinstance(first_frame_art, Artifact)
                else (str(first_frame_art) if first_frame_art else None)
            )
            refs = _extract_uris(resolved_inputs.get("references"))

            vid_fn = self.provider.generate_video
            call_args = _filter_kwargs(
                vid_fn,
                {
                    "prompt": prompt,
                    "first_frame_uri": first_frame_uri,
                    "duration_sec": duration,
                    "aspect_ratio": aspect,
                    "has_audio": has_audio,
                    "node_id": node.id,
                    "run_id": run_id,
                    "references": refs or None,
                    "model": model_param,
                    "cancel_event": self.cancel_event,
                },
            )
            art = await vid_fn(**call_args)
            outputs["video"] = art
            primary_artifact = art
            cost_usd = art.provenance.cost_usd

        elif node_type == "voice_tts":
            text = str(resolved_inputs.get("text", "Chào các bạn, mình là Sóc Nhỏ Bi nè!"))
            char_obj = resolved_inputs.get("character")
            default_vid = (
                char_obj.get("defaultVoice", "soc-nho")
                if isinstance(char_obj, dict)
                else "soc-nho"
            )
            voice_id = str(resolved_inputs.get("voiceId") or default_vid)
            tempo = float(resolved_inputs.get("tempo", 1.10))

            if not is_mock:
                voice_adapter = VoiceAdapter(self.store)
                art = await voice_adapter.synthesize(
                    text=text,
                    voice_id=voice_id,
                    tempo=tempo,
                    node_id=node.id,
                    run_id=run_id,
                )
            else:
                art = await self.provider.speak_voice(
                    text=text,
                    voice_id=voice_id,
                    tempo=tempo,
                    node_id=node.id,
                    run_id=run_id,
                )
            outputs["audio"] = art
            primary_artifact = art
            cost_usd = art.provenance.cost_usd

        elif node_type == "captions":
            audio_art = resolved_inputs.get("audio")
            if not is_mock and audio_art:
                caption_adapter = CaptionAdapter(self.store)
                art = await caption_adapter.generate_captions(
                    audio_source=audio_art,
                    node_id=node.id,
                    run_id=run_id,
                )
            else:
                sub_text = "00:00:00,000 --> 00:00:04,000\nChào các bạn, mình là Sóc Nhỏ Bi nè!\n"
                prov = ArtifactProvenance(
                    node_id=node.id,
                    run_id=run_id,
                    provider="mock-whisper",
                    model="whisper-large-v3",
                    params={},
                    input_hashes=[audio_art.hash] if isinstance(audio_art, Artifact) else [],
                    cost_usd=0.0,
                    created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
                art = self.store.store_bytes(
                    data=sub_text.encode("utf-8"),
                    ext="srt",
                    kind=ArtifactKind.CAPTIONS,
                    provenance=prov,
                )
            outputs["captions"] = art
            primary_artifact = art
            cost_usd = 0.0

        elif node_type in ("hyperframes_render", "export"):
            if not is_mock:
                hf_adapter = HyperFramesAdapter(self.store)
                scenes = resolved_inputs.get("scenes") or []
                if not scenes:
                    media_input = (
                        resolved_inputs.get("video")
                        or resolved_inputs.get("image")
                        or resolved_inputs.get("first_frame")
                    )
                    media_path = ""
                    if isinstance(media_input, Artifact):
                        media_path = str(self.store.project_dir / media_input.uri)
                    elif isinstance(media_input, str):
                        media_path = media_input

                    scenes = [{
                        "sceneNumber": 1,
                        "video": media_path if media_path.endswith((".mp4", ".mov", ".webm")) else None,
                        "image": media_path if not media_path.endswith((".mp4", ".mov", ".webm")) else None,
                        "durationSec": 6.0,
                        "dialogue": "Sóc Nhỏ Bi TV",
                    }]

                voice_art = resolved_inputs.get("audio") or resolved_inputs.get("voice")
                if not isinstance(voice_art, Artifact):
                    voice_art = None

                cap_art = resolved_inputs.get("captions")
                if not isinstance(cap_art, Artifact):
                    cap_art = None

                art = await hf_adapter.render_from_artifacts(
                    scenes=scenes,
                    voice_artifact=voice_art,
                    captions_artifact=cap_art,
                    title_badge=node.params.get("titleBadge", "SÓC NHỎ TV • TẬP MỚI"),
                    node_id=node.id,
                    run_id=run_id,
                )
            else:
                vid_fn = self.provider.generate_video
                art = await vid_fn(
                    **_filter_kwargs(
                        vid_fn,
                        {
                            "prompt": "Final rendered video composition 9:16",
                            "duration_sec": 12.0,
                            "aspect_ratio": "9:16",
                            "has_audio": True,
                            "node_id": node.id,
                            "run_id": run_id,
                        },
                    )
                )
            outputs["video"] = art
            outputs["manifest"] = art
            primary_artifact = art
            cost_usd = 0.0

        elif node_type == "quality_check":
            media_in = resolved_inputs.get("media")
            criteria = str(
                resolved_inputs.get(
                    "criteria",
                    node.params.get("criteria", "Chuẩn nhận diện DNA Sóc Nhỏ 100cm, áo vàng, quần đen"),
                )
            )
            threshold = float(node.params.get("thresholdScore", 0.85))
            passed = True
            score = 0.98
            report_text = f"ĐẠT · 9.8/10 — Khớp tiêu chí: {criteria}"

            if not is_mock and isinstance(media_in, Artifact) and self._is_real_provider():
                vis_fn = self.provider.analyze_vision
                vis_res = await vis_fn(
                    **_filter_kwargs(
                        vis_fn,
                        {
                            "media_uri": media_in.uri,
                            "prompt": f"Chấm điểm media theo tiêu chí: {criteria}. Trả JSON pass, score (0..1), feedback.",
                            "node_id": node.id,
                            "run_id": run_id,
                            "schema": {
                                "type": "OBJECT",
                                "properties": {
                                    "pass": {"type": "BOOLEAN"},
                                    "score": {"type": "NUMBER"},
                                    "confidence": {"type": "NUMBER"},
                                    "feedback": {"type": "STRING"},
                                },
                                "required": ["pass", "score", "feedback"],
                            },
                        },
                    )
                )
                score = float(vis_res.get("score", 0.9))
                passed = bool(vis_res.get("pass", score >= threshold)) and score >= threshold
                fb = str(vis_res.get("feedback") or vis_res.get("text") or criteria)
                report_text = f"{'ĐẠT' if passed else 'KHÔNG ĐẠT'} · {score:.2f} — {fb}"
                cost_usd = float(vis_res.get("costUsd", 0.01))

            outputs["pass"] = passed
            outputs["score"] = score
            outputs["feedback"] = report_text
            outputs["pass_fail"] = report_text
            if isinstance(media_in, Artifact):
                outputs["media"] = media_in
                primary_artifact = media_in
            else:
                gen_fn = self.provider.generate_images
                arts = await gen_fn(
                    **_filter_kwargs(
                        gen_fn,
                        {
                            "prompt": f"Quality checked frame: {criteria}",
                            "node_id": node.id,
                            "run_id": run_id,
                            "n": 1,
                        },
                    )
                )
                primary_artifact = arts[0] if arts else None
                outputs["media"] = primary_artifact

        elif node_type == "vision_analyze":
            media_obj = resolved_inputs.get("video") or resolved_inputs.get("image")
            media_uri = media_obj.uri if isinstance(media_obj, Artifact) else str(media_obj or "")
            vis_fn = self.provider.analyze_vision
            res = await vis_fn(
                **_filter_kwargs(
                    vis_fn,
                    {
                        "media_uri": media_uri,
                        "prompt": "Phân tích bố cục, góc quay, nhịp cảnh và lời thoại",
                        "node_id": node.id,
                        "run_id": run_id,
                    },
                )
            )
            outputs["scenes"] = res.get("scenes", [])
            outputs["script"] = res.get("text", res.get("overview", ""))
            outputs["overview"] = res.get("overview", res.get("text", ""))
            cost_usd = float(res.get("costUsd", 0.0))

        else:
            gen_fn = self.provider.generate_images
            arts = await gen_fn(
                **_filter_kwargs(
                    gen_fn,
                    {
                        "prompt": f"Generic execution for {node.type}",
                        "node_id": node.id,
                        "run_id": run_id,
                    },
                )
            )
            primary_artifact = arts[0] if arts else None
            outputs["output"] = primary_artifact

        return outputs, primary_artifact, cost_usd

    async def run(self, graph: Graph, req: GraphRunRequest) -> GraphRunSummary:
        """Hàm thực thi chính của GraphRunner."""
        run_id = f"run_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        self.store.create_run_session(run_id)

        # 1. Kiểm tra tính hợp lệ của Đồ thị
        validation = validate_graph(graph)
        if not validation.is_valid:
            err_msg = "; ".join(validation.errors)
            self._emit_event(
                SSEEvent(
                    event_type=SSEEventType.RUN_FAILED,
                    run_id=run_id,
                    message=f"Đồ thị không hợp lệ: {err_msg}",
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
            )
            return GraphRunSummary(
                run_id=run_id,
                project_id=req.project_id,
                total_nodes=len(graph.nodes),
                executed_nodes=[],
                skipped_nodes=[n.id for n in graph.nodes],
                failed_nodes=[],
                total_cost_usd=0.0,
                is_success=False,
                errors={"graph": err_msg},
            )

        topo_order = validation.topological_order
        node_map = {n.id: n for n in graph.nodes}

        # 2. Xác định danh sách các node cần thực thi theo Chế độ chạy (RunMode)
        nodes_to_execute = self.select_nodes_to_execute(graph, topo_order, req)

        # 3. Ước tính chi phí & Kiểm tra Trần ngân sách (Spending Limit Guard)
        total_estimated_cost = self.estimate_graph_cost(
            graph, nodes_to_execute, real_mode=not req.mock_mode
        )
        if req.spending_limit_usd is not None and total_estimated_cost > req.spending_limit_usd:
            exceed_msg = (
                f"Chi phí ước tính ${total_estimated_cost:.4f} USD vượt quá trần ngân sách cho phép "
                f"${req.spending_limit_usd:.4f} USD."
            )
            self._emit_event(
                SSEEvent(
                    event_type=SSEEventType.RUN_FAILED,
                    run_id=run_id,
                    message=exceed_msg,
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
            )
            raise BudgetExceededError(exceed_msg)

        # 4. Khởi tạo phiên thực thi
        self._emit_event(
            SSEEvent(
                event_type=SSEEventType.RUN_STARTED,
                run_id=run_id,
                message=f"Bắt đầu chạy {len(nodes_to_execute)} node theo chế độ '{req.mode.value}'",
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
        )

        executed_nodes: List[str] = []
        skipped_nodes: List[str] = []
        failed_nodes: List[str] = []
        node_errors: Dict[str, str] = {}
        total_actual_cost = 0.0

        # Khôi phục node_outputs từ các node đã có sẵn pinned generation
        node_outputs: Dict[str, Dict[str, Any]] = {}
        for nid, node in node_map.items():
            if node.pinned_generation_id:
                pinned_gen = next((g for g in node.generations if g.id == node.pinned_generation_id), None)
                if pinned_gen:
                    art = self.store.get_artifact(pinned_gen.artifact_id)
                    if art:
                        node_outputs[nid] = {
                            "artifact": art,
                            "image": art,
                            "images": [art],
                            "video": art,
                            "audio": art,
                            "captions": art,
                        }

        semaphore = asyncio.Semaphore(max(1, req.concurrency_limit))
        completed_nodes_set: Set[str] = {
            nid
            for nid, node in node_map.items()
            if node.state == NodeState.COMPLETED and not node.is_stale and nid not in nodes_to_execute
        }

        # 5. Thực thi các node theo thứ tự topo có quản lý phụ thuộc, hủy và retry
        for nid in topo_order:
            if nid not in nodes_to_execute:
                continue

            node = node_map[nid]

            if self.cancel_event is not None and self.cancel_event.is_set():
                node.state = NodeState.CANCELLED
                skipped_nodes.append(nid)
                self._emit_event(
                    SSEEvent(
                        event_type=SSEEventType.NODE_STATE,
                        run_id=run_id,
                        node_id=nid,
                        state=NodeState.CANCELLED,
                        message=f"Đã hủy node '{nid}' theo yêu cầu người dùng.",
                        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    )
                )
                continue

            direct_parents = self._find_direct_parents(graph, nid)

            failed_parents = [p for p in direct_parents if p in failed_nodes or p in skipped_nodes]
            if failed_parents:
                node.state = NodeState.FAILED
                skipped_nodes.append(nid)
                self._emit_event(
                    SSEEvent(
                        event_type=SSEEventType.NODE_STATE,
                        run_id=run_id,
                        node_id=nid,
                        state=NodeState.FAILED,
                        message=f"Bỏ qua node '{nid}' do node cha {failed_parents} bị lỗi.",
                        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    )
                )
                continue

            missing_parents = [p for p in direct_parents if p not in completed_nodes_set and p not in node_outputs]
            if missing_parents:
                err_text = f"Chưa chạy được node '{nid}': đang chờ đầu vào từ node {missing_parents}"
                node.state = NodeState.FAILED
                failed_nodes.append(nid)
                node_errors[nid] = err_text
                self._emit_event(
                    SSEEvent(
                        event_type=SSEEventType.NODE_STATE,
                        run_id=run_id,
                        node_id=nid,
                        state=NodeState.FAILED,
                        message=err_text,
                        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    )
                )
                continue

            # 6. Chạy Node với Retry thông minh (chỉ retry lỗi tạm thời)
            async with semaphore:
                node.state = NodeState.RUNNING
                self._emit_event(
                    SSEEvent(
                        event_type=SSEEventType.NODE_STATE,
                        run_id=run_id,
                        node_id=nid,
                        state=NodeState.RUNNING,
                        progress=0.1,
                        message=f"Đang thực thi node {node.type} ({nid})...",
                        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    )
                )

                resolved_inputs = self._gather_node_inputs(node, graph, node_outputs)

                success = False
                attempt_error = ""
                was_cancelled = False

                for attempt in range(1, req.max_retries + 1):
                    try:
                        self._emit_event(
                            SSEEvent(
                                event_type=SSEEventType.NODE_PROGRESS,
                                run_id=run_id,
                                node_id=nid,
                                state=NodeState.RUNNING,
                                progress=round(0.2 + (0.6 * attempt / req.max_retries), 2),
                                message=f"Đang xử lý (lần thử {attempt}/{req.max_retries})...",
                                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            )
                        )

                        outputs, primary_art, cost = await self._execute_node_handler(
                            node, resolved_inputs, run_id, is_mock=req.mock_mode
                        )

                        node_outputs[nid] = outputs
                        total_actual_cost += cost

                        art_id = primary_art.id if primary_art else f"art_virtual_{uuid.uuid4().hex[:6]}"
                        gen_id = f"gen_{uuid.uuid4().hex[:8]}"
                        new_gen = Generation(
                            id=gen_id,
                            node_id=nid,
                            params=node.params,
                            artifact_id=art_id,
                            cost_usd=cost,
                            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            is_pinned=True,
                        )

                        if node.generations:
                            direct_children = self._find_direct_children(graph, nid)
                            for cid in direct_children:
                                child_node = node_map.get(cid)
                                if child_node:
                                    child_node.is_stale = True

                        for g in node.generations:
                            g.is_pinned = False
                        node.generations.insert(0, new_gen)
                        node.pinned_generation_id = gen_id
                        node.state = NodeState.COMPLETED
                        node.is_stale = False

                        if cost > 0:
                            prov_used = (
                                primary_art.provenance.provider
                                if primary_art
                                else ("mock" if req.mock_mode else "provider")
                            )
                            model_used = (
                                primary_art.provenance.model
                                if primary_art
                                else str(node.params.get("model", node.type))
                            )
                            self.store.record_cost_ledger(
                                run_id=run_id,
                                node_id=nid,
                                provider=prov_used,
                                model=model_used,
                                cost_usd=cost,
                            )
                            self._emit_event(
                                SSEEvent(
                                    event_type=SSEEventType.COST_UPDATE,
                                    run_id=run_id,
                                    node_id=nid,
                                    cost_usd=cost,
                                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                )
                            )

                        self._emit_event(
                            SSEEvent(
                                event_type=SSEEventType.NODE_STATE,
                                run_id=run_id,
                                node_id=nid,
                                state=NodeState.COMPLETED,
                                progress=1.0,
                                message=f"Node {node.type} hoàn thành xuất sắc.",
                                cost_usd=cost,
                                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            )
                        )

                        completed_nodes_set.add(nid)
                        executed_nodes.append(nid)
                        success = True
                        break

                    except Exception as exc:
                        attempt_error = redact_secrets(str(exc))
                        is_non_retryable = isinstance(exc, ProviderError) and not exc.retryable
                        if isinstance(exc, ProviderError) and exc.kind.value == "cancelled":
                            was_cancelled = True

                        self._emit_event(
                            SSEEvent(
                                event_type=SSEEventType.NODE_LOG,
                                run_id=run_id,
                                node_id=nid,
                                message=f"Lỗi lần thử {attempt}/{req.max_retries}: {attempt_error}",
                                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            )
                        )
                        if is_non_retryable:
                            break
                        if attempt < req.max_retries:
                            backoff_sec = 0.2 * (2 ** (attempt - 1))
                            await asyncio.sleep(backoff_sec)

                if not success:
                    node.state = NodeState.CANCELLED if was_cancelled else NodeState.FAILED
                    failed_nodes.append(nid)
                    node_errors[nid] = attempt_error
                    self._emit_event(
                        SSEEvent(
                            event_type=SSEEventType.NODE_STATE,
                            run_id=run_id,
                            node_id=nid,
                            state=node.state,
                            progress=0.0,
                            message=f"Node dừng lại: {attempt_error}",
                            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        )
                    )

        # 7. Lưu đồ thị sau khi chạy
        graph.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.store.save_graph(graph)

        is_overall_success = len(failed_nodes) == 0
        final_event_type = SSEEventType.RUN_COMPLETED if is_overall_success else SSEEventType.RUN_FAILED

        self._emit_event(
            SSEEvent(
                event_type=final_event_type,
                run_id=run_id,
                message=(
                    f"Phiên chạy hoàn tất. Đã thực thi {len(executed_nodes)} node, "
                    f"thất bại {len(failed_nodes)} node, bỏ qua {len(skipped_nodes)} node. "
                    f"Tổng chi phí: ${total_actual_cost:.4f} USD."
                ),
                cost_usd=total_actual_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
        )

        return GraphRunSummary(
            run_id=run_id,
            project_id=req.project_id,
            total_nodes=len(graph.nodes),
            executed_nodes=executed_nodes,
            skipped_nodes=skipped_nodes,
            failed_nodes=failed_nodes,
            total_cost_usd=round(total_actual_cost, 6),
            is_success=is_overall_success,
            errors=node_errors,
        )
