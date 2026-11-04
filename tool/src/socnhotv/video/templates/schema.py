from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

from socnhotv.video.contracts import Platform

TemplateCategory = Literal[
    "sales", "review", "reup", "animation", "education", "affiliate", "story"
]


class Slot(BaseModel):
    key: str
    type: str  # text, media, media[], product, color, number, boolean
    label: Optional[str] = None
    description: Optional[str] = None
    required: bool = False
    default: Optional[Any] = None
    max_chars: Optional[int] = None
    min_chars: Optional[int] = None
    min: Optional[int] = None
    max: Optional[int] = None


class DurationConfig(BaseModel):
    mode: Literal["auto_from_voice", "fixed", "manual"] = "auto_from_voice"
    min: float = 5.0
    max: float = 600.0
    fixed_duration: Optional[float] = None


class VoiceConfig(BaseModel):
    required: bool = True
    default_voice_id: str = "soc-nho"


class CaptionsConfig(BaseModel):
    style: str = "anchor"
    position: str = "lower_third_safe"


class BgmConfig(BaseModel):
    mood: str = "upbeat"
    duck_db: float = -12.0


class SceneConfig(BaseModel):
    role: str
    dur: Optional[str] = None
    summary: Optional[str] = None


class TemplateMeta(BaseModel):
    id: str
    name: str
    version: Union[int, str] = 1
    category: TemplateCategory
    platforms: List[Platform] = Field(default_factory=lambda: ["tiktok", "reels", "shorts"])
    default_platform: Platform = "tiktok"
    duration: DurationConfig = Field(default_factory=DurationConfig)
    slots: List[Slot] = Field(default_factory=list)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    captions: CaptionsConfig = Field(default_factory=CaptionsConfig)
    bgm: BgmConfig = Field(default_factory=BgmConfig)
    scenes: List[SceneConfig] = Field(default_factory=list)
    responsive: Dict[str, str] = Field(default_factory=dict)


def validate_template_data(template: TemplateMeta, data: Dict[str, Any]) -> List[str]:
    """Validate dữ liệu người dùng truyền vào slot của template.
    Trả về danh sách lỗi tiếng Việt rõ ràng, rỗng nếu hợp lệ.
    """
    errors: List[str] = []

    for slot in template.slots:
        val = data.get(slot.key)

        # 1. Kiểm tra trường bắt buộc
        if slot.required:
            if val is None or (isinstance(val, str) and not val.strip()) or (isinstance(val, list) and len(val) == 0):
                errors.append(f"Thiếu trường bắt buộc '{slot.key}' ({slot.label or slot.key}).")
                continue

        if val is None:
            continue

        # 2. Kiểm tra chuỗi ký tự
        if slot.type == "text" and isinstance(val, str):
            if slot.max_chars is not None and len(val) > slot.max_chars:
                errors.append(
                    f"Trường '{slot.key}' quá dài: tối đa {slot.max_chars} ký tự (hiện có {len(val)} ký tự)."
                )
            if slot.min_chars is not None and len(val) < slot.min_chars:
                errors.append(
                    f"Trường '{slot.key}' quá ngắn: tối thiểu {slot.min_chars} ký tự (hiện có {len(val)} ký tự)."
                )

        # 3. Kiểm tra danh sách media[]
        if slot.type in ("media[]", "list") and isinstance(val, list):
            if slot.min is not None and len(val) < slot.min:
                errors.append(
                    f"Trường '{slot.key}' yêu cầu tối thiểu {slot.min} mục (hiện có {len(val)} mục)."
                )
            if slot.max is not None and len(val) > slot.max:
                errors.append(
                    f"Trường '{slot.key}' vượt quá giới hạn: tối đa {slot.max} mục (hiện có {len(val)} mục)."
                )

        # 4. Kiểm tra product slot
        if slot.type == "product":
            if not isinstance(val, dict):
                errors.append(f"Trường sản phẩm '{slot.key}' phải là một đối tượng JSON hợp lệ.")
            else:
                if not val.get("title") and not val.get("name"):
                    errors.append(f"Sản phẩm trong '{slot.key}' cần có tên ('title' hoặc 'name').")

    return errors
