from __future__ import annotations

import asyncio

import json
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import imageio_ffmpeg
import soundfile as sf

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
)
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root
from socnhotv.video.fallback_ffmpeg import render_fallback_ffmpeg
from socnhotv.video.hyperframes_engine import HyperFramesEngine
from socnhotv.video.platforms import PlatformPreset, get_platform

logger = logging.getLogger("socnhotv.adapters.hyperframes")
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


class HyperFramesAdapter:
    """Tool Adapter HeyGen HyperFrames:
    Lớp bọc mỏng tích hợp HyperFramesEngine vào hệ thống DAG & ProjectStore.
    Bảo toàn toàn bộ API public cho graph_runner và các test hiện hành.
    """

    def __init__(self, store: ProjectStore):
        self.store = store
        self.repo_root = get_repo_root()
        self.ffmpeg = FFMPEG_EXE
        self.engine = HyperFramesEngine(ffmpeg_exe=self.ffmpeg)
        self.last_engine: str = "ffmpeg_fallback"
        self.last_cli_error: str = ""

    def get_audio_duration(self, audio_path: str | Path) -> float:
        """Đo thời lượng file audio chính xác."""
        return self.engine.get_audio_duration(audio_path)

    def generate_html_composition(
        self,
        scenes: List[Dict[str, Any]],
        voiceover_rel_path: str,
        total_duration: float,
        title_badge: str = "SÓC NHỎ TV • HOẠT HÌNH 3D",
        bgm_rel_path: Optional[str] = None,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
    ) -> str:
        """Sinh mã nguồn HTML5/CSS/GSAP composition tuân thủ quy chuẩn HyperFrames."""
        platform = "youtube" if width == 1920 and height == 1080 else "tiktok"
        return self.engine.generate_composition_html(
            scenes=scenes,
            voiceover_rel_path=voiceover_rel_path,
            total_duration=total_duration,
            title_badge=title_badge,
            bgm_rel_path=bgm_rel_path,
            platform=platform,
        )

    def build_project_bundle(
        self,
        target_dir: Path,
        scenes: List[Dict[str, Any]],
        audio_voiceover_path: str | Path,
        title_badge: str = "SÓC NHỎ TV • HOẠT HÌNH 3D",
        bgm_path: Optional[str | Path] = None,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
    ) -> Path:
        """Đóng gói toàn bộ cấu trúc dự án HyperFrames vào target_dir."""
        platform = "youtube" if width == 1920 and height == 1080 else "tiktok"
        return self.engine.build_from_scenes(
            scenes=scenes,
            audio_voiceover_path=audio_voiceover_path,
            platform=platform,
            target_dir=target_dir,
            title_badge=title_badge,
            bgm_path=bgm_path,
        )

    def render_fallback_ffmpeg(
        self,
        project_dir: Path,
        output_mp4: Path,
        fps: int = 30,
    ) -> Path:
        """Render fallback bằng FFmpeg."""
        return render_fallback_ffmpeg(
            project_dir=project_dir,
            output_mp4=output_mp4,
            width=1080,
            height=1920,
            fps=fps,
            ffmpeg_exe=self.ffmpeg,
        )

    def render(
        self,
        project_dir: Path,
        output_mp4: Path,
        quality: str = "looks",
        fps: int = 30,
        platform: str = "tiktok",
    ) -> Path:
        """Render video thông qua HyperFramesEngine."""
        out = self.engine.render(
            bundle_dir=project_dir,
            out_path=output_mp4,
            platform=platform,
            quality=quality,
        )
        self.last_engine = self.engine.last_engine
        self.last_cli_error = self.engine.last_cli_error
        return out

    async def render_from_artifacts(
        self,
        scenes: List[Dict[str, Any]],
        voice_artifact: Optional[Artifact] = None,
        captions_artifact: Optional[Artifact] = None,
        title_badge: str = "SÓC NHỎ TV • TẬP MỚI",
        node_id: str = "unknown",
        run_id: str = "run_default",
        width: int = 1080,
        height: int = 1920,
    ) -> Artifact:
        """Đầu vào là Artifacts, trả về Video Artifact MP4. width×height 1920×1080 = YouTube 16:9."""
        platform = "youtube" if (width, height) == (1920, 1080) else "tiktok"
        aspect = "16:9" if platform == "youtube" else "9:16"
        run_session_dir = self.store.runs_dir / run_id
        run_session_dir.mkdir(parents=True, exist_ok=True)
        hf_project_dir = run_session_dir / f"hf_composition_{node_id}"

        voice_path = (
            str(self.store.project_dir / voice_artifact.uri)
            if voice_artifact
            else ""
        )

        # Xây dựng bundle
        # Dựng bundle + render là việc nặng, chạy đồng bộ (subprocess): đưa sang thread để KHÔNG chặn
        # vòng lặp sự kiện của Core (nếu không, trong lúc render Studio không tải được gì và SSE đứng).
        await asyncio.to_thread(
            self.build_project_bundle,
            target_dir=hf_project_dir,
            scenes=scenes,
            audio_voiceover_path=voice_path,
            title_badge=title_badge,
            width=width,
            height=height,
            fps=30,
        )

        output_mp4_temp = run_session_dir / f"{node_id}_rendered.mp4"
        final_mp4 = await asyncio.to_thread(
            self.render,
            project_dir=hf_project_dir,
            output_mp4=output_mp4_temp,
            fps=30,
            platform=platform,
        )

        with open(final_mp4, "rb") as f:
            mp4_bytes = f.read()

        total_dur = await asyncio.to_thread(self.get_audio_duration, final_mp4)

        provenance = ArtifactProvenance(
            node_id=node_id,
            run_id=run_id,
            provider=getattr(self, "last_engine", "hyperframes"),
            model="hyperframes-v0.9.12" if getattr(self, "last_engine", "") == "hyperframes" else "ffmpeg-compositor",
            params={
                "aspectRatio": aspect,
                "width": width,
                "height": height,
                "fps": 30,
                "sceneCount": len(scenes),
            },
            input_hashes=[art.hash for art in (voice_artifact, captions_artifact) if art],
            cost_usd=0.0,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        meta = ArtifactMeta(
            width=width,
            height=height,
            duration=total_dur,
            fps=30.0,
            aspect=aspect,
        )

        return self.store.store_bytes(
            data=mp4_bytes,
            ext="mp4",
            kind=ArtifactKind.VIDEO,
            provenance=provenance,
            meta=meta,
        )
