"""Provider đám mây dự phòng: Cloudflare Workers AI (FLUX.1-schnell), 10.000 neurons/ngày free."""
from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, List, Optional

import httpx

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
)
from socnhotv.core.providers.base import BaseProvider
from socnhotv.core.providers.errors import (
    MissingApiKey,
    ProviderError,
    ProviderErrorKind,
    classify_http_error,
)
from socnhotv.core.providers.spend_guard import SpendGuard
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root

DEFAULT_CF_MODEL = "@cf/black-forest-labs/flux-1-schnell"


def load_cloudflare_credentials() -> tuple[str, str]:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()

    if not (token and account_id):
        root = get_repo_root()
        for fname in (".env.local", ".env"):
            env_file = root / fname
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if stripped.startswith("CLOUDFLARE_API_TOKEN="):
                        token = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                    elif stripped.startswith("CLOUDFLARE_ACCOUNT_ID="):
                        account_id = stripped.split("=", 1)[1].strip().strip('"').strip("'")
            if token and account_id:
                break
    return token, account_id


class CloudflareProvider(BaseProvider):
    """Adapter gọi Cloudflare Workers AI: Free tier 10.000 neurons/ngày (~55 ảnh FLUX/ngày)."""

    def __init__(
        self,
        store: ProjectStore,
        guard: Optional[SpendGuard] = None,
        key: Optional[str] = None,
        account_id: Optional[str] = None,
        source: str = "api",
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.store = store
        self.guard = guard or SpendGuard(store.runs_dir)
        env_token, env_acc = load_cloudflare_credentials()
        self.token = key or env_token
        self.account_id = account_id or env_acc
        self.source = source
        self.transport = transport

    def provider_name(self) -> str:
        return "cloudflare"

    def capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "cloudflare",
            "supportsFirstFrame": False,
            "supportsImageEdit": False,
            "supportsReferences": False,
            "supportsAudioVideo": False,
            "supportsVision": False,
            "supportsStructuredText": False,
            "aspectRatios": ["1:1", "16:9"],
            "durationsSec": [],
            "models": ["cf-flux-schnell"],
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=self.transport)

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
        if not self.token or not self.account_id:
            raise MissingApiKey(
                "Chưa có CLOUDFLARE_API_TOKEN hoặc CLOUDFLARE_ACCOUNT_ID trong .env. "
                "Tạo token miễn phí tại https://dash.cloudflare.com/profile/api-tokens.",
                provider="cloudflare",
            )

        api_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{DEFAULT_CF_MODEL}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        width, height = (1024, 576) if aspect_ratio == "16:9" else (1024, 1024)
        out: List[Artifact] = []

        async with self._client() as client:
            for i in range(max(1, n)):
                body: Dict[str, Any] = {
                    "prompt": prompt,
                    "num_steps": 4,
                }
                if seed is not None:
                    body["seed"] = int(seed) + i

                try:
                    r = await client.post(api_url, headers=headers, json=body, timeout=60)
                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    raise ProviderError(
                        f"Lỗi kết nối tới Cloudflare Workers AI: {exc}",
                        kind=ProviderErrorKind.TRANSIENT,
                        provider="cloudflare",
                        retryable=True,
                    ) from exc

                if r.status_code == 429:
                    raise ProviderError(
                        "Cloudflare Workers AI chạm giới hạn 10.000 neurons/ngày của gói Free.",
                        kind=ProviderErrorKind.QUOTA,
                        provider="cloudflare",
                        status_code=429,
                        retryable=False,
                    )
                if r.status_code >= 400:
                    raise classify_http_error("cloudflare", r.status_code, r.text, extra_secrets=[self.token])

                data = r.content
                now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

                artifact = self.store.store_bytes(
                    data=data,
                    ext="jpg",
                    kind=ArtifactKind.IMAGE,
                    meta=ArtifactMeta(width=width, height=height, aspect=aspect_ratio),
                    provenance=ArtifactProvenance(
                        node_id=node_id,
                        run_id=run_id,
                        provider="cloudflare",
                        model="cf-flux-schnell",
                        cost_usd=0.0,
                        created_at=now_iso,
                        params={"prompt": prompt, "aspectRatio": aspect_ratio, "steps": 4},
                    ),
                )
                out.append(artifact)

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
            "Cloudflare Workers AI chưa hỗ trợ model sinh video trực tiếp.",
            kind=ProviderErrorKind.INVALID_PARAMS,
            provider="cloudflare",
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
            "Cloudflare Workers AI không dùng cho giọng nói hoạt hình tiếng Việt (dùng OmniVoice).",
            kind=ProviderErrorKind.INVALID_PARAMS,
            provider="cloudflare",
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
            "Chưa cấu hình analyze_vision trên Cloudflare.",
            kind=ProviderErrorKind.INVALID_PARAMS,
            provider="cloudflare",
        )
