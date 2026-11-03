"""Khung Provider cho Replicate REST Predictions API (sẵn sàng mở rộng qua models.yaml)."""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

import httpx

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
)
from socnhotv.core.models_registry.registry import ModelRegistry
from socnhotv.core.providers.base import BaseProvider
from socnhotv.core.providers.errors import (
    ProviderError,
    ProviderErrorKind,
    classify_http_error,
)
from socnhotv.core.providers.key_vault import KeyVault, validate_key_format
from socnhotv.core.providers.spend_guard import SpendGuard
from socnhotv.core.storage.project_store import ProjectStore

REPLICATE_API_BASE = "https://api.replicate.com/v1"


class ReplicateProvider(BaseProvider):
    """Khung Adapter chuẩn cho Replicate Predictions API."""

    def __init__(
        self,
        store: ProjectStore,
        guard: Optional[SpendGuard] = None,
        key: Optional[str] = None,
        poll_interval_sec: float = 3.0,
        source: str = "api",
    ):
        self.store = store
        self.guard = guard or SpendGuard(store.runs_dir)
        raw = key or KeyVault(persist_local=False).get_raw_key("replicate")
        self.key = validate_key_format("replicate", raw)
        self.poll_interval_sec = poll_interval_sec
        self.source = source

    def provider_name(self) -> str:
        return "replicate"

    def capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "replicate",
            "supportsFirstFrame": True,
            "supportsImageEdit": False,
            "supportsReferences": False,
            "supportsAudioVideo": False,
            "aspectRatios": ["9:16", "16:9", "1:1", "4:5"],
            "durationsSec": [5],
            "models": [m.key for m in ModelRegistry.get_instance().list_by_provider("replicate")],
        }

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}

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
        spec = ModelRegistry.get_instance().get(model or "replicate-flux-schnell")
        model_slug = spec.model_id if spec else "black-forest-labs/flux-schnell"
        cost = ModelRegistry.get_instance().estimate_cost(model or "replicate-flux-schnell", num_images=n) or 0.003 * n
        label = f"replicate ảnh {node_id}"
        self.guard.reserve(cost, label, source=self.source)

        inp: Dict[str, Any] = {"prompt": prompt, "aspect_ratio": aspect_ratio, "num_outputs": max(1, n)}
        if seed is not None:
            inp["seed"] = int(seed)

        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{REPLICATE_API_BASE}/models/{model_slug}/predictions",
                headers=self._headers(),
                json={"input": inp},
            )
            if r.status_code >= 400:
                self.guard.refund(cost, label, source=self.source)
                raise classify_http_error("replicate", r.status_code, r.text, extra_secrets=[self.key])
            pred = r.json()
            poll_url = pred.get("urls", {}).get("get")
            while pred.get("status") in ("starting", "processing") and poll_url:
                await asyncio.sleep(self.poll_interval_sec)
                pr = await client.get(poll_url, headers=self._headers())
                if pr.status_code >= 400:
                    raise classify_http_error("replicate", pr.status_code, pr.text, extra_secrets=[self.key])
                pred = pr.json()

            if pred.get("status") != "succeeded":
                raise ProviderError(
                    f"Replicate thất bại: {pred.get('error') or pred.get('status')}",
                    kind=ProviderErrorKind.UNKNOWN,
                    provider="replicate",
                    retryable=False,
                    extra_secrets=[self.key],
                )
            outputs = pred.get("output") or []
            if isinstance(outputs, str):
                outputs = [outputs]

            out: List[Artifact] = []
            for idx, url in enumerate(outputs):
                dl = await client.get(url, follow_redirects=True)
                dl.raise_for_status()
                out.append(
                    self.store.store_bytes(
                        data=dl.content,
                        ext="png",
                        kind=ArtifactKind.IMAGE,
                        provenance=ArtifactProvenance(
                            node_id=node_id,
                            run_id=run_id,
                            provider="replicate",
                            model=model_slug,
                            params={"prompt": prompt, "aspectRatio": aspect_ratio, "index": idx},
                            cost_usd=round(cost / max(1, len(outputs)), 4),
                            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        ),
                        meta=ArtifactMeta(aspect=aspect_ratio),
                    )
                )
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
            "Chưa khai báo model video cho Replicate trong models.yaml; hãy dùng Google Veo hoặc fal.ai.",
            kind=ProviderErrorKind.INVALID_PARAMS,
            provider="replicate",
            retryable=False,
        )

    async def speak_voice(
        self,
        text: str,
        voice_id: str = "soc-nho",
        tempo: float = 1.10,
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> Artifact:
        from socnhotv.core.adapters.voice_adapter import VoiceAdapter

        return await VoiceAdapter(self.store).synthesize(
            text=text, voice_id=voice_id, tempo=tempo, node_id=node_id, run_id=run_id
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
            "Replicate chưa cấu hình cho vision_analyze; hãy chọn Google Gemini.",
            kind=ProviderErrorKind.INVALID_PARAMS,
            provider="replicate",
            retryable=False,
        )
