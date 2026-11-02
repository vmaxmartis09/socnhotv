"""Mastering bắt buộc cho mọi output voice: de-esser -> EQ presence -> compressor -> -14 LUFS -> MP3."""

import os
import subprocess

import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


class AudioMastering:
    def __init__(self):
        self.ffmpeg = FFMPEG_EXE

    def master_tiktok_koc(
        self,
        input_audio_path: str,
        output_audio_path: str,
        target_lufs: float = -14.0,
        presence_boost_db: float = 3.5,
        tempo_factor: float = 1.10,
        bitrate: str = "192k",
    ) -> str:
        """De-esser -> presence EQ +3.5dB @3.2kHz -> compressor 4:1 -> loudnorm -14 LUFS -> MP3 192k 44.1kHz mono."""
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

        res = self._run("," .join(chain), input_audio_path, output_audio_path, bitrate)
        if res.returncode != 0:
            # ffmpeg build thiếu deesser: bỏ filter đó, giữ phần còn lại
            res = self._run(",".join(chain[1:]), input_audio_path, output_audio_path, bitrate)
        if res.returncode != 0:
            raise RuntimeError(f"Mastering thất bại: {res.stderr[-500:]}")
        return os.path.abspath(output_audio_path)

    def _run(self, filters: str, src: str, dst: str, bitrate: str):
        cmd = [
            self.ffmpeg, "-y", "-i", str(src),
            "-af", filters,
            "-ar", "44100", "-ac", "1", "-b:a", bitrate,
            str(dst),
        ]
        return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
