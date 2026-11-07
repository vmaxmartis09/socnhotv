from __future__ import annotations

import asyncio
import copy
import time
from typing import Any, Dict, List
import pytest
from fastapi.testclient import TestClient

from socnhotv.core.api.app import app
from socnhotv.core.contracts.types import (
    Edge,
    Graph,
    NodeInstance,
    NodeState,
    RunMode,
)
from socnhotv.core.engine.batch_runner import (
    BatchEpisodeRunConfig,
    BatchRunEstimate,
    BatchRunSummary,
    BatchRunner,
    clone_graph_for_episode,
    get_node_cache_path,
)
from socnhotv.core.nodes.registry import NodeRegistry
from socnhotv.core.storage.project_store import ProjectStore

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_node_registry():
    NodeRegistry.initialize_defaults()


def build_sample_episode_graph(project_id: str = "soc-nho-tv") -> Graph:
    """Tạo đồ thị mẫu cho tập phim: Script -> Quality -> ImageGen -> VideoGen -> Export."""
    nodes = [
        NodeInstance(
            id="n_script",
            type="script",
            params={
                "mode": "episode",
                "episodeId": "ep01-nui-lua-trong-bung-bi",
                "granularity": "shot",
                "targetSceneCount": 4,
            },
        ),
        NodeInstance(
            id="n_quality",
            type="quality_check",
            params={"blockOnFail": True, "policyAutoScan": True},
        ),
        NodeInstance(
            id="n_image",
            type="image_gen",
            params={"model": "mock-image", "aspectRatio": "16:9"},
        ),
        NodeInstance(
            id="n_video",
            type="video_gen",
            params={"model": "mock-video", "durationSec": 5.0},
        ),
        NodeInstance(
            id="n_export",
            type="export",
            params={"platforms": ["youtube"], "outputFileName": ""},
        ),
    ]
    edges = [
        Edge(id="e1", source_node_id="n_script", source_port="scenes", target_node_id="n_quality", target_port="scenes"),
        Edge(id="e2", source_node_id="n_script", source_port="lines", target_node_id="n_quality", target_port="text"),
        Edge(id="e3", source_node_id="n_script", source_port="scenes", target_node_id="n_image", target_port="scenes"),
        Edge(id="e4", source_node_id="n_image", source_port="scenes", target_node_id="n_video", target_port="scenes"),
        Edge(id="e5", source_node_id="n_video", source_port="video", target_node_id="n_export", target_port="video"),
    ]
    return Graph(
        id="graph_sample_template",
        projectId=project_id,
        name="Template Episode Flow",
        nodes=nodes,
        edges=edges,
        updatedAt="2026-11-06T18:00:00Z",
    )


def test_clone_graph_does_not_mutate_base_graph():
    """H3.1: Nhân bản graph cho từng tập không làm thay đổi graph gốc."""
    base_graph = build_sample_episode_graph()
    original_dump = copy.deepcopy(base_graph.model_dump())

    ep1_id = "ep02-mun-so-bong-toi"
    cloned1 = clone_graph_for_episode(base_graph, ep1_id)

    # Đồ thị gốc không hề thay đổi
    assert base_graph.model_dump() == original_dump
    assert base_graph.id == "graph_sample_template"
    assert base_graph.nodes[0].params["episodeId"] == "ep01-nui-lua-trong-bung-bi"

    # Đồ thị nhân bản có id mới mang định danh tập
    assert cloned1.id == f"graph_sample_template__{ep1_id}"
    script_node = next(n for n in cloned1.nodes if n.id == "n_script")
    assert script_node.params["mode"] == "episode"
    assert script_node.params["episodeId"] == ep1_id

    export_node = next(n for n in cloned1.nodes if n.id == "n_export")
    assert export_node.params["outputFileName"] == f"{ep1_id}.mp4"
    assert export_node.params["outputSlug"] == ep1_id


def test_cache_by_graph_episode_node():
    """H3.2: Cache cổng ra lưu theo bộ ba (graphId, episodeId, nodeId)."""
    store = ProjectStore("soc-nho-tv")
    runs_dir = store.runs_dir

    p1 = get_node_cache_path(runs_dir, "graph_main", "ep01", "n_script")
    p2 = get_node_cache_path(runs_dir, "graph_main", "ep02", "n_script")
    p3 = get_node_cache_path(runs_dir, "graph_other", "ep01", "n_script")

    # Đường dẫn phân biệt rõ ràng theo graphId, episodeId, nodeId
    assert "graph_main__ep01" in str(p1)
    assert "graph_main__ep02" in str(p2)
    assert "graph_other__ep01" in str(p3)
    assert p1 != p2
    assert p1 != p3


def test_batch_cache_hit_and_isolation():
    """H3.3: Lần chạy 2 của cùng một tập trúng cache và bỏ qua node, tập khác chạy độc lập."""
    async def _run():
        store = ProjectStore("soc-nho-tv")
        base_graph = build_sample_episode_graph()
        batch_runner = BatchRunner(store=store)

        # Chạy lần 1 cho ep01
        cfg1 = BatchEpisodeRunConfig(
            episodeIds=["ep01-nui-lua-trong-bung-bi"],
            mockMode=True,
            concurrency=1,
        )
        summary1 = await batch_runner.run_batch(base_graph, cfg1)
        assert summary1.completed_count == 1
        ep1_res1 = summary1.episode_results[0]
        assert ep1_res1.is_success is True
        assert "n_script" in ep1_res1.executed_nodes

        # Chạy lần 2 cho ep01: n_script và n_quality phải được nạp từ cache
        summary2 = await batch_runner.run_batch(base_graph, cfg1)
        assert summary2.completed_count == 1
        ep1_res2 = summary2.episode_results[0]
        assert ep1_res2.is_success is True
        assert "n_script" in ep1_res2.cached_nodes

        # Chạy cho ep02: không dùng cache của ep01
        cfg2 = BatchEpisodeRunConfig(
            episodeIds=["ep02-mun-so-bong-toi"],
            mockMode=True,
            concurrency=1,
        )
        summary3 = await batch_runner.run_batch(base_graph, cfg2)
        assert summary3.completed_count == 1
        ep2_res = summary3.episode_results[0]
        assert ep2_res.is_success is True
        # Lần đầu của ep02 không được có n_script trong cachedNodes
        assert "n_script" in ep2_res.executed_nodes

    asyncio.run(_run())


def test_fault_isolation_one_failing_does_not_break_others():
    """H3.4: Tập lỗi không làm hỏng tập khác, báo cáo chi tiết từng tập."""
    async def _run():
        store = ProjectStore("soc-nho-tv")
        base_graph = build_sample_episode_graph()
        batch_runner = BatchRunner(store=store)

        # ep_khong_ton_tai sẽ lỗi vì không có kịch bản
        eps = [
            "ep01-nui-lua-trong-bung-bi",
            "ep_khong_ton_tai_12345",
            "ep02-mun-so-bong-toi",
        ]
        cfg = BatchEpisodeRunConfig(
            episodeIds=eps,
            mockMode=True,
            concurrency=1,
        )

        summary = await batch_runner.run_batch(base_graph, cfg)
        assert summary.total_episodes == 3
        assert summary.completed_count == 2
        assert summary.failed_count == 1
        assert summary.is_success is False

        r1, r2, r3 = summary.episode_results
        assert r1.episode_id == "ep01-nui-lua-trong-bung-bi"
        assert r1.is_success is True
        assert r1.status == "completed"

        assert r2.episode_id == "ep_khong_ton_tai_12345"
        assert r2.is_success is False
        assert r2.status == "failed"
        assert len(r2.errors) > 0 or len(r2.failed_nodes) > 0

        # Tập thứ 3 vẫn chạy và hoàn thành bình thường
        assert r3.episode_id == "ep02-mun-so-bong-toi"
        assert r3.is_success is True
        assert r3.status == "completed"

    asyncio.run(_run())


def test_batch_cancellation():
    """H3.5: Hủy đợt chạy giữa chừng đánh dấu các tập còn lại là cancelled."""
    async def _run():
        store = ProjectStore("soc-nho-tv")
        base_graph = build_sample_episode_graph()
        batch_runner = BatchRunner(store=store)

        cancel_ev = asyncio.Event()
        cancel_ev.set()  # Hủy ngay từ đầu

        cfg = BatchEpisodeRunConfig(
            episodeIds=["ep01-nui-lua-trong-bung-bi", "ep02-mun-so-bong-toi"],
            mockMode=True,
            concurrency=1,
        )
        summary = await batch_runner.run_batch(base_graph, cfg, cancel_event=cancel_ev)
        assert summary.cancelled_count == 2
        assert summary.completed_count == 0
        assert all(r.status == "cancelled" for r in summary.episode_results)

    asyncio.run(_run())


def test_api_estimate_and_run_endpoints():
    """H3.6: Kiểm tra các endpoint API POST /projects/{id}/estimate-episodes và run-episodes."""
    eps = ["ep01-nui-lua-trong-bung-bi", "ep02-mun-so-bong-toi"]
    sample_graph = build_sample_episode_graph().model_dump()

    # 1. Estimate
    res_est = client.post(
        "/projects/soc-nho-tv/estimate-episodes",
        json={"graph": sample_graph, "episodeIds": eps, "mockMode": True},
    )
    assert res_est.status_code == 200
    data_est = res_est.json()
    assert data_est["totalEpisodes"] == 2
    assert data_est["canProceed"] is True
    assert data_est["totalEstimatedCostUsd"] == 0.0

    # 2. Run episodes (mockMode=True)
    res_run = client.post(
        "/projects/soc-nho-tv/run-episodes",
        json={"graph": sample_graph, "episodeIds": eps, "mockMode": True, "concurrency": 1},
    )
    assert res_run.status_code == 200
    data_run = res_run.json()
    assert data_run["totalEpisodes"] == 2
    assert data_run["completedCount"] == 2
    assert data_run["failedCount"] == 0
    assert len(data_run["episodeResults"]) == 2

    # 3. Lấy báo cáo batch vừa chạy
    batch_id = data_run["batchId"]
    res_rep = client.get(f"/projects/soc-nho-tv/batch-runs/{batch_id}")
    assert res_rep.status_code == 200
    assert res_rep.json()["batchId"] == batch_id

    # 4. Danh sách các batch run
    res_list = client.get("/projects/soc-nho-tv/batch-runs")
    assert res_list.status_code == 200
    assert any(b["batchId"] == batch_id for b in res_list.json())

    # 5. Cancel batch endpoint
    res_cancel = client.post("/projects/soc-nho-tv/run-episodes/cancel", json={"batchId": batch_id})
    assert res_cancel.status_code == 200


def test_api_paid_run_requires_confirmation_via_spendguard():
    """H3.7: Chạy chế độ thật có chi phí > 0 khi chưa xác nhận sẽ trả 409 qua SpendGuard."""
    nodes = [
        NodeInstance(
            id="n_script",
            type="script",
            params={"mode": "episode", "episodeId": "ep01-nui-lua-trong-bung-bi"},
        ),
        NodeInstance(
            id="n_img",
            type="image_gen",
            params={"model": "fal-flux-pro", "prompt": "test prompt"},
        ),
    ]
    graph = Graph(
        id="graph_paid_test",
        projectId="soc-nho-tv",
        nodes=nodes,
        edges=[],
        updatedAt="2026-11-06T18:00:00Z",
    )

    res = client.post(
        "/projects/soc-nho-tv/run-episodes",
        json={
            "graph": graph.model_dump(),
            "episodeIds": ["ep01-nui-lua-trong-bung-bi"],
            "mockMode": False,
            "confirmPaidRun": False,
        },
    )
    # Nếu thiếu API key thì trả 400, nếu có key mà chưa confirm thì trả 409
    assert res.status_code in (400, 409)
    if res.status_code == 409:
        assert "confirmPaidRun=true" in res.json()["detail"]


def test_run_3_episodes_cheapest_mode():
    """H3.8: Chạy thử 3 tập ở chế độ rẻ nhất (mock/ảnh tĩnh) và báo cáo từng tập đúng."""
    async def _run():
        store = ProjectStore("soc-nho-tv")
        base_graph = build_sample_episode_graph()
        batch_runner = BatchRunner(store=store)

        three_eps = [
            "ep01-nui-lua-trong-bung-bi",
            "ep02-mun-so-bong-toi",
            "ep03-chu-tho-bong-cua-mimi-dau-roi",
        ]

        t0 = time.time()
        cfg = BatchEpisodeRunConfig(
            episodeIds=three_eps,
            mockMode=True,
            concurrency=1,
        )

        summary = await batch_runner.run_batch(base_graph, cfg)
        elapsed = time.time() - t0

        assert summary.total_episodes == 3
        assert summary.completed_count == 3
        assert summary.failed_count == 0
        assert summary.is_success is True
        assert summary.total_cost_usd == 0.0

        # Báo cáo từng tập
        for r in summary.episode_results:
            assert r.is_success is True
            assert r.status == "completed"
            assert r.duration_sec >= 0.0
            assert r.episode_id in three_eps
            assert "n_script" in r.executed_nodes or "n_script" in r.cached_nodes
            assert r.output_video_path is not None

        print(f"\n[H3 Verified] Chạy 3 tập mock hoàn tất trong {elapsed:.2f}s ({summary.duration_sec}s).")

    asyncio.run(_run())
