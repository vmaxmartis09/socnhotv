"""Bộ định tuyến đa Provider (ProviderRouter) với giới hạn luồng riêng (rate-limit) cho từng nhà cung cấp."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from socnhotv.core.contracts.types import Artifact
from socnhotv.core.models_registry.registry import ModelRegistry
from socnhotv.core.providers.base import BaseProvider
from socnhotv.core.providers.errors import MissingApiKey
from socnhotv.core.providers.fal_provider import FalProvider
from socnhotv.core.providers.google_provider import GoogleProvider
from socnhotv.core.providers.key_vault import KeyVault
from socnhotv.core.providers.mock_provider import MockProvider
from socnhotv.core.providers.replicate_provider import ReplicateProvider
from socnhotv.core.providers.spend_guard import SpendGuard
from socnhotv.core.storage.project_store import ProjectStore

DEFAULT_PROVIDER_LIMITS: Dict[str, int] = {
    "google": 2,
    "fal": 3,
    "replicate": 2,
    "mock": 8,
}


def resolve_provider_for_model(model: Optional[str], default_provider: str = "google") -> str:
    """Tra cứu tên provider ('google', 'fal', 'replicate', 'mock', 'local_tool') từ model key."""
    if not model:
        return default_provider
    m_low = model.strip().lower()
    if m_low.startswith("mock"):
        return "mock"
    spec = ModelRegistry.get_instance().get(model)
    if spec:
        return spec.provider
    if m_low.startswith(("fal-", "fal/", "fal-ai/")):
        return "fal"
    if m_low.startswith("replicate"):
        return "replicate"
    if any(k in m_low for k in ("gemini", "veo", "imagen", "google")):
        return "google"
    return default_provider


class ProviderRouter(BaseProvider):
    """Định tuyến các lệnh sinh ảnh/video/văn bản/thị giác sang đúng Provider thật hoặc Mock."""

    def __init__(
        self,
        store: ProjectStore,
        guard: Optional[SpendGuard] = None,
        vault: Optional[KeyVault] = None,
        mock_mode: bool = False,
        fallback_to_mock: bool = False,
        provider_limits: Optional[Dict[str, int]] = None,
        providers: Optional[Dict[str, BaseProvider]] = None,
        source: str = "api",
    ):
        self.store = store
        self.guard = guard or SpendGuard(store.runs_dir)
        self.vault = vault or KeyVault(persist_local=False)
        self.mock_mode = mock_mode
        self.fallback_to_mock = fallback_to_mock
        self.source = source
        self._mock = MockProvider(store)
        self._instances: Dict[str, BaseProvider] = {"mock": self._mock}
        if providers:
            self._instances.update(providers)

        limits = dict(DEFAULT_PROVIDER_LIMITS)
        if provider_limits:
            limits.update(provider_limits)
        self._semaphores: Dict[str, asyncio.Semaphore] = {
            k: asyncio.Semaphore(max(1, int(v))) for k, v in limits.items()
        }

    def provider_name(self) -> str:
        return "mock" if self.mock_mode else "router"

    def _sem_for(self, pname: str) -> asyncio.Semaphore:
        if pname not in self._semaphores:
            self._semaphores[pname] = asyncio.Semaphore(2)
        return self._semaphores[pname]

    def get_provider(self, pname: str) -> BaseProvider:
        if self.mock_mode or pname == "mock":
            return self._mock
        if pname in self._instances:
            return self._instances[pname]

        try:
            if pname in ("google", "gemini"):
                key = self.vault.require_key("gemini")
                inst: BaseProvider = GoogleProvider(
                    self.store, guard=self.guard, key=key, source=self.source
                )
            elif pname == "fal":
                key = self.vault.require_key("fal")
                inst = FalProvider(
                    self.store, guard=self.guard, key=key, source=self.source
                )
            elif pname == "replicate":
                key = self.vault.require_key("replicate")
                inst = ReplicateProvider(
                    self.store, guard=self.guard, key=key, source=self.source
                )
            else:
                return self._mock
        except MissingApiKey:
            if self.fallback_to_mock:
                return self._mock
            raise

        self._instances[pname] = inst
        return inst

    def _pick(self, model: Optional[str], default_provider: str = "google") -> tuple[str, BaseProvider]:
        if self.mock_mode:
            return "mock", self._mock
        pname = resolve_provider_for_model(model, default_provider=default_provider)
        if pname == "local_tool":
            pname = "mock"
        # Nếu model mặc định là mock-* khi đang bật chế độ thật -> tự nâng sang provider thật khả dụng
        if pname == "mock":
            if "google" in self._instances or self.vault.has_valid_key("gemini"):
                pname = "google"
            elif "fal" in self._instances or self.vault.has_valid_key("fal"):
                pname = "fal"
            else:
                pname = default_provider
        prov = self.get_provider(pname)
        return prov.provider_name(), prov

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
        pname, prov = self._pick(model, default_provider="google")
        effective_model = None if (model and model.startswith("mock")) else model
        async with self._sem_for(pname):
            return await prov.generate_images(
                prompt=prompt,
                references=references,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                n=n,
                seed=seed,
                node_id=node_id,
                run_id=run_id,
                model=effective_model,
            )

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
        pname, prov = self._pick(model, default_provider="google")
        effective_model = None if (model and model.startswith("mock")) else model
        async with self._sem_for(pname):
            return await prov.edit_image(
                image_uri=image_uri,
                prompt=prompt,
                references=references,
                aspect_ratio=aspect_ratio,
                node_id=node_id,
                run_id=run_id,
                model=effective_model,
            )

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
        pname, prov = self._pick(model, default_provider="google")
        effective_model = None if (model and model.startswith("mock")) else model
        async with self._sem_for(pname):
            return await prov.generate_video(
                prompt=prompt,
                first_frame_uri=first_frame_uri,
                duration_sec=duration_sec,
                aspect_ratio=aspect_ratio,
                has_audio=has_audio,
                node_id=node_id,
                run_id=run_id,
                last_frame_uri=last_frame_uri,
                references=references,
                model=effective_model,
                cancel_event=cancel_event,
            )

    async def speak_voice(
        self,
        text: str,
        voice_id: str = "soc-nho",
        tempo: float = 1.10,
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> Artifact:
        if self.mock_mode:
            return await self._mock.speak_voice(
                text=text, voice_id=voice_id, tempo=tempo, node_id=node_id, run_id=run_id
            )
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
        pname, prov = self._pick(model or "gemini-2.5-flash", default_provider="google")
        async with self._sem_for(pname):
            return await prov.analyze_vision(
                media_uri=media_uri,
                prompt=prompt,
                node_id=node_id,
                run_id=run_id,
                schema=schema,
                model=model,
            )

    async def text_complete(
        self,
        system: str,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        pname, prov = self._pick(model or "gemini-2.5-flash", default_provider="google")
        async with self._sem_for(pname):
            return await prov.text_complete(
                system=system,
                prompt=prompt,
                schema=schema,
                model=model,
            )
