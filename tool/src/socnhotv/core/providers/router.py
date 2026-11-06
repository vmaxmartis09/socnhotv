"""Bộ định tuyến đa Provider (ProviderRouter) với giới hạn luồng riêng (rate-limit) cho từng nhà cung cấp."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from socnhotv.core.contracts.types import Artifact, RunPolicy
from socnhotv.core.models_registry.registry import ModelRegistry
from socnhotv.core.providers.base import BaseProvider
from socnhotv.core.providers.errors import MissingApiKey, ProviderError, ProviderErrorKind
from socnhotv.core.providers.fal_provider import FalProvider
from socnhotv.core.providers.google_provider import GoogleProvider
from socnhotv.core.providers.key_vault import KeyVault
from socnhotv.core.providers.mock_provider import MockProvider
from socnhotv.core.providers.replicate_provider import ReplicateProvider
from socnhotv.core.providers.spend_guard import SpendGuard
from socnhotv.core.storage.project_store import ProjectStore

logger = logging.getLogger("socnhotv.core.router")

DEFAULT_PROVIDER_LIMITS: Dict[str, int] = {
    "google": 2,
    "fal": 3,
    "replicate": 2,
    "pollinations": 2,
    "cloudflare": 3,
    "local": 1,
    "mock": 8,
}


def resolve_provider_for_model(model: Optional[str], default_provider: str = "google") -> str:
    """Tra cứu tên provider ('google', 'fal', 'replicate', 'pollinations', 'cloudflare', 'local', 'mock') từ model key."""
    if not model:
        return default_provider
    m_low = model.strip().lower()
    if m_low.startswith("mock"):
        return "mock"
    spec = ModelRegistry.get_instance().get(model)
    if spec and spec.provider:
        return spec.provider.lower()
    if m_low.startswith(("fal-", "fal/", "fal-ai/")):
        return "fal"
    if m_low.startswith("replicate"):
        return "replicate"
    if any(k in m_low for k in ("pollinations", "pollen")):
        return "pollinations"
    if any(k in m_low for k in ("cf-", "cloudflare")):
        return "cloudflare"
    if any(k in m_low for k in ("local-", "mflux")):
        return "local"
    if any(k in m_low for k in ("gemini", "veo", "imagen", "google")):
        return "google"
    return default_provider


def _is_free_or_local_model(model_key: Optional[str]) -> bool:
    """Kiểm tra model có thuộc tier free/local/freemium không tính phí (không bao giờ chuyển sang paid)."""
    if not model_key:
        return False
    if model_key.startswith("mock"):
        return True
    spec = ModelRegistry.get_instance().get(model_key)
    if not spec:
        return False
    # Tuyệt đối cấm tier paid
    if spec.tier in ("paid",):
        return False
    # Kiểm tra chi phí tính toán nếu có định giá
    if spec.pricing:
        if spec.pricing.cost_per_generation and spec.pricing.cost_per_generation > 0:
            return False
        if spec.pricing.cost_per_second and spec.pricing.cost_per_second > 0:
            return False
        if spec.pricing.cost_per_minute and spec.pricing.cost_per_minute > 0:
            return False
    return spec.tier in ("free", "local", "freemium")


class ProviderRouter(BaseProvider):
    """Định tuyến các lệnh sinh ảnh/video/văn bản/thị giác sang đúng Provider thật hoặc Mock theo RunPolicy."""

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
        run_policy: Optional[RunPolicy] = None,
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

        # Chế độ chạy theo hợp đồng C3
        if run_policy is not None:
            self.run_policy = run_policy
        elif mock_mode:
            self.run_policy = RunPolicy(image="mock", video="mock", text="mock", voice="local")
        else:
            self.run_policy = RunPolicy(image="real", video="real", text="real", voice="local")

        limits = dict(DEFAULT_PROVIDER_LIMITS)
        if provider_limits:
            limits.update(provider_limits)
        self._semaphores: Dict[str, asyncio.Semaphore] = {
            k: asyncio.Semaphore(max(1, int(v))) for k, v in limits.items()
        }

    def provider_name(self) -> str:
        # Nếu mọi tài nguyên đều ở chế độ mock thì trả về "mock"
        if (
            self.run_policy.image == "mock"
            and self.run_policy.video in ("mock", "off")
            and self.run_policy.text == "mock"
            and self.run_policy.voice == "mock"
        ):
            return "mock"
        return "router"

    def _sem_for(self, pname: str) -> asyncio.Semaphore:
        if pname not in self._semaphores:
            self._semaphores[pname] = asyncio.Semaphore(2)
        return self._semaphores[pname]

    def get_provider(self, pname: str) -> BaseProvider:
        norm = pname.strip().lower()
        if norm == "mock":
            return self._mock
        if norm in self._instances:
            return self._instances[norm]

        # 1. Tra cứu PROVIDER_FACTORIES (hợp đồng C1 của G1) trước các nhánh cũ:
        try:
            from socnhotv.core.providers.factories import PROVIDER_FACTORIES, PROVIDER_META

            if norm in PROVIDER_FACTORIES:
                factory = PROVIDER_FACTORIES[norm]
                meta = PROVIDER_META.get(norm, {})
                needs_key = bool(meta.get("needs_key", False))
                key = None
                if needs_key:
                    key = self.vault.require_key(norm)
                else:
                    try:
                        key = self.vault.get_raw_key(norm)
                    except Exception:
                        key = None
                inst = factory(self.store, self.guard, key, self.source)
                self._instances[norm] = inst
                return inst
        except ImportError:
            pass
        except MissingApiKey:
            if self.fallback_to_mock:
                return self._mock
            raise

        # 2. Các nhánh cũ nếu chưa có trong factories
        try:
            if norm in ("google", "gemini"):
                key = self.vault.require_key("gemini")
                inst: BaseProvider = GoogleProvider(
                    self.store, guard=self.guard, key=key, source=self.source
                )
            elif norm == "fal":
                key = self.vault.require_key("fal")
                inst = FalProvider(
                    self.store, guard=self.guard, key=key, source=self.source
                )
            elif norm == "replicate":
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

        self._instances[norm] = inst
        return inst

    def _pick(
        self,
        model: Optional[str],
        default_provider: str = "google",
        kind: str = "image",
    ) -> tuple[str, BaseProvider]:
        """Chọn provider dựa trên RunPolicy của từng loại tài nguyên (image, video, text)."""
        # Phân xử theo RunPolicy của từng loại tài nguyên
        if kind == "image" and self.run_policy.image == "mock":
            return "mock", self._mock
        if kind == "video" and self.run_policy.video in ("mock", "off"):
            return "mock", self._mock
        if kind == "text" and self.run_policy.text == "mock":
            return "mock", self._mock

        pname = resolve_provider_for_model(model, default_provider=default_provider)
        if pname == "local_tool":
            pname = "mock"

        # Nếu model chọn là mock-* khi đang ở chế độ real:
        if pname == "mock":
            # Tuyệt đối không tự động rơi sang nguồn trả phí nếu không được yêu cầu
            if kind == "image":
                # Tìm nguồn free/local khả dụng trước
                if self.vault.has_valid_key("cloudflare"):
                    pname = "cloudflare"
                elif "local" in self._instances:
                    pname = "local"
                elif "google" in self._instances or self.vault.has_valid_key("gemini"):
                    pname = "google"
                elif "fal" in self._instances or self.vault.has_valid_key("fal"):
                    pname = "fal"
                else:
                    pname = "mock"
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
        fallback_models: Optional[List[str]] = None,
    ) -> List[Artifact]:
        models_to_try = [model]
        if fallback_models:
            for fb in fallback_models:
                if fb and fb not in models_to_try:
                    models_to_try.append(fb)

        last_err: Optional[Exception] = None
        for idx, cur_model in enumerate(models_to_try):
            # Model dự phòng (idx > 0) BẮT BUỘC chỉ nằm trong các model tier free/local
            if idx > 0:
                if not _is_free_or_local_model(cur_model):
                    logger.warning(
                        f"Bỏ qua model dự phòng '{cur_model}' vì không phải nguồn free/local "
                        f"(Luật an toàn chi phí)."
                    )
                    continue

            pname, prov = self._pick(cur_model, default_provider="google", kind="image")
            effective_model = None if (cur_model and cur_model.startswith("mock")) else cur_model
            try:
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
            except (ProviderError, MissingApiKey) as err:
                is_quota_or_auth = isinstance(err, MissingApiKey) or (
                    isinstance(err, ProviderError)
                    and (
                        getattr(err, "kind", None) in (ProviderErrorKind.QUOTA, ProviderErrorKind.AUTH)
                        or getattr(err, "error_kind", None) in (ProviderErrorKind.QUOTA, ProviderErrorKind.AUTH)
                    )
                )
                if is_quota_or_auth and idx < len(models_to_try) - 1:
                    logger.warning(
                        f"Model '{cur_model}' ({pname}) gặp lỗi quota/auth ({err}). "
                        f"Thử sang model dự phòng tiếp theo..."
                    )
                    last_err = err
                    continue
                raise err
            except Exception as err:
                raise err

        if last_err:
            raise last_err
        return []

    async def edit_image(
        self,
        image_uri: str,
        prompt: str,
        references: Optional[List[str]] = None,
        aspect_ratio: str = "9:16",
        node_id: str = "unknown",
        run_id: str = "run_default",
        model: Optional[str] = None,
        fallback_models: Optional[List[str]] = None,
    ) -> Artifact:
        models_to_try = [model]
        if fallback_models:
            for fb in fallback_models:
                if fb and fb not in models_to_try:
                    models_to_try.append(fb)

        last_err: Optional[Exception] = None
        for idx, cur_model in enumerate(models_to_try):
            if idx > 0 and not _is_free_or_local_model(cur_model):
                logger.warning(f"Bỏ qua model dự phòng '{cur_model}' vì không phải nguồn free/local.")
                continue

            pname, prov = self._pick(cur_model, default_provider="google", kind="image")
            effective_model = None if (cur_model and cur_model.startswith("mock")) else cur_model
            try:
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
            except (ProviderError, MissingApiKey) as err:
                is_quota_or_auth = isinstance(err, MissingApiKey) or (
                    isinstance(err, ProviderError)
                    and (
                        getattr(err, "kind", None) in (ProviderErrorKind.QUOTA, ProviderErrorKind.AUTH)
                        or getattr(err, "error_kind", None) in (ProviderErrorKind.QUOTA, ProviderErrorKind.AUTH)
                    )
                )
                if is_quota_or_auth and idx < len(models_to_try) - 1:
                    last_err = err
                    continue
                raise err
            except Exception as err:
                raise err

        if last_err:
            raise last_err
        raise RuntimeError("Không thể chỉnh sửa ảnh")

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
        fallback_models: Optional[List[str]] = None,
    ) -> Artifact:
        models_to_try = [model]
        if fallback_models:
            for fb in fallback_models:
                if fb and fb not in models_to_try:
                    models_to_try.append(fb)

        last_err: Optional[Exception] = None
        for idx, cur_model in enumerate(models_to_try):
            if idx > 0 and not _is_free_or_local_model(cur_model):
                logger.warning(f"Bỏ qua model dự phòng '{cur_model}' vì không phải nguồn free/local.")
                continue

            pname, prov = self._pick(cur_model, default_provider="google", kind="video")
            effective_model = None if (cur_model and cur_model.startswith("mock")) else cur_model
            try:
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
            except (ProviderError, MissingApiKey) as err:
                is_quota_or_auth = isinstance(err, MissingApiKey) or (
                    isinstance(err, ProviderError)
                    and (
                        getattr(err, "kind", None) in (ProviderErrorKind.QUOTA, ProviderErrorKind.AUTH)
                        or getattr(err, "error_kind", None) in (ProviderErrorKind.QUOTA, ProviderErrorKind.AUTH)
                    )
                )
                if is_quota_or_auth and idx < len(models_to_try) - 1:
                    last_err = err
                    continue
                raise err
            except Exception as err:
                raise err

        if last_err:
            raise last_err
        raise RuntimeError("Không thể sinh video")

    async def speak_voice(
        self,
        text: str,
        voice_id: str = "soc-nho",
        tempo: float = 1.10,
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> Artifact:
        """Đọc giọng theo RunPolicy: nếu voice == 'mock' thì dùng mock, còn lại luôn dùng VoiceAdapter local."""
        if self.run_policy.voice == "mock":
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
        pname, prov = self._pick(model or "gemini-2.5-flash", default_provider="google", kind="text")
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
        pname, prov = self._pick(model or "gemini-2.5-flash", default_provider="google", kind="text")
        async with self._sem_for(pname):
            return await prov.text_complete(
                system=system,
                prompt=prompt,
                schema=schema,
                model=model,
            )
