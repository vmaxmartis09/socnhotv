"""Kho khóa API phía máy chủ (KeyVault): không lưu vào mã, không ghi log, không trả về giao diện."""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from socnhotv.core.providers.errors import MissingApiKey, ProviderError, ProviderErrorKind
from socnhotv.core.storage.project_store import get_repo_root

PROVIDER_SPECS: Dict[str, Dict[str, Any]] = {
    "gemini": {
        "label": "Google Gemini & Veo",
        "env_vars": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "min_len": 20,
    },
    "fal": {
        "label": "fal.ai (FLUX & Kling/LTX Video Queue)",
        "env_vars": ["FAL_KEY"],
        "min_len": 16,
    },
    "openai": {
        "label": "OpenAI (GPT / Whisper)",
        "env_vars": ["OPENAI_API_KEY"],
        "min_len": 16,
    },
    "replicate": {
        "label": "Replicate",
        "env_vars": ["REPLICATE_API_TOKEN"],
        "min_len": 16,
    },
}

_PROVIDER_ALIAS = {
    "google": "gemini",
    "gemini": "gemini",
    "fal": "fal",
    "fal.ai": "fal",
    "openai": "openai",
    "replicate": "replicate",
}

_PLACEHOLDER_MARKERS = ("your_", "your-", "placeholder", "xxxx", "change_me", "insert_", "<", ">")


def normalize_provider_key(provider: str) -> str:
    p = (provider or "").strip().lower()
    if p not in _PROVIDER_ALIAS:
        raise ProviderError(
            f"Nhà cung cấp không được hỗ trợ: '{provider}'",
            kind=ProviderErrorKind.INVALID_PARAMS,
            provider=p or "unknown",
        )
    return _PROVIDER_ALIAS[p]


def validate_key_format(provider: str, key: str) -> str:
    """Kiểm tra khóa API có định dạng hợp lệ (ASCII, không khoảng trắng, không phải chữ giữ chỗ)."""
    norm = normalize_provider_key(provider)
    spec = PROVIDER_SPECS[norm]
    cleaned = (key or "").strip().strip('"').strip("'")
    if not cleaned:
        env_hint = spec["env_vars"][0]
        raise MissingApiKey(
            f"Chưa có {env_hint} (biến môi trường, kho khóa máy chủ hoặc tệp .env ở gốc repo).",
            provider=norm,
        )
    lower = cleaned.lower()
    if (
        not cleaned.isascii()
        or " " in cleaned
        or len(cleaned) < spec["min_len"]
        or any(m in lower for m in _PLACEHOLDER_MARKERS)
    ):
        raise MissingApiKey(
            f"Khóa API của {spec['label']} không giống khóa thật (còn là chữ giữ chỗ, có dấu, khoảng trắng hoặc quá ngắn).",
            provider=norm,
        )
    return cleaned


def _parse_env_file(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


class KeyVault:
    """Kho khóa API trung tâm của Core Engine."""

    _memory_keys: Dict[str, str] = {}
    _updated_at: Dict[str, str] = {}

    def __init__(self, repo_root: Optional[Path] = None, persist_local: bool = True):
        self.repo_root = Path(repo_root) if repo_root is not None else get_repo_root()
        self.persist_local = persist_local
        self.env_local_path = self.repo_root / ".env.local"
        self.env_path = self.repo_root / ".env"

    def get_raw_key(self, provider: str) -> str:
        """Tìm khóa theo thứ tự ưu tiên: RAM -> os.environ -> .env.local -> .env."""
        norm = normalize_provider_key(provider)
        if norm in self._memory_keys and self._memory_keys[norm]:
            return self._memory_keys[norm]

        env_vars = PROVIDER_SPECS[norm]["env_vars"]
        for env_name in env_vars:
            val = os.environ.get(env_name, "").strip()
            if val:
                return val

        for env_file in (self.env_local_path, self.env_path):
            parsed = _parse_env_file(env_file)
            for env_name in env_vars:
                if parsed.get(env_name):
                    return parsed[env_name]

        return ""

    def require_key(self, provider: str) -> str:
        """Lấy và xác thực định dạng khóa; ném MissingApiKey nếu thiếu hoặc sai."""
        raw = self.get_raw_key(provider)
        return validate_key_format(provider, raw)

    def has_valid_key(self, provider: str) -> bool:
        try:
            self.require_key(provider)
            return True
        except MissingApiKey:
            return False

    def set_key(self, provider: str, api_key: str) -> Dict[str, Any]:
        """Lưu khóa mới (hoặc xóa nếu truyền chuỗi rỗng) và chỉ trả về trạng thái, KHÔNG trả khóa."""
        norm = normalize_provider_key(provider)
        primary_env = PROVIDER_SPECS[norm]["env_vars"][0]
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        if not (api_key or "").strip():
            self._memory_keys.pop(norm, None)
            self._updated_at[norm] = now_iso
            if self.persist_local and self.env_local_path.exists():
                existing = _parse_env_file(self.env_local_path)
                existing.pop(primary_env, None)
                self._write_env_local(existing)
            return {"provider": norm, "configured": False, "updatedAt": now_iso}

        validated = validate_key_format(norm, api_key)
        self._memory_keys[norm] = validated
        self._updated_at[norm] = now_iso

        if self.persist_local:
            existing = _parse_env_file(self.env_local_path)
            existing[primary_env] = validated
            self._write_env_local(existing)

        return {"provider": norm, "configured": True, "updatedAt": now_iso}

    def _write_env_local(self, values: Dict[str, str]) -> None:
        lines = ["# Khóa API cục bộ của AI Video Studio (gitignore, không đẩy lên git)"]
        for k, v in sorted(values.items()):
            lines.append(f'{k}="{v}"')
        self.env_local_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        try:
            os.chmod(self.env_local_path, 0o600)
        except OSError:
            pass

    def list_status(self) -> List[Dict[str, Any]]:
        """Trả về trạng thái cấu hình của mọi provider (tuyệt đối không có giá trị khóa)."""
        items: List[Dict[str, Any]] = []
        for code, spec in PROVIDER_SPECS.items():
            items.append(
                {
                    "provider": code,
                    "label": spec["label"],
                    "envVars": spec["env_vars"],
                    "configured": self.has_valid_key(code),
                    "updatedAt": self._updated_at.get(code),
                }
            )
        return items

    def all_secrets(self) -> List[str]:
        """Thu thập danh sách các khóa đang có để cung cấp cho bộ lọc che khóa (redactor)."""
        secrets: List[str] = []
        for code in PROVIDER_SPECS:
            raw = self.get_raw_key(code)
            if raw and len(raw) >= 6:
                secrets.append(raw)
        return secrets

    async def verify_key_live(self, provider: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Kiểm tra trực tuyến khóa API có hoạt động thật không (gọi endpoint miễn phí $0.00)."""
        norm = normalize_provider_key(provider)
        key = validate_key_format(norm, api_key) if api_key is not None else self.require_key(norm)

        async with httpx.AsyncClient(timeout=15.0) as client:
            if norm == "gemini":
                r = await client.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    params={"pageSize": 1},
                    headers={"x-goog-api-key": key},
                )
                if r.status_code >= 400:
                    raise ProviderError(
                        f"Khóa Gemini không hợp lệ (HTTP {r.status_code}).",
                        kind=ProviderErrorKind.AUTH,
                        provider=norm,
                        status_code=r.status_code,
                        extra_secrets=[key],
                    )
                return {"provider": norm, "valid": True, "checkedLive": True}

            if norm == "fal":
                # Kiểm tra xác thực nhẹ với REST API của fal.ai (không tạo job tính phí)
                r = await client.get(
                    "https://rest.alpha.fal.ai/models",
                    params={"limit": 1},
                    headers={"Authorization": f"Key {key}"},
                )
                if r.status_code in (401, 403):
                    raise ProviderError(
                        f"Khóa fal.ai không hợp lệ (HTTP {r.status_code}).",
                        kind=ProviderErrorKind.AUTH,
                        provider=norm,
                        status_code=r.status_code,
                        extra_secrets=[key],
                    )
                return {"provider": norm, "valid": True, "checkedLive": True}

            if norm == "replicate":
                r = await client.get(
                    "https://api.replicate.com/v1/account",
                    headers={"Authorization": f"Bearer {key}"},
                )
                if r.status_code in (401, 403):
                    raise ProviderError(
                        f"Khóa Replicate không hợp lệ (HTTP {r.status_code}).",
                        kind=ProviderErrorKind.AUTH,
                        provider=norm,
                        status_code=r.status_code,
                        extra_secrets=[key],
                    )
                return {"provider": norm, "valid": True, "checkedLive": True}

            if norm == "openai":
                r = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {key}"},
                )
                if r.status_code in (401, 403):
                    raise ProviderError(
                        f"Khóa OpenAI không hợp lệ (HTTP {r.status_code}).",
                        kind=ProviderErrorKind.AUTH,
                        provider=norm,
                        status_code=r.status_code,
                        extra_secrets=[key],
                    )
                return {"provider": norm, "valid": True, "checkedLive": True}

        return {"provider": norm, "valid": True, "checkedLive": False}
