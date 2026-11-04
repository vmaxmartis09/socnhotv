"""Sources API routes plugin.

Cung cấp các API quản lý nguồn nội dung đa nền tảng (Douyin, TikTok, YouTube, File local).
"""
from __future__ import annotations

import os
import shutil
import tempfile
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from socnhotv.video.contracts import Platform
from socnhotv.sources.jobs import enqueue_ingest, get_job_status
from socnhotv.sources.local import ingest_local_file
from socnhotv.sources.models import IngestRequest, RightsType, SourceItem, UpdateRightsRequest
from socnhotv.sources.scenes import detect_and_save_scenes
from socnhotv.sources.service import (
    delete_source_to_trash,
    get_source,
    get_source_file_path,
    list_sources,
    update_source_rights,
)

router = APIRouter(tags=["sources"])


@router.get("/sources/_ping")
async def ping_sources():
    return {"status": "ok", "module": "sources"}


@router.post("/projects/{project_id}/sources")
async def ingest_sources_api(
    project_id: str,
    req: Optional[IngestRequest] = None,
    file: Optional[UploadFile] = File(None),
    rights: RightsType = Form("reference_only"),
    rights_note: str = Form(""),
):
    """Ingest sources: either via URLs JSON or multipart file upload."""
    if file and file.filename:
        # Handle file upload
        suffix = os.path.splitext(file.filename)[1] or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        try:
            item = ingest_local_file(
                project_id=project_id,
                source_file_path=tmp_path,
                title=file.filename,
                rights="owned" if rights == "reference_only" else rights,
                rights_note=rights_note or f"Tải lên trực tiếp: {file.filename}",
            )
            # Trigger scenes automatically
            try:
                detect_and_save_scenes(project_id, item.id)
            except Exception:
                pass
            return {"type": "file", "source": item.model_dump()}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    if req and req.urls:
        job_ids = enqueue_ingest(
            project_id=project_id,
            urls=req.urls,
            rights=req.rights,
            rights_note=req.rights_note,
        )
        return {"type": "jobs", "job_ids": job_ids}

    raise HTTPException(status_code=400, detail="Vui lòng cung cấp danh sách URLs hoặc tải lên tập tin video.")


@router.get("/projects/{project_id}/sources")
async def list_sources_api(
    project_id: str,
    platform: Optional[str] = Query(None),
    rights: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
):
    items = list_sources(project_id, platform=platform, rights=rights, q=q)
    return [i.model_dump() for i in items]


@router.get("/projects/{project_id}/sources/jobs/{job_id}")
async def get_job_status_api(project_id: str, job_id: str):
    job = get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy tiến trình tải.")
    return job


@router.get("/projects/{project_id}/sources/{source_id}")
async def get_source_api(project_id: str, source_id: str):
    item = get_source(project_id, source_id)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy nguồn nội dung.")
    return item.model_dump()


@router.patch("/projects/{project_id}/sources/{source_id}")
async def update_source_rights_api(
    project_id: str,
    source_id: str,
    req: UpdateRightsRequest,
):
    try:
        updated = update_source_rights(
            project_id=project_id,
            source_id=source_id,
            new_rights=req.rights,
            note=req.rights_note,
            confirm_rights=req.confirm_rights,
        )
        return updated.model_dump()
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Không tìm thấy nguồn nội dung.")


@router.delete("/projects/{project_id}/sources/{source_id}")
async def delete_source_api(project_id: str, source_id: str):
    ok = delete_source_to_trash(project_id, source_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy nguồn nội dung để chuyển vào thùng rác.")
    return {"status": "ok", "message": f"Nguồn {source_id} đã chuyển vào thùng rác raw/_trash/"}


@router.get("/projects/{project_id}/sources/{source_id}/file/{file_name:path}")
async def get_source_file_api(project_id: str, source_id: str, file_name: str):
    path = get_source_file_path(project_id, source_id, file_name)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail=f"Không tìm thấy tập tin: {file_name}")

    media_type = "application/octet-stream"
    if path.suffix == ".mp4":
        media_type = "video/mp4"
    elif path.suffix in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif path.suffix == ".png":
        media_type = "image/png"
    elif path.suffix == ".wav":
        media_type = "audio/wav"
    elif path.suffix == ".vtt":
        media_type = "text/vtt"
    elif path.suffix == ".json":
        media_type = "application/json"

    return FileResponse(path, media_type=media_type)


@router.post("/projects/{project_id}/sources/{source_id}/scenes")
async def detect_scenes_api(project_id: str, source_id: str):
    try:
        scenes = detect_and_save_scenes(project_id, source_id)
        return [s.model_dump() for s in scenes]
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tách cảnh: {e}")


class LocalizeRequest(BaseModel):
    mode: Literal["R", "L"] = "R"
    style: Literal["faithful", "hook_boost", "character"] = "faithful"
    voice_id: str = "soc-nho"
    platforms: List[Platform] = ["tiktok", "reels", "shorts"]
    template_id: Optional[str] = None
    auto_draft: bool = True


@router.post("/projects/{project_id}/sources/{source_id}/localize")
async def localize_source_api(
    project_id: str,
    source_id: str,
    req: LocalizeRequest,
):
    from socnhotv.sources.localize_pipeline import run_localize_pipeline
    try:
        summary = await run_localize_pipeline(
            project_id=project_id,
            source_id=source_id,
            mode=req.mode,
            style=req.style,
            voice_id=req.voice_id,
            platforms=req.platforms,
            template_id=req.template_id,
            auto_draft=req.auto_draft,
        )
        return summary
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi bản địa hoá: {e}")


@router.get("/projects/{project_id}/sources/{source_id}/localize/{job_id}")
async def get_localize_job_api(project_id: str, source_id: str, job_id: str):
    from socnhotv.workspace import project_path
    from socnhotv.video.contracts import get_render
    try:
        render_job = get_render(project_id, job_id)
        return render_job.model_dump()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/projects/{project_id}/sources/{source_id}/transcript")
async def get_transcript_api(
    project_id: str,
    source_id: str,
    lang: Literal["orig", "vi"] = "vi",
):
    from socnhotv.workspace import project_path
    fpath = project_path(project_id, "raw", source_id, f"transcript.{lang}.json")
    if not fpath.exists():
        raise HTTPException(status_code=404, detail=f"Chưa có transcript {lang}")
    import json
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)


@router.put("/projects/{project_id}/sources/{source_id}/transcript")
async def update_transcript_api(
    project_id: str,
    source_id: str,
    segments: List[Dict[str, Any]],
    lang: Literal["orig", "vi"] = "vi",
):
    from socnhotv.workspace import project_path
    import json
    fpath = project_path(project_id, "raw", source_id, f"transcript.{lang}.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
    return {"status": "ok", "saved_segments": len(segments)}


@router.get("/projects/{project_id}/sources/{source_id}/script")
async def get_script_api(
    project_id: str,
    source_id: str,
    style: str = "faithful",
):
    from socnhotv.workspace import project_path
    import json
    fpath = project_path(project_id, "content", "scripts", f"{source_id}.{style}.json")
    if not fpath.exists():
        fpath = project_path(project_id, "raw", source_id, f"script.{style}.json")
    if not fpath.exists():
        raise HTTPException(status_code=404, detail="Chưa có kịch bản cho style này.")
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)


@router.put("/projects/{project_id}/sources/{source_id}/script")
async def update_script_api(
    project_id: str,
    source_id: str,
    lines: List[Dict[str, Any]],
    style: str = "faithful",
):
    from socnhotv.workspace import project_path
    import json
    fpath = project_path(project_id, "content", "scripts", f"{source_id}.{style}.json", ensure=True)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(lines, f, ensure_ascii=False, indent=2)
    return {"status": "ok", "saved_lines": len(lines)}
