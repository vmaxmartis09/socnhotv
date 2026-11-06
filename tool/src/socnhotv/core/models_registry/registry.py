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
    cost_per_1k_chars: Optional[float] = None


class ModelSpec(BaseModel):
    key: str
    display_name: str = Field(..., alias="display_name")
    provider: str
    model_id: str = Field(..., alias="model_id")
    kind: str
    tier: str = "paid"  # "free" | "freemium" | "paid" | "local"
    supports_reference: bool = Field(False, alias="supports_reference")
    max_references: int = Field(0, alias="max_references")
    quota_note: str = Field("", alias="quota_note")
    speed_note: str = Field("", alias="speed_note")
    durations_sec: List[int] = Field(default_factory=list, alias="durations_sec")
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    pricing: ModelPricing = Field(default_factory=ModelPricing)

    model_config = ConfigDict(populate_by_name=True)

    def model_post_init(self, __context: Any) -> None:
        # Tự động đồng bộ các trường capabilities cũ sang trường phẳng C2 nếu chưa có
        if "supports_reference" in self.capabilities and not self.supports_reference:
            self.supports_reference = bool(self.capabilities.get("supports_reference"))
        if "durations_sec" in self.capabilities and not self.durations_sec:
            self.durations_sec = list(self.capabilities.get("durations_sec", []))


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
        if key in self._models:
            return self._models[key]
        # Tìm kiếm dự phòng theo model_id hoặc chứa key
        k_lower = key.lower()
        for spec in self._models.values():
            if spec.model_id.lower() == k_lower or k_lower in spec.key.lower():
                return spec
        return None

    def list_all(self) -> List[ModelSpec]:
        return list(self._models.values())

    def list_by_kind(self, kind: str) -> List[ModelSpec]:
        return [m for m in self._models.values() if m.kind == kind]

    def list_by_provider(self, provider: str) -> List[ModelSpec]:
        return [m for m in self._models.values() if m.provider == provider]

    def estimate_cost(
        self,
        model_key: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> float:
        spec = self.get(model_key)
        if not spec or not spec.pricing:
            return 0.0

        merged_params = dict(params or {})
        merged_params.update(kwargs)

        p = spec.pricing
        if p.cost_per_generation is not None:
            count = merged_params.get("n", merged_params.get("num_images", 1))
            return round(p.cost_per_generation * count, 4)

        if p.cost_per_second is not None:
            duration = merged_params.get(
                "duration_sec",
                merged_params.get("duration", merged_params.get("durationSec", 5.0)),
            )
            return round(p.cost_per_second * float(duration), 4)

        if p.cost_per_minute is not None:
            duration_sec = merged_params.get(
                "duration_sec",
                merged_params.get("duration", merged_params.get("durationSec", 60.0)),
            )
            return round(p.cost_per_minute * (float(duration_sec) / 60.0), 4)

        if p.cost_per_1k_chars is not None:
            length = merged_params.get("text_length", len(str(merged_params.get("text", ""))))
            return round(p.cost_per_1k_chars * (length / 1000.0), 4)

        if p.cost_per_1k_tokens is not None:
            tokens = merged_params.get("tokens", max(1, len(str(merged_params.get("text", ""))) // 4))
            return round(p.cost_per_1k_tokens * (tokens / 1000.0), 4)

        return 0.0
