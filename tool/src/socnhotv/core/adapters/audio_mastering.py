from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


class AudioMastering:
    """Mastering chuẩn TikTok KOC: de-esser -> EQ presence -> compressor -> -14 LUFS -> MP3/WAV."""

    def __init__(self, ffmpeg_exe: Optional[str] = None):
        self.ffmpeg = ffmpeg_exe or FFMPEG_EXE

    def master_tiktok(
        self,
        input_audio_path: str,
        output_audio_path: str,
        target_lufs: float = -14.0,
        presence_boost_db: float = 3.5,
        tempo_factor: float = 1.10,
        bitrate: str = "192k",
    ) -> str:
        """Thực thi chuỗi xử lý âm thanh chuyên nghiệp:
        1. De-esser: giảm các âm gió / tiếng chói (s, x, ch).
        2. Presence EQ: tăng +3.5dB ở tần số 3.2kHz để giọng nổi bật trên loa điện thoại.
        3. Compressor: tỉ lệ 4:1 làm đều âm lượng giữa các từ.
        4. Tempo: điều chỉnh tốc độ đọc tự nhiên (mặc định 1.10x).
        5. Loudnorm: chuẩn hóa âm lượng EBU R128 (-14.0 LUFS) chuẩn phát TikTok / YouTube Shorts.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_audio_path)), exist_ok=True)
        tempo_factor = max(0.5, min(2.0, tempo_factor))

        chain = [
            "deesser=i=0.4:m=0.4:f=6500:s=o",
            f"equalizer=f=3200:t=q:w=2.0:g={presence_boost_db}",
            "acompressor=threshold=-18dB:ratio=4:attack=15:release=120:makeup=2dB",
        ]
        if abs(tempo_factor - 1.0) > 1e-3:
            chain.append(f"atempo={tempo_factor}")

        # loudnorm đứng cuối để -14 LUFS đo sau mọi biến đổi khác
        chain.append(f"loudnorm=I={target_lufs}:LRA=8:TP=-1.5")

        filters_str = ",".join(chain)
        res = self._run(filters_str, input_audio_path, output_audio_path, bitrate)

        if res.returncode != 0:
            # Nếu bản build ffmpeg thiếu bộ lọc deesser: tự động bỏ deesser và giữ các bộ lọc còn lại
            fallback_filters = ",".join(chain[1:])
            res = self._run(fallback_filters, input_audio_path, output_audio_path, bitrate)

        if res.returncode != 0:
            # Fallback tối giản nhất nếu audio source quá ngắn hoặc lỗi phức tạp: chỉ convert sang 44100Hz mono
            simple_res = self._run_simple(input_audio_path, output_audio_path, bitrate)
            if simple_res.returncode != 0:
                raise RuntimeError(f"Audio Mastering thất bại:\n{res.stderr[-500:]}")

        return os.path.abspath(output_audio_path)

    def mix_voice_and_bgm_ducking(
        self,
        voice_audio_path: str,
        bgm_audio_path: str,
        output_audio_path: str,
        ducking_ratio: float = 0.18,
        target_lufs: float = -14.0,
    ) -> str:
        """Trộn giọng đọc và nhạc nền BGM với hiệu ứng Ducking (BGM tự động giảm khi có giọng) và chuẩn hóa -14 LUFS."""
        os.makedirs(os.path.dirname(os.path.abspath(output_audio_path)), exist_ok=True)
        # Filtergraph: Sidechain compression hoặc volume mix
        filtergraph = (
            f"[1:a]volume=0.35[bgm];"
            f"[bgm][0:a]sidechaincompress=threshold=0.08:ratio=4:attack=80:release=350[ducked_bgm];"
            f"[0:a][ducked_bgm]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I={target_lufs}:LRA=8:TP=-1.5[out]"
        )
        cmd = [
            self.ffmpeg,
            "-y",
            "-i", str(voice_audio_path),
            "-i", str(bgm_audio_path),
            "-filter_complex", filtergraph,
            "-map", "[out]",
            "-ar", "44100",
            "-ac", "2",
            "-b:a", "192k",
            str(output_audio_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            # Fallback đơn giản hơn nếu sidechaincompress không hỗ trợ
            fallback_filter = (
                f"[1:a]volume={ducking_ratio}[bgm];"
                f"[0:a][bgm]amix=inputs=2:duration=first,loudnorm=I={target_lufs}:LRA=8:TP=-1.5"
            )
            cmd_fb = [
                self.ffmpeg,
                "-y",
                "-i", str(voice_audio_path),
                "-i", str(bgm_audio_path),
                "-filter_complex", fallback_filter,
                "-ar", "44100",
                "-ac", "2",
                "-b:a", "192k",
                str(output_audio_path),
            ]
            res_fb = subprocess.run(cmd_fb, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            if res_fb.returncode != 0:
                return self.master_tiktok(voice_audio_path, output_audio_path, target_lufs=target_lufs)

        return os.path.abspath(output_audio_path)

    def _run(self, filters: str, src: str, dst: str, bitrate: str) -> subprocess.CompletedProcess:
        is_mp3 = dst.lower().endswith(".mp3")
        cmd = [
            self.ffmpeg,
            "-y",
            "-i",
            str(src),
            "-af",
            filters,
            "-ar",
            "44100",
            "-ac",
            "1",
        ]
        if is_mp3:
            cmd.extend(["-b:a", bitrate])
        cmd.append(str(dst))
        return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)

    def _run_simple(self, src: str, dst: str, bitrate: str) -> subprocess.CompletedProcess:
        is_mp3 = dst.lower().endswith(".mp3")
        cmd = [
            self.ffmpeg,
            "-y",
            "-i",
            str(src),
            "-ar",
            "44100",
            "-ac",
            "1",
        ]
        if is_mp3:
            cmd.extend(["-b:a", bitrate])
        cmd.append(str(dst))
        return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
