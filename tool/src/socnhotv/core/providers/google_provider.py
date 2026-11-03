"""Provider thật: Google Gemini (ảnh Nano Banana, văn bản, thị giác) & Veo (video), kèm khóa chi tiêu cứng."""
from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
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
from socnhotv.core.models_registry.registry import ModelRegistry
from socnhotv.core.providers.base import BaseProvider
from socnhotv.core.providers.errors import (
    MissingApiKey,
    ProviderError,
    ProviderErrorKind,
    classify_http_error,
    redact_secrets,
)
from socnhotv.core.providers.spend_guard import SpendGuard
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root

API = "https://generativelanguage.googleapis.com/v1beta"
IMAGE_MODEL = "gemini-2.5-flash-image"
VISION_MODEL = "gemini-2.5-flash"
TEXT_MODEL = "gemini-2.5-flash"
VIDEO_MODEL = "veo-3.1-fast-generate-preview"

IMAGE_COST_USD = float(os.environ.get("SOCNHOTV_IMAGE_COST_USD", "0.04"))
VIDEO_COST_PER_SEC_USD = float(os.environ.get("SOCNHOTV_VIDEO_COST_PER_SEC_USD", "0.40"))
TEXT_COST_USD = float(os.environ.get("SOCNHOTV_TEXT_COST_USD", "0.005"))


def load_gemini_key() -> str:
    """Đọc khóa Gemini từ biến môi trường hoặc .env.local / .env ở gốc repo."""
    key = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip()
    if not key:
        root = get_repo_root()
        for fname in (".env.local", ".env"):
            env_file = root / fname
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if stripped.startswith(("GEMINI_API_KEY=", "GOOGLE_API_KEY=")):
                        val = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            key = val
                            break
            if key:
                break
    if not key:
        raise MissingApiKey(
            "Chưa có GEMINI_API_KEY (biến môi trường, kho khóa máy chủ hoặc tệp .env ở gốc repo).",
            provider="google",
        )
    if not key.isascii() or " " in key or len(key) < 20:
        raise MissingApiKey(
            "GEMINI_API_KEY không giống khóa thật (còn là chữ giữ chỗ, có dấu hoặc quá ngắn). "
            "Dán khóa lấy từ Google AI Studio (thường bắt đầu bằng AIza).",
            provider="google",
        )
    return key


def estimate_image_usd(n: int = 1, model: Optional[str] = None) -> float:
    if model:
        reg_cost = ModelRegistry.get_instance().estimate_cost(model, num_images=max(1, n))
        if reg_cost > 0:
            return reg_cost
    return IMAGE_COST_USD * max(1, n)


def estimate_video_usd(duration_sec: float, model: Optional[str] = None) -> float:
    if model:
        reg_cost = ModelRegistry.get_instance().estimate_cost(model, duration_sec=duration_sec)
        if reg_cost > 0:
            return reg_cost
    return VIDEO_COST_PER_SEC_USD * duration_sec


class GoogleProvider(BaseProvider):
    """Adapter chính thức gọi Google Generative Language API (Gemini & Veo)."""

    def __init__(
        self,
        store: ProjectStore,
        guard: Optional[SpendGuard] = None,
        key: Optional[str] = None,
        poll_interval_sec: float = 10.0,
        max_poll_attempts: int = 90,
        source: str = "api",
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.store = store
        self.guard = guard or SpendGuard(store.runs_dir)
        self.key = key or load_gemini_key()
        self.poll_interval_sec = poll_interval_sec
        self.max_poll_attempts = max_poll_attempts
        self.source = source
        self.transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=self.transport)

    def provider_name(self) -> str:
        return "google"

    def capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "google",
            "supportsFirstFrame": True,
            "supportsLastFrame": True,
            "supportsImageEdit": True,
            "supportsReferences": True,
            "supportsAudioVideo": True,
            "supportsVision": True,
            "supportsStructuredText": True,
            "aspectRatios": ["9:16", "16:9", "1:1", "4:5"],
            "durationsSec": [4, 5, 6, 8],
            "models": [m.key for m in ModelRegistry.get_instance().list_by_provider("google")],
        }

    def _resolve_model_id(self, requested: Optional[str], default_model_id: str) -> str:
        if not requested:
            return default_model_id
        spec = ModelRegistry.get_instance().get(requested)
        if spec and spec.provider == "google":
            return spec.model_id
        return requested

    def _headers(self) -> Dict[str, str]:
        return {"x-goog-api-key": self.key, "Content-Type": "application/json"}

    async def _post(self, client: httpx.AsyncClient, url: str, body: Dict[str, Any]) -> Dict[str, Any]:
        try:
            r = await client.post(url, headers=self._headers(), json=body, timeout=180)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise ProviderError(
                f"Lỗi kết nối tạm thời tới Google API: {exc}",
                kind=ProviderErrorKind.TRANSIENT,
                provider="google",
                retryable=True,
                extra_secrets=[self.key],
            ) from exc
        if r.status_code >= 400:
            raise classify_http_error("google", r.status_code, r.text, extra_secrets=[self.key])
        return r.json()

    async def _get(self, client: httpx.AsyncClient, url: str, timeout: float = 60.0) -> httpx.Response:
        try:
            r = await client.get(url, headers={"x-goog-api-key": self.key}, timeout=timeout, follow_redirects=True)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise ProviderError(
                f"Lỗi kết nối tạm thời khi thăm dò Google API: {exc}",
                kind=ProviderErrorKind.TRANSIENT,
                provider="google",
                retryable=True,
                extra_secrets=[self.key],
            ) from exc
        if r.status_code >= 400:
            raise classify_http_error("google", r.status_code, r.text, extra_secrets=[self.key])
        return r

    def _read_uri(self, uri: str) -> tuple[bytes, str]:
        candidate = Path_or_rel = self.store.project_dir / uri
        if not Path_or_rel.exists():
            alt = get_repo_root() / uri.lstrip("/")
            if alt.exists():
                candidate = alt
        data = candidate.read_bytes()
        guessed, _ = mimetypes.guess_type(str(candidate))
        if guessed:
            return data, guessed
        ext = candidate.suffix.lower().lstrip(".")
        return data, "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext or 'png'}"

    def _check_safety_blocks(self, resp: Dict[str, Any]) -> None:
        block_reason = resp.get("promptFeedback", {}).get("blockReason")
        if block_reason:
            raise ProviderError(
                f"Google Gemini chặn prompt do chính sách an toàn ({block_reason}).",
                kind=ProviderErrorKind.CONTENT_BLOCKED,
                provider="google",
                retryable=False,
            )
        for cand in resp.get("candidates", []):
            finish = str(cand.get("finishReason", "")).upper()
            if finish in ("SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "IMAGE_SAFETY"):
                raise ProviderError(
                    f"Google Gemini từ chối sinh nội dung ({finish}).",
                    kind=ProviderErrorKind.CONTENT_BLOCKED,
                    provider="google",
                    retryable=False,
                )

    # ---- Ảnh (Tạo & Sửa) ----
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
        model_id = self._resolve_model_id(model, IMAGE_MODEL)
        unit_cost = estimate_image_usd(1, model=model)
        out: List[Artifact] = []

        async with self._client() as client:
            for _ in range(max(1, n)):
                label = f"ảnh {node_id}"
                self.guard.reserve(unit_cost, label, source=self.source)
                try:
                    parts: List[Dict[str, Any]] = []
                    for ref in references or []:
                        data, mime = self._read_uri(ref)
                        parts.append(
                            {
                                "inlineData": {
                                    "mimeType": mime,
                                    "data": base64.b64encode(data).decode(),
                                }
                            }
                        )
                    parts.append({"text": prompt})
                    gen_cfg: Dict[str, Any] = {
                        "responseModalities": ["IMAGE"],
                        "imageConfig": {"aspectRatio": aspect_ratio},
                    }
                    if seed is not None:
                        gen_cfg["seed"] = int(seed)

                    resp = await self._post(
                        client,
                        f"{API}/models/{model_id}:generateContent",
                        {"contents": [{"parts": parts}], "generationConfig": gen_cfg},
                    )
                    self._check_safety_blocks(resp)
                except ProviderError as err:
                    if err.kind in (
                        ProviderErrorKind.AUTH,
                        ProviderErrorKind.INVALID_PARAMS,
                        ProviderErrorKind.QUOTA,
                        ProviderErrorKind.CONTENT_BLOCKED,
                    ):
                        self.guard.refund(unit_cost, label, source=self.source)
                    raise

                img = next(
                    (
                        p["inlineData"]
                        for c in resp.get("candidates", [])
                        for p in c.get("content", {}).get("parts", [])
                        if "inlineData" in p
                    ),
                    None,
                )
                if not img:
                    raise ProviderError(
                        f"Gemini không trả ảnh: {redact_secrets(str(resp)[:300], [self.key])}",
                        kind=ProviderErrorKind.UNKNOWN,
                        provider="google",
                        retryable=False,
                    )
                mime = img.get("mimeType", "image/png")
                width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
                out.append(
                    self.store.store_bytes(
                        data=base64.b64decode(img["data"]),
                        ext="jpg" if "jpeg" in mime else "png",
                        kind=ArtifactKind.IMAGE,
                        provenance=ArtifactProvenance(
                            node_id=node_id,
                            run_id=run_id,
                            provider="google",
                            model=model_id,
                            params={
                                "prompt": prompt,
                                "aspectRatio": aspect_ratio,
                                "resolution": resolution,
                                "seed": seed,
                                "references": references or [],
                            },
                            input_hashes=list(references or []),
                            cost_usd=unit_cost,
                            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        ),
                        meta=ArtifactMeta(width=width, height=height, aspect=aspect_ratio),
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
            model=model,
        )
        return arts[0]

    # ---- Video (Veo Long-Running Operation: submit -> poll -> fetch) ----
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
        model_id = self._resolve_model_id(model, VIDEO_MODEL)
        cost = estimate_video_usd(duration_sec, model=model)
        label = f"video {node_id} {duration_sec}s"
        self.guard.reserve(cost, label, source=self.source)

        instance: Dict[str, Any] = {"prompt": prompt}
        if first_frame_uri:
            data, mime = self._read_uri(first_frame_uri)
            instance["image"] = {
                "bytesBase64Encoded": base64.b64encode(data).decode(),
                "mimeType": mime,
            }
        if last_frame_uri:
            ldata, lmime = self._read_uri(last_frame_uri)
            instance["lastFrame"] = {
                "bytesBase64Encoded": base64.b64encode(ldata).decode(),
                "mimeType": lmime,
            }

        params_body: Dict[str, Any] = {
            "aspectRatio": aspect_ratio,
            "durationSeconds": int(duration_sec),
        }

        async with self._client() as client:
            try:
                op = await self._post(
                    client,
                    f"{API}/models/{model_id}:predictLongRunning",
                    {"instances": [instance], "parameters": params_body},
                )
            except ProviderError as err:
                if err.kind in (
                    ProviderErrorKind.AUTH,
                    ProviderErrorKind.INVALID_PARAMS,
                    ProviderErrorKind.QUOTA,
                    ProviderErrorKind.CONTENT_BLOCKED,
                ):
                    self.guard.refund(cost, label, source=self.source)
                raise

            for _ in range(self.max_poll_attempts):
                if op.get("done"):
                    break
                if cancel_event is not None and cancel_event.is_set():
                    raise ProviderError(
                        f"Đã hủy chờ video Veo ({op.get('name', '')}).",
                        kind=ProviderErrorKind.CANCELLED,
                        provider="google",
                        retryable=False,
                    )
                await asyncio.sleep(self.poll_interval_sec)
                r = await self._get(client, f"{API}/{op['name']}", timeout=60.0)
                op = r.json()

            if not op.get("done"):
                raise ProviderError(
                    "Veo chưa xong sau thời gian chờ tối đa; việc có thể vẫn chạy trên Google: "
                    + redact_secrets(str(op.get("name", "")), [self.key]),
                    kind=ProviderErrorKind.TRANSIENT,
                    provider="google",
                    retryable=False,
                )
            if "error" in op:
                err_msg = str(op["error"].get("message", op["error"]))
                kind = (
                    ProviderErrorKind.CONTENT_BLOCKED
                    if any(w in err_msg.lower() for w in ("safety", "blocked", "policy", "filtered"))
                    else ProviderErrorKind.UNKNOWN
                )
                raise ProviderError(
                    f"Veo lỗi: {err_msg}",
                    kind=kind,
                    provider="google",
                    retryable=False,
                    extra_secrets=[self.key],
                )

            resp_payload = op.get("response", {}).get("generateVideoResponse", {})
            if resp_payload.get("raiMediaFilteredCount"):
                raise ProviderError(
                    f"Veo chặn video do bộ lọc an toàn: {resp_payload.get('raiMediaFilteredReasons')}",
                    kind=ProviderErrorKind.CONTENT_BLOCKED,
                    provider="google",
                    retryable=False,
                )
            samples = resp_payload.get("generatedSamples", [])
            uri = samples[0].get("video", {}).get("uri") if samples else None
            if not uri:
                raise ProviderError(
                    f"Veo không trả video: {redact_secrets(str(op.get('response'))[:300], [self.key])}",
                    kind=ProviderErrorKind.CONTENT_BLOCKED,
                    provider="google",
                    retryable=False,
                )
            vr = await self._get(client, uri, timeout=300.0)

        input_hashes = [u for u in [first_frame_uri, last_frame_uri, *(references or [])] if u]
        return self.store.store_bytes(
            data=vr.content,
            ext="mp4",
            kind=ArtifactKind.VIDEO,
            provenance=ArtifactProvenance(
                node_id=node_id,
                run_id=run_id,
                provider="google",
                model=model_id,
                params={
                    "prompt": prompt,
                    "firstFrameUri": first_frame_uri,
                    "lastFrameUri": last_frame_uri,
                    "durationSec": duration_sec,
                    "aspectRatio": aspect_ratio,
                    "hasAudio": has_audio,
                },
                input_hashes=input_hashes,
                cost_usd=cost,
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            ),
            meta=ArtifactMeta(duration=duration_sec, aspect=aspect_ratio),
        )

    # ---- Giọng: OmniVoice local, không tốn tiền ----
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

    # ---- Nhìn: chấm ảnh/video hoặc trích xuất kịch bản bằng Gemini ----
    async def analyze_vision(
        self,
        media_uri: str,
        prompt: str,
        node_id: str = "unknown",
        run_id: str = "run_default",
        schema: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        model_id = self._resolve_model_id(model, VISION_MODEL)
        cost = 0.01
        label = f"nhìn {node_id}"
        self.guard.reserve(cost, label, source=self.source)
        data, mime = self._read_uri(media_uri)

        body: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [
                        {"inlineData": {"mimeType": mime, "data": base64.b64encode(data).decode()}},
                        {"text": prompt},
                    ]
                }
            ]
        }
        if schema:
            body["generationConfig"] = {
                "responseMimeType": "application/json",
                "responseSchema": schema,
            }

        async with self._client() as client:
            try:
                resp = await self._post(client, f"{API}/models/{model_id}:generateContent", body)
                self._check_safety_blocks(resp)
            except ProviderError as err:
                if err.kind in (ProviderErrorKind.AUTH, ProviderErrorKind.INVALID_PARAMS):
                    self.guard.refund(cost, label, source=self.source)
                raise

        text = "".join(
            p.get("text", "")
            for c in resp.get("candidates", [])
            for p in c.get("content", {}).get("parts", [])
        )
        out: Dict[str, Any] = {"text": text, "provider": "google", "model": model_id, "costUsd": cost}
        if schema and text.strip():
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    out.update(parsed)
                else:
                    out["data"] = parsed
            except json.JSONDecodeError:
                pass
        return out

    # ---- Văn bản / Kịch bản JSON có cấu trúc ----
    async def text_complete(
        self,
        system: str,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        model_id = self._resolve_model_id(model, TEXT_MODEL)
        cost = TEXT_COST_USD
        label = "text_complete"
        self.guard.reserve(cost, label, source=self.source)

        body: Dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": prompt}]}],
        }
        if schema:
            body["generationConfig"] = {
                "responseMimeType": "application/json",
                "responseSchema": schema,
            }

        async with self._client() as client:
            try:
                resp = await self._post(client, f"{API}/models/{model_id}:generateContent", body)
                self._check_safety_blocks(resp)
            except ProviderError as err:
                if err.kind in (ProviderErrorKind.AUTH, ProviderErrorKind.INVALID_PARAMS):
                    self.guard.refund(cost, label, source=self.source)
                raise

        text = "".join(
            p.get("text", "")
            for c in resp.get("candidates", [])
            for p in c.get("content", {}).get("parts", [])
        )
        result: Dict[str, Any] = {
            "text": text,
            "reply": text,
            "mode": "google_live",
            "provider": "google",
            "model": model_id,
            "costUsd": cost,
            "actions": [],
        }
        if schema and text.strip():
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    result.update(parsed)
                else:
                    result["data"] = parsed
            except json.JSONDecodeError:
                pass
        return result
