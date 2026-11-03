"""Provider thật cho fal.ai Queue API (FLUX ảnh, Kontext sửa ảnh, Kling v3 & LTX Video).

Tái sử dụng và nâng cấp bất đồng bộ quy trình hàng đợi từ video_gen_backends.py:
submit -> poll status_url -> fetch response_url -> download binary -> lưu ProjectStore,
kèm khóa chi tiêu cứng SpendGuard, hỗ trợ hủy qua cancel_url và che khóa FAL_KEY.
"""
from __future__ import annotations

import asyncio
import base64
import mimetypes
import time
from pathlib import Path
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
    MissingApiKey,
    ProviderError,
    ProviderErrorKind,
    classify_http_error,
    redact_secrets,
)
from socnhotv.core.providers.key_vault import KeyVault, validate_key_format
from socnhotv.core.providers.spend_guard import SpendGuard
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root

FAL_QUEUE_BASE = "https://queue.fal.run"
DEFAULT_FAL_IMAGE_KEY = "fal-flux-schnell"
DEFAULT_FAL_EDIT_KEY = "fal-flux-kontext"
DEFAULT_FAL_VIDEO_KEY = "fal-kling-v3-std"

_ASPECT_TO_FAL_SIZE = {
    "9:16": "portrait_16_9",
    "16:9": "landscape_16_9",
    "1:1": "square_hd",
    "4:5": "portrait_4_3",
}


def load_fal_key(repo_root: Optional[Path] = None) -> str:
    """Đọc khóa FAL_KEY từ biến môi trường, kho khóa hoặc .env ở gốc repo."""
    vault = KeyVault(repo_root=repo_root, persist_local=False)
    raw = vault.get_raw_key("fal")
    return validate_key_format("fal", raw)


def file_to_data_uri(path: Path) -> str:
    """Chuyển tệp ảnh cục bộ thành Data URI base64 để truyền thẳng vào fal.ai Queue."""
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def estimate_fal_image_usd(n: int = 1, model: Optional[str] = None) -> float:
    key = model or DEFAULT_FAL_IMAGE_KEY
    cost = ModelRegistry.get_instance().estimate_cost(key, num_images=max(1, n))
    return cost if cost > 0 else round(0.003 * max(1, n), 4)


def estimate_fal_video_usd(
    duration_sec: float = 8.0,
    model: Optional[str] = None,
    has_audio: bool = False,
) -> float:
    key = model or DEFAULT_FAL_VIDEO_KEY
    base = ModelRegistry.get_instance().estimate_cost(key, duration_sec=duration_sec)
    if base <= 0:
        base = round(0.084 * float(duration_sec), 4)
    if has_audio and "kling" in key.lower():
        base = round(base * 1.5, 4)
    return base


class FalProvider(BaseProvider):
    """Adapter chính thức cho fal.ai Queue API."""

    def __init__(
        self,
        store: ProjectStore,
        guard: Optional[SpendGuard] = None,
        key: Optional[str] = None,
        poll_interval_sec: float = 4.0,
        timeout_sec: float = 900.0,
        source: str = "api",
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.store = store
        self.guard = guard or SpendGuard(store.runs_dir)
        self.key = key or load_fal_key()
        self.poll_interval_sec = poll_interval_sec
        self.timeout_sec = timeout_sec
        self.source = source
        self.transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=self.transport)

    def provider_name(self) -> str:
        return "fal"

    def capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "fal",
            "supportsFirstFrame": True,
            "supportsLastFrame": False,
            "supportsImageEdit": True,
            "supportsReferences": True,
            "supportsAudioVideo": True,
            "supportsVision": False,
            "supportsStructuredText": False,
            "aspectRatios": ["9:16", "16:9", "1:1", "4:5"],
            "durationsSec": [5, 8, 10],
            "models": [m.key for m in ModelRegistry.get_instance().list_by_provider("fal")],
        }

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Key {self.key}", "Content-Type": "application/json"}

    def _resolve_endpoint(self, requested: Optional[str], default_key: str) -> str:
        target = requested or default_key
        spec = ModelRegistry.get_instance().get(target)
        if spec and spec.provider == "fal":
            return spec.model_id
        if "/" in target:
            return target
        fallback = ModelRegistry.get_instance().get(default_key)
        return fallback.model_id if fallback else "fal-ai/flux/schnell"

    def _resolve_local_file(self, uri: str) -> Path:
        p = self.store.project_dir / uri
        if p.exists():
            return p
        alt = get_repo_root() / uri.lstrip("/")
        if alt.exists():
            return alt
        raise ProviderError(
            f"Không tìm thấy tệp tham chiếu '{uri}' trong thư mục dự án.",
            kind=ProviderErrorKind.INVALID_PARAMS,
            provider="fal",
            retryable=False,
        )

    async def _request_json(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        json_body: Optional[Dict[str, Any]] = None,
        timeout: float = 120.0,
    ) -> Dict[str, Any]:
        try:
            r = await client.request(
                method,
                url,
                headers=self._headers(),
                json=json_body,
                timeout=timeout,
            )
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise ProviderError(
                f"Lỗi kết nối tạm thời tới fal.ai: {exc}",
                kind=ProviderErrorKind.TRANSIENT,
                provider="fal",
                retryable=True,
                extra_secrets=[self.key],
            ) from exc
        if r.status_code >= 400:
            raise classify_http_error("fal", r.status_code, r.text, extra_secrets=[self.key])
        return r.json()

    async def _download_bytes(self, client: httpx.AsyncClient, url: str) -> bytes:
        try:
            r = await client.get(url, timeout=300.0, follow_redirects=True)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise ProviderError(
                f"Lỗi tải kết quả media từ fal.ai: {exc}",
                kind=ProviderErrorKind.TRANSIENT,
                provider="fal",
                retryable=True,
                extra_secrets=[self.key],
            ) from exc
        if r.status_code >= 400:
            raise classify_http_error("fal", r.status_code, r.text, extra_secrets=[self.key])
        return r.content

    async def _submit_and_poll(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        body: Dict[str, Any],
        reserve_cost: float,
        reserve_label: str,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> Dict[str, Any]:
        """Thực thi trọn vẹn chu trình fal.ai Queue: Submit -> Poll -> Fetch Response."""
        try:
            job = await self._request_json(
                client,
                "POST",
                f"{FAL_QUEUE_BASE}/{endpoint.lstrip('/')}",
                json_body=body,
                timeout=120.0,
            )
        except ProviderError as err:
            if err.kind in (
                ProviderErrorKind.AUTH,
                ProviderErrorKind.INVALID_PARAMS,
                ProviderErrorKind.QUOTA,
                ProviderErrorKind.CONTENT_BLOCKED,
            ):
                self.guard.refund(reserve_cost, reserve_label, source=self.source)
            raise

        # Nếu phản hồi đã chứa thẳng media (trường hợp đồng bộ), trả ngay
        if "images" in job or "video" in job or "image" in job:
            return job

        status_url = job.get("status_url")
        response_url = job.get("response_url")
        cancel_url = job.get("cancel_url")
        if not status_url or not response_url:
            raise ProviderError(
                f"Phản hồi hàng đợi fal.ai thiếu status_url/response_url: {redact_secrets(str(job)[:240], [self.key])}",
                kind=ProviderErrorKind.UNKNOWN,
                provider="fal",
                retryable=False,
            )

        deadline = time.monotonic() + self.timeout_sec
        while time.monotonic() < deadline:
            if cancel_event is not None and cancel_event.is_set():
                if cancel_url:
                    try:
                        await client.put(cancel_url, headers=self._headers(), timeout=15.0)
                    except Exception:
                        pass
                raise ProviderError(
                    f"Đã hủy tác vụ trên hàng đợi fal.ai ({job.get('request_id', '')}).",
                    kind=ProviderErrorKind.CANCELLED,
                    provider="fal",
                    retryable=False,
                )

            st = await self._request_json(client, "GET", status_url, timeout=60.0)
            state = str(st.get("status", "")).upper()
            if state == "COMPLETED":
                break
            if state in ("FAILED", "ERROR", "CANCELLED", "CANCELED"):
                err_detail = str(st.get("error") or st)
                kind = (
                    ProviderErrorKind.CONTENT_BLOCKED
                    if any(w in err_detail.lower() for w in ("nsfw", "safety", "policy", "blocked"))
                    else ProviderErrorKind.UNKNOWN
                )
                raise ProviderError(
                    f"Tác vụ fal.ai thất bại ({state}): {err_detail[:300]}",
                    kind=kind,
                    provider="fal",
                    retryable=False,
                    extra_secrets=[self.key],
                )
            await asyncio.sleep(self.poll_interval_sec)
        else:
            raise ProviderError(
                f"Tác vụ fal.ai ({endpoint}) chưa hoàn tất sau {int(self.timeout_sec)}s.",
                kind=ProviderErrorKind.TRANSIENT,
                provider="fal",
                retryable=False,
            )

        return await self._request_json(client, "GET", response_url, timeout=90.0)

    # ---- Ảnh (FLUX.1 / Kontext) ----
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
        default_key = DEFAULT_FAL_EDIT_KEY if references else DEFAULT_FAL_IMAGE_KEY
        endpoint = self._resolve_endpoint(model, default_key)
        count = max(1, int(n))
        total_cost = estimate_fal_image_usd(count, model=model or default_key)
        label = f"fal ảnh {node_id} x{count}"
        self.guard.reserve(total_cost, label, source=self.source)

        body: Dict[str, Any] = {
            "prompt": prompt,
            "num_images": count,
            "image_size": _ASPECT_TO_FAL_SIZE.get(aspect_ratio, "portrait_16_9"),
            "aspect_ratio": aspect_ratio,
        }
        if seed is not None:
            body["seed"] = int(seed)
        if references:
            ref_path = self._resolve_local_file(references[0])
            body["image_url"] = file_to_data_uri(ref_path)

        out: List[Artifact] = []
        async with self._client() as client:
            result = await self._submit_and_poll(
                client=client,
                endpoint=endpoint,
                body=body,
                reserve_cost=total_cost,
                reserve_label=label,
            )
            images = result.get("images") or ([result["image"]] if "image" in result else [])
            if not images:
                raise ProviderError(
                    f"fal.ai không trả danh sách ảnh: {redact_secrets(str(result)[:240], [self.key])}",
                    kind=ProviderErrorKind.UNKNOWN,
                    provider="fal",
                    retryable=False,
                )

            per_img_cost = round(total_cost / max(1, len(images)), 4)
            default_w, default_h = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
            for idx, item in enumerate(images):
                img_url = item.get("url", "")
                if not img_url:
                    continue
                img_bytes = await self._download_bytes(client, img_url)
                ctype = str(item.get("content_type", "image/png")).lower()
                ext = "jpg" if ("jpeg" in ctype or img_url.lower().endswith((".jpg", ".jpeg"))) else "png"
                w = int(item.get("width") or default_w)
                h = int(item.get("height") or default_h)
                out.append(
                    self.store.store_bytes(
                        data=img_bytes,
                        ext=ext,
                        kind=ArtifactKind.IMAGE,
                        provenance=ArtifactProvenance(
                            node_id=node_id,
                            run_id=run_id,
                            provider="fal",
                            model=endpoint,
                            params={
                                "prompt": prompt,
                                "aspectRatio": aspect_ratio,
                                "resolution": resolution,
                                "index": idx,
                                "seed": result.get("seed", seed),
                            },
                            input_hashes=list(references or []),
                            cost_usd=per_img_cost,
                            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        ),
                        meta=ArtifactMeta(width=w, height=h, aspect=aspect_ratio),
                    )
                )
        return out

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
        refs = [image_uri] + list(references or [])
        arts = await self.generate_images(
            prompt=prompt,
            references=refs,
            aspect_ratio=aspect_ratio,
            n=1,
            node_id=node_id,
            run_id=run_id,
            model=model or DEFAULT_FAL_EDIT_KEY,
        )
        return arts[0]

    # ---- Video (Kling v3 / LTX Video trên fal.ai Queue) ----
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
        endpoint = self._resolve_endpoint(model, DEFAULT_FAL_VIDEO_KEY)
        if first_frame_uri and endpoint == "fal-ai/ltx-video":
            endpoint = "fal-ai/ltx-video/image-to-video"

        cost = estimate_fal_video_usd(duration_sec, model=model, has_audio=has_audio)
        label = f"fal video {node_id} {duration_sec}s"
        self.guard.reserve(cost, label, source=self.source)

        body: Dict[str, Any] = {"prompt": prompt, "aspect_ratio": aspect_ratio}
        if "kling" in endpoint:
            body["duration"] = str(int(duration_sec))
            body["generate_audio"] = bool(has_audio)
            if first_frame_uri:
                body["start_image_url"] = file_to_data_uri(self._resolve_local_file(first_frame_uri))
        else:
            if first_frame_uri:
                body["image_url"] = file_to_data_uri(self._resolve_local_file(first_frame_uri))

        async with self._client() as client:
            result = await self._submit_and_poll(
                client=client,
                endpoint=endpoint,
                body=body,
                reserve_cost=cost,
                reserve_label=label,
                cancel_event=cancel_event,
            )
            video_info = result.get("video") or {}
            video_url = video_info.get("url") if isinstance(video_info, dict) else None
            if not video_url:
                raise ProviderError(
                    f"fal.ai không trả URL video: {redact_secrets(str(result)[:240], [self.key])}",
                    kind=ProviderErrorKind.UNKNOWN,
                    provider="fal",
                    retryable=False,
                )
            video_bytes = await self._download_bytes(client, video_url)

        width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
        input_hashes = [u for u in [first_frame_uri, last_frame_uri, *(references or [])] if u]
        return self.store.store_bytes(
            data=video_bytes,
            ext="mp4",
            kind=ArtifactKind.VIDEO,
            provenance=ArtifactProvenance(
                node_id=node_id,
                run_id=run_id,
                provider="fal",
                model=endpoint,
                params={
                    "prompt": prompt,
                    "firstFrameUri": first_frame_uri,
                    "durationSec": duration_sec,
                    "aspectRatio": aspect_ratio,
                    "hasAudio": has_audio,
                },
                input_hashes=input_hashes,
                cost_usd=cost,
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            ),
            meta=ArtifactMeta(width=width, height=height, duration=duration_sec, aspect=aspect_ratio),
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
            "fal.ai chưa dùng cho tác vụ phân tích thị giác; hãy chọn model của Google Gemini.",
            kind=ProviderErrorKind.INVALID_PARAMS,
            provider="fal",
            retryable=False,
        )
