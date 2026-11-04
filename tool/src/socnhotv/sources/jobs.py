from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from socnhotv.sources.downloader import download_source
from socnhotv.sources.models import RightsType, SourceItem
from socnhotv.sources.scenes import detect_and_save_scenes
from socnhotv.workspace import project_path

logger = logging.getLogger(__name__)

# In-memory job state tracking
_jobs: Dict[str, Dict[str, Any]] = {}
_queue: Optional[asyncio.Queue] = None
_workers_started = False
MAX_CONCURRENT_WORKERS = 3


def emit_source_event(project_id: str, event_type: str, payload: Dict[str, Any]) -> None:
    """Append event to data/projects/<id>/runs/events/sources.jsonl."""
    try:
        events_file = project_path(project_id, "runs", "events", "sources.jsonl", ensure=True)
        rec = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": "B",
            "type": event_type,
            "payload": payload,
        }
        with open(events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning("Failed to emit source event: %s", e)


async def _worker_loop(worker_id: int):
    global _queue
    assert _queue is not None
    while True:
        task = await _queue.get()
        job_id = task["job_id"]
        project_id = task["project_id"]
        url = task["url"]
        rights = task["rights"]
        rights_note = task["rights_note"]

        _jobs[job_id]["status"] = "downloading"
        _jobs[job_id]["started_at"] = datetime.now(timezone.utc).isoformat()
        emit_source_event(project_id, "source_download_start", {"job_id": job_id, "url": url})

        try:
            # Run download in thread executor to not block asyncio loop
            loop = asyncio.get_running_loop()
            item = await loop.run_in_executor(
                None,
                download_source,
                project_id,
                url,
                rights,
                rights_note,
            )

            if item.status == "ready":
                _jobs[job_id]["status"] = "processing_scenes"
                try:
                    await loop.run_in_executor(None, detect_and_save_scenes, project_id, item.id)
                except Exception as sc_err:
                    logger.warning("Auto scene detection error: %s", sc_err)

                _jobs[job_id]["status"] = "ready"
                _jobs[job_id]["source_id"] = item.id
                _jobs[job_id]["finished_at"] = datetime.now(timezone.utc).isoformat()
                emit_source_event(project_id, "source_ready", {"job_id": job_id, "source_id": item.id})
            else:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["error"] = item.error
                _jobs[job_id]["finished_at"] = datetime.now(timezone.utc).isoformat()
                emit_source_event(project_id, "source_failed", {"job_id": job_id, "error": item.error})

        except Exception as e:
            logger.exception("Ingest job %s failed: %s", job_id, e)
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["error"] = str(e)
            _jobs[job_id]["finished_at"] = datetime.now(timezone.utc).isoformat()
            emit_source_event(project_id, "source_failed", {"job_id": job_id, "error": str(e)})
        finally:
            _queue.task_done()


def ensure_workers():
    global _queue, _workers_started
    if _queue is None:
        _queue = asyncio.Queue()
    if not _workers_started:
        for i in range(MAX_CONCURRENT_WORKERS):
            asyncio.create_task(_worker_loop(i + 1))
        _workers_started = True


def enqueue_ingest(
    project_id: str,
    urls: List[str],
    rights: RightsType = "reference_only",
    rights_note: str = "",
) -> List[str]:
    """Enqueue multiple URLs for downloading. Returns list of job_ids."""
    ensure_workers()
    assert _queue is not None

    job_ids = []
    for url in urls:
        url_clean = url.strip()
        if not url_clean:
            continue
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        _jobs[job_id] = {
            "job_id": job_id,
            "project_id": project_id,
            "url": url_clean,
            "rights": rights,
            "rights_note": rights_note,
            "status": "queued",
            "source_id": None,
            "error": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _queue.put_nowait({
            "job_id": job_id,
            "project_id": project_id,
            "url": url_clean,
            "rights": rights,
            "rights_note": rights_note,
        })
        job_ids.append(job_id)
        emit_source_event(project_id, "source_enqueued", {"job_id": job_id, "url": url_clean})

    return job_ids


def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    return _jobs.get(job_id)


def list_jobs(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    if project_id:
        return [j for j in _jobs.values() if j.get("project_id") == project_id]
    return list(_jobs.values())
