from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import shutil
import tempfile
import uuid
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional

from socnhotv.video.contracts import Platform, RenderJob, RenderRequest
from socnhotv.video.hyperframes_engine import HyperFramesEngine
from socnhotv.video.platforms import get_platform
from socnhotv.workspace.paths import project_path

logger = logging.getLogger("socnhotv.video.queue")


class RenderQueue:
    """Async background worker for video render jobs with concurrency control."""

    def __init__(self, max_parallel: Optional[int] = None):
        self.max_parallel = max_parallel or int(os.environ.get("SOCNHOTV_RENDER_PARALLEL", "2"))
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._queue: Optional[asyncio.Queue[RenderJob]] = None
        self._workers: List[asyncio.Task] = []
        self._cancelled_jobs: set[str] = set()
        self.engine = HyperFramesEngine()

    def _ensure_running(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_parallel)
        if self._queue is None:
            self._queue = asyncio.Queue()
        if not self._workers:
            for i in range(self.max_parallel):
                t = loop.create_task(self._worker_loop(i), name=f"render-worker-{i}")
                self._workers.append(t)

    def _record_event(self, project_id: str, event_type: str, payload: Dict[str, Any]):
        try:
            event_file = project_path(project_id, "runs", "events", "render.jsonl", ensure=True)
            record = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "source": "A",
                "type": event_type,
                "payload": payload,
            }
            with open(event_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"Ghi event thất bại ({event_type}): {e}")

    def _save_job(self, job: RenderJob):
        job_file = project_path(job.project_id, "runs", "render_queue", f"{job.job_id}.json", ensure=True)
        with open(job_file, "w", encoding="utf-8") as f:
            f.write(job.model_dump_json(indent=2))

    def submit(self, req: RenderRequest) -> RenderJob:
        job_id = f"render_{uuid.uuid4().hex[:12]}"
        job = RenderJob(
            job_id=job_id,
            project_id=req.project_id,
            status="queued",
            outputs={},
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._save_job(job)

        # Lưu request đi kèm job để worker đọc
        req_file = project_path(req.project_id, "runs", "render_queue", f"{job_id}.req.json", ensure=True)
        with open(req_file, "w", encoding="utf-8") as f:
            f.write(req.model_dump_json(indent=2))

        self._record_event(req.project_id, "render_queued", {
            "job_id": job_id,
            "template_id": req.template_id,
            "platforms": req.platforms,
            "output_name": req.output_name,
        })

        self._ensure_running()
        if self._queue is not None:
            self._queue.put_nowait(job)
        return job

    def get(self, project_id: str, job_id: str) -> RenderJob:
        job_file = project_path(project_id, "runs", "render_queue", f"{job_id}.json")
        if not job_file.exists():
            raise FileNotFoundError(f"Render job not found: {job_id}")
        with open(job_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return RenderJob(**data)

    def list_jobs(self, project_id: str, status: Optional[str] = None) -> List[RenderJob]:
        queue_dir = project_path(project_id, "runs", "render_queue", ensure=True)
        jobs: List[RenderJob] = []
        for p in queue_dir.glob("render_*.json"):
            if p.name.endswith(".req.json"):
                continue
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                job = RenderJob(**data)
                if status is None or job.status == status:
                    jobs.append(job)
            except Exception:
                continue
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs

    def cancel(self, project_id: str, job_id: str) -> RenderJob:
        self._cancelled_jobs.add(job_id)
        job = self.get(project_id, job_id)
        if job.status in ("queued", "rendering"):
            job.status = "failed"
            job.error = "Cancelled by user"
            self._save_job(job)
            self._record_event(project_id, "render_cancelled", {"job_id": job_id})
        return job

    async def _worker_loop(self, worker_id: int):
        while True:
            try:
                if self._queue is None:
                    await asyncio.sleep(0.5)
                    continue
                job = await self._queue.get()
                if self._semaphore is None:
                    self._semaphore = asyncio.Semaphore(self.max_parallel)

                async with self._semaphore:
                    await self._process_job(job)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Render worker {worker_id} lỗi: {e}", exc_info=True)
                await asyncio.sleep(1.0)

    async def _process_job(self, job: RenderJob):
        if job.job_id in self._cancelled_jobs:
            job.status = "failed"
            job.error = "Cancelled before processing"
            self._save_job(job)
            return

        # Đọc RenderRequest
        req_file = project_path(job.project_id, "runs", "render_queue", f"{job.job_id}.req.json")
        if not req_file.exists():
            job.status = "failed"
            job.error = "Request metadata not found"
            self._save_job(job)
            return

        with open(req_file, "r", encoding="utf-8") as f:
            req_data = json.load(f)
        req = RenderRequest(**req_data)

        job.status = "rendering"
        self._save_job(job)
        self._record_event(req.project_id, "render_started", {"job_id": job.job_id})

        log_path = project_path(req.project_id, "runs", "render_queue", f"{job.job_id}.log", ensure=True)

        try:
            # Chuẩn bị scenes và voiceover
            scenes = req.data.get("scenes") or []
            if not scenes:
                # Tạo 1 scene mặc định từ data
                default_dialogue = req.data.get("dialogue") or req.data.get("hook") or "Chào các bạn!"
                default_img = req.data.get("image") or req.data.get("img") or ""
                scenes = [{"dialogue": default_dialogue, "image": default_img, "durationSec": 4.0}]

            voice_audio = ""
            if req.voice:
                if req.voice.audio_path:
                    v_path = Path(req.voice.audio_path)
                    if not v_path.is_absolute():
                        v_path = project_path(req.project_id, v_path)
                    voice_audio = str(v_path)
                elif req.voice.script:
                    # Tạo audio qua VoiceAdapter nếu có script
                    try:
                        from socnhotv.core.storage.project_store import ProjectStore
                        from socnhotv.core.adapters.voice_adapter import VoiceAdapter
                        store = ProjectStore(req.project_id)
                        v_adapter = VoiceAdapter(store)
                        art = await v_adapter.synthesize(
                            text=req.voice.script,
                            voice_id=req.voice.voice_id or "soc-nho",
                            node_id=f"node_{job.job_id}",
                            run_id=job.job_id,
                        )
                        voice_audio = str(store.project_dir / art.uri)
                    except Exception as e:
                        logger.warning(f"VoiceAdapter synthesize failed: {e}")

            # Render tuần tự cho từng nền tảng
            outputs: Dict[Platform, str] = {}
            for idx, plat in enumerate(req.platforms):
                if job.job_id in self._cancelled_jobs:
                    job.status = "failed"
                    job.error = "Job cancelled during multi-platform render"
                    self._save_job(job)
                    return

                preset = get_platform(plat)
                out_file = project_path(req.project_id, "output", req.output_name, f"{plat}.mp4", ensure=True)

                # Build bundle
                with tempfile.TemporaryDirectory(prefix=f"bundle_{plat}_") as b_tmp:
                    bundle_dir = Path(b_tmp)
                    self.engine.build_from_scenes(
                        scenes=scenes,
                        audio_voiceover_path=voice_audio or str(bundle_dir / "dummy.wav"),
                        platform=preset,
                        target_dir=bundle_dir,
                        title_badge=req.data.get("titleBadge") or req.data.get("title") or "SÓC NHỎ TV",
                        bgm_path=req.data.get("bgm_path"),
                    )

                    # Render
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        None,
                        lambda: self.engine.render(
                            bundle_dir=bundle_dir,
                            out_path=out_file,
                            platform=preset,
                            log_file=log_path,
                        ),
                    )

                rel_output = f"output/{req.output_name}/{plat}.mp4"
                outputs[plat] = rel_output
                job.outputs = outputs
                self._save_job(job)

                self._record_event(req.project_id, "render_platform_done", {
                    "job_id": job.job_id,
                    "platform": plat,
                    "output": rel_output,
                    "progress_pct": round((idx + 1) / len(req.platforms) * 100.0, 1),
                })

            job.status = "done"
            job.outputs = outputs
            self._save_job(job)
            self._record_event(req.project_id, "render_completed", {
                "job_id": job.job_id,
                "outputs": outputs,
            })

            # Tự động tạo draft post nếu auto_draft được kích hoạt
            if req.data.get("auto_draft"):
                try:
                    from socnhotv.social.contracts import create_draft_post
                    primary_media = next(iter(outputs.values()))
                    create_draft_post(
                        project_id=req.project_id,
                        media_path=primary_media,
                        title=req.data.get("title", req.output_name),
                        caption=req.data.get("caption", ""),
                        platforms=[str(p) for p in req.platforms],
                        source_ref=req.source_ref,
                        render_job_id=job.job_id,
                    )
                    self._record_event(req.project_id, "auto_draft_created", {"job_id": job.job_id})
                except Exception as ex:
                    logger.warning(f"Lỗi gọi create_draft_post trong auto_draft: {ex}")

        except Exception as e:
            logger.error(f"Render job {job.job_id} thất bại: {e}", exc_info=True)
            job.status = "failed"
            job.error = str(e)
            self._save_job(job)
            self._record_event(req.project_id, "render_failed", {
                "job_id": job.job_id,
                "error": str(e),
            })


_GLOBAL_QUEUE: Optional[RenderQueue] = None


def get_render_queue() -> RenderQueue:
    global _GLOBAL_QUEUE
    if _GLOBAL_QUEUE is None:
        _GLOBAL_QUEUE = RenderQueue()
    return _GLOBAL_QUEUE
