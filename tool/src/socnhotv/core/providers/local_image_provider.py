"""Provider sinh ảnh cục bộ trên Apple Silicon qua MLX / mflux (FLUX.1-schnell 4-bit, $0)."""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
)
from socnhotv.core.providers.base import BaseProvider
from socnhotv.core.providers.errors import ProviderError, ProviderErrorKind
from socnhotv.core.providers.spend_guard import SpendGuard
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root


class LocalImageProvider(BaseProvider):
    """Adapter sinh ảnh trên máy (Local MLX / mflux), $0, hoàn toàn offline."""

    def __init__(
        self,
        store: ProjectStore,
        guard: Optional[SpendGuard] = None,
        key: Optional[str] = None,
        source: str = "api",
    ):
        self.store = store
        self.guard = guard or SpendGuard(store.runs_dir)
        self.source = source
        self.script_path = get_repo_root() / "scripts" / "local_ai" / "run_local_image.py"

    def provider_name(self) -> str:
        return "local"

    def capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "local",
            "supportsFirstFrame": False,
            "supportsImageEdit": False,
            "supportsReferences": False,
            "supportsAudioVideo": False,
            "supportsVision": False,
            "supportsStructuredText": False,
            "aspectRatios": ["16:9", "1:1"],
            "durationsSec": [],
            "models": ["local-flux-schnell"],
        }

    async def generate_images(
        self,
        prompt: str,
        references: Optional[List[str]] = None,
        aspect_ratio: str = "16:9",
        resolution: str = "1080p",
        n: int = 1,
        seed: Optional[int] = None,
        node_id: str = "unknown",
        run_id: str = "run_default",
        model: Optional[str] = None,
    ) -> List[Artifact]:
        width, height = (1024, 576) if aspect_ratio == "16:9" else (1024, 1024)
        out: List[Artifact] = []

        for i in range(max(1, n)):
            current_seed = (seed + i) if seed is not None else int(time.time()) % 100000

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                cmd = [
                    sys_executable(),
                    str(self.script_path),
                    "--prompt", prompt,
                    "--output", str(tmp_path),
                    "--width", str(width),
                    "--height", str(height),
                    "--steps", "4",
                    "--seed", str(current_seed),
                ]

                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()

                if proc.returncode != 0:
                    err_msg = stderr.decode().strip() or stdout.decode().strip()
                    raise ProviderError(
                        f"Lỗi khi chạy model ảnh local: {err_msg}",
                        kind=ProviderErrorKind.INVALID_PARAMS,
                        provider="local",
                        retryable=False,
                    )

                if not tmp_path.exists() or tmp_path.stat().st_size == 0:
                    raise ProviderError(
                        "Không tạo được tệp ảnh sau khi gọi local runner.",
                        kind=ProviderErrorKind.UNKNOWN,
                        provider="local",
                    )

                data = tmp_path.read_bytes()
                now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

                artifact = self.store.store_bytes(
                    data=data,
                    ext="png",
                    kind=ArtifactKind.IMAGE,
                    meta=ArtifactMeta(width=width, height=height, aspect=aspect_ratio),
                    provenance=ArtifactProvenance(
                        node_id=node_id,
                        run_id=run_id,
                        provider="local",
                        model="local-flux-schnell",
                        cost_usd=0.0,
                        created_at=now_iso,
                        params={"prompt": prompt, "aspectRatio": aspect_ratio, "steps": 4, "seed": current_seed},
                    ),
                )
                out.append(artifact)
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

        return out

    async def generate_video(
        self,
        prompt: str,
        first_frame_uri: Optional[str] = None,
        duration_sec: float = 8.0,
        aspect_ratio: str = "9:16",
        has_audio: bool = False,
        node_id: str = "unknown",
        run_id: str = "run_default",
        last_frame_uri: Optional[str] = None,
        references: Optional[List[str]] = None,
        model: Optional[str] = None,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> Artifact:
        raise ProviderError(
            "Local video generation (Wan/LTX) chưa được bật tự động (mỗi clip 5-10 phút trên M4 16GB). "
            "Khuyến nghị người dùng làm clip thủ công bằng web credit hằng ngày theo chuẩn C5.",
            kind=ProviderErrorKind.INVALID_PARAMS,
            provider="local",
        )

    async def speak_voice(
        self,
        text: str,
        voice_id: str = "soc-nho",
        tempo: float = 1.10,
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> Artifact:
        raise ProviderError(
            "LocalImageProvider chỉ phụ trách ảnh. Giọng nói tiếng Việt do OmniVoice đảm nhiệm.",
            kind=ProviderErrorKind.INVALID_PARAMS,
            provider="local",
        )

    async def analyze_vision(
        self,
        media_uri: str,
        prompt: str,
        node_id: str = "unknown",
        run_id: str = "run_default",
        schema: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise ProviderError(
            "Chưa cấu hình analyze_vision cho local provider.",
            kind=ProviderErrorKind.INVALID_PARAMS,
            provider="local",
        )


def sys_executable() -> str:
    local_py = get_repo_root() / ".venv-local-ai" / "bin" / "python"
    if local_py.exists():
        return str(local_py)
    root_py = get_repo_root() / ".venv" / "bin" / "python"
    if root_py.exists():
        return str(root_py)
    import sys
    return sys.executable
