from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, ConfigDict, Field


class ModelPricing(BaseModel):
    cost_per_generation: Optional[float] = None
    cost_per_second: Optional[float] = None
    cost_per_minute: Optional[float] = None
    cost_per_1k_tokens: Optional[float] = None


class ModelSpec(BaseModel):
    key: str
    display_name: str = Field(..., alias="display_name")
    provider: str
    model_id: str = Field(..., alias="model_id")
    kind: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    pricing: ModelPricing = Field(default_factory=ModelPricing)

    model_config = ConfigDict(populate_by_name=True)


class ModelRegistry:
    _instance: Optional[ModelRegistry] = None
    _models: Dict[str, ModelSpec] = {}

    def __init__(self, config_path: Optional[str] = None):
        if not config_path:
            current_dir = Path(__file__).resolve().parent
            config_path = str(current_dir / "models.yaml")
        self.config_path = config_path
        self.load()

    @classmethod
    def get_instance(cls) -> ModelRegistry:
        if cls._instance is None:
            cls._instance = ModelRegistry()
        return cls._instance

    def load(self) -> None:
        if not os.path.exists(self.config_path):
            self._models = {}
            return

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        raw_models = data.get("models", {})
        parsed: Dict[str, ModelSpec] = {}
        for key, val in raw_models.items():
            parsed[key] = ModelSpec(key=key, **val)
        self._models = parsed

    def get(self, key: str) -> Optional[ModelSpec]:
        return self._models.get(key)

    def list_all(self) -> List[ModelSpec]:
        return list(self._models.values())

    def list_by_kind(self, kind: str) -> List[ModelSpec]:
        return [m for m in self._models.values() if m.kind == kind]

    def estimate_cost(self, model_key: str, params: Dict[str, Any]) -> float:
        spec = self.get(model_key)
        if not spec or not spec.pricing:
            return 0.0

        p = spec.pricing
        if p.cost_per_generation is not None:
            count = params.get("n", 1)
            return round(p.cost_per_generation * count, 4)

        if p.cost_per_second is not None:
            duration = params.get("duration", 5.0)
            return round(p.cost_per_second * duration, 4)

        if p.cost_per_minute is not None:
            duration_sec = params.get("duration", 60.0)
            return round(p.cost_per_minute * (duration_sec / 60.0), 4)

        return 0.0
