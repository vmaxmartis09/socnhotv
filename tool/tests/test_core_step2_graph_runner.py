from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List
import pytest
from fastapi.testclient import TestClient

from socnhotv.core.contracts.types import (
    Edge,
    Graph,
    GraphRunRequest,
    NodeInstance,
    NodeState,
    RunMode,
    SSEEvent,
)
from socnhotv.core.engine.graph_runner import BudgetExceededError, GraphRunner
from socnhotv.core.engine.validator import validate_graph
from socnhotv.core.models_registry.registry import ModelRegistry
from socnhotv.core.nodes.registry import NodeRegistry
from socnhotv.core.storage.project_store import ProjectStore
from socnhotv.core.api.app import app


@pytest.fixture(autouse=True)
def setup_registry():
    NodeRegistry.initialize_defaults()


def create_sample_dag_graph(project_id: str = "soc-nho-tv") -> Graph:
    """Tạo đồ thị DAG chuẩn cho tập phim Sóc Nhỏ:
    Text (Ý tưởng) -> Script (Phân cảnh) -> ImageGen (Tạo hình) -> VideoGen (Chuyển động)
    """
    node_text = NodeInstance(
        id="node_idea",
        type="text",
        params={"content": "Sóc Nhỏ Bi thức dậy chào buổi sáng vui tươi"},
    )
    node_script = NodeInstance(
        id="node_script",
        type="script",
        params={"targetSceneCount": 2},
    )
    node_image = NodeInstance(
        id="node_image_gen",
        type="image_gen",
        params={"prompt": "Sóc Nhỏ Bi trong căn phòng gỗ ấm cúng", "aspectRatio": "9:16"},
    )
    node_video = NodeInstance(
        id="node_video_gen",
        type="video_gen",
        params={"prompt": "Camera dolly nhẹ nhàng", "durationSec": 5.0, "aspectRatio": "9:16"},
    )

    edges = [
        Edge(
            id="edge_1",
            source_node_id="node_idea",
            source_port="text",
            target_node_id="node_script",
            target_port="text",
        ),
        Edge(
            id="edge_2",
            source_node_id="node_image_gen",
            source_port="image",
            target_node_id="node_video_gen",
            target_port="image",
        ),
    ]

    return Graph(
        id="graph_sample_dag",
        project_id=project_id,
        name="Quy trình mẫu Sóc Nhỏ DAG",
        nodes=[node_text, node_script, node_image, node_video],
        edges=edges,
        updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


def test_dag_validation_success():
    """Kiểm tra DAG hợp lệ và thứ tự Topological Sort."""
    graph = create_sample_dag_graph()
    result = validate_graph(graph)

    assert result.is_valid is True
    assert len(result.errors) == 0
    assert len(result.topological_order) == 4
    # node_idea phải xuất hiện trước node_script
    assert result.topological_order.index("node_idea") < result.topological_order.index("node_script")
    # node_image_gen phải xuất hiện trước node_video_gen
    assert result.topological_order.index("node_image_gen") < result.topological_order.index("node_video_gen")


def test_dag_cycle_detection():
    """Kiểm tra phát hiện chu trình (Cycle Detection)."""
    node_a = NodeInstance(id="node_a", type="text", params={"content": "A"})
    node_b = NodeInstance(id="node_b", type="text", params={"content": "B"})

    # Tạo vòng lặp vô hạn A -> B và B -> A
    edges = [
        Edge(id="e1", source_node_id="node_a", source_port="text", target_node_id="node_b", target_port="text"),
        Edge(id="e2", source_node_id="node_b", source_port="text", target_node_id="node_a", target_port="text"),
    ]
    graph = Graph(
        id="graph_cycle",
        project_id="soc-nho-tv",
        nodes=[node_a, node_b],
        edges=edges,
        updated_at="2026-11-03T00:00:00Z",
    )

    result = validate_graph(graph)
    assert result.is_valid is False
    assert any("chu trình" in err.lower() or "vòng lặp" in err.lower() for err in result.errors)


def test_port_type_incompatibility():
    """Kiểm tra phát hiện sai lệch kiểu cổng (Text không thể nối vào cổng Image)."""
    node_text = NodeInstance(id="node_text", type="text", params={"content": "Hello"})
    node_video = NodeInstance(id="node_video", type="video_gen", params={})

    # Nối cổng ra 'text' (PortType.TEXT) vào cổng vào 'image' (PortType.IMAGE) của video_gen
    edges = [
        Edge(
            id="bad_edge",
            source_node_id="node_text",
            source_port="text",
            target_node_id="node_video",
            target_port="image",
        )
    ]
    graph = Graph(
        id="graph_bad_port",
        project_id="soc-nho-tv",
        nodes=[node_text, node_video],
        edges=edges,
        updated_at="2026-11-03T00:00:00Z",
    )

    result = validate_graph(graph)
    assert result.is_valid is False
    assert any("không tương thích kiểu cổng" in err.lower() for err in result.errors)


def test_spending_limit_budget_exceeded():
    """Kiểm tra chặn vượt quá hạn mức chi phí (BudgetExceededError)."""
    async def _test():
        store = ProjectStore("soc-nho-tv")
        runner = GraphRunner(store=store, model_registry=ModelRegistry())

        node_video = NodeInstance(
            id="node_heavy_video",
            type="video_gen",
            params={"model": "google-veo-2", "durationSec": 30.0},
        )
        graph = Graph(
            id="graph_heavy",
            project_id="soc-nho-tv",
            nodes=[node_video],
            edges=[],
            updated_at="2026-11-03T00:00:00Z",
        )

        # Đặt trần chi phí cực nhỏ ($0.0001 USD) trong khi video veo-2 30s tốn hơn $1.00 USD
        req = GraphRunRequest(
            project_id="soc-nho-tv",
            mode=RunMode.ALL,
            spending_limit_usd=0.0001,
        )

        with pytest.raises(BudgetExceededError):
            await runner.run(graph, req)

    asyncio.run(_test())


def test_run_mode_all_and_caching():
    """Kiểm tra chạy chế độ ALL: lần đầu chạy tất cả, lần 2 bỏ qua các node đã ghim hợp lệ."""
    async def _test():
        store = ProjectStore("soc-nho-tv")
        events: List[SSEEvent] = []
        runner = GraphRunner(store=store, event_callback=events.append)

        graph = create_sample_dag_graph()

        # Lần chạy 1: Toàn bộ node chưa có generation -> chạy cả 4 node
        req1 = GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.ALL)
        summary1 = await runner.run(graph, req1)

        assert summary1.is_success is True
        assert len(summary1.executed_nodes) == 4
        assert len(summary1.failed_nodes) == 0

        # Kiểm tra node đã có pinned_generation_id
        for n in graph.nodes:
            assert n.state == NodeState.COMPLETED
            assert n.pinned_generation_id is not None
            assert n.is_stale is False

        # Lần chạy 2: Tất cả node đã COMPLETED và không stale -> số node cần chạy = 0
        req2 = GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.ALL)
        summary2 = await runner.run(graph, req2)

        assert summary2.is_success is True
        assert len(summary2.executed_nodes) == 0

    asyncio.run(_test())


def test_run_mode_single_node():
    """Kiểm tra chạy đơn lẻ đúng 1 node cụ thể (SINGLE_NODE)."""
    async def _test():
        store = ProjectStore("soc-nho-tv")
        runner = GraphRunner(store=store)

        graph = create_sample_dag_graph()

        req = GraphRunRequest(
            project_id="soc-nho-tv",
            mode=RunMode.SINGLE_NODE,
            target_node_id="node_idea",
        )
        summary = await runner.run(graph, req)

        assert summary.is_success is True
        assert summary.executed_nodes == ["node_idea"]
        # Các node khác giữ nguyên trạng thái cũ
        node_script = next(n for n in graph.nodes if n.id == "node_script")
        assert node_script.state == NodeState.IDLE

    asyncio.run(_test())


def test_run_mode_downstream():
    """Kiểm tra chạy từ 1 node và toàn bộ các node con cháu (DOWNSTREAM)."""
    async def _test():
        store = ProjectStore("soc-nho-tv")
        runner = GraphRunner(store=store)

        # Đồ thị: node_idea -> node_script, và node_image_gen -> node_video_gen
        graph = create_sample_dag_graph()

        # Chạy downstream từ node_image_gen -> chỉ chạy node_image_gen và node_video_gen
        req = GraphRunRequest(
            project_id="soc-nho-tv",
            mode=RunMode.DOWNSTREAM,
            target_node_id="node_image_gen",
        )
        summary = await runner.run(graph, req)

        assert summary.is_success is True
        assert set(summary.executed_nodes) == {"node_image_gen", "node_video_gen"}
        assert "node_idea" not in summary.executed_nodes
        assert "node_script" not in summary.executed_nodes

    asyncio.run(_test())


def test_generation_pinning_and_stale_propagation():
    """Kiểm tra quy tắc Mục 11 (lỗi thời theo từng cổng ra, E5 bước 1):
    Node cha chạy lại tạo Generation mới VÀ dữ liệu cổng ra đổi -> node con bị đánh dấu isStale=True
    nhưng KHÔNG tự động kích hoạt chạy lại. Chạy lại ra kết quả y hệt -> con không bị đánh dấu.
    """
    async def _test():
        store = ProjectStore("soc-nho-tv")
        runner = GraphRunner(store=store)

        graph = create_sample_dag_graph()

        # Chạy toàn bộ lần 1
        await runner.run(graph, GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.ALL))

        # Kiểm tra ban đầu node_video_gen không stale
        video_node = next(n for n in graph.nodes if n.id == "node_video_gen")
        assert video_node.is_stale is False

        single = GraphRunRequest(
            project_id="soc-nho-tv",
            mode=RunMode.SINGLE_NODE,
            target_node_id="node_image_gen",
        )
        # Chạy lại node cha với cùng tham số -> ảnh y hệt (mock tất định) -> con KHÔNG lỗi thời
        await runner.run(graph, single)
        img_node = next(n for n in graph.nodes if n.id == "node_image_gen")
        assert len(img_node.generations) >= 2
        assert next(n for n in graph.nodes if n.id == "node_video_gen").is_stale is False

        # Ảnh mock luôn là cùng 1 tệp nên dùng node văn bản để kiểm trường hợp dữ liệu đổi:
        # đổi nội dung ý tưởng rồi chạy lại -> cổng 'text' đổi -> node kịch bản bị đánh dấu lỗi thời
        idea = next(n for n in graph.nodes if n.id == "node_idea")
        idea.params = {**idea.params, "content": str(idea.params.get("content", "")) + " (bản khác)"}
        await runner.run(
            graph,
            GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.SINGLE_NODE, target_node_id="node_idea"),
        )
        assert len(idea.generations) >= 2
        assert idea.is_stale is False
        assert next(n for n in graph.nodes if n.id == "node_script").is_stale is True
        # Nhánh ảnh không liên quan vẫn sạch
        assert next(n for n in graph.nodes if n.id == "node_video_gen").is_stale is False

    asyncio.run(_test())


def test_fault_isolation():
    """Kiểm tra cô lập lỗi (Fault Isolation):
    Nếu nhánh A bị lỗi -> con của A bị skip, nhưng nhánh B độc lập vẫn chạy thành công!
    """
    async def _test():
        store = ProjectStore("soc-nho-tv")

        # Mock handler giả lập lỗi cho node nhánh 1
        class FlakyProvider:
            async def generate_images(self, **kwargs):
                if kwargs.get("node_id") == "node_faulty":
                    raise RuntimeError("Lỗi mạng cố ý tại node_faulty!")
                from socnhotv.core.providers.mock_provider import MockProvider
                return await MockProvider(store).generate_images(**kwargs)

            async def generate_video(self, **kwargs):
                from socnhotv.core.providers.mock_provider import MockProvider
                return await MockProvider(store).generate_video(**kwargs)

            async def speak_voice(self, **kwargs):
                from socnhotv.core.providers.mock_provider import MockProvider
                return await MockProvider(store).speak_voice(**kwargs)

        runner = GraphRunner(store=store, provider=FlakyProvider())

        # Nhánh 1: node_faulty -> node_faulty_child
        node_f1 = NodeInstance(id="node_faulty", type="image_gen", params={"prompt": "error"})
        node_f2 = NodeInstance(id="node_faulty_child", type="video_gen", params={"prompt": "child"})

        # Nhánh 2 (độc lập): node_good -> node_good_child
        node_g1 = NodeInstance(id="node_good", type="text", params={"content": "healthy"})
        node_g2 = NodeInstance(id="node_good_child", type="script", params={})

        edges = [
            Edge(id="e_f", source_node_id="node_faulty", source_port="image", target_node_id="node_faulty_child", target_port="image"),
            Edge(id="e_g", source_node_id="node_good", source_port="text", target_node_id="node_good_child", target_port="text"),
        ]

        graph = Graph(
            id="graph_fault_isolation",
            project_id="soc-nho-tv",
            nodes=[node_f1, node_f2, node_g1, node_g2],
            edges=edges,
            updated_at="2026-11-03T00:00:00Z",
        )

        req = GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.ALL, max_retries=1)
        summary = await runner.run(graph, req)

        # Node lỗi bị đánh dấu failed
        assert "node_faulty" in summary.failed_nodes
        # Node con phụ thuộc vào node lỗi bị skip
        assert "node_faulty_child" in summary.skipped_nodes
        # Nhưng NHÁNH ĐỘC LẬP (node_good và node_good_child) VẪN CHẠY THÀNH CÔNG!
        assert "node_good" in summary.executed_nodes
        assert "node_good_child" in summary.executed_nodes

    asyncio.run(_test())


def test_retry_with_backoff():
    """Kiểm tra tự động thử lại (Retry with Backoff) khi gặp lỗi tạm thời."""
    async def _test():
        store = ProjectStore("soc-nho-tv")
        attempt_count = 0

        class FlakyOnceProvider:
            async def generate_images(self, **kwargs):
                nonlocal attempt_count
                attempt_count += 1
                if attempt_count == 1:
                    raise ConnectionResetError("Mất kết nối tạm thời lần 1!")
                from socnhotv.core.providers.mock_provider import MockProvider
                return await MockProvider(store).generate_images(**kwargs)

        runner = GraphRunner(store=store, provider=FlakyOnceProvider())

        node = NodeInstance(id="node_retry", type="image_gen", params={"prompt": "retry test"})
        graph = Graph(
            id="graph_retry",
            project_id="soc-nho-tv",
            nodes=[node],
            edges=[],
            updated_at="2026-11-03T00:00:00Z",
        )

        req = GraphRunRequest(project_id="soc-nho-tv", mode=RunMode.ALL, max_retries=3)
        summary = await runner.run(graph, req)

        # Lần 1 thất bại, lần 2 thành công -> kết quả cuối cùng là thành công!
        assert attempt_count == 2
        assert summary.is_success is True
        assert "node_retry" in summary.executed_nodes

    asyncio.run(_test())


def test_fastapi_validate_and_run_endpoints():
    """Kiểm tra các endpoints FastAPI /graph/validate và /run."""
    client = TestClient(app)

    # Nạp đồ thị mẫu cho project soc-nho-tv
    sample_graph = create_sample_dag_graph()
    res_save = client.post(
        "/projects/soc-nho-tv/graph",
        json=sample_graph.model_dump(by_alias=True),
    )
    assert res_save.status_code == 200

    # 1. Test validate endpoint
    res_val = client.post("/projects/soc-nho-tv/graph/validate")
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["isValid"] is True
    assert "topologicalOrder" in val_data

    # 2. Test run endpoint với chế độ SINGLE_NODE
    res_run = client.post(
        "/projects/soc-nho-tv/run",
        json={
            "mode": "single_node",
            "targetNodeId": "node_idea",
            "mockMode": True,
        },
    )
    assert res_run.status_code == 200
    run_data = res_run.json()
    assert run_data["isSuccess"] is True
    assert "runId" in run_data
    assert "node_idea" in run_data["executedNodes"]
