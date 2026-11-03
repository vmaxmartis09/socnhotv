from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import imageio_ffmpeg
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
)
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root


def load_audio_waveform(audio_path: str, target_sr: int = 16000) -> np.ndarray:
    """Giải mã âm thanh từ tệp bất kỳ (MP3, WAV, AAC, MP4) thành mảng numpy float32 16kHz mono.
    Sử dụng ffmpeg nhúng giúp xử lý đa định dạng siêu tốc và tránh lỗi PyAV metadata_errors.
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i",
        str(audio_path),
        "-ar",
        str(target_sr),
        "-ac",
        "1",
        "-f",
        "f32le",
        "-",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if proc.returncode == 0 and proc.stdout:
        return np.frombuffer(proc.stdout, dtype=np.float32)

    # Fallback qua soundfile
    data, sr = sf.read(audio_path, dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data


def format_timestamp_srt(seconds: float) -> str:
    """Chuyển đổi giây thành định dạng SRT: 00:00:00,000."""
    millis = int(round(max(0.0, seconds) * 1000))
    hours = millis // 3600000
    millis %= 3600000
    mins = millis // 60000
    millis %= 60000
    secs = millis // 1000
    millis %= 1000
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """Chuyển đổi giây thành định dạng WebVTT: 00:00:00.000."""
    millis = int(round(max(0.0, seconds) * 1000))
    hours = millis // 3600000
    millis %= 3600000
    mins = millis // 60000
    millis %= 60000
    secs = millis // 1000
    millis %= 1000
    return f"{hours:02d}:{mins:02d}:{secs:02d}.{millis:03d}"


class CaptionAdapter:
    """Adapter tách phụ đề AI sử dụng Faster-Whisper:
    - Nhận diện giọng nói tiếng Việt độ chính xác cao.
    - Hỗ trợ word-level timestamps phục vụ HyperFrames Kinetic Subtitles.
    - Xuất định dạng SRT chuẩn và VTT.
    """

    _model_instance: Optional[WhisperModel] = None

    def __init__(self, store: ProjectStore, model_size: str = "tiny"):
        self.store = store
        self.model_size = model_size
        self.repo_root = get_repo_root()

    def _get_model(self) -> WhisperModel:
        """Khởi tạo hoặc tái sử dụng model Whisper (singleton in-memory)."""
        if CaptionAdapter._model_instance is None:
            # Tự động chọn device (cpu hoặc mps trên macOS)
            CaptionAdapter._model_instance = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
            )
        return CaptionAdapter._model_instance

    def transcribe(
        self,
        audio_path: str,
        language: str = "vi",
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Tách từ và câu từ audio_path. Trả về (srt_content, vtt_content, segments_data)."""
        model = self._get_model()
        audio_waveform = load_audio_waveform(audio_path, target_sr=16000)
        segments_gen, info = model.transcribe(
            audio_waveform,
            language=language,
            word_timestamps=True,
            beam_size=5,
        )

        segments = list(segments_gen)

        srt_lines: List[str] = []
        vtt_lines: List[str] = ["WEBVTT\n"]
        segments_data: List[Dict[str, Any]] = []

        for idx, seg in enumerate(segments, start=1):
            start_srt = format_timestamp_srt(seg.start)
            end_srt = format_timestamp_srt(seg.end)
            start_vtt = format_timestamp_vtt(seg.start)
            end_vtt = format_timestamp_vtt(seg.end)
            text_clean = seg.text.strip()

            # SRT block
            srt_lines.append(f"{idx}")
            srt_lines.append(f"{start_srt} --> {end_srt}")
            srt_lines.append(f"{text_clean}\n")

            # VTT block
            vtt_lines.append(f"{idx}")
            vtt_lines.append(f"{start_vtt} --> {end_vtt}")
            vtt_lines.append(f"{text_clean}\n")

            # Word-level breakdown
            words_info = []
            if seg.words:
                for w in seg.words:
                    words_info.append({
                        "word": w.word.strip(),
                        "start": round(w.start, 3),
                        "end": round(w.end, 3),
                        "probability": round(w.probability, 3),
                    })

            segments_data.append({
                "index": idx,
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": text_clean,
                "words": words_info,
            })

        srt_content = "\n".join(srt_lines).strip() + "\n"
        vtt_content = "\n".join(vtt_lines).strip() + "\n"

        return srt_content, vtt_content, segments_data

    async def generate_captions(
        self,
        audio_source: Union[Artifact, str, Path],
        node_id: str = "unknown",
        run_id: str = "run_default",
        language: str = "vi",
    ) -> Artifact:
        """Tách phụ đề từ Artifact Audio hoặc tệp âm thanh, lưu kết quả SRT vào ProjectStore."""
        input_hash = ""
        if isinstance(audio_source, Artifact):
            input_hash = audio_source.hash
            resolved_path = str(self.store.project_dir / audio_source.uri)
        else:
            resolved_path = str(audio_source)

        if not os.path.exists(resolved_path):
            raise FileNotFoundError(f"Tệp âm thanh không tồn tại: {resolved_path}")

        srt_content, vtt_content, segments_data = self.transcribe(resolved_path, language=language)

        total_duration = segments_data[-1]["end"] if segments_data else 0.0

        provenance = ArtifactProvenance(
            node_id=node_id,
            run_id=run_id,
            provider="faster-whisper",
            model=f"whisper-{self.model_size}",
            params={
                "language": language,
                "segmentCount": len(segments_data),
            },
            input_hashes=[input_hash] if input_hash else [],
            cost_usd=0.0,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        meta = ArtifactMeta(duration=total_duration)

        artifact = self.store.store_bytes(
            data=srt_content.encode("utf-8"),
            ext="srt",
            kind=ArtifactKind.CAPTIONS,
            provenance=provenance,
            meta=meta,
        )
        return artifact
