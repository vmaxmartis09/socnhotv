from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from socnhotv.social.models import PlatformType, PostMedia, PostTarget, SocialAccount


class Capabilities(BaseModel):
    direct_post: bool = True
    draft_upload: bool = False
    schedule_native: bool = False
    thumbnail: bool = False
    first_comment: bool = False
    product_link: bool = False


class Issue(BaseModel):
    level: Literal["error", "warning"]
    code: str
    message: str


class PublishResult(BaseModel):
    external_id: Optional[str] = None
    url: Optional[str] = None
    status: Literal["published", "failed", "publishing"]
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class PublishAdapter(ABC):
    platform: PlatformType

    @abstractmethod
    def capabilities(self) -> Capabilities:
        """Return supported features of this adapter."""
        pass

    @abstractmethod
    def connect_url(self, account: SocialAccount, redirect_uri: str) -> str:
        """Return OAuth consent authorization URL."""
        pass

    @abstractmethod
    def exchange_code(self, account: SocialAccount, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for token details."""
        pass

    @abstractmethod
    def refresh(self, account: SocialAccount) -> Dict[str, Any]:
        """Refresh expired access token."""
        pass

    @abstractmethod
    def validate(self, target: PostTarget, media: Optional[PostMedia]) -> List[Issue]:
        """Validate target content & media specs against platform limits."""
        pass

    @abstractmethod
    def publish(self, account: SocialAccount, target: PostTarget, media: Optional[PostMedia]) -> PublishResult:
        """Publish target to platform."""
        pass

    @abstractmethod
    def fetch_status(self, account: SocialAccount, external_id: str) -> PublishResult:
        """Fetch remote publishing status for async/chunked uploads."""
        pass
