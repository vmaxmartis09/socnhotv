from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from socnhotv.core.engine.edit_decisions import EditDecisionsManager
from socnhotv.core.storage.project_store import ProjectStore

logger = logging.getLogger("socnhotv.core.api.routes.editor")

router = APIRouter(prefix="/projects/{project_id}/editor", tags=["editor"])


class DecisionRequest(BaseModel):
    action: str = Field(..., description="reorder | update_duration | replace_media | toggle_shot | update_subtitle | reset_shot | reset_all")
    shotId: Optional[str] = Field(None, description="ID của shot cần chỉnh sửa (nếu có)")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tham số đi kèm action")


class RenderRequest(BaseModel):
    forceAll: bool = Field(False, description="Bắt buộc render lại toàn bộ các shot, không dùng cache")
    width: int = Field(1920, description="Chiều rộng video (1920 cho 16:9, 1080 cho 9:16)")
    height: int = Field(1080, description="Chiều cao video (1080 cho 16:9, 1920 cho 9:16)")
    fps: int = Field(30, description="Tốc độ khung hình")


def _get_manager(project_id: str) -> EditDecisionsManager:
    store = ProjectStore(project_id)
    if not store.project_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Dự án '{project_id}' không tồn tại")
    return EditDecisionsManager(store)


@router.get("/{episode_id}")
async def get_editor_timeline(project_id: str, episode_id: str):
    """Lấy danh sách shot và các quyết định chỉnh sửa của tập phim."""
    manager = _get_manager(project_id)
    try:
        script = manager.load_base_script(episode_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy kịch bản cho tập '{episode_id}'")

    decisions = manager.load_decisions(episode_id)
    effective_shots = manager.get_effective_shots(episode_id)
    total_duration = sum(s["durationSec"] for s in effective_shots if s["enabled"])

    # Kiểm tra xem có video thành phẩm sẵn có không
    output_video_path = manager.store.project_dir / "output" / episode_id / f"{episode_id}.mp4"
    has_output = output_video_path.is_file()
    output_video_url = (
        f"/projects/{project_id}/files/output/{episode_id}/{episode_id}.mp4"
        if has_output
        else None
    )
    thumb_url = (
        f"/projects/{project_id}/files/output/{episode_id}/thumb.jpg"
        if (manager.store.project_dir / "output" / episode_id / "thumb.jpg").is_file()
        else None
    )

    return {
        "episodeId": episode_id,
        "title": script.get("title", episode_id),
        "aspect": script.get("aspect", "16:9 Widescreen"),
        "baseDurationSec": script.get("durationSec", 600),
        "effectiveDurationSec": round(total_duration, 3),
        "hasDecisions": decisions is not None,
        "decisions": decisions,
        "shots": effective_shots,
        "outputVideoUrl": output_video_url,
        "thumbUrl": thumb_url,
    }


@router.post("/{episode_id}/decisions")
async def apply_editor_decision(
    project_id: str,
    episode_id: str,
    req: DecisionRequest,
):
    """Áp dụng một quyết định chỉnh sửa thủ công lên timeline và lưu vào edit_decisions.json."""
    manager = _get_manager(project_id)
    try:
        res = manager.apply_decision(
            episode_id=episode_id,
            action=req.action,
            shot_id=req.shotId,
            params=req.params,
        )
        return res
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy tập phim '{episode_id}'")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Lỗi khi lưu quyết định chỉnh sửa: %s", e)
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý: {e}")


@router.post("/{episode_id}/render")
async def trigger_selective_render(
    project_id: str,
    episode_id: str,
    req: RenderRequest = RenderRequest(),
):
    """Thực hiện render vi sai (chỉ render lại các shot bị thay đổi)."""
    manager = _get_manager(project_id)
    try:
        result = manager.selective_rerender(
            episode_id=episode_id,
            force_all=req.forceAll,
            width=req.width,
            height=req.height,
            fps=req.fps,
        )
        # Bổ sung URL phục vụ phát video
        result["videoUrl"] = f"/projects/{project_id}/files/{result['outputVideo']}"
        result["thumbUrl"] = f"/projects/{project_id}/files/output/{episode_id}/thumb.jpg"
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy tập phim '{episode_id}'")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Lỗi trong quá trình selective rerender: %s", e)
        raise HTTPException(status_code=500, detail=f"Lỗi render: {e}")
