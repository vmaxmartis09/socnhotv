"""Hội thoại nhiều nhân vật (E5 bước 5–6).

- Chức năng "Nói" của node Nhân vật (`SpeakCapability`): lọc câu thoại của chính nhân vật từ cổng `lines`
  của Kịch bản, đọc TỪNG CÂU bằng giọng của nhân vật, cache theo từng câu (sửa 1 câu chỉ đọc lại 1 câu).
  Ra cổng `voice` (kiểu `voice_clips`): danh sách câu đã đọc, CHƯA đặt mốc thời gian.
- Bộ dựng (`hyperframes_render`) gom clip của mọi nhân vật (cổng `voice_clips`, nhận nhiều dây), xếp theo thứ tự
  câu trong kịch bản (`build_timeline`), trộn thành 1 track (`mix_timeline`) và làm phụ đề từ mốc thật
  (`timeline_to_srt`). Mốc do bộ dựng tính để 2 nhân vật nói cùng shot không chồng tiếng.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from socnhotv.core.contracts.types import (
    Artifact,
    CapabilityDefinition,
    NodeInstance,
    PortDefinition,
    PortType,
    SSEEvent,
    SSEEventType,
    NodeState,
)
from socnhotv.core.engine.character_profile import name_tokens
from socnhotv.core.nodes.capabilities import CapabilityRuntime, register_capability

if TYPE_CHECKING:  # pragma: no cover
    from socnhotv.core.engine.graph_runner import GraphRunner

logger = logging.getLogger(__name__)

SPEAK = CapabilityDefinition(
    name="speak",
    display_name="Nói",
    description="Nhân vật tự đọc lời thoại của mình trong kịch bản bằng giọng của nhân vật",
    input_ports=[
        PortDefinition(
            name="lines",
            port_type=PortType.DIALOGUE,
            description="Lời thoại từ Kịch bản (cổng lines): nhân vật tự lọc câu của mình",
            required=False,
        ),
        PortDefinition(
            name="text",
            port_type=PortType.TEXT,
            description="Hoặc 1 đoạn văn bản để nhân vật đọc (khi không có lines)",
            required=False,
        ),
    ],
    output_ports=[
        PortDefinition(
            name="voice",
            port_type=PortType.VOICE_CLIPS,
            description="Các câu đã đọc (từng clip) — nối vào cổng voice_clips của bộ dựng",
        ),
    ],
    default_params={"voiceId": "", "tempo": None, "concurrency": 2},
)


# ------------------------------------------------------------------ lọc câu của nhân vật
def lines_for_character(lines: Any, char_id: str, aliases: List[str]) -> List[Dict[str, Any]]:
    """Câu của nhân vật: khớp characterId; câu chưa ghép nhân vật thì khớp tên người nói với bí danh."""
    out: List[Dict[str, Any]] = []
    alias_tokens = [t for t in (name_tokens(a) for a in aliases or []) if t]
    for ln in lines or []:
        if not isinstance(ln, dict) or not str(ln.get("text") or "").strip():
            continue
        cid = ln.get("characterId")
        if cid:
            if cid == char_id:
                out.append(ln)
            continue
        sp = name_tokens(str(ln.get("speaker") or ""))
        if sp and any(a <= sp and len(a) * 2 >= len(sp) for a in alias_tokens):
            out.append(ln)
    return out


def _clip_duration(art: Artifact, project_dir: Path) -> float:
    dur = getattr(getattr(art, "meta", None), "duration", None)
    if isinstance(dur, (int, float)) and dur > 0:
        return float(dur)
    try:
        import soundfile as sf

        info = sf.info(str(project_dir / art.uri))
        return float(info.frames) / float(info.samplerate or 1)
    except Exception:
        pass
    try:
        from socnhotv.video.hyperframes_engine import HyperFramesEngine

        return float(HyperFramesEngine().get_audio_duration(project_dir / art.uri))
    except Exception:
        return 0.0


def definition_text(node) -> str:
    sp = (node.params or {}).get("speak")
    return str(sp.get("text") or "").strip() if isinstance(sp, dict) else ""


class SpeakCapability(CapabilityRuntime):
    def cache_inputs(self, node, resolved_inputs, definition, core_outputs=None):
        char = (core_outputs or {}).get("character") or {}
        cid = str(node.params.get("characterId") or char.get("characterId") or "")
        lines = resolved_inputs.get("lines")
        mine = lines_for_character(lines, cid, char.get("aliases") or []) if isinstance(lines, list) else []
        return {
            "lines": [{"id": l.get("id"), "text": l.get("text"), "order": l.get("order"), "sceneIndex": l.get("sceneIndex")} for l in mine],
            "text": (str(definition_text(node)) or resolved_inputs.get("text")) if not mine else None,
            "voiceId": char.get("voiceId"),
            "tempo": char.get("defaultTempo"),
        }

    async def run(self, runner, node, params, resolved_inputs, core_outputs, run_id, is_mock):
        char = core_outputs.get("character") or {}
        cid = str(char.get("characterId") or node.params.get("characterId") or "")
        name = str(char.get("name") or cid)
        lines = resolved_inputs.get("lines")
        mine = lines_for_character(lines, cid, char.get("aliases") or []) if isinstance(lines, list) else []
        if not mine:
            # Lời đọc tuỳ chỉnh gõ ngay trên node (speak.text) được ưu tiên hơn văn bản nối vào cổng text
            text = definition_text(node) or str(resolved_inputs.get("text") or "").strip()
            if text and not (isinstance(lines, list) and lines):
                mine = [{"id": f"{node.id}-1", "order": 0, "speaker": name, "characterId": cid, "text": text}]
        if not mine:
            runner._emit_event(_progress(run_id, node.id, 0.9, f"{name}: không có câu thoại nào trong kịch bản"))
            return {"voice": []}, 0.0

        voice_id = str(params.get("voiceId") or char.get("voiceId") or "").strip()
        if not voice_id:
            raise ValueError(
                f"Chức năng Nói của '{name}': "
                + str(char.get("voiceMessage") or "nhân vật chưa có giọng dùng được trong kho giọng.")
            )
        tempo = float(params.get("tempo") or char.get("defaultTempo") or 1.10)
        conc = max(1, min(4, int(params.get("concurrency") or 2)))
        sem = asyncio.Semaphore(conc)
        total = len(mine)
        done = {"n": 0}
        clips: List[Optional[Dict[str, Any]]] = [None] * total

        async def _one(i: int, ln: Dict[str, Any]) -> None:
            async with sem:
                text = str(ln.get("text") or "").strip()
                art = runner._voice_line_cache_get(voice_id, text, tempo, is_mock)
                if art is None:
                    art = await runner._synthesize_line(text, voice_id, tempo, node.id, run_id, is_mock)
                    runner._voice_line_cache_put(voice_id, text, tempo, is_mock, art)
                done["n"] += 1
                runner._emit_event(
                    _progress(run_id, node.id, 0.3 + 0.6 * done["n"] / total, f"{name} đọc {done['n']}/{total}")
                )
                clips[i] = {
                    "lineId": ln.get("id"),
                    "order": ln.get("order", i),
                    "characterId": cid,
                    "speaker": ln.get("speaker") or name,
                    "text": text,
                    "audio": art,
                    "durationSec": round(_clip_duration(art, runner.store.project_dir), 3),
                    "voiceId": voice_id,
                    "shotId": ln.get("shotId"),
                    "sceneIndex": ln.get("sceneIndex"),
                    "startSec": ln.get("startSec"),
                    "endSec": ln.get("endSec"),
                }

        await asyncio.gather(*(_one(i, ln) for i, ln in enumerate(mine)))
        return {"voice": [c for c in clips if c]}, 0.0


def _progress(run_id: str, node_id: str, progress: float, message: str) -> SSEEvent:
    return SSEEvent(
        event_type=SSEEventType.NODE_PROGRESS,
        run_id=run_id,
        node_id=node_id,
        state=NodeState.RUNNING,
        progress=round(min(0.95, max(0.0, progress)), 3),
        message=message,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


def register_speak_capability() -> None:
    register_capability("character", SPEAK, SpeakCapability())


# ------------------------------------------------------------------ dòng thời gian (bộ dựng)
def build_timeline(
    scenes: List[Dict[str, Any]],
    clips: List[Dict[str, Any]],
    gap_sec: float = 0.35,
    lead_sec: float = 0.3,
    tail_sec: float = 0.6,
    timing: str = "script",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], float]:
    """Đặt mốc từng câu và độ dài từng cảnh.

    - Câu xếp theo `order` (thứ tự trong kịch bản), trong cùng cảnh nói nối tiếp nhau cách `gap_sec`.
    - timing="script": cảnh giữ độ dài dự kiến của kịch bản, thoại dài hơn thì kéo dài cảnh.
      timing="voice": cảnh dài vừa đủ thoại (tối thiểu 2 giây) — dùng xem nhanh.
    - Câu không thuộc cảnh nào (sceneIndex trống/ngoài phạm vi) nối vào cuối.
    Trả (timeline, cảnh đã chỉnh độ dài/mốc, tổng thời lượng).
    """
    ordered = sorted(
        [c for c in clips if isinstance(c, dict) and c.get("audio") is not None],
        key=lambda c: (float(c.get("order") if c.get("order") is not None else 1e9)),
    )
    by_scene: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    orphans: List[Dict[str, Any]] = []
    for c in ordered:
        si = c.get("sceneIndex")
        if isinstance(si, int) and 0 <= si < len(scenes):
            by_scene[si].append(c)
        else:
            orphans.append(c)

    timeline: List[Dict[str, Any]] = []
    new_scenes: List[Dict[str, Any]] = []
    cursor = 0.0

    def _place(c: Dict[str, Any], t: float) -> float:
        dur = max(0.05, float(c.get("durationSec") or 0.0))
        timeline.append(
            {
                "lineId": c.get("lineId"),
                "order": c.get("order"),
                "characterId": c.get("characterId"),
                "speaker": c.get("speaker"),
                "text": c.get("text"),
                "audio": c.get("audio"),
                "sceneIndex": c.get("sceneIndex"),
                "audioStartSec": round(t, 3),
                "audioEndSec": round(t + dur, 3),
            }
        )
        return t + dur

    for i, sc in enumerate(scenes):
        sc = dict(sc) if isinstance(sc, dict) else {}
        start = cursor
        t = start + lead_sec
        last_end = None
        for c in by_scene.get(i, []):
            last_end = _place(c, t)
            t = last_end + gap_sec
        speech_end = (last_end + tail_sec) if last_end is not None else start
        planned = float(sc.get("durationSec") or sc.get("duration") or 0.0)
        if timing == "voice":
            end = max(speech_end, start + 2.0)
        else:
            end = max(speech_end, start + (planned if planned > 0 else 3.0))
        sc["durationSec"] = round(end - start, 3)
        sc["startSec"] = round(start, 3)
        new_scenes.append(sc)
        cursor = end

    if orphans:
        t = cursor + lead_sec
        last_end = cursor
        for c in orphans:
            last_end = _place(c, t)
            t = last_end + gap_sec
        end = last_end + tail_sec
        if new_scenes:
            new_scenes[-1]["durationSec"] = round(new_scenes[-1]["durationSec"] + (end - cursor), 3)
        cursor = end
    return timeline, new_scenes, round(cursor, 3)


def mix_timeline(
    timeline: List[Dict[str, Any]], total_sec: float, project_dir: Path, out_path: Path, ffmpeg: str
) -> Path:
    """Trộn các câu đúng mốc thành 1 track MP3 192kbps 44.1kHz dài đúng total_sec (khoảng lặng giữa câu)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    total = max(0.5, float(total_sec))
    if not timeline:
        cmd = [ffmpeg, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{total:.3f}",
               "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "44100", str(out_path)]
    else:
        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
        parts = []
        for i, item in enumerate(timeline):
            cmd += ["-i", str(project_dir / item["audio"].uri)]
            ms = int(round(float(item["audioStartSec"]) * 1000))
            parts.append(
                f"[{i}:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,adelay={ms}|{ms}[a{i}]"
            )
        mix_in = "".join(f"[a{i}]" for i in range(len(timeline)))
        parts.append(
            f"{mix_in}amix=inputs={len(timeline)}:normalize=0:duration=longest,"
            f"apad=whole_dur={total:.3f},atrim=0:{total:.3f}[out]"
        )
        cmd += ["-filter_complex", ";".join(parts), "-map", "[out]",
                "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "44100", str(out_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0 or not out_path.is_file():
        raise RuntimeError(f"Trộn hội thoại lỗi (ffmpeg {proc.returncode}): {(proc.stderr or '')[-400:]}")
    return out_path


def _srt_time(t: float) -> str:
    ms = int(round(max(0.0, t) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def timeline_to_srt(timeline: List[Dict[str, Any]], with_speaker: bool = True) -> str:
    rows = []
    for i, it in enumerate(sorted(timeline, key=lambda x: x["audioStartSec"]), 1):
        text = str(it.get("text") or "").strip()
        if with_speaker and it.get("speaker"):
            text = f"{it['speaker']}: {text}"
        rows.append(f"{i}\n{_srt_time(it['audioStartSec'])} --> {_srt_time(it['audioEndSec'])}\n{text}\n")
    return "\n".join(rows)


def line_cache_key(voice_id: str, text: str, tempo: float, is_mock: bool) -> str:
    raw = json.dumps({"v": voice_id, "t": text, "tempo": round(float(tempo), 3), "mock": bool(is_mock)},
                     ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
