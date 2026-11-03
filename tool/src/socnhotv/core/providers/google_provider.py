"""Provider thật: Gemini (ảnh, nhìn) và Veo (video) qua Gemini API; giọng qua OmniVoice local."""
from __future__ import annotations

import asyncio
import base64
import os
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
from socnhotv.core.providers.base import BaseProvider
from socnhotv.core.providers.spend_guard import SpendGuard
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root

API = "https://generativelanguage.googleapis.com/v1beta"
IMAGE_MODEL = "gemini-2.5-flash-image"
VISION_MODEL = "gemini-2.5-flash"
VIDEO_MODEL = "veo-3.1-fast-generate-preview"
# Giá ước tính để giữ trần chi tiêu. CHƯA đối chiếu bảng giá Google: sửa bằng biến môi trường nếu khác.
IMAGE_COST_USD = float(os.environ.get("SOCNHOTV_IMAGE_COST_USD", "0.04"))
VIDEO_COST_PER_SEC_USD = float(os.environ.get("SOCNHOTV_VIDEO_COST_PER_SEC_USD", "0.40"))


class MissingApiKey(Exception):
    pass


def load_gemini_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        env_file = get_repo_root() / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        raise MissingApiKey("Chưa có GEMINI_API_KEY (biến môi trường hoặc tệp .env ở gốc repo).")
    if not key.isascii() or " " in key or len(key) < 20:
        raise MissingApiKey(
            "GEMINI_API_KEY trong .env không giống khóa thật (còn là chữ giữ chỗ, có dấu hoặc quá ngắn). "
            "Dán khóa lấy từ Google AI Studio (thường bắt đầu bằng AIza)."
        )
    return key


def estimate_image_usd(n: int = 1) -> float:
    return IMAGE_COST_USD * max(1, n)


def estimate_video_usd(duration_sec: float) -> float:
    return VIDEO_COST_PER_SEC_USD * duration_sec


class GoogleProvider(BaseProvider):
    def __init__(self, store: ProjectStore, guard: Optional[SpendGuard] = None, key: Optional[str] = None):
        self.store = store
        self.guard = guard or SpendGuard(store.runs_dir)
        self.key = key or load_gemini_key()

    def provider_name(self) -> str:
        return "google"

    # ---- HTTP ----
    def _headers(self) -> Dict[str, str]:
        return {"x-goog-api-key": self.key, "Content-Type": "application/json"}

    async def _post(self, client: httpx.AsyncClient, url: str, body: Dict[str, Any]) -> Dict[str, Any]:
        r = await client.post(url, headers=self._headers(), json=body, timeout=180)
        if r.status_code >= 400:
            raise RuntimeError(f"Google API {r.status_code}: {r.text[:400]}")
        return r.json()

    def _read_uri(self, uri: str) -> tuple[bytes, str]:
        path = self.store.project_dir / uri
        data = path.read_bytes()
        ext = path.suffix.lower().lstrip(".")
        return data, "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext or 'png'}"

    # ---- Ảnh ----
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
        out: List[Artifact] = []
        async with httpx.AsyncClient() as client:
            for _ in range(max(1, n)):
                self.guard.reserve(estimate_image_usd(), f"ảnh {node_id}")
                parts: List[Dict[str, Any]] = []
                for ref in references or []:
                    data, mime = self._read_uri(ref)
                    parts.append({"inlineData": {"mimeType": mime, "data": base64.b64encode(data).decode()}})
                parts.append({"text": prompt})
                resp = await self._post(
                    client,
                    f"{API}/models/{IMAGE_MODEL}:generateContent",
                    {
                        "contents": [{"parts": parts}],
                        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect_ratio}},
                    },
                )
                img = next(
                    (p["inlineData"] for c in resp.get("candidates", []) for p in c.get("content", {}).get("parts", []) if "inlineData" in p),
                    None,
                )
                if not img:
                    raise RuntimeError(f"Gemini không trả ảnh: {str(resp)[:300]}")
                mime = img.get("mimeType", "image/png")
                out.append(
                    self.store.store_bytes(
                        data=base64.b64decode(img["data"]),
                        ext="jpg" if "jpeg" in mime else "png",
                        kind=ArtifactKind.IMAGE,
                        provenance=ArtifactProvenance(
                            node_id=node_id, run_id=run_id, provider="google", model=IMAGE_MODEL,
                            params={"prompt": prompt, "aspectRatio": aspect_ratio, "references": references or []},
                            input_hashes=list(references or []), cost_usd=estimate_image_usd(),
                            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        ),
                        meta=ArtifactMeta(aspect=aspect_ratio),
                    )
                )
        return out

    # ---- Video ----
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
        self.guard.reserve(estimate_video_usd(duration_sec), f"video {node_id} {duration_sec}s")
        instance: Dict[str, Any] = {"prompt": prompt}
        if first_frame_uri:
            data, mime = self._read_uri(first_frame_uri)
            instance["image"] = {"bytesBase64Encoded": base64.b64encode(data).decode(), "mimeType": mime}
        async with httpx.AsyncClient() as client:
            op = await self._post(
                client,
                f"{API}/models/{VIDEO_MODEL}:predictLongRunning",
                {"instances": [instance], "parameters": {"aspectRatio": aspect_ratio, "durationSeconds": int(duration_sec)}},
            )
            for _ in range(90):  # tối đa ~15 phút
                if op.get("done"):
                    break
                await asyncio.sleep(10)
                r = await client.get(f"{API}/{op['name']}", headers=self._headers(), timeout=60)
                if r.status_code >= 400:
                    raise RuntimeError(f"Google API {r.status_code}: {r.text[:300]}")
                op = r.json()
            if not op.get("done"):
                raise RuntimeError("Veo chưa xong sau 15 phút; việc có thể vẫn chạy và vẫn tính phí: " + op.get("name", ""))
            if "error" in op:
                raise RuntimeError(f"Veo lỗi: {op['error'].get('message', op['error'])}")
            samples = op.get("response", {}).get("generateVideoResponse", {}).get("generatedSamples", [])
            uri = samples[0]["video"]["uri"] if samples else None
            if not uri:
                raise RuntimeError(f"Veo không trả video (có thể bị lọc nội dung): {str(op.get('response'))[:300]}")
            vr = await client.get(uri, headers={"x-goog-api-key": self.key}, timeout=300, follow_redirects=True)
            vr.raise_for_status()
        return self.store.store_bytes(
            data=vr.content, ext="mp4", kind=ArtifactKind.VIDEO,
            provenance=ArtifactProvenance(
                node_id=node_id, run_id=run_id, provider="google", model=VIDEO_MODEL,
                params={"prompt": prompt, "firstFrameUri": first_frame_uri, "durationSec": duration_sec, "aspectRatio": aspect_ratio},
                input_hashes=[first_frame_uri] if first_frame_uri else [], cost_usd=estimate_video_usd(duration_sec),
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            ),
            meta=ArtifactMeta(duration=duration_sec, aspect=aspect_ratio),
        )

    # ---- Giọng: OmniVoice local, không tốn tiền ----
    async def speak_voice(
        self, text: str, voice_id: str = "soc-nho", tempo: float = 1.10, node_id: str = "unknown", run_id: str = "run_default",
    ) -> Artifact:
        from socnhotv.core.adapters.voice_adapter import VoiceAdapter

        return await VoiceAdapter(self.store).synthesize(text=text, voice_id=voice_id, tempo=tempo, node_id=node_id, run_id=run_id)

    # ---- Nhìn: chấm ảnh/video bằng Gemini ----
    async def analyze_vision(self, media_uri: str, prompt: str, node_id: str = "unknown", run_id: str = "run_default") -> Dict[str, Any]:
        self.guard.reserve(0.01, f"nhìn {node_id}")
        data, mime = self._read_uri(media_uri)
        async with httpx.AsyncClient() as client:
            resp = await self._post(
                client,
                f"{API}/models/{VISION_MODEL}:generateContent",
                {"contents": [{"parts": [{"inlineData": {"mimeType": mime, "data": base64.b64encode(data).decode()}}, {"text": prompt}]}]},
            )
        text = "".join(p.get("text", "") for c in resp.get("candidates", []) for p in c.get("content", {}).get("parts", []))
        return {"text": text, "provider": "google", "model": VISION_MODEL}
