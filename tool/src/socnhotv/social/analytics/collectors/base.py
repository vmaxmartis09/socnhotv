from __future__ import annotations

import abc
from typing import Optional

from socnhotv.social.models import PostMetricsSnapshot, PostTarget, SocialAccount, now_iso
from socnhotv.social.vault import SocialKeyVault


class BaseCollector(abc.ABC):
    def __init__(self, key_vault: Optional[SocialKeyVault] = None):
        self.key_vault = key_vault or SocialKeyVault()

    @abc.abstractmethod
    async def collect(
        self,
        account: SocialAccount,
        target: PostTarget,
        checkpoint: str = "custom",
    ) -> PostMetricsSnapshot:
        """Fetch metrics for a published target."""
        raise NotImplementedError
