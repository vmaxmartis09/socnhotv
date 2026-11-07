from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from socnhotv.core.contracts.types import Graph, SSEEvent
from socnhotv.core.engine.batch_runner import (
    BatchEpisodeRunConfig,
    BatchRunEstimate,
    BatchRunSummary,
    BatchRunner,
)
from socnhotv.core.engine.graph_runner import (
    BudgetExceededError,
    GraphExecutionError,
)
from socnhotv.core.models_registry.registry import ModelRegistry
from socnhotv.core.providers import (
    MissingApiKey,
    ProviderError,
    SpendCapExceeded,
    SpendGuard,
    redact_secrets,
)
from socnhotv.core.storage.project_store import ProjectStore

logger = logging.getLogger("socnhotv.routes.batch")

router = APIRouter(tags=["batch"])


def _get_sse_broadcast(project_id: str):
    try:
        from socnhotv.core.api.app import broadcast_event

        def _cb(ev: SSEEvent):
            broadcast_event(project_id, ev)

        return _cb
    except Exception:
        return None


def _parse_batch_config(payload: Dict[str, Any]) -> BatchEpisodeRunConfig:
    ep_ids = payload.get("episodeIds") or payload.get("episode_ids") or []
    if not isinstance(ep_ids, list) or not ep_ids:
        raise HTTPException(
            status_code=400,
            detail="Danh sách 'episodeIds' không được để trống.",
        )

    # Xử lý cờ mockMode linh hoạt
    mock_mode = True
    if "mockMode" in payload:
        mock_mode = bool(payload["mockMode"])
    elif "mock" in payload:
        mock_mode = bool(payload["mock"])
    elif "isMockMode" in payload:
        mock_mode = bool(payload["isMockMode"])

    confirm_paid = bool(
        payload.get("confirmPaidRun") or payload.get("confirm_paid_run") or payload.get("confirmed", False)
    )

    concurrency = int(payload.get("concurrency") or 1)
    spending_limit = payload.get("spendingLimitUsd")
    if spending_limit is not None:
        spending_limit = float(spending_limit)

    return BatchEpisodeRunConfig(
        episodeIds=[str(e).strip() for e in ep_ids if str(e).strip()],
        mockMode=mock_mode,
        runPolicy=payload.get("runPolicy"),
        concurrency=concurrency,
        confirmPaidRun=confirm_paid,
        spendingLimitUsd=spending_limit,
        source=str(payload.get("source", "batch_api")),
    )


@router.post("/projects/{project_id}/estimate-episodes")
async def estimate_batch_episodes(project_id: str, payload: Dict[str, Any] = Body(...)):
    """Ước tính chi phí và kiểm tra trần SpendGuard cho nhiều tập trước khi chạy."""
    store = ProjectStore(project_id)
    config = _parse_batch_config(payload)

    if "graph" in payload and payload["graph"]:
        base_graph = Graph.model_validate(payload["graph"])
    else:
        base_graph = store.get_graph()

    batch_runner = BatchRunner(store=store, model_registry=ModelRegistry())
    try:
        estimate = batch_runner.estimate_batch(
            base_graph=base_graph,
            episode_ids=config.episode_ids,
            config=config,
        )
        return estimate.model_dump(by_alias=True)
    except GraphExecutionError as ge:
        raise HTTPException(status_code=400, detail=redact_secrets(str(ge)))
    except Exception as e:
        logger.exception("Lỗi khi ước tính batch episodes: %s", e)
        raise HTTPException(status_code=500, detail=redact_secrets(str(e)))


@router.post("/projects/{project_id}/run-episodes")
async def run_batch_episodes(project_id: str, payload: Dict[str, Any] = Body(...)):
    """Chạy hàng loạt nhiều tập phim lần lượt cùng 1 flow mẫu:

    - Nhân bản graph cho từng tập (không sửa graph gốc).
    - Cache theo (graphId, episodeId, nodeId).
    - Ước tính tổng chi phí trước khi chạy qua SpendGuard.
    - Tập lỗi không làm hỏng tập khác (Fault Isolation).
    - Báo cáo chi tiết từng tập.
    """
    store = ProjectStore(project_id)
    config = _parse_batch_config(payload)

    if "graph" in payload and payload["graph"]:
        base_graph = Graph.model_validate(payload["graph"])
    else:
        base_graph = store.get_graph()

    sse_callback = _get_sse_broadcast(project_id)
    batch_runner = BatchRunner(
        store=store,
        model_registry=ModelRegistry(),
        event_callback=sse_callback,
    )

    # 1. Kiểm tra trước khả năng chi tiêu & xác nhận chi phí
    guard = SpendGuard(store.runs_dir)
    estimate = batch_runner.estimate_batch(
        base_graph=base_graph,
        episode_ids=config.episode_ids,
        config=config,
        guard=guard,
    )

    if not config.mock_mode:
        if estimate.missing_api_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Thiếu khóa API hợp lệ cho provider: {', '.join(estimate.missing_api_keys)}",
            )
        if not estimate.can_proceed:
            raise HTTPException(
                status_code=400,
                detail=str(estimate.reason or "Vượt trần chi tiêu cho phép."),
            )
        if estimate.requires_confirmation:
            return JSONResponse(
                status_code=409,
                content={
                    "detail": "Cần xác nhận chi phí trước khi gọi model trả phí (truyền confirmPaidRun=true).",
                    "estimate": estimate.model_dump(by_alias=True),
                },
            )

    try:
        summary = await batch_runner.run_batch(base_graph=base_graph, config=config)
        return summary.model_dump(by_alias=True)
    except (BudgetExceededError, GraphExecutionError, MissingApiKey, SpendCapExceeded) as be:
        raise HTTPException(status_code=400, detail=redact_secrets(str(be)))
    except ProviderError as pe:
        raise HTTPException(status_code=400, detail=redact_secrets(str(pe)))
    except Exception as e:
        logger.exception("Lỗi thực thi batch episodes: %s", e)
        raise HTTPException(status_code=500, detail=redact_secrets(str(e)))


@router.post("/projects/{project_id}/run-episodes/cancel")
async def cancel_batch_episodes(project_id: str, payload: Dict[str, Any] = Body(default_factory=dict)):
    """Hủy tiến trình chạy hàng loạt tập đang diễn ra."""
    batch_id = payload.get("batchId")
    cancelled = False

    if batch_id:
        cancelled = BatchRunner.cancel_batch(str(batch_id))
    else:
        # Nếu không truyền batchId, tìm và hủy tất cả batch đang hoạt động
        for bid in list(BatchRunner._active_batches.keys()):
            BatchRunner.cancel_batch(bid)
            cancelled = True

    return {
        "status": "cancelled" if cancelled else "not_found",
        "projectId": project_id,
        "batchId": batch_id,
    }


@router.get("/projects/{project_id}/batch-runs/{batch_id}")
async def get_batch_run_report(project_id: str, batch_id: str):
    """Lấy báo cáo chi tiết một đợt chạy hàng loạt tập."""
    summary = BatchRunner.get_batch_summary(batch_id)
    if summary:
        return summary.model_dump(by_alias=True)

    store = ProjectStore(project_id)
    report_file = store.runs_dir / "_batch_runs" / f"{batch_id}.json"
    if not report_file.is_file():
        raise HTTPException(status_code=404, detail=f"Không tìm thấy đợt chạy batch '{batch_id}'.")

    try:
        return json.loads(report_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đọc báo cáo batch: {e}")


@router.get("/projects/{project_id}/batch-runs")
async def list_batch_runs(project_id: str, limit: int = 20):
    """Liệt kê danh sách các đợt chạy hàng loạt gần đây."""
    store = ProjectStore(project_id)
    report_dir = store.runs_dir / "_batch_runs"
    if not report_dir.is_dir():
        return []

    reports: List[Dict[str, Any]] = []
    files = sorted(report_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)[:limit]
    for f in files:
        try:
            reports.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return reports
