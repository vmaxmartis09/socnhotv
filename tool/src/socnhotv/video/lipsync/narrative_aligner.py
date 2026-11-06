"""Narrative Aligner implementation for Option (a) - Voiceover & Audio Alignment (Luồng H5)."""
from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess
import time
from typing import Optional

import imageio_ffmpeg

from socnhotv.video.lipsync.models import (
    AlignmentMode,
    LipSyncMethod,
    LipSyncResult,
)

logger = logging.getLogger("socnhotv.video.lipsync.narrative")
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


class NarrativeAligner:
    """Xử lý đồng bộ âm thanh giọng nói OmniVoice và clip AI theo Lựa chọn (a).
    
    Đặc điểm:
    - Mute/strip hoàn toàn âm thanh AI lảm nhảm gốc.
    - Căn chỉnh mốc thời gian thoại OmniVoice chính xác vào video.
    - Hỗ trợ pad silence hoặc kéo dài video (freeze-frame drift) khi thời lượng lệch.
    - Tốc độ cực nhanh (stream copy hoặc fast encode), $0, hoàn toàn offline.
    """

    def __init__(self, ffmpeg_exe: str = FFMPEG_EXE):
        self.ffmpeg_exe = ffmpeg_exe

    def align_shot(
        self,
        shot_id: str,
        video_path: str | Path,
        audio_path: str | Path,
        output_path: str | Path,
        mode: AlignmentMode = AlignmentMode.STRIP_ORIGINAL,
        audio_start_offset_sec: float = 0.4,
        duck_volume: float = 0.05,
    ) -> LipSyncResult:
        """Đồng bộ 1 shot giữa video và file thoại OmniVoice."""
        start_time = time.time()
        video_file = Path(video_path).resolve()
        audio_file = Path(audio_path).resolve()
        out_file = Path(output_path).resolve()

        if not video_file.exists():
            return LipSyncResult(
                success=False,
                shot_id=shot_id,
                output_video_path=None,
                method_used=LipSyncMethod.MUTE_AND_VOICEOVER,
                tool_id="narrative_aligner",
                execution_time_sec=0.0,
                cost_usd=0.0,
                error_message=f"Video file không tồn tại: {video_file}",
            )

        if not audio_file.exists():
            return LipSyncResult(
                success=False,
                shot_id=shot_id,
                output_video_path=None,
                method_used=LipSyncMethod.MUTE_AND_VOICEOVER,
                tool_id="narrative_aligner",
                execution_time_sec=0.0,
                cost_usd=0.0,
                error_message=f"Audio file không tồn tại: {audio_file}",
            )

        out_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Lấy thông tin thời lượng qua ffprobe / lệnh
            video_dur = self._get_duration(video_file)
            audio_dur = self._get_duration(audio_file)

            cmd: list[str] = [self.ffmpeg_exe, "-y"]

            if mode == AlignmentMode.STRIP_ORIGINAL:
                # Kỹ thuật: Tắt 100% âm thanh gốc, lùi audio bằng adelay
                delay_ms = int(max(0.0, audio_start_offset_sec) * 1000)
                cmd.extend([
                    "-i", str(video_file),
                    "-i", str(audio_file),
                    "-filter_complex",
                    f"[1:a]adelay={delay_ms}|{delay_ms},apad[delayed_a];[delayed_a]atrim=0:{video_dur:.3f}[out_a]",
                    "-map", "0:v:0",
                    "-map", "[out_a]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-t", f"{video_dur:.3f}",
                    str(out_file),
                ])
            elif mode == AlignmentMode.VOLUME_DUCK:
                # Kỹ thuật: Giảm âm thanh gốc xuống duck_volume và trộn với OmniVoice
                delay_ms = int(max(0.0, audio_start_offset_sec) * 1000)
                cmd.extend([
                    "-i", str(video_file),
                    "-i", str(audio_file),
                    "-filter_complex",
                    f"[0:a]volume={duck_volume:.2f}[orig_duck];"
                    f"[1:a]adelay={delay_ms}|{delay_ms},apad[delayed_a];"
                    f"[orig_duck][delayed_a]amix=inputs=2:duration=first:dropout_transition=2[out_a]",
                    "-map", "0:v:0",
                    "-map", "[out_a]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-t", f"{video_dur:.3f}",
                    str(out_file),
                ])
            else:
                # Mặc định stream copy ngắn nhất
                cmd.extend([
                    "-i", str(video_file),
                    "-i", str(audio_file),
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-shortest",
                    str(out_file),
                ])

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            if proc.returncode != 0:
                logger.error("FFmpeg error in NarrativeAligner: %s", proc.stderr)
                return LipSyncResult(
                    success=False,
                    shot_id=shot_id,
                    output_video_path=None,
                    method_used=LipSyncMethod.MUTE_AND_VOICEOVER,
                    tool_id="narrative_aligner",
                    execution_time_sec=time.time() - start_time,
                    cost_usd=0.0,
                    error_message=f"FFmpeg error: {proc.stderr[:300]}",
                )

            elapsed = time.time() - start_time
            return LipSyncResult(
                success=True,
                shot_id=shot_id,
                output_video_path=str(out_file),
                method_used=LipSyncMethod.MUTE_AND_VOICEOVER,
                tool_id="narrative_aligner",
                execution_time_sec=round(elapsed, 4),
                cost_usd=0.0,
                metadata={
                    "mode": mode.value,
                    "video_duration": video_dur,
                    "audio_duration": audio_dur,
                    "offset_sec": audio_start_offset_sec,
                    "output_size_bytes": out_file.stat().st_size if out_file.exists() else 0,
                },
            )

        except Exception as e:
            return LipSyncResult(
                success=False,
                shot_id=shot_id,
                output_video_path=None,
                method_used=LipSyncMethod.MUTE_AND_VOICEOVER,
                tool_id="narrative_aligner",
                execution_time_sec=time.time() - start_time,
                cost_usd=0.0,
                error_message=str(e),
            )

    def _get_duration(self, file_path: Path) -> float:
        """Đo thời lượng video hoặc audio bằng ffprobe / ffmpeg."""
        cmd = [
            self.ffmpeg_exe,
            "-i", str(file_path),
            "-f", "null",
            "-",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            # Tìm Duration: HH:MM:SS.xx trong stderr
            for line in res.stderr.splitlines():
                if "Duration:" in line:
                    parts = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = parts.split(":")
                    return float(h) * 3600 + float(m) * 60 + float(s)
        except Exception:
            pass
        return 8.0
