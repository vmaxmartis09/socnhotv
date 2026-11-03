from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from socnhotv.core.contracts.types import Artifact


class BaseProvider(ABC):
    """Giao diện trừu tượng cơ sở cho mọi Model AI Provider (Google, fal.ai, Replicate, Mock)."""

    @abstractmethod
    def provider_name(self) -> str:
        pass

    def capabilities(self) -> Dict[str, Any]:
        """Ma trận khả năng của Provider (khung đầu, âm thanh, tỉ lệ khung, thời lượng)."""
        return {
            "provider": self.provider_name(),
            "supportsFirstFrame": True,
            "supportsImageEdit": True,
            "supportsReferences": True,
            "supportsAudioVideo": False,
            "aspectRatios": ["9:16", "16:9", "1:1", "4:5"],
            "durationsSec": [5, 8],
        }

    def estimate_cost(self, kind: str, model: Optional[str] = None, **params: Any) -> float:
        """Ước tính giá USD dựa trên ModelRegistry, fallback về 0.0 cho provider miễn phí."""
        if model:
            from socnhotv.core.models_registry.registry import ModelRegistry

            return ModelRegistry.get_instance().estimate_cost(model, params=params)
        return 0.0

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
        model: Optional[str] = None,
    ) -> List[Artifact]:
        pass

    async def edit_image(
        self,
        image_uri: str,
        prompt: str,
        references: Optional[List[str]] = None,
        aspect_ratio: str = "9:16",
        node_id: str = "unknown",
        run_id: str = "run_default",
        model: Optional[str] = None,
    ) -> Artifact:
        """Chỉnh sửa ảnh gốc kết hợp ảnh tham chiếu và prompt (image.edit)."""
        refs = [image_uri] + list(references or [])
        arts = await self.generate_images(
            prompt=prompt,
            references=refs,
            aspect_ratio=aspect_ratio,
            n=1,
            node_id=node_id,
            run_id=run_id,
            model=model,
        )
        return arts[0]

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
        last_frame_uri: Optional[str] = None,
        references: Optional[List[str]] = None,
        model: Optional[str] = None,
        cancel_event: Optional[asyncio.Event] = None,
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
        schema: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        pass

    async def text_complete(
        self,
        system: str,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Hoàn thành văn bản hoặc sinh JSON theo schema (text.complete)."""
        return {"text": prompt, "mode": "mock"}
