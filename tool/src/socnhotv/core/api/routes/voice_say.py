"""Đọc thử một câu bằng giọng THẬT (OmniVoice trên máy, $0) của nhân vật/giọng đã chọn."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException

from socnhotv.core.adapters.voice_adapter import VoiceAdapter
from socnhotv.core.storage.project_store import ProjectStore

router = APIRouter(prefix="/projects/{project_id}/voice", tags=["voice"])

MAX_CHARS = 400


@router.post("/say")
async def say(project_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Body: {text, voiceId, tempo?}. Trả {audioUrl, durationSec}. Khác /voice/preview (chỉ mock)."""
    text = str(payload.get("text") or "").strip()
    voice_id = str(payload.get("voiceId") or "").strip()
    if not text:
        raise HTTPException(400, "Thiếu nội dung cần đọc")
    if not voice_id:
        raise HTTPException(400, "Nhân vật chưa có giọng (voiceId)")
    if len(text) > MAX_CHARS:
        raise HTTPException(400, f"Câu quá dài ({len(text)} ký tự, tối đa {MAX_CHARS})")
    tempo = float(payload.get("tempo") or 1.05)
    store = ProjectStore(project_id)
    try:
        art = await VoiceAdapter(store).synthesize(
            text=text, voice_id=voice_id, tempo=tempo, node_id="voice_say", run_id="say"
        )
    except Exception as e:  # noqa: BLE001 — báo lỗi thật, không trả giọng giả
        raise HTTPException(502, f"Không đọc được bằng giọng '{voice_id}': {e}")
    uri = art.uri.lstrip("/")
    return {
        "voiceId": voice_id,
        "provider": art.provenance.provider,
        "audioUrl": f"/projects/{project_id}/files/{uri}",
        "durationSec": art.meta.duration,
    }

