"""Provider ảnh AI miễn phí: Pollinations.ai (FLUX / Sana), hỗ trợ ảnh tham chiếu nhân vật."""
from __future__ import annotations

import asyncio
import os
import re
import time
import urllib.parse
from pathlib import Path
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
    ProviderError,
    ProviderErrorKind,
    classify_http_error,
    redact_secrets,
)
from socnhotv.core.providers.spend_guard import SpendGuard
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root

POLLINATIONS_IMAGE_URL = "https://image.pollinations.ai/prompt"
LITTERBOX_API_URL = "https://litterbox.catbox.moe/resources/internals/api.php"

# Bộ nhớ đệm URL công khai tạm thời cho ảnh tham chiếu cục bộ (tránh upload lặp lại)
_UPLOADED_REF_CACHE: Dict[str, str] = {}


def load_pollinations_key() -> Optional[str]:
    """Đọc token Pollen tùy chọn từ biến môi trường hoặc .env."""
    key = os.environ.get("POLLINATIONS_API_KEY", "").strip() or os.environ.get("POLLINATIONS_TOKEN", "").strip()
    if not key:
        root = get_repo_root()
        for fname in (".env.local", ".env"):
            env_file = root / fname
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if stripped.startswith(("POLLINATIONS_API_KEY=", "POLLINATIONS_TOKEN=")):
                        val = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            key = val
                            break
            if key:
                break
    return key or None


class PollinationsProvider(BaseProvider):
    """Adapter gọi Pollinations.ai API: Miễn phí $0, không bắt buộc key, nhận ảnh tham chiếu."""

    def __init__(
        self,
        store: ProjectStore,
        guard: Optional[SpendGuard] = None,
        key: Optional[str] = None,
        source: str = "api",
        transport: Optional[httpx.AsyncBaseTransport] = None,
        max_retries: int = 4,
    ):
        self.store = store
        self.guard = guard or SpendGuard(store.runs_dir)
        self.key = key or load_pollinations_key()
        self.source = source
        self.transport = transport
        self.max_retries = max_retries

    def provider_name(self) -> str:
        return "pollinations"

    def capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "pollinations",
            "supportsFirstFrame": False,
            "supportsImageEdit": True,
            "supportsReferences": True,
            "supportsAudioVideo": False,
            "supportsVision": False,
            "supportsStructuredText": False,
            "aspectRatios": ["16:9", "9:16", "1:1", "4:5"],
            "durationsSec": [],
            "models": ["pollinations-flux", "pollinations-sana", "pollinations-turbo"],
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=self.transport)

    def _resolve_model_id(self, requested: Optional[str]) -> str:
        if not requested:
            return "flux"
        req = requested.lower().strip()
        if req in ("pollinations-flux", "flux"):
            return "flux"
        if req in ("pollinations-sana", "sana"):
            return "sana"
        if req in ("pollinations-turbo", "turbo"):
            return "turbo"
        return req

    def _resolve_dimensions(self, aspect_ratio: str) -> tuple[int, int]:
        ar = (aspect_ratio or "16:9").strip()
        if ar == "9:16":
            return (720, 1280)
        if ar == "1:1":
            return (1024, 1024)
        if ar == "4:5":
            return (864, 1080)
        # Mặc định 16:9
        return (1280, 720)

    def _resolve_reference_file(self, uri: str) -> Optional[Path]:
        """Tìm đường dẫn tệp ảnh tham chiếu trên máy cục bộ."""
        cand = self.store.project_dir / uri
        if cand.exists():
            return cand
        cand_root = get_repo_root() / uri.lstrip("/")
        if cand_root.exists():
            return cand_root
        cand_direct = Path(uri)
        if cand_direct.exists():
            return cand_direct
        return None

    async def _get_public_ref_url(self, client: httpx.AsyncClient, uri: str) -> Optional[str]:
        """Chuyển đổi URI ảnh tham chiếu cục bộ thành URL công khai tạm thời qua host Litterbox."""
        if uri.startswith(("http://", "https://")):
            return uri

        file_path = self._resolve_reference_file(uri)
        if not file_path:
            return None

        cache_key = str(file_path.resolve())
        if cache_key in _UPLOADED_REF_CACHE:
            return _UPLOADED_REF_CACHE[cache_key]

        try:
            data = {"reqtype": "fileupload", "time": "1h"}
            files = {"fileToUpload": (file_path.name, file_path.read_bytes(), "image/png")}
            r = await client.post(LITTERBOX_API_URL, data=data, files=files, timeout=30)
            if r.status_code == 200 and r.text.startswith("http"):
                public_url = r.text.strip()
                _UPLOADED_REF_CACHE[cache_key] = public_url
                return public_url
        except Exception:
            # Nếu host upload tạm lỗi, bỏ qua tham chiếu và fallback về text prompt
            pass
        return None

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
        model_id = self._resolve_model_id(model)
        width, height = self._resolve_dimensions(aspect_ratio)
        out: List[Artifact] = []

        async with self._client() as client:
            ref_url = None
            if references:
                for ref_uri in references:
                    ref_url = await self._get_public_ref_url(client, ref_uri)
                    if ref_url:
                        break

            for i in range(max(1, n)):
                current_seed = (seed + i) if seed is not None else int(time.time() * 1000) % 100000

                encoded_prompt = urllib.parse.quote(prompt)
                query_parts = [
                    f"width={width}",
                    f"height={height}",
                    f"model={model_id}",
                    "nologo=true",
                    f"seed={current_seed}",
                ]
                if ref_url:
                    query_parts.append(f"image={urllib.parse.quote(ref_url)}")
                if self.key:
                    query_parts.append(f"key={urllib.parse.quote(self.key)}")

                request_url = f"{POLLINATIONS_IMAGE_URL}/{encoded_prompt}?{'&'.join(query_parts)}"

                content: Optional[bytes] = None
                content_type: str = "image/jpeg"

                for attempt in range(1, self.max_retries + 1):
                    try:
                        r = await client.get(request_url, timeout=120, follow_redirects=True)
                        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
                            content = r.content
                            content_type = r.headers.get("content-type", "image/jpeg")
                            break

                        if r.status_code in (402, 429):
                            # Rate limit free tier: chờ theo chỉ dẫn
                            msg = r.text
                            match = re.search(r"Retry after (\d+)s", msg)
                            wait_sec = int(match.group(1)) + 2 if match else 46
                            if attempt < self.max_retries:
                                await asyncio.sleep(wait_sec)
                                continue
                            raise ProviderError(
                                f"Pollinations chạm hạn mức tốc độ (Free Limit: 1 img/45s per IP): {msg[:200]}",
                                kind=ProviderErrorKind.QUOTA,
                                provider="pollinations",
                                status_code=r.status_code,
                                retryable=False,
                            )

                        if r.status_code >= 400:
                            raise classify_http_error("pollinations", r.status_code, r.text)

                    except (httpx.TimeoutException, httpx.TransportError) as exc:
                        if attempt < self.max_retries:
                            await asyncio.sleep(3 * attempt)
                            continue
                        raise ProviderError(
                            f"Lỗi kết nối tới Pollinations API: {exc}",
                            kind=ProviderErrorKind.TRANSIENT,
                            provider="pollinations",
                            retryable=True,
                        ) from exc

                if not content:
                    raise ProviderError(
                        "Pollinations không trả về dữ liệu ảnh sau các lần thử.",
                        kind=ProviderErrorKind.UNKNOWN,
                        provider="pollinations",
                    )

                ext = "png" if "png" in content_type else "jpg"
                now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

                artifact = self.store.store_bytes(
                    data=content,
                    ext=ext,
                    kind=ArtifactKind.IMAGE,
                    meta=ArtifactMeta(
                        width=width,
                        height=height,
                        aspect=aspect_ratio,
                    ),
                    provenance=ArtifactProvenance(
                        node_id=node_id,
                        run_id=run_id,
                        provider="pollinations",
                        model=model_id,
                        cost_usd=0.0,
                        created_at=now_iso,
                        params={
                            "prompt": prompt,
                            "aspectRatio": aspect_ratio,
                            "resolution": resolution,
                            "seed": current_seed,
                            "references": references or [],
                            "reference_url": ref_url,
                        },
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
            "Pollinations provider chuyên dụng cho sinh ảnh, chưa hỗ trợ sinh video trực tiếp.",
            kind=ProviderErrorKind.INVALID_PARAMS,
            provider="pollinations",
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
        raise ProviderError(
            "Pollinations provider không hỗ trợ TTS giọng nói. Sử dụng OmniVoice chạy trên máy cục bộ ($0).",
            kind=ProviderErrorKind.INVALID_PARAMS,
            provider="pollinations",
            retryable=False,
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
            "Pollinations provider chưa cấu hình vision analysis.",
            kind=ProviderErrorKind.INVALID_PARAMS,
            provider="pollinations",
            retryable=False,
        )
