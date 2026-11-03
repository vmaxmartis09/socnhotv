"""Tập lỗi chung của các Provider AI và bộ lọc che khóa API nhạy cảm."""
from __future__ import annotations

import enum
import os
import re
from typing import Iterable, Optional, Sequence

_SECRET_ENV_NAMES = (
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "FAL_KEY",
    "OPENAI_API_KEY",
    "REPLICATE_API_TOKEN",
)

_SECRET_PATTERNS = [
    re.compile(r"AIza[A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?i)(Authorization\s*:\s*(?:Key|Bearer|Token)\s+)[^\s\"',;]+"),
    re.compile(r"(?i)(\b(?:Key|Bearer)\s+)[A-Za-z0-9._:\-]{12,}"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"\br8_[A-Za-z0-9_\-]{12,}"),
    re.compile(r"(?i)([?&](?:key|api_key|token)=)[^&\s\"']+"),
    re.compile(r"(?i)(x-goog-api-key\s*[:=]\s*)[^\s\"',;]+"),
]


def redact_secrets(text: str, extra_secrets: Sequence[str] = ()) -> str:
    """Che toàn bộ khóa API trong chuỗi thông báo lỗi hoặc nhật ký."""
    if not text:
        return text

    cleaned = str(text)
    candidates: list[str] = [s for s in extra_secrets if s and len(s) >= 6]
    for env_name in _SECRET_ENV_NAMES:
        val = os.environ.get(env_name, "").strip()
        if len(val) >= 6:
            candidates.append(val)

    for secret in sorted(set(candidates), key=len, reverse=True):
        cleaned = cleaned.replace(secret, "***REDACTED***")

    for idx, pat in enumerate(_SECRET_PATTERNS):
        if idx == 0 or idx in (3, 4):
            cleaned = pat.sub("***REDACTED***", cleaned)
        else:
            cleaned = pat.sub(r"\1***REDACTED***", cleaned)

    return cleaned


class ProviderErrorKind(str, enum.Enum):
    """Phân loại lỗi chuẩn hóa giữa mọi nhà cung cấp AI."""
    AUTH = "auth"                        # Khóa thiếu, sai hoặc không có quyền (401, 403)
    QUOTA = "quota"                      # Hết hạn mức cứng / hết tiền tài khoản
    CONTENT_BLOCKED = "content_blocked"  # Bị bộ lọc an toàn chặn nội dung
    TRANSIENT = "transient"              # Lỗi tạm thời (429 rate-limit, 5xx, timeout) -> được phép retry
    INVALID_PARAMS = "invalid_params"    # Tham số sai (400, 422) -> không retry
    SPEND_CAP = "spend_cap"              # Vượt trần chi tiêu của Studio
    CANCELLED = "cancelled"              # Người dùng hủy tác vụ đang chạy
    UNKNOWN = "unknown"


class ProviderError(Exception):
    """Ngoại lệ chuẩn hóa của Provider, tự động che khóa nhạy cảm trong message."""

    def __init__(
        self,
        message: str,
        kind: ProviderErrorKind = ProviderErrorKind.UNKNOWN,
        provider: str = "unknown",
        status_code: Optional[int] = None,
        retryable: Optional[bool] = None,
        extra_secrets: Iterable[str] = (),
    ):
        clean_msg = redact_secrets(message, tuple(extra_secrets))
        super().__init__(clean_msg)
        self.kind = kind
        self.provider = provider
        self.status_code = status_code
        self.retryable = (kind == ProviderErrorKind.TRANSIENT) if retryable is None else retryable


class MissingApiKey(ProviderError):
    """Thiếu hoặc sai định dạng khóa API trước khi gửi yêu cầu."""

    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(
            message=message,
            kind=ProviderErrorKind.AUTH,
            provider=provider,
            retryable=False,
        )


def classify_http_error(
    provider: str,
    status_code: int,
    body_text: str,
    extra_secrets: Sequence[str] = (),
) -> ProviderError:
    """Ánh xạ mã HTTP và thân phản hồi từ Google/fal/Replicate sang ProviderError chuẩn."""
    safe_body = redact_secrets((body_text or "")[:400], extra_secrets)
    lower = safe_body.lower()

    if any(w in lower for w in ("safety", "prohibited", "content_policy", "blocked", "rai_media_filtered")):
        kind = ProviderErrorKind.CONTENT_BLOCKED
        retryable = False
    elif status_code in (401, 403):
        if any(w in lower for w in ("quota", "billing", "insufficient", "exhausted_balance")):
            kind = ProviderErrorKind.QUOTA
        else:
            kind = ProviderErrorKind.AUTH
        retryable = False
    elif status_code == 402:
        kind = ProviderErrorKind.QUOTA
        retryable = False
    elif status_code == 429:
        if any(w in lower for w in ("billing", "insufficient_quota", "monthly limit", "exhausted balance")):
            kind = ProviderErrorKind.QUOTA
            retryable = False
        else:
            kind = ProviderErrorKind.TRANSIENT
            retryable = True
    elif status_code in (400, 404, 422):
        if "api_key_invalid" in lower or "api key not valid" in lower:
            kind = ProviderErrorKind.AUTH
        else:
            kind = ProviderErrorKind.INVALID_PARAMS
        retryable = False
    elif status_code in (408, 425, 500, 502, 503, 504):
        kind = ProviderErrorKind.TRANSIENT
        retryable = True
    else:
        kind = ProviderErrorKind.UNKNOWN
        retryable = False

    return ProviderError(
        message=f"{provider} HTTP {status_code} ({kind.value}): {safe_body}",
        kind=kind,
        provider=provider,
        status_code=status_code,
        retryable=retryable,
        extra_secrets=extra_secrets,
    )
