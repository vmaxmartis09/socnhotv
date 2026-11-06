from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from socnhotv.sources.asr import run_asr
from socnhotv.sources.models import PlatformType, SourceItem
from socnhotv.sources.revoice import run_revoice
from socnhotv.sources.rewrite import RewriteStyle, run_rewrite
from socnhotv.sources.service import get_source
from socnhotv.sources.translate import run_translation
from socnhotv.video.contracts import Platform, RenderJob, RenderRequest, VoiceSpec, submit_render
from socnhotv.workspace import project_path

logger = logging.getLogger(__name__)

LocalizeMode = Literal["R", "L"]


async def run_localize_pipeline(
    project_id: str,
    source_id: str,
    mode: LocalizeMode = "R",
    style: RewriteStyle = "faithful",
    voice_id: str = "soc-nho",
    platforms: Optional[List[Platform]] = None,
    template_id: Optional[str] = None,
    auto_draft: bool = True,
) -> Dict[str, Any]:
    """Execute complete end-to-end Douyin/TikTok localization pipeline."""
    target_platforms: List[Platform] = platforms or ["tiktok", "reels", "shorts"]
    source = get_source(project_id, source_id)
    if not source:
        raise FileNotFoundError(f"Source item not found: {source_id}")

    # STRICT COPYRIGHT GUARD: Mode L requires rights != reference_only
    if mode == "L" and source.rights == "reference_only":
        raise ValueError(
            "Chế độ Localize (Mode L) giữ lại video gốc, yêu cầu rights khác 'reference_only'. "
            "Nguồn này đang là 'reference_only'. Vui lòng nâng cấp bản quyền hoặc chọn Mode R (Remake) "
            "để tạo video mới hoàn toàn an toàn."
        )

    # Step 1: ASR Transcription
    source_dir = project_path(project_id, "raw", source_id)
    orig_transcript = source_dir / "transcript.orig.json"
    if not orig_transcript.exists():
        run_asr(project_id, source_id)

    # Step 2: Translation
    vi_transcript = source_dir / "transcript.vi.json"
    if not vi_transcript.exists():
        run_translation(project_id, source_id)

    # Step 3: Rewrite
    run_rewrite(project_id, source_id, style=style)

    # Step 4: Revoice TTS & -14 LUFS Mastering
    voice_path = await run_revoice(project_id, source_id, voice_id=voice_id, style=style)

    # Step 5: Render Request via socnhotv.video.contracts
    tmpl = template_id or ("localized-reup-v1" if mode == "L" else "story-cartoon-v1")
    render_req = RenderRequest(
        project_id=project_id,
        template_id=tmpl,
        platforms=target_platforms,
        data={
            "mode": mode,
            "source_id": source_id,
            "title": source.title or f"Video {source_id}",
            "source_author": f"@{source.author}" if source.author else "@source",
            "character_reaction": "Sóc Nhỏ cùng các bạn theo dõi nhé!",
            "story_title": source.title or f"Video {source_id}",
            "video_path": f"raw/{source_id}/video.mp4" if mode == "L" else None,
            "voice_path": f"raw/{source_id}/voice.vi.mp3",
            "script_path": f"content/scripts/{source_id}.{style}.json",
            "style": style,
        },
        voice=VoiceSpec(voice_id=voice_id, audio_path=f"raw/{source_id}/voice.vi.mp3"),
        source_ref=source_id,
        output_name=f"loc_{source_id}_{style}",
    )

    render_job = submit_render(render_req)

    # Save pipeline report in raw/<source_id>/localize_job.json
    job_summary = {
        "source_id": source_id,
        "project_id": project_id,
        "mode": mode,
        "style": style,
        "voice_id": voice_id,
        "platforms": target_platforms,
        "template_id": tmpl,
        "render_job_id": render_job.job_id,
        "voice_path": str(voice_path),
        "status": render_job.status,
    }
    with open(source_dir / "localize_job.json", "w", encoding="utf-8") as f:
        json.dump(job_summary, f, indent=2)

    return job_summary
