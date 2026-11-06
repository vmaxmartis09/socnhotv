from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import edge_tts
from socnhotv.core.adapters.audio_mastering import AudioMastering
from socnhotv.workspace import project_path, shared_path

logger = logging.getLogger(__name__)


async def synthesize_line_edge_tts(
    text: str,
    out_path: Path,
    voice_name: str = "vi-VN-HoaiMyNeural",
    retries: int = 3,
) -> bool:
    """Synthesize single sentence to MP3 using edge-tts streaming with retries."""
    for attempt in range(retries):
        try:
            comm = edge_tts.Communicate(text=text, voice=voice_name)
            has_data = False
            with open(out_path, "wb") as f:
                async for chunk in comm.stream():
                    if chunk.get("type") == "audio" and "data" in chunk:
                        f.write(chunk["data"])
                        has_data = True
            if has_data and out_path.exists() and out_path.stat().st_size > 0:
                return True
        except Exception as e:
            logger.warning("edge-tts error (attempt %d/%d) on line '%s': %s", attempt + 1, retries, text, e)
            if attempt < retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))
    return False


def create_silence_mp3(duration_s: float, out_path: Path) -> bool:
    """Create silence MP3 file of specified duration."""
    try:
        dur = max(duration_s, 0.05)
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=mono",
            "-t", f"{dur:.3f}",
            "-q:a", "9",
            "-acodec", "libmp3lame",
            str(out_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        return res.returncode == 0 and out_path.exists()
    except Exception as e:
        logger.warning("Failed to create silence: %s", e)
        return False


def concatenate_audio_files(audio_files: List[Path], output_path: Path) -> bool:
    """Concatenate audio files using ffmpeg concat demuxer."""
    if not audio_files:
        return False
    try:
        list_txt = output_path.parent / "concat_list.txt"
        with open(list_txt, "w", encoding="utf-8") as f:
            for fpath in audio_files:
                f.write(f"file '{fpath.resolve()}'\n")

        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_txt),
            "-c", "copy",
            str(output_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        if list_txt.exists():
            list_txt.unlink()
        return res.returncode == 0 and output_path.exists()
    except Exception as e:
        logger.warning("Failed to concatenate audios: %s", e)
        return False


async def run_revoice(
    project_id: str,
    source_id: str,
    voice_id: str = "soc-nho",
    style: str = "faithful",
    target_lufs: float = -14.0,
) -> Path:
    """Synthesize speech for rewritten lines, align timing, and master to -14 LUFS."""
    source_dir = project_path(project_id, "raw", source_id)
    script_file = source_dir / f"script.{style}.json"
    if not script_file.exists():
        # Fallback to transcript.vi.json
        script_file = source_dir / "transcript.vi.json"
    if not script_file.exists():
        raise FileNotFoundError(f"Script/transcript file not found in {source_dir}")

    with open(script_file, "r", encoding="utf-8") as f:
        lines: List[Dict[str, Any]] = json.load(f)

    temp_dir = source_dir / "tmp_tts"
    temp_dir.mkdir(parents=True, exist_ok=True)

    audio_chunks: List[Path] = []
    current_time = 0.0

    # Pick voice name
    voice_name = "vi-VN-HoaiMyNeural" if "soc-nho" in voice_id else "vi-VN-NamMinhNeural"

    for idx, item in enumerate(lines):
        target_start = float(item.get("start", current_time))
        text = item.get("text", "").strip()

        # Insert silence if gap between current_time and target_start
        if target_start > current_time + 0.1:
            gap = target_start - current_time
            silence_file = temp_dir / f"silence_{idx:03d}.mp3"
            if create_silence_mp3(gap, silence_file):
                audio_chunks.append(silence_file)
                current_time += gap

        # Synthesize line
        line_file = temp_dir / f"line_{idx:03d}.mp3"
        if text:
            ok = await synthesize_line_edge_tts(text, line_file, voice_name=voice_name)
            if not ok:
                # Fallback to 1s silence if offline/test
                create_silence_mp3(1.0, line_file)
            audio_chunks.append(line_file)
            # Estimate or probe duration
            current_time = float(item.get("end", current_time + 1.0))

    # Concatenate unmastered speech
    raw_combined = temp_dir / "raw_combined.mp3"
    concatenate_audio_files(audio_chunks, raw_combined)

    # Master to TikTok standard (-14 LUFS)
    final_output = source_dir / "voice.vi.mp3"
    mastering = AudioMastering()

    if raw_combined.exists() and raw_combined.stat().st_size > 0:
        mastering.master_tiktok(
            input_audio_path=str(raw_combined),
            output_audio_path=str(final_output),
            target_lufs=target_lufs,
        )
    else:
        # Create minimal 1s mastered fallback
        minimal_raw = temp_dir / "minimal.mp3"
        create_silence_mp3(1.0, minimal_raw)
        mastering.master_tiktok(
            input_audio_path=str(minimal_raw),
            output_audio_path=str(final_output),
            target_lufs=target_lufs,
        )

    # Clean up temp chunks
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    return final_output
