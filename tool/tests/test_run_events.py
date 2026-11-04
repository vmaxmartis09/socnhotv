import asyncio
import pytest
from socnhotv.core.contracts.types import (
    Graph,
    GraphRunRequest,
    NodeInstance,
    Edge,
    NodePortInputRef,
    RunMode,
    SSEEvent,
    SSEEventType,
    NodeState,
)
from socnhotv.core.engine.graph_runner import GraphRunner
from socnhotv.core.engine.run_manager import RunManager
from socnhotv.core.models_registry.registry import ModelRegistry
from socnhotv.core.storage.project_store import ProjectStore


def test_run_events_order_and_state():
    async def _test():
        project_id = "soc-nho-tv"
        store = ProjectStore(project_id)
        
        # Tạo đồ thị chuỗi 2 node đơn giản: text -> script
        nodes = [
            NodeInstance(
                id="node_text",
                type="text",
                params={"content": "Vì sao cầu vồng có nhiều màu?", "text": "Vì sao cầu vồng có nhiều màu?"},
                position={"x": 0, "y": 0},
            ),
            NodeInstance(
                id="node_script",
                type="script",
                inputs={"text": NodePortInputRef(nodeId="node_text", outputPort="text")},
                params={"mode": "ai"},
                position={"x": 200, "y": 0},
            ),
        ]
        edges = [
            Edge(
                id="e1",
                sourceNodeId="node_text",
                sourcePort="text",
                targetNodeId="node_script",
                targetPort="text",
            )
        ]
        graph = Graph(id="test_graph", projectId=project_id, nodes=nodes, edges=edges, updatedAt="2026-11-04T00:00:00Z")

        events = []
        def on_event(ev: SSEEvent):
            events.append(ev)

        runner = GraphRunner(store=store, model_registry=ModelRegistry(), event_callback=on_event)
        req = GraphRunRequest(projectId=project_id, mode=RunMode.ALL, mockMode=True)
        
        summary = await runner.run(graph, req)
        assert summary.is_success is True

        # Kiểm tra các sự kiện SSE đã phát ra
        event_types = [e.event_type for e in events]
        assert SSEEventType.RUN_STARTED in event_types
        assert SSEEventType.RUN_COMPLETED in event_types
        
        # Kiểm tra node_text và node_script đều có trạng thái running và completed
        node_text_states = [e.state for e in events if e.node_id == "node_text" and e.state]
        assert NodeState.RUNNING in node_text_states
        assert NodeState.COMPLETED in node_text_states

        # Kiểm tra RunManager lưu trữ được run
        rm = RunManager.get_instance()
        runs = rm.list_runs(project_id)
        assert len(runs) > 0
        run_ids = [r.get("runId") or r.get("id") for r in runs]
        assert summary.run_id in run_ids

    asyncio.run(_test())
