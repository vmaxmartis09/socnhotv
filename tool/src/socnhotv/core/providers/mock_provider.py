from __future__ import annotations

import struct
import time
from typing import Any, Dict, List, Optional

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
)
from socnhotv.core.providers.base import BaseProvider
from socnhotv.core.storage.project_store import ProjectStore


def create_minimal_png_bytes(width: int = 1080, height: int = 1920) -> bytes:
    """Tạo tệp PNG nhị phân hợp lệ tối giản cho Mock Image."""
    import zlib

    # PNG Signature
    signature = b"\x89PNG\r\n\x1a\n"

    # IHDR Chunk
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data))
    ihdr_chunk = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + ihdr_crc

    # IDAT Chunk (1 pixel hoặc scanlines tối giản nén zlib)
    raw_scanlines = b"\x00" + b"\x6d\x4a\xff" * width  # màu tím primary
    compressed_data = zlib.compress(raw_scanlines)
    idat_crc = struct.pack(">I", zlib.crc32(b"IDAT" + compressed_data))
    idat_chunk = (
        struct.pack(">I", len(compressed_data))
        + b"IDAT"
        + compressed_data
        + idat_crc
    )

    # IEND Chunk
    iend_chunk = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND"))

    return signature + ihdr_chunk + idat_chunk + iend_chunk


def create_minimal_mp4_bytes() -> bytes:
    """Tạo tệp MP4 dummy hợp lệ (ISO Media / MP4 v2)."""
    # ftyp box
    ftyp_data = b"isom\x00\x00\x02\x00isomiso2mp41"
    ftyp_box = struct.pack(">I", len(ftyp_data) + 8) + b"ftyp" + ftyp_data

    # mdat box
    mdat_data = b"MOCK_VIDEO_DATA_SOCNHOTV"
    mdat_box = struct.pack(">I", len(mdat_data) + 8) + b"mdat" + mdat_data

    return ftyp_box + mdat_box


def create_minimal_wav_bytes(duration_sec: float = 4.0) -> bytes:
    """Tạo tệp WAV PCM âm thanh hợp lệ cho Mock Voice."""
    sample_rate = 22050
    num_samples = int(sample_rate * duration_sec)
    data_size = num_samples * 2

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,  # PCM
        1,  # mono
        sample_rate,
        sample_rate * 2,
        2,  # block align
        16,  # bits per sample
        b"data",
        data_size,
    )
    # Tắt tiếng (silence)
    pcm_data = b"\x00" * data_size
    return header + pcm_data


class MockProvider(BaseProvider):
    """Provider giả lập hoạt động của các Model AI (Gemini, Veo, OmniVoice) để kiểm thử."""

    def __init__(self, store: ProjectStore):
        self.store = store

    def provider_name(self) -> str:
        return "mock"

    async def generate_images(
        self,
        prompt: str,
        references: Optional[List[str]] = None,
        aspect_ratio: str = "9:16",
        resolution: str = "1080p",
        n: int = 1,
        seed: Optional[int] = None,
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> List[Artifact]:
        artifacts = []
        width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
        png_bytes = create_minimal_png_bytes(width=width, height=height)

        for i in range(max(1, n)):
            provenance = ArtifactProvenance(
                node_id=node_id,
                run_id=run_id,
                provider="mock",
                model="mock-image-v1",
                params={
                    "prompt": prompt,
                    "aspectRatio": aspect_ratio,
                    "resolution": resolution,
                    "index": i,
                    "seed": seed,
                },
                input_hashes=references or [],
                cost_usd=0.0,
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            meta = ArtifactMeta(width=width, height=height, aspect=aspect_ratio)
            artifact = self.store.store_bytes(
                data=png_bytes,
                ext="png",
                kind=ArtifactKind.IMAGE,
                provenance=provenance,
                meta=meta,
            )
            artifacts.append(artifact)

        return artifacts

    async def generate_video(
        self,
        prompt: str,
        first_frame_uri: Optional[str] = None,
        duration_sec: float = 8.0,
        aspect_ratio: str = "9:16",
        has_audio: bool = False,
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> Artifact:
        width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
        mp4_bytes = create_minimal_mp4_bytes()

        provenance = ArtifactProvenance(
            node_id=node_id,
            run_id=run_id,
            provider="mock",
            model="mock-veo-video-v1",
            params={
                "prompt": prompt,
                "firstFrameUri": first_frame_uri,
                "durationSec": duration_sec,
                "aspectRatio": aspect_ratio,
                "hasAudio": has_audio,
            },
            input_hashes=[first_frame_uri] if first_frame_uri else [],
            cost_usd=0.0,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        meta = ArtifactMeta(
            width=width,
            height=height,
            duration=duration_sec,
            fps=24.0,
            aspect=aspect_ratio,
        )

        return self.store.store_bytes(
            data=mp4_bytes,
            ext="mp4",
            kind=ArtifactKind.VIDEO,
            provenance=provenance,
            meta=meta,
        )

    async def speak_voice(
        self,
        text: str,
        voice_id: str = "soc-nho",
        tempo: float = 1.10,
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> Artifact:
        # Tính thời lượng ước lượng theo số từ (trung bình 3 từ / giây)
        words_count = max(1, len(text.split()))
        est_duration = round(words_count / 3.0 / tempo, 2)
        wav_bytes = create_minimal_wav_bytes(duration_sec=est_duration)

        provenance = ArtifactProvenance(
            node_id=node_id,
            run_id=run_id,
            provider="mock",
            model="mock-omnivoice-v1",
            params={"text": text, "voiceId": voice_id, "tempo": tempo},
            input_hashes=[],
            cost_usd=0.0,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        meta = ArtifactMeta(duration=est_duration)

        return self.store.store_bytes(
            data=wav_bytes,
            ext="wav",
            kind=ArtifactKind.AUDIO,
            provenance=provenance,
            meta=meta,
        )

    async def analyze_vision(
        self,
        media_uri: str,
        prompt: str,
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> Dict[str, Any]:
        return {
            "title": "Phân cảnh trích xuất từ video nguồn (Mock)",
            "overview": "Video hoạt hình 3D vui nhộn",
            "scenes": [
                {
                    "index": 1,
                    "title": "Cảnh 1: Sóc Nhỏ thức dậy",
                    "imagePrompt": "Sóc Nhỏ Bi vươn vai thức dậy trong căn phòng gỗ ấm cúng",
                    "videoPrompt": "Camera lia nhẹ từ trên xuống thấy Sóc Nhỏ mở mắt tươi cười",
                    "dialogue": "Oa, chào buổi sáng các bạn!",
                    "durationSec": 7.0,
                },
                {
                    "index": 2,
                    "title": "Cảnh 2: Gặp bạn Koala",
                    "imagePrompt": "Sóc Nhỏ và bạn Koala cùng ăn sáng",
                    "videoPrompt": "Bạn Koala vẫy tay chào và đưa cho Bi một chiếc bàn chải",
                    "dialogue": "Nhớ đánh răng trước khi đi chơi nha Bi!",
                    "durationSec": 8.0,
                },
            ],
        }
