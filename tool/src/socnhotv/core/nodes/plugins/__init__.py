from __future__ import annotations

import importlib
import logging
import pkgutil
from typing import Any

logger = logging.getLogger(__name__)


def load_all(registry_cls: Any) -> None:
    """Import every plugin submodule and invoke module.register(registry_cls) if present."""
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        try:
            mod = importlib.import_module(f"{__name__}.{module_name}")
            reg_func = getattr(mod, "register", None)
            if callable(reg_func):
                reg_func(registry_cls)
                logger.info("Successfully loaded node plugin: %s", module_name)
        except Exception as e:
            logger.warning("Failed to load node plugin %s: %s", module_name, e)
