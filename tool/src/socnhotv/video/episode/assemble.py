from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from socnhotv.video.contracts import RenderRequest, VoiceSpec
from socnhotv.video.episode.planner import ScenePlan
from socnhotv.workspace.paths import project_path

logger = logging.getLogger("socnhotv.video.episode.assemble")


def format_timestamp(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def assemble_episode(
    project_id: str,
    episode_id: str,
    title: str,
    scenes: List[ScenePlan],
    scene_assets: List[Dict[str, Any]],
    voice_audio_path: Path,
) -> RenderRequest:
    """Tạo RenderRequest YouTube 16:9 hoàn chỉnh và xuất chapters.txt + youtube_meta.json."""
    ep_dir = project_path(project_id, "output", episode_id)
    ep_dir.mkdir(parents=True, exist_ok=True)

    # 1. Sinh danh sách Chapters YouTube tự động
    chapters: List[str] = ["00:00 Mở đầu & Giới thiệu tập"]
    curr_time = 4.0  # sau intro title card

    for sc in scenes:
        time_str = format_timestamp(curr_time)
        summary = sc.action[:45] if sc.action else f"Cảnh {sc.scene_number}"
        chapters.append(f"{time_str} Cảnh {sc.scene_number}: {summary}")
        curr_time += sc.duration_est

    chapters_file = ep_dir / "chapters.txt"
    chapters_content = "\n".join(chapters)
    chapters_file.write_text(chapters_content, encoding="utf-8")

    # 2. Sinh Metadata gợi ý cho YouTube
    youtube_meta = {
        "title": f"Sóc Nhỏ TV | {title} (Hoạt Hình 3D)",
        "description": (
            f"Chào mừng các bạn nhỏ và quý phụ huynh đến với Sóc Nhỏ TV!\n\n"
            f"Nội dung tập phim: {title}\n"
            f"Nhân vật chính: Sóc Nhỏ (Bi) cao 100cm, Bác sĩ Koala cao 150cm.\n\n"
            f"MỤC LỤC TẬP PHIM:\n{chapters_content}\n\n"
            f"© Bản quyền thuộc về Sóc Nhỏ TV. Vui lòng không reup dưới mọi hình thức."
        ),
        "tags": [
            "socnhotv",
            "soc nho bi",
            "hoat hinh 3d",
            "hoat hinh thieu nhi",
            "koala",
            "ke chuyen thieu nhi",
            "bai hoc cuoc song",
        ],
        "category_id": "1",  # Film & Animation
    }
    meta_file = ep_dir / "youtube_meta.json"
    meta_file.write_text(json.dumps(youtube_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3. Đóng gói RenderRequest
    return RenderRequest(
        project_id=project_id,
        template_id="yt-animation-episode-v1",
        platforms=["youtube"],
        data={
            "episode_number": f"TẬP {episode_id.upper()}",
            "episode_title": title,
            "character_scale_lock": "Sóc Nhỏ 100cm · Bạn Koala 150cm (Scale Lock)",
            "scenes": scene_assets,
            "auto_draft": True,
            "title": title,
        },
        voice=VoiceSpec(
            audio_path=str(voice_audio_path),
        ),
        output_name=f"{episode_id}_main",
    )
