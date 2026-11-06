"""Data models and contract definitions for LipSync and Voice-Mouth Alignment (Luồng H5)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class LipSyncMethod(str, Enum):
    """Các nhóm phương pháp xử lý khẩu hình."""
    MUTE_AND_VOICEOVER = "mute_and_voiceover"        # Lựa chọn (a): Tắt tiếng gốc, dẫn chuyện/thoại OmniVoice
    LOCAL_OSS = "local_oss"                          # Lựa chọn (b1): Tool mã nguồn mở chạy máy (Wav2Lip, MuseTalk, ...)
    CLOUD_API = "cloud_api"                          # Lựa chọn (b2): API thương mại đám mây (SyncLabs, HeyGen, ...)
    NATIVE_MODEL_TTS = "native_model_tts"            # Lựa chọn (c): Model video tự sinh tiếng và khẩu hình


class CharacterType(str, Enum):
    """Phân loại hình thái nhân vật để đánh giá khả năng nhận diện khuôn mặt."""
    ANTHROPOMORPHIC_3D = "anthropomorphic_3d"        # Động vật nhân hóa 3D (Sóc Bi, Dê Mun, Koala): mõm nhô, tai thú
    HUMAN_REALISTIC = "human_realistic"              # Người thật / KOC người thật (Gobi LyLy, Neau)
    STYLIZED_2D = "stylized_2d"                      # Hoạt hình 2D anime/cartoon phẳng
    ABSTRACT = "abstract"                            # Đồ vật nhân hoá / trừu tượng


class FeasibilityStatus(str, Enum):
    """Mức độ khả thi thực tế."""
    FEASIBLE_RECOMMENDED = "feasible_recommended"    # Khả thi cao, ổn định 100%, khuyến nghị dùng ngay
    FEASIBLE_PAID_API = "feasible_paid_api"          # Khả thi qua API thương mại nhưng tốn tiền và upload ảnh
    EXPERIMENTAL_GLITCHY = "experimental_glitchy"    # Chạy được nhưng hay méo mặt / lệch landmark trên 3D
    INFEASIBLE = "infeasible"                        # Không khả thi (thiếu phần cứng CUDA hoặc model từ chối)


class HardwareRequirement(str, Enum):
    """Yêu cầu phần cứng tối thiểu."""
    CPU_OR_MPS = "cpu_or_mps"                        # Chạy tốt trên Apple Silicon M4 16GB
    NVIDIA_CUDA_8GB = "nvidia_cuda_8gb"              # Cần GPU NVIDIA CUDA ≥ 8GB VRAM
    NVIDIA_CUDA_24GB = "nvidia_cuda_24gb"            # Cần GPU NVIDIA CUDA ≥ 24GB VRAM
    CLOUD_ONLY = "cloud_only"                        # Xử lý trên đám mây của nhà cung cấp


class AlignmentMode(str, Enum):
    """Chế độ đồng bộ âm thanh - hình ảnh cho Lựa chọn (a)."""
    STRIP_ORIGINAL = "strip_original"                # Loại bỏ hoàn toàn track âm thanh gốc, thay bằng OmniVoice
    VOLUME_DUCK = "volume_duck"                      # Giảm âm thanh gốc xuống 0-5% làm ambient nền
    FREEZE_TAIL_DRIFT = "freeze_tail_drift"          # Video ngắn hơn thoại: giữ khung cuối và drift máy quay
    PAD_AUDIO_SILENCE = "pad_audio_silence"          # Thoại ngắn hơn video: căn chỉnh thoại ở giữa, giữ hành động


@dataclass
class ToolEvaluation:
    """Đánh giá chi tiết một công cụ/phương pháp lip-sync."""
    tool_id: str
    name: str
    category: LipSyncMethod
    official_url: str
    pricing_type: str                                # "$0 Open-Source", "Pay-as-you-go", "Subscription", v.v.
    cost_per_minute_usd: float                       # Ước tính chi phí USD / 1 phút video
    hardware: HardwareRequirement
    character_compatibility: Dict[CharacterType, FeasibilityStatus]
    terms_summary: str
    requires_external_upload: bool                   # Có bắt buộc upload ảnh/video nhân vật lên server ngoài?
    notes: str = ""


@dataclass
class LipSyncPlan:
    """Kế hoạch xử lý khẩu hình cho một shot."""
    shot_id: str
    method: LipSyncMethod
    tool_id: str
    estimated_cost_usd: float
    estimated_time_sec: float
    requires_user_confirmation: bool
    requires_external_upload: bool
    reasons: List[str] = field(default_factory=list)


@dataclass
class LipSyncResult:
    """Kết quả thực thi xử lý khẩu hình."""
    success: bool
    shot_id: str
    output_video_path: Optional[str]
    method_used: LipSyncMethod
    tool_id: str
    execution_time_sec: float
    cost_usd: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
