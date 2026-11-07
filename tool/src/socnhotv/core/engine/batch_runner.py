from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field

from socnhotv.core.contracts.types import (
    Generation,
    Graph,
    GraphRunRequest,
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
from socnhotv.core.models_registry.registry import ModelRegistry
from socnhotv.core.providers import (
    KeyVault,
    MissingApiKey,
    MockProvider,
    ProviderError,
    ProviderRouter,
    SpendCapExceeded,
    SpendGuard,
    redact_secrets,
)
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


class EpisodeRunResult(BaseModel):
    """Kết quả thực thi của một tập phim trong batch run."""

    episode_id: str = Field(..., alias="episodeId")
    run_id: Optional[str] = Field(None, alias="runId")
    is_success: bool = Field(False, alias="isSuccess")
    status: str = Field("pending", alias="status")  # pending, completed, failed, cancelled, blocked_policy
    total_cost_usd: float = Field(0.0, alias="totalCostUsd")
    executed_nodes: List[str] = Field(default_factory=list, alias="executedNodes")
    skipped_nodes: List[str] = Field(default_factory=list, alias="skippedNodes")
    failed_nodes: List[str] = Field(default_factory=list, alias="failedNodes")
    cached_nodes: List[str] = Field(default_factory=list, alias="cachedNodes")
    errors: Dict[str, str] = Field(default_factory=dict, alias="errors")
    output_video_path: Optional[str] = Field(None, alias="outputVideoPath")
    duration_sec: float = Field(0.0, alias="durationSec")

    model_config = ConfigDict(populate_by_name=True)


class BatchRunEstimate(BaseModel):
    """Ước tính chi phí và khả năng thực thi của cả đợt batch qua SpendGuard."""

    total_episodes: int = Field(..., alias="totalEpisodes")
    total_estimated_cost_usd: float = Field(0.0, alias="totalEstimatedCostUsd")
    per_episode_estimates: Dict[str, float] = Field(default_factory=dict, alias="perEpisodeEstimates")
    missing_api_keys: List[str] = Field(default_factory=list, alias="missingApiKeys")
    spend_status: Dict[str, Any] = Field(default_factory=dict, alias="spendStatus")
    can_proceed: bool = Field(True, alias="canProceed")
    requires_confirmation: bool = Field(False, alias="requiresConfirmation")
    reason: Optional[str] = Field(None, alias="reason")

    model_config = ConfigDict(populate_by_name=True)


class BatchEpisodeRunConfig(BaseModel):
    """Cấu hình yêu cầu chạy hàng loạt tập."""

    graph: Optional[Graph] = None
    episode_ids: List[str] = Field(..., alias="episodeIds")
    mock_mode: bool = Field(True, alias="mockMode")
    run_policy: Optional[Dict[str, Any]] = Field(None, alias="runPolicy")
    concurrency: int = Field(1, alias="concurrency")
    confirm_paid_run: bool = Field(False, alias="confirmPaidRun")
    spending_limit_usd: Optional[float] = Field(None, alias="spendingLimitUsd")
    source: str = Field("batch_runner", alias="source")

    model_config = ConfigDict(populate_by_name=True)


class BatchRunSummary(BaseModel):
    """Báo cáo tổng kết đợt chạy hàng loạt tập."""

    batch_id: str = Field(..., alias="batchId")
    project_id: str = Field(..., alias="projectId")
    total_episodes: int = Field(..., alias="totalEpisodes")
    completed_count: int = Field(0, alias="completedCount")
    failed_count: int = Field(0, alias="failedCount")
    cancelled_count: int = Field(0, alias="cancelledCount")
    total_cost_usd: float = Field(0.0, alias="totalCostUsd")
    is_success: bool = Field(False, alias="isSuccess")
    episode_results: List[EpisodeRunResult] = Field(default_factory=list, alias="episodeResults")
    started_at: str = Field(..., alias="startedAt")
    finished_at: str = Field(..., alias="finishedAt")
    duration_sec: float = Field(0.0, alias="durationSec")

    model_config = ConfigDict(populate_by_name=True)


# ---------------------------------------------------------------------------
# Graph Cloning & Cache Helpers
# ---------------------------------------------------------------------------


def clone_graph_for_episode(base_graph: Graph, episode_id: str) -> Graph:
    """Nhân bản đồ thị mẫu cho một tập cụ thể mà KHÔNG làm thay đổi đồ thị gốc.

    - Đổi graph.id thành '{base_graph.id}__{episode_id}' để phân biệt cache snapshot theo tập.
    - Cập nhật tham số node 'script' sang mode 'episode' và gán 'episodeId'.
    - Gán 'episodeId' cho các node liên quan ('cast', 'export', 'hyperframes_render',...).
    - Ở node 'export', điều hướng tên tệp xuất thành '{episode_id}.mp4' và slug thành '{episode_id}' (chuẩn C6).
    """
    raw_data = base_graph.model_dump()
    cloned = Graph.model_validate(raw_data)
    cloned.id = f"{base_graph.id}__{episode_id}"

    for node in cloned.nodes:
        if node.type == "script":
            node.params["mode"] = "episode"
            node.params["episodeId"] = episode_id
        elif node.type in ("cast", "export", "hyperframes_render") or "episodeId" in node.params:
            node.params["episodeId"] = episode_id

        if node.type == "export":
            raw_fn = str(node.params.get("outputFileName") or "").strip()
            if not raw_fn or raw_fn == "final_video.mp4" or raw_fn.endswith(".mp4"):
                node.params["outputFileName"] = f"{episode_id}.mp4"
            node.params["outputSlug"] = episode_id

    return cloned


def get_node_cache_path(runs_dir: Path, base_graph_id: str, episode_id: str, node_id: str) -> Path:
    """Đường dẫn tệp cache cổng ra theo bộ ba (graphId, episodeId, nodeId)."""
    safe = lambda x: re.sub(r"[^A-Za-z0-9_.-]+", "_", str(x or "graph"))[:120]
    subfolder = f"{safe(base_graph_id)}__{safe(episode_id)}"
    return Path(runs_dir) / "_node_outputs" / subfolder / f"{safe(node_id)}.json"


# ---------------------------------------------------------------------------
# BatchRunner Engine
# ---------------------------------------------------------------------------


class BatchRunner:
    """Bộ thực thi chạy hàng loạt tập phim (Batch Episode Runner - Luồng H3):

    - Nhân bản graph mẫu cho từng tập (không sửa graph gốc).
    - Quản lý bộ nhớ đệm (cache) theo (graphId, episodeId, nodeId).
    - Lập kế hoạch và ước tính chi phí tổng trước khi chạy qua SpendGuard.
    - Cách ly lỗi: tập lỗi không làm hỏng tập khác, báo cáo chi tiết từng tập.
    - Hỗ trợ dừng / hủy giữa chừng an toàn.
    """

    _active_batches: Dict[str, asyncio.Event] = {}  # batch_id -> cancel_event
    _active_batch_summaries: Dict[str, BatchRunSummary] = {}

    def __init__(
        self,
        store: ProjectStore,
        model_registry: Optional[ModelRegistry] = None,
        event_callback: Optional[Callable[[SSEEvent], None]] = None,
    ):
        self.store = store
        self.model_registry = model_registry or ModelRegistry()
        self.event_callback = event_callback

    @classmethod
    def cancel_batch(cls, batch_id: str) -> bool:
        """Kích hoạt tín hiệu hủy cho đợt chạy hàng loạt."""
        ev = cls._active_batches.get(batch_id)
        if ev:
            ev.set()
            return True
        return False

    @classmethod
    def get_batch_summary(cls, batch_id: str) -> Optional[BatchRunSummary]:
        return cls._active_batch_summaries.get(batch_id)

    def _emit_event(self, event: SSEEvent) -> None:
        if event.message:
            event.message = redact_secrets(event.message)
        if self.event_callback:
            try:
                self.event_callback(event)
            except Exception:
                pass

    def estimate_batch(
        self,
        base_graph: Graph,
        episode_ids: List[str],
        config: BatchEpisodeRunConfig,
        vault: Optional[KeyVault] = None,
        guard: Optional[SpendGuard] = None,
    ) -> BatchRunEstimate:
        """Lập bảng ước tính tổng chi phí cho N tập qua SpendGuard."""
        vault = vault or KeyVault()
        guard = guard or SpendGuard(self.store.runs_dir)

        total_cost = 0.0
        per_episode: Dict[str, float] = {}
        missing_keys: Set[str] = set()

        for ep_id in episode_ids:
            cloned = clone_graph_for_episode(base_graph, ep_id)
            ep_req = GraphRunRequest(
                project_id=self.store.project_id,
                graph_id=cloned.id,
                mode=RunMode.ALL,
                spending_limit_usd=config.spending_limit_usd,
                mock_mode=bool(config.mock_mode),
                confirm_paid_run=bool(config.confirm_paid_run),
                source=config.source,
            )
            runner = GraphRunner(store=self.store, model_registry=self.model_registry)
            try:
                plan = runner.plan_execution(cloned, ep_req, vault=vault, guard=guard)
                per_episode[ep_id] = plan.total_estimated_cost_usd
                total_cost += plan.total_estimated_cost_usd
                missing_keys.update(plan.missing_api_keys)
            except Exception as e:
                logger.warning(f"Không thể ước tính chi phí tập {ep_id}: {e}")
                per_episode[ep_id] = 0.0

        spend_status = guard.preview(total_cost, source=config.source)
        can_proceed = True
        reason: Optional[str] = None

        if not config.mock_mode:
            if missing_keys:
                can_proceed = False
                reason = f"Thiếu khóa API hợp lệ cho: {', '.join(sorted(missing_keys))}"
            elif not spend_status.get("canProceed", True):
                can_proceed = False
                reason = str(spend_status.get("reason") or "Vượt trần chi tiêu cho phép.")

        requires_conf = bool(not config.mock_mode and total_cost > 0 and not config.confirm_paid_run)

        return BatchRunEstimate(
            total_episodes=len(episode_ids),
            total_estimated_cost_usd=round(total_cost, 4),
            per_episode_estimates=per_episode,
            missing_api_keys=sorted(list(missing_keys)),
            spend_status=spend_status,
            can_proceed=can_proceed,
            requires_confirmation=requires_conf,
            reason=reason,
        )

    def _prepare_cached_nodes(
        self,
        cloned_graph: Graph,
        episode_id: str,
        runner: GraphRunner,
        is_mock: bool,
    ) -> List[str]:
        """Kiểm tra và nạp cache theo (graphId, episodeId, nodeId).

        Trả về danh sách id các node đã có cache hợp lệ để GraphRunner bỏ qua trong RunMode.ALL.
        """
        cached_nodes: List[str] = []
        for node in cloned_graph.nodes:
            snap = runner._load_outputs_snapshot(cloned_graph.id, node, is_mock)
            if snap is not None:
                cached_nodes.append(node.id)
                node.state = NodeState.COMPLETED
                node.is_stale = False
                if not node.pinned_generation_id:
                    gen_id = f"gen_cached_{node.id}"
                    node.pinned_generation_id = gen_id
                    node.generations = [
                        Generation(
                            id=gen_id,
                            node_id=node.id,
                            params=node.params,
                            artifact_id="",
                            cost_usd=0.0,
                            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            is_pinned=True,
                        )
                    ]
        return cached_nodes

    async def run_batch(
        self,
        base_graph: Graph,
        config: BatchEpisodeRunConfig,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> BatchRunSummary:
        """Thực thi chạy hàng loạt các tập phim với cơ chế cách ly lỗi & SpendGuard."""
        batch_id = f"batch_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        t0 = time.time()

        internal_cancel = cancel_event or asyncio.Event()
        self._active_batches[batch_id] = internal_cancel

        vault = KeyVault()
        guard = SpendGuard(self.store.runs_dir)

        # 1. Ước tính trước chi phí của toàn bộ batch
        estimate = self.estimate_batch(
            base_graph=base_graph,
            episode_ids=config.episode_ids,
            config=config,
            vault=vault,
            guard=guard,
        )

        if not config.mock_mode and not estimate.can_proceed:
            raise BudgetExceededError(estimate.reason or "Không thể chạy batch do vi phạm ngân sách hoặc thiếu khóa.")

        if estimate.requires_confirmation:
            raise BudgetExceededError(
                f"Cần xác nhận chi phí ${estimate.total_estimated_cost_usd:.4f} USD trước khi chạy thật "
                f"(truyền confirmPaidRun=true)."
            )

        self._emit_event(
            SSEEvent(
                event_type=SSEEventType.RUN_STARTED,
                run_id=batch_id,
                message=f"Bắt đầu chạy batch {len(config.episode_ids)} tập (Chế độ: {'Mock' if config.mock_mode else 'Live'})",
                timestamp=started_at,
            )
        )

        episode_results: List[EpisodeRunResult] = []
        concurrency = max(1, config.concurrency)
        semaphore = asyncio.Semaphore(concurrency)

        async def _run_single_episode(ep_id: str, index: int) -> EpisodeRunResult:
            ep_start = time.time()
            if internal_cancel.is_set():
                return EpisodeRunResult(
                    episodeId=ep_id,
                    isSuccess=False,
                    status="cancelled",
                    errors={"batch": "Đã hủy theo yêu cầu người dùng trước khi bắt đầu tập."},
                    durationSec=0.0,
                )

            async with semaphore:
                if internal_cancel.is_set():
                    return EpisodeRunResult(
                        episodeId=ep_id,
                        isSuccess=False,
                        status="cancelled",
                        errors={"batch": "Đã hủy theo yêu cầu người dùng."},
                        durationSec=0.0,
                    )

                self._emit_event(
                    SSEEvent(
                        event_type=SSEEventType.NODE_PROGRESS,
                        run_id=batch_id,
                        message=f"[{index + 1}/{len(config.episode_ids)}] Bắt đầu xử lý tập '{ep_id}'",
                        progress=round(index / len(config.episode_ids), 2),
                        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    )
                )

                cloned = clone_graph_for_episode(base_graph, ep_id)
                ep_req = GraphRunRequest(
                    project_id=self.store.project_id,
                    graph_id=cloned.id,
                    mode=RunMode.ALL,
                    spending_limit_usd=config.spending_limit_usd,
                    mock_mode=bool(config.mock_mode),
                    confirm_paid_run=bool(config.confirm_paid_run),
                    source=config.source,
                )

                provider = ProviderRouter(
                    store=self.store,
                    guard=guard,
                    vault=vault,
                    mock_mode=ep_req.mock_mode,
                    fallback_to_mock=False,
                    source=ep_req.source,
                )

                ep_cancel = asyncio.Event()

                def _chain_cancel():
                    if internal_cancel.is_set():
                        ep_cancel.set()

                # Kiểm tra cancel định kỳ
                cancel_watcher = asyncio.create_task(self._watch_cancel(internal_cancel, ep_cancel))

                runner = GraphRunner(
                    store=self.store,
                    model_registry=self.model_registry,
                    event_callback=self.event_callback,
                    provider=provider,
                    cancel_event=ep_cancel,
                )

                # Nạp cache theo (graphId, episodeId, nodeId)
                cached_nodes = self._prepare_cached_nodes(
                    cloned_graph=cloned,
                    episode_id=ep_id,
                    runner=runner,
                    is_mock=bool(config.mock_mode),
                )

                try:
                    summary = await runner.run(cloned, ep_req)
                    cancel_watcher.cancel()

                    output_path: Optional[str] = None
                    expected_file = self.store.project_dir / "output" / ep_id / f"{ep_id}.mp4"
                    if expected_file.is_file():
                        output_path = f"output/{ep_id}/{ep_id}.mp4"

                    status = "completed" if summary.is_success else "failed"
                    if ep_cancel.is_set() or internal_cancel.is_set():
                        status = "cancelled"

                    return EpisodeRunResult(
                        episodeId=ep_id,
                        runId=summary.run_id,
                        isSuccess=summary.is_success,
                        status=status,
                        totalCostUsd=round(summary.total_cost_usd, 4),
                        executedNodes=summary.executed_nodes,
                        skippedNodes=summary.skipped_nodes,
                        failedNodes=summary.failed_nodes,
                        cachedNodes=cached_nodes,
                        errors=summary.errors,
                        outputVideoPath=output_path,
                        durationSec=round(time.time() - ep_start, 2),
                    )
                except Exception as exc:
                    cancel_watcher.cancel()
                    logger.exception(f"Lỗi khi chạy tập '{ep_id}' trong batch: {exc}")
                    err_msg = redact_secrets(str(exc))
                    return EpisodeRunResult(
                        episodeId=ep_id,
                        isSuccess=False,
                        status="failed",
                        totalCostUsd=0.0,
                        errors={"execution": err_msg},
                        durationSec=round(time.time() - ep_start, 2),
                    )

        # Chạy các tập (tuần tự nếu concurrency=1, song song nếu concurrency>1)
        if concurrency == 1:
            for idx, ep_id in enumerate(config.episode_ids):
                res = await _run_single_episode(ep_id, idx)
                episode_results.append(res)
                if internal_cancel.is_set():
                    # Đánh dấu các tập còn lại là cancelled
                    for rem_ep in config.episode_ids[idx + 1 :]:
                        episode_results.append(
                            EpisodeRunResult(
                                episodeId=rem_ep,
                                isSuccess=False,
                                status="cancelled",
                                errors={"batch": "Đã hủy trước khi chạy."},
                                durationSec=0.0,
                            )
                        )
                    break
        else:
            tasks = [_run_single_episode(ep_id, idx) for idx, ep_id in enumerate(config.episode_ids)]
            episode_results = await asyncio.gather(*tasks)

        finished_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        duration = round(time.time() - t0, 2)

        completed_cnt = sum(1 for r in episode_results if r.status == "completed")
        failed_cnt = sum(1 for r in episode_results if r.status == "failed")
        cancelled_cnt = sum(1 for r in episode_results if r.status == "cancelled")
        total_spent = sum(r.total_cost_usd for r in episode_results)
        all_success = completed_cnt == len(episode_results) and len(episode_results) > 0

        summary = BatchRunSummary(
            batchId=batch_id,
            projectId=self.store.project_id,
            totalEpisodes=len(config.episode_ids),
            completedCount=completed_cnt,
            failedCount=failed_cnt,
            cancelledCount=cancelled_cnt,
            totalCostUsd=round(total_spent, 4),
            isSuccess=all_success,
            episodeResults=episode_results,
            startedAt=started_at,
            finishedAt=finished_at,
            durationSec=duration,
        )

        self._active_batch_summaries[batch_id] = summary
        if batch_id in self._active_batches:
            del self._active_batches[batch_id]

        # Lưu bản ghi báo cáo batch vào disk
        self._save_batch_report(batch_id, summary)

        self._emit_event(
            SSEEvent(
                event_type=SSEEventType.RUN_COMPLETED if all_success else SSEEventType.RUN_FAILED,
                run_id=batch_id,
                message=(
                    f"Hoàn thành batch {len(config.episode_ids)} tập: "
                    f"{completed_cnt} thành công, {failed_cnt} lỗi, {cancelled_cnt} đã hủy. "
                    f"Tổng thời gian: {duration}s"
                ),
                progress=1.0,
                timestamp=finished_at,
            )
        )

        return summary

    async def _watch_cancel(self, source: asyncio.Event, target: asyncio.Event) -> None:
        """Theo dõi cancel event của batch để chuyển tiếp sang cancel event của tập."""
        try:
            while not source.is_set():
                await asyncio.sleep(0.2)
            target.set()
        except asyncio.CancelledError:
            pass

    def _save_batch_report(self, batch_id: str, summary: BatchRunSummary) -> None:
        try:
            report_dir = self.store.runs_dir / "_batch_runs"
            report_dir.mkdir(parents=True, exist_ok=True)
            report_file = report_dir / f"{batch_id}.json"
            report_file.write_text(
                json.dumps(summary.model_dump(by_alias=True), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"Không thể ghi báo cáo batch {batch_id}: {e}")
