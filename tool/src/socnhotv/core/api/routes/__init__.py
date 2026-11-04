from __future__ import annotations

import importlib
import logging
import pkgutil
from fastapi import APIRouter, FastAPI

logger = logging.getLogger(__name__)


def include_all(app: FastAPI) -> None:
    """Scan and include all submodules defining an APIRouter named `router`."""
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        try:
            mod = importlib.import_module(f"{__name__}.{module_name}")
            router = getattr(mod, "router", None)
            if isinstance(router, APIRouter):
                app.include_router(router)
                logger.info("Successfully loaded route plugin: %s", module_name)
        except Exception as e:
            logger.warning("Failed to include route module %s: %s", module_name, e)
