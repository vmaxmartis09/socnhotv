"""Kho giọng (voice vault): liệt kê, tạo giọng từ mp3/mp4, nghe mẫu, gắn vào nhân vật."""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from socnhotv.core.storage.project_store import get_repo_root

router = APIRouter(prefix="/voices", tags=["voices"])

ALLOWED_EXT = {".mp3", ".mp4", ".wav", ".m4a", ".mov", ".webm"}
MAX_UPLOAD = 200 * 1024 * 1024
JOBS: Dict[str, Dict[str, Any]] = {}


def _vault() -> Path:
    return get_repo_root() / "data" / "shared" / "voice_vault"


def _valid_id(voice_id: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,40}", voice_id):
        raise HTTPException(400, "Mã giọng chỉ gồm chữ thường, số, '-' hoặc '_' (2 đến 41 ký tự)")
    return voice_id


def _used_by(voice_id: str) -> list[Dict[str, str]]:
    out = []
    projects = get_repo_root() / "data" / "projects"
    if projects.exists():
        for pj in projects.glob("*/project.json"):
            data = json.loads(pj.read_text(encoding="utf-8"))
            for cid, c in data.get("characters", {}).items():
                if c.get("voice_id") == voice_id:
                    out.append({"projectId": data["id"], "characterId": cid, "name": c.get("name", cid)})
    return out


def _view(d: Path) -> Dict[str, Any]:
    p = json.loads((d / "profile.json").read_text(encoding="utf-8")) if (d / "profile.json").exists() else {}
    sample = p.get("files", {}).get("cloned_sample", "cloned_default_sample.mp3")
    return {
        "id": d.name,
        "name": p.get("speaker_name", d.name),
        "dialect": p.get("dialect", ""),
        "engine": p.get("engine", ""),
        "durationSec": p.get("duration"),
        "transcript": p.get("transcript", ""),
        "createdAt": p.get("created_at", ""),
        "hasSample": (d / sample).exists(),
        "sampleUrl": f"/voices/{d.name}/sample" if (d / sample).exists() else None,
        "usedBy": _used_by(d.name),
    }


@router.get("")
async def list_voices():
    v = _vault()
    if not v.exists():
        return []
    return [_view(d) for d in sorted(v.iterdir()) if d.is_dir() and (d / "profile.json").exists()]


@router.get("/{voice_id}/sample")
async def voice_sample(voice_id: str):
    d = _vault() / _valid_id(voice_id)
    view = _view(d) if (d / "profile.json").exists() else None
    if not view or not view["hasSample"]:
        raise HTTPException(404, "Chưa có mẫu nghe thử")
    sample = json.loads((d / "profile.json").read_text(encoding="utf-8")).get("files", {}).get("cloned_sample", "cloned_default_sample.mp3")
    return FileResponse(d / sample)


async def _run_clone(job_id: str, src: Path, voice_id: str, dialect: str, transcript: str | None) -> None:
    job = JOBS[job_id]
    script = get_repo_root() / "scripts" / "voice" / "voice_studio.py"
    cmd = [sys.executable, str(script), "clone", "--input", str(src), "--name", voice_id, "--dialect", dialect]
    if transcript:
        cmd += ["--text", transcript]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, cwd=str(get_repo_root())
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=1800)
        tail = out.decode("utf-8", "ignore")[-600:]
        if proc.returncode == 0 and (_vault() / voice_id / "profile.json").exists():
            job.update(status="done", voice=_view(_vault() / voice_id))
        else:
            job.update(status="failed", error=tail or f"mã thoát {proc.returncode}")
    except Exception as e:  # noqa: BLE001
        job.update(status="failed", error=str(e)[:600])
    finally:
        src.unlink(missing_ok=True)
        job["finishedAt"] = time.time()


@router.post("/clone")
async def clone_voice(request: Request, name: str, filename: str, consent: bool = False, dialect: str = "south", transcript: str | None = None, overwrite: bool = False):
    """Tạo giọng từ tệp mp3/mp4 (gửi nội dung tệp làm body, tên tệp ở ?filename=).

    consent=true bắt buộc: chỉ nhân bản giọng của chính bạn hoặc người đã đồng ý (giọng trẻ em cần phụ huynh đồng ý).
    """
    if not consent:
        raise HTTPException(400, "Cần xác nhận quyền: chỉ nhân bản giọng của chính bạn hoặc người đã đồng ý (giọng trẻ em cần phụ huynh đồng ý).")
    voice_id = _valid_id(name)
    if dialect not in ("north", "south", "central"):
        raise HTTPException(400, "dialect phải là north, south hoặc central")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Chỉ nhận {sorted(ALLOWED_EXT)}")
    if (_vault() / voice_id).exists() and not overwrite:
        raise HTTPException(409, f"Giọng '{voice_id}' đã có trong kho; dùng tên khác hoặc overwrite=true")
    if voice_id == "soc-nho" and not overwrite:
        raise HTTPException(409, "Không ghi đè giọng chuẩn soc-nho")

    tmp_dir = get_repo_root() / "data" / "shared" / "voice_vault" / ".uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4().hex[:10]
    src = tmp_dir / f"{job_id}{ext}"
    size = 0
    with src.open("wb") as f:
        async for chunk in request.stream():
            size += len(chunk)
            if size > MAX_UPLOAD:
                f.close()
                src.unlink(missing_ok=True)
                raise HTTPException(413, "Tệp quá lớn (tối đa 200 MB)")
            f.write(chunk)
    if size == 0:
        src.unlink(missing_ok=True)
        raise HTTPException(400, "Tệp rỗng")

    JOBS[job_id] = {"id": job_id, "voiceId": voice_id, "status": "running", "startedAt": time.time()}
    asyncio.create_task(_run_clone(job_id, src, voice_id, dialect, transcript))
    return JOBS[job_id]


@router.get("/jobs/{job_id}")
async def clone_job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "Không có việc này")
    return JOBS[job_id]
