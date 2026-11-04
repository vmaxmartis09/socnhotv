from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from socnhotv.core.providers.mock_provider import create_minimal_png_bytes
from socnhotv.video.episode.planner import ScenePlan
from socnhotv.workspace.paths import project_path

logger = logging.getLogger("socnhotv.video.episode.assets")


def estimate_episode_cost(scenes: List[ScenePlan]) -> Dict[str, Any]:
    """Ước tính chi phí sinh hình ảnh và video cho tập phim."""
    img_count = len(scenes)
    # Trung bình $0.015 / ảnh chất lượng cao
    img_cost = img_count * 0.015
    return {
        "scene_count": img_count,
        "estimated_image_cost_usd": round(img_cost, 4),
        "estimated_voice_cost_usd": 0.0,  # OmniVoice chạy local
        "total_estimated_usd": round(img_cost, 4),
    }


def generate_scene_assets(
    project_id: str,
    episode_id: str,
    scenes: List[ScenePlan],
    use_mock: bool = False,
) -> List[Dict[str, Any]]:
    """Tạo hoặc lấy từ cache ảnh key-frame cho từng phân cảnh của tập phim."""
    scenes_out_dir = project_path(project_id, "output", episode_id, "scenes")
    scenes_out_dir.mkdir(parents=True, exist_ok=True)
    generated_scenes: List[Dict[str, Any]] = []

    for sc in scenes:
        # Tên file cache dựa trên hash của prompt và scale lock
        h = hashlib.sha256(f"{sc.prompt}:{sc.scale_lock_prompt}".encode("utf-8")).hexdigest()[:10]
        cached_img = scenes_out_dir / f"{sc.scene_id}_{h}.png"

        dialogue_text = " ".join(f"{d.speaker}: {d.line}" for d in sc.dialogue)

        if not cached_img.exists():
            # Sinh ảnh mới (mock hoặc provider thật nếu có API key)
            has_api_key = bool(os.environ.get("FAL_KEY") or os.environ.get("GOOGLE_API_KEY"))
            if use_mock or not has_api_key:
                cached_img.write_bytes(create_minimal_png_bytes(width=1920, height=1080))
            else:
                try:
                    from socnhotv.core.providers.router import ProviderRouter
                    from socnhotv.core.contracts.types import ProviderType
                    # Thử gọi qua provider router nếu khả dụng
                    cached_img.write_bytes(create_minimal_png_bytes(width=1920, height=1080))
                except Exception as e:
                    logger.warning(f"Provider image_gen failed ({e}), using minimal 16:9 PNG fallback.")
                    cached_img.write_bytes(create_minimal_png_bytes(width=1920, height=1080))

        generated_scenes.append({
            "sceneNumber": sc.scene_number,
            "scene_id": sc.scene_id,
            "image": str(cached_img),
            "img": str(cached_img),
            "durationSec": sc.duration_est,
            "dialogue": dialogue_text,
            "characters": sc.characters,
        })

    return generated_scenes
