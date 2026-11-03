from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from socnhotv.core.contracts.types import Artifact


class BaseProvider(ABC):
    """Giao diện trừu tượng cơ sở cho mọi Model AI Provider."""

    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def speak_voice(
        self,
        text: str,
        voice_id: str = "soc-nho",
        tempo: float = 1.10,
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> Artifact:
        pass

    @abstractmethod
    async def analyze_vision(
        self,
        media_uri: str,
        prompt: str,
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> Dict[str, Any]:
        pass
