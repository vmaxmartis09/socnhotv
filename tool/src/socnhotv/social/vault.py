from __future__ import annotations

import os
from typing import Optional
from socnhotv.core.providers.key_vault import KeyVault


class SocialKeyVault:
    """Helper vault for Session C OAuth keys and token references."""

    def __init__(self):
        self._vault = KeyVault(persist_local=False)
        self._extra_keys: dict[str, str] = {}

    def get_key(self, name: str) -> Optional[str]:
        if name in self._extra_keys:
            return self._extra_keys[name]
        env_val = os.environ.get(name) or os.environ.get(name.upper())
        if env_val:
            return env_val
        try:
            return self._vault.get_raw_key(name)
        except Exception:
            return ""

    def set_key(self, name: str, value: str) -> None:
        self._extra_keys[name] = value


_INSTANCE = SocialKeyVault()


def get_social_vault() -> SocialKeyVault:
    return _INSTANCE
