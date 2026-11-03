from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
    Generation,
    Graph,
    GraphRunRequest,
    GraphRunSummary,
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
from socnhotv.core.providers.mock_provider import MockProvider
from socnhotv.core.storage.project_store import ProjectStore


class BudgetExceededError(Exception):
    """Ngoại lệ khi chi phí ước tính vượt quá trần ngân sách cho phép."""
    pass


class GraphExecutionError(Exception):
    """Lỗi khi thực thi đồ thị node."""
    pass


class GraphRunner:
    """Bộ chạy đồ thị node (Execution Engine):
    - Kiểm tra tính hợp lệ đồ thị (DAG, không vòng lặp, tương thích cổng).
    - Hỗ trợ 4 chế độ chạy: ALL, FORCE_ALL, SINGLE_NODE, DOWNSTREAM.
    - Kiểm tra trần chi phí (spending limit) trước khi chạy.
    - Xử lý lỗi từng cảnh / từng node độc lập (Fault Isolation).
    - Tự động thử lại có lùi thời gian (Exponential Backoff Retry).
    - Cập nhật Generation, Ghim kết quả và đánh dấu Stale chuẩn hợp đồng.
    - Phát sự kiện SSE thời gian thực và ghi sổ chi phí (Cost Ledger).
    """

    def __init__(
        self,
        store: ProjectStore,
        model_registry: Optional[ModelRegistry] = None,
        provider: Optional[Any] = None,
        event_callback: Optional[Callable[[SSEEvent], None]] = None,
    ):
        self.store = store
        self.model_registry = model_registry or ModelRegistry()
        self.provider = provider or MockProvider(store)
        self.event_callback = event_callback

    def _emit_event(self, event: SSEEvent) -> None:
        if self.event_callback:
            try:
                self.event_callback(event)
            except Exception:
                pass

    def _find_descendants(self, graph: Graph, start_node_id: str) -> Set[str]:
        """Tìm toàn bộ các node con, cháu (hậu duệ) đi ra từ một node."""
        descendants: Set[str] = set()
        queue = [start_node_id]

        # Xây dựng danh sách cạnh đi ra
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

    def estimate_node_cost(self, node: NodeInstance) -> float:
        """Ước tính chi phí USD cho một node dựa trên sổ model."""
        node_def = NodeRegistry.get(node.type)
        if not node_def:
            return 0.0

        if node.type == "image_gen":
            model_id = node.params.get("model", "mock-image-v1")
            n = int(node.params.get("n", 1))
            return self.model_registry.estimate_cost(model_id, num_images=n)
        elif node.type == "video_gen":
            model_id = node.params.get("model", "mock-veo-video-v1")
            duration = float(node.params.get("durationSec", 8.0))
            return self.model_registry.estimate_cost(model_id, duration_sec=duration)
        elif node.type == "voice_tts":
            model_id = node.params.get("model", "mock-omnivoice-v1")
            text = str(node.params.get("text", ""))
            return self.model_registry.estimate_cost(model_id, text_length=len(text))

        return 0.0

    def estimate_graph_cost(self, graph: Graph, node_ids_to_run: List[str]) -> float:
        """Tính tổng chi phí USD ước tính của toàn bộ các node sẽ chạy."""
        total = 0.0
        node_map = {n.id: n for n in graph.nodes}
        for nid in node_ids_to_run:
            if nid in node_map:
                total += self.estimate_node_cost(node_map[nid])
        return round(total, 6)

    def _gather_node_inputs(
        self,
        node: NodeInstance,
        graph: Graph,
        node_outputs: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Thu thập dữ liệu đầu vào cho node từ params, inputs và kết quả các node cha."""
        resolved: Dict[str, Any] = dict(node.params)

        # Đọc dữ liệu từ edge
        for edge in graph.edges:
            if edge.target_node_id == node.id:
                src_out = node_outputs.get(edge.source_node_id, {})
                if edge.source_port in src_out:
                    val = src_out[edge.source_port]
                    # Hỗ trợ tự động wrap thành list nếu cổng vào cần IMAGE_LIST mà output là IMAGE đơn
                    tgt_def = NodeRegistry.get(node.type)
                    if tgt_def:
                        tgt_port_def = next((p for p in tgt_def.input_ports if p.name == edge.target_port), None)
                        if tgt_port_def and tgt_port_def.port_type == PortType.IMAGE_LIST and not isinstance(val, list):
                            val = [val]
                    resolved[edge.target_port] = val

        # Đọc dữ liệu từ node.inputs dạng NodePortInputRef
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

    async def _execute_node_handler(
        self,
        node: NodeInstance,
        resolved_inputs: Dict[str, Any],
        run_id: str,
    ) -> Tuple[Dict[str, Any], Optional[Artifact], float]:
        """Thực thi logic sinh sản phẩm của một Node cụ thể."""
        outputs: Dict[str, Any] = {}
        primary_artifact: Optional[Artifact] = None
        cost_usd = self.estimate_node_cost(node)

        node_type = node.type

        if node_type == "text":
            content = resolved_inputs.get("content", "")
            outputs["text"] = content
            # Lưu text thành artifact
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
            char_id = resolved_inputs.get("characterId", "soc_nho")
            # Nạp DNA ảnh từ character
            char_info = {
                "characterId": char_id,
                "name": "Sóc Nhỏ (Bi)" if char_id == "soc_nho" else char_id,
                "scaleLock": "100cm",
                "defaultVoice": "soc-nho",
            }
            outputs["character"] = char_info
            # Tạo dummy mock images nếu cần
            ref_arts = await self.provider.generate_images(
                prompt=f"Master DNA character panel for {char_id}",
                node_id=node.id,
                run_id=run_id,
                n=2,
            )
            outputs["reference_images"] = ref_arts
            primary_artifact = ref_arts[0] if ref_arts else None

        elif node_type == "image":
            uri = resolved_inputs.get("uri", "")
            # Tạo mock image nếu chưa có
            arts = await self.provider.generate_images(
                prompt=f"Uploaded image reference: {uri or 'default image'}",
                node_id=node.id,
                run_id=run_id,
                n=1,
            )
            primary_artifact = arts[0]
            outputs["image"] = primary_artifact

        elif node_type == "script":
            text_in = str(resolved_inputs.get("text", "Ý tưởng phân cảnh"))
            scenes = [
                {
                    "sceneNumber": 1,
                    "title": "Mở đầu",
                    "imagePrompt": f"Cảnh mở đầu: {text_in[:60]}",
                    "videoPrompt": "Camera panning nhẹ nhàng",
                    "dialogue": "Xin chào các bạn nhỏ!",
                    "durationSec": 5.0,
                },
                {
                    "sceneNumber": 2,
                    "title": "Cao trào & Bài học",
                    "imagePrompt": f"Cảnh cao trào vui nhộn với Bi",
                    "videoPrompt": "Nhân vật tươi cười hào hứng",
                    "dialogue": "Cùng học thói quen tốt mỗi ngày nhé!",
                    "durationSec": 6.0,
                },
            ]
            outputs["scenes"] = scenes

        elif node_type == "image_gen":
            prompt = str(resolved_inputs.get("prompt", "Sóc Nhỏ Bi đang khám phá khu rừng diệu kỳ"))
            aspect = str(resolved_inputs.get("aspectRatio", "9:16"))
            n = int(resolved_inputs.get("n", 1))
            arts = await self.provider.generate_images(
                prompt=prompt,
                aspect_ratio=aspect,
                n=n,
                node_id=node.id,
                run_id=run_id,
            )
            outputs["images"] = arts
            outputs["image"] = arts[0] if arts else None
            primary_artifact = arts[0] if arts else None

        elif node_type == "video_gen":
            prompt = str(resolved_inputs.get("prompt", "Camera dolly zoom theo bước chân Sóc Nhỏ Bi"))
            aspect = str(resolved_inputs.get("aspectRatio", "9:16"))
            duration = float(resolved_inputs.get("durationSec", 8.0))
            first_frame_art = resolved_inputs.get("first_frame") or resolved_inputs.get("image")
            first_frame_uri = first_frame_art.uri if isinstance(first_frame_art, Artifact) else None

            art = await self.provider.generate_video(
                prompt=prompt,
                first_frame_uri=first_frame_uri,
                duration_sec=duration,
                aspect_ratio=aspect,
                node_id=node.id,
                run_id=run_id,
            )
            outputs["video"] = art
            primary_artifact = art

        elif node_type == "voice_tts":
            text = str(resolved_inputs.get("text", "Chào các bạn, mình là Sóc Nhỏ Bi nè!"))
            voice_id = str(resolved_inputs.get("voiceId", "soc-nho"))
            tempo = float(resolved_inputs.get("tempo", 1.10))

            art = await self.provider.speak_voice(
                text=text,
                voice_id=voice_id,
                tempo=tempo,
                node_id=node.id,
                run_id=run_id,
            )
            outputs["audio"] = art
            primary_artifact = art

        elif node_type == "captions":
            audio_art = resolved_inputs.get("audio")
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

        elif node_type in ("hyperframes_render", "export"):
            # Mock render video composition
            art = await self.provider.generate_video(
                prompt="Final rendered video composition 9:16",
                duration_sec=12.0,
                aspect_ratio="9:16",
                has_audio=True,
                node_id=node.id,
                run_id=run_id,
            )
            outputs["video"] = art
            primary_artifact = art

        elif node_type == "quality_check":
            outputs["pass"] = True
            outputs["score"] = 9.8
            outputs["feedback"] = "Nhân vật Sóc Nhỏ chuẩn nhận diện DNA và tỉ lệ 100cm."

        elif node_type == "vision_analyze":
            media_uri = str(resolved_inputs.get("video") or resolved_inputs.get("image") or "")
            res = await self.provider.analyze_vision(
                media_uri=media_uri,
                prompt="Phân tích bố cục và chuyển động",
                node_id=node.id,
                run_id=run_id,
            )
            outputs["scenes"] = res.get("scenes", [])
            outputs["overview"] = res.get("overview", "")

        else:
            # Fallback mock
            arts = await self.provider.generate_images(
                prompt=f"Generic execution for {node.type}",
                node_id=node.id,
                run_id=run_id,
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
        nodes_to_execute: List[str] = []

        if req.mode == RunMode.FORCE_ALL:
            nodes_to_execute = list(topo_order)
        elif req.mode == RunMode.SINGLE_NODE:
            if not req.target_node_id or req.target_node_id not in node_map:
                raise GraphExecutionError(f"Target node '{req.target_node_id}' không tồn tại trong đồ thị.")
            nodes_to_execute = [req.target_node_id]
        elif req.mode == RunMode.DOWNSTREAM:
            if not req.target_node_id or req.target_node_id not in node_map:
                raise GraphExecutionError(f"Target node '{req.target_node_id}' không tồn tại trong đồ thị.")
            descendants = self._find_descendants(graph, req.target_node_id)
            descendants.add(req.target_node_id)
            # Giữ đúng thứ tự topo
            nodes_to_execute = [nid for nid in topo_order if nid in descendants]
        else:  # RunMode.ALL (mặc định)
            # Chạy các node chưa completed, hoặc bị stale, hoặc chưa có pinned generation
            for nid in topo_order:
                n = node_map[nid]
                has_valid_pin = bool(n.pinned_generation_id and any(g.id == n.pinned_generation_id for g in n.generations))
                if n.state != NodeState.COMPLETED or n.is_stale or not has_valid_pin:
                    nodes_to_execute.append(nid)

        # 3. Ước tính chi phí & Kiểm tra Trần ngân sách (Spending Limit Guard)
        total_estimated_cost = self.estimate_graph_cost(graph, nodes_to_execute)
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
                        node_outputs[nid] = {"artifact": art, "image": art, "video": art, "audio": art}

        semaphore = asyncio.Semaphore(max(1, req.concurrency_limit))
        completed_nodes_set: Set[str] = {
            nid for nid, node in node_map.items() if node.state == NodeState.COMPLETED and not node.is_stale and nid not in nodes_to_execute
        }

        # 5. Thực thi các node theo thứ tự topo có quản lý phụ thuộc và retry
        for nid in topo_order:
            if nid not in nodes_to_execute:
                continue

            node = node_map[nid]
            direct_parents = self._find_direct_parents(graph, nid)

            # Kiểm tra xem có node cha nào bị failed không -> nếu có thì cô lập lỗi (fault isolation) và skip node này
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

            # Kiểm tra xem tất cả node cha đã hoàn thành chưa (đặc biệt khi chạy SINGLE_NODE)
            missing_parents = [p for p in direct_parents if p not in completed_nodes_set and p not in node_outputs]
            if missing_parents:
                err_text = f"Node '{nid}' không thể chạy do thiếu dữ liệu từ node cha: {missing_parents}"
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

            # 6. Chạy Node với Retry & Exponential Backoff
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
                            node, resolved_inputs, run_id
                        )

                        # Lưu trữ kết quả
                        node_outputs[nid] = outputs
                        total_actual_cost += cost

                        # Ghi nhận Generation mới (Mục 11: mỗi lần chạy là 1 generation, không ghi đè)
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

                        # Nếu đây là lần chạy lại và đã có generation trước đó -> đánh dấu các con trực tiếp là is_stale = True
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

                        # Ghi sổ chi phí
                        if cost > 0:
                            self.store.record_cost_ledger(
                                run_id=run_id,
                                node_id=nid,
                                provider="mock",
                                model=node.params.get("model", node.type),
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
                        attempt_error = str(exc)
                        self._emit_event(
                            SSEEvent(
                                event_type=SSEEventType.NODE_LOG,
                                run_id=run_id,
                                node_id=nid,
                                message=f"Lỗi lần thử {attempt}/{req.max_retries}: {attempt_error}",
                                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            )
                        )
                        if attempt < req.max_retries:
                            backoff_sec = 0.2 * (2 ** (attempt - 1))
                            await asyncio.sleep(backoff_sec)

                if not success:
                    node.state = NodeState.FAILED
                    failed_nodes.append(nid)
                    node_errors[nid] = attempt_error
                    self._emit_event(
                        SSEEvent(
                            event_type=SSEEventType.NODE_STATE,
                            run_id=run_id,
                            node_id=nid,
                            state=NodeState.FAILED,
                            progress=0.0,
                            message=f"Node thất bại sau {req.max_retries} lần thử: {attempt_error}",
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
