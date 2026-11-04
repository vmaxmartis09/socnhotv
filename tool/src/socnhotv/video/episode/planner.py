from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DialogueLine(BaseModel):
    speaker: str
    line: str


class ScenePlan(BaseModel):
    scene_id: str
    scene_number: int
    characters: List[str] = Field(default_factory=lambda: ["soc_nho"])
    location: str = "Khu rừng thông xanh mát"
    action: str = ""
    dialogue: List[DialogueLine] = Field(default_factory=list)
    camera: str = "Medium shot, eye-level cinematic"
    duration_est: float = 5.0
    prompt: str = ""
    scale_lock_prompt: str = (
        "Bi the squirrel is 100cm tall, Koala doctor is 150cm tall. "
        "Bi's head reaches the doctor's chest. Pixar 3D style."
    )


class EpisodePlan(BaseModel):
    episode_id: str
    title: str
    scenes: List[ScenePlan]
    estimated_cost_usd: float = 0.0
    total_duration_est: float = 0.0


def plan_episode(
    script_text: str,
    episode_id: str = "ep_01",
    title: str = "Hoạt hình Sóc Nhỏ Bi & Bạn Koala",
) -> EpisodePlan:
    """Chuyển đổi kịch bản tập phim thô thành danh sách phân cảnh ScenePlan[]
    khóa cứng tỉ lệ Bi 100cm / Koala 150cm theo SCALE_LOCK.md.
    """
    raw_lines = [l.strip() for l in script_text.splitlines() if l.strip()]
    scenes: List[ScenePlan] = []

    # Nhận diện phân cảnh theo từ khóa: Cảnh 1, Scene 1, hoặc nhóm hội thoại
    current_scene_num = 1
    current_dialogues: List[DialogueLine] = []
    current_action = ""
    current_location = "Phòng khám Bác sĩ Koala"

    def flush_scene(num: int, dialogues: List[DialogueLine], action: str):
        characters = set()
        for d in dialogues:
            spk = d.speaker.lower()
            if "bi" in spk or "sóc" in spk:
                characters.add("soc_nho")
            elif "koala" in spk or "bác sĩ" in spk:
                characters.add("koala")
        if not characters:
            characters.add("soc_nho")

        # Tính thời lượng ước tính từ số chữ (khoảng 3 từ / giây + 1s đệm)
        total_words = sum(len(d.line.split()) for d in dialogues)
        dur = max(3.5, round(total_words / 2.8 + 1.2, 1))

        chars_list = sorted(list(characters))
        has_both = "soc_nho" in characters and "koala" in characters
        scale_rule = (
            "Bi the squirrel is two-thirds the height of the koala doctor (100cm vs 150cm), "
            "Bi's head reaches the doctor's chest."
            if has_both
            else "Character Sóc Nhỏ Bi 100cm tall, Pixar 3D style."
        )

        full_prompt = (
            f"3D Pixar animation shot of {', '.join(chars_list)} in {current_location}. "
            f"Action: {action or 'character talking and interacting'}. {scale_rule}"
        )

        return ScenePlan(
            scene_id=f"{episode_id}_sc_{num:02d}",
            scene_number=num,
            characters=chars_list,
            location=current_location,
            action=action or "Diễn xuất biểu cảm sinh động",
            dialogue=list(dialogues),
            camera="Cinematic medium shot" if has_both else "Close-up expression shot",
            duration_est=dur,
            prompt=full_prompt,
            scale_lock_prompt=scale_rule,
        )

    for line in raw_lines:
        scene_match = re.match(r"^(cảnh|scene|phân cảnh)\s*(\d+)[:.-]?\s*(.*)", line, re.IGNORECASE)
        if scene_match:
            if current_dialogues or current_action:
                scenes.append(flush_scene(current_scene_num, current_dialogues, current_action))
                current_scene_num += 1
                current_dialogues = []
                current_action = ""
            desc = scene_match.group(3).strip()
            if desc:
                current_action = desc
            continue

        diag_match = re.match(r"^([^:：]+)[:：]\s*(.+)$", line)
        if diag_match:
            speaker = diag_match.group(1).strip()
            text = diag_match.group(2).strip()
            current_dialogues.append(DialogueLine(speaker=speaker, line=text))
        else:
            current_action += " " + line

    if current_dialogues or current_action:
        scenes.append(flush_scene(current_scene_num, current_dialogues, current_action))

    if not scenes:
        # Kịch bản tối giản 1 cảnh
        scenes.append(
            ScenePlan(
                scene_id=f"{episode_id}_sc_01",
                scene_number=1,
                characters=["soc_nho", "koala"],
                location="Rừng thông Sóc Nhỏ",
                action="Bi và Bác sĩ Koala trò chuyện vui vẻ",
                dialogue=[DialogueLine(speaker="Bi", line=script_text[:100])],
                duration_est=5.0,
            )
        )

    total_dur = sum(s.duration_est for s in scenes)
    cost = round(len(scenes) * 0.015, 3)

    return EpisodePlan(
        episode_id=episode_id,
        title=title or "Tập Hoạt Hình Sóc Nhỏ",
        scenes=scenes,
        estimated_cost_usd=cost,
        total_duration_est=round(total_dur, 1),
    )
