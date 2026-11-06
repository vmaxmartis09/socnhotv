from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Literal, Optional


ShortVideoMode = Literal["static", "ai_clip"]
ShortVideoAspectRatio = Literal["9:16", "16:9"]
GeneratorType = Literal["koc_review", "tiktok_sales", "affiliate_compare", "story"]


def slugify(text: str) -> str:
    """Chuyển chuỗi tiếng Việt/Unicode thành slug an toàn cho đường dẫn tệp."""
    s = text.lower().strip()
    s = re.sub(r"[àáạảãâầấậẩẫăằắặẳẵ]", "a", s)
    s = re.sub(r"[èéẹẻẽêềếệểễ]", "e", s)
    s = re.sub(r"[ìíịỉĩ]", "i", s)
    s = re.sub(r"[òóọỏõôồốộổỗơờớợởỡ]", "o", s)
    s = re.sub(r"[ùúụủũưừứựửữ]", "u", s)
    s = re.sub(r"[ỳýỵỷỹ]", "y", s)
    s = re.sub(r"[đ]", "d", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "short-video"


@dataclass
class ShortVideoConfig:
    """Cấu hình đầu vào cho luồng sinh video ngắn 30–90 giây."""
    prompt: str
    project_id: str = "soc-nho-tv"
    character_id: str = "soc_nho"
    character_name: str = "Sóc Nhỏ"
    target_duration_sec: float = 30.0
    aspect_ratio: ShortVideoAspectRatio = "9:16"
    mode: ShortVideoMode = "static"
    image_model: str = "pollinations-flux"
    video_model: str = "mock-video"
    max_clips: int = 5
    generator_type: GeneratorType = "koc_review"
    output_slug: Optional[str] = None
    environment: str = "forest"

    def __post_init__(self):
        # Giới hạn thời lượng trong khoảng 30–90 giây theo hợp đồng H1
        self.target_duration_sec = float(max(30.0, min(self.target_duration_sec, 90.0)))
        if not self.output_slug:
            prefix = "short"
            clean_title = slugify(self.prompt[:40])
            self.output_slug = f"{prefix}-{clean_title}"


@dataclass
class ShortVideoShot:
    """Thông tin chi tiết một shot trong video ngắn."""
    shot_id: str             # "S01", "S02"...
    scene_number: int        # 1, 2, 3...
    title: str
    role: str                # "hook", "problem", "demo", "proof", "cta"...
    speaker: str             # "Sóc Nhỏ"
    speaker_id: str          # "soc_nho"
    dialogue: str            # Lời thoại
    duration_sec: float      # Thời lượng tính theo giây
    image_prompt: str        # Prompt hình ảnh 3 tầng (Depth craft)
    video_prompt: str        # Chỉ dẫn camera và chuyển động
    camera: str              # Tên preset camera (push-in, pan-left...)
    safe_zone: str = "tiktok_9_16"


@dataclass
class ShortVideoCostEstimate:
    """Ước tính chi phí minh bạch cho video ngắn theo SpendGuard."""
    mode: ShortVideoMode
    total_cost_usd: float
    breakdown: Dict[str, float]
    is_free: boolean = True
    spend_guard_required: bool = False
    note: str = ""


@dataclass
class ShortVideoResult:
    """Kết quả hoàn chỉnh của kịch bản và đồ thị video ngắn."""
    config: ShortVideoConfig
    shots: List[ShortVideoShot]
    scenes: List[Dict[str, Any]]
    lines: List[Dict[str, Any]]
    raw_script: str
    total_duration_sec: float
    shot_count: int
    cost_estimate: Dict[str, Any]
    graph: Dict[str, Any] = field(default_factory=dict)
