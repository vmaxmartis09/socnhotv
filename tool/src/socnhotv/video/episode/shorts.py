from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from socnhotv.video.contracts import RenderRequest, VoiceSpec
from socnhotv.video.episode.planner import ScenePlan

logger = logging.getLogger("socnhotv.video.episode.shorts")


def extract_and_assemble_shorts(
    project_id: str,
    episode_id: str,
    scenes: List[ScenePlan],
    scene_assets: List[Dict[str, Any]],
    voice_audio_path: Path,
) -> List[RenderRequest]:
    """Tự động phân tích và trích xuất 3 đoạn Shorts 9:16 hấp dẫn nhất từ tập phim:
    1. Short 1 (Story/Drama): Tình huống đối đáp bất ngờ giữa Bi và Koala
    2. Short 2 (Fact/Education): Bài học sức khỏe / kiến thức thú vị rút ra
    3. Short 3 (Highlight Clip): Khoảnh khắc vui nhộn điểm nhấn
    """
    shorts_requests: List[RenderRequest] = []

    # 1. Short Story Clip
    sc_sample = scenes[0] if scenes else None
    dialogue_text = " ".join(d.line for d in (sc_sample.dialogue if sc_sample else [])) or "Bi và Bác sĩ Koala"
    shorts_requests.append(
        RenderRequest(
            project_id=project_id,
            template_id="story-cartoon-v1",
            platforms=["shorts", "tiktok", "reels"],
            data={
                "story_title": f"Trích đoạn hài hước {episode_id.upper()}",
                "book_page_text": dialogue_text[:120],
                "moral_lesson": "Xem trọn vẹn tập phim trên YouTube Sóc Nhỏ TV!",
                "auto_draft": True,
                "title": f"Shorts 1 - {episode_id}",
            },
            voice=VoiceSpec(audio_path=str(voice_audio_path)),
            output_name=f"{episode_id}_short_01",
        )
    )

    # 2. Short Fact / Giáo dục
    shorts_requests.append(
        RenderRequest(
            project_id=project_id,
            template_id="shorts-fact-v1",
            platforms=["shorts", "tiktok", "reels"],
            data={
                "fact_question": "BẠN CÓ BIẾT?",
                "stat_number": "100%",
                "fact_statement": "Mỗi ngày đánh răng 2 lần giúp các bạn nhỏ có hàm răng chắc khỏe như Sóc Bi!",
                "follow_cta": "Đăng ký kênh YouTube Sóc Nhỏ TV ngay nhé!",
                "auto_draft": True,
                "title": f"Shorts 2 - {episode_id}",
            },
            voice=VoiceSpec(audio_path=str(voice_audio_path)),
            output_name=f"{episode_id}_short_02",
        )
    )

    # 3. Short Highlight
    sc_last = scenes[-1] if len(scenes) > 1 else (scenes[0] if scenes else None)
    last_text = " ".join(d.line for d in (sc_last.dialogue if sc_last else [])) or "Khoảnh khắc đáng yêu"
    shorts_requests.append(
        RenderRequest(
            project_id=project_id,
            template_id="story-cartoon-v1",
            platforms=["shorts", "tiktok", "reels"],
            data={
                "story_title": f"Bài Học Ý Nghĩa - {episode_id.upper()}",
                "book_page_text": last_text[:120],
                "moral_lesson": "Hãy cùng theo dõi chuyến phiêu lưu tiếp theo!",
                "auto_draft": True,
                "title": f"Shorts 3 - {episode_id}",
            },
            voice=VoiceSpec(audio_path=str(voice_audio_path)),
            output_name=f"{episode_id}_short_03",
        )
    )

    return shorts_requests
