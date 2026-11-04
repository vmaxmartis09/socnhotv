from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

PlatformId = Literal["tiktok", "douyin", "reels", "shorts", "youtube", "facebook"]
FitStrategyType = Literal["cover", "contain", "blur-pad"]


class SafeZone(BaseModel):
    top: int
    bottom: int
    left: int
    right: int

    @property
    def height_safe(self) -> int:
        return self.top + self.bottom

    @property
    def width_safe(self) -> int:
        return self.left + self.right


class PlatformPreset(BaseModel):
    id: PlatformId
    name: str
    width: int
    height: int
    aspect_ratio: str
    fps: int = 30
    max_duration_sec: Optional[float] = None
    safe_zone: SafeZone
    loudness_lufs: float = -14.0
    audio_bitrate: str = "192k"
    video_bitrate: str = "8000k"
    codec: str = "libx264"
    audio_codec: str = "aac"
    notes: str = ""


PLATFORMS: Dict[PlatformId, PlatformPreset] = {
    "tiktok": PlatformPreset(
        id="tiktok",
        name="TikTok",
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        fps=30,
        max_duration_sec=600.0,
        safe_zone=SafeZone(top=180, bottom=320, left=40, right=120),
        loudness_lufs=-14.0,
        audio_bitrate="192k",
        video_bitrate="8000k",
        codec="libx264",
        notes="cột nút phải",
    ),
    "douyin": PlatformPreset(
        id="douyin",
        name="Douyin",
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        fps=30,
        max_duration_sec=900.0,
        safe_zone=SafeZone(top=200, bottom=340, left=40, right=120),
        loudness_lufs=-14.0,
        audio_bitrate="192k",
        video_bitrate="8000k",
        codec="libx264",
        notes="",
    ),
    "reels": PlatformPreset(
        id="reels",
        name="Instagram Reels",
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        fps=30,
        max_duration_sec=180.0,
        safe_zone=SafeZone(top=220, bottom=380, left=40, right=100),
        loudness_lufs=-14.0,
        audio_bitrate="192k",
        video_bitrate="8000k",
        codec="libx264",
        notes="",
    ),
    "shorts": PlatformPreset(
        id="shorts",
        name="YouTube Shorts",
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        fps=30,
        max_duration_sec=180.0,
        safe_zone=SafeZone(top=160, bottom=300, left=40, right=110),
        loudness_lufs=-14.0,
        audio_bitrate="192k",
        video_bitrate="8000k",
        codec="libx264",
        notes="",
    ),
    "youtube": PlatformPreset(
        id="youtube",
        name="YouTube Standard",
        width=1920,
        height=1080,
        aspect_ratio="16:9",
        fps=30,
        max_duration_sec=None,
        safe_zone=SafeZone(top=60, bottom=90, left=60, right=60),
        loudness_lufs=-14.0,
        audio_bitrate="192k",
        video_bitrate="12000k",
        codec="libx264",
        notes="title-safe 90%",
    ),
    "facebook": PlatformPreset(
        id="facebook",
        name="Facebook Feed",
        width=1080,
        height=1350,
        aspect_ratio="4:5",
        fps=30,
        max_duration_sec=240.0,
        safe_zone=SafeZone(top=80, bottom=160, left=40, right=40),
        loudness_lufs=-14.0,
        audio_bitrate="192k",
        video_bitrate="8000k",
        codec="libx264",
        notes="feed",
    ),
}


def get_platform(platform_id: str | PlatformId) -> PlatformPreset:
    """Trả về preset cấu hình của nền tảng tương ứng."""
    key = str(platform_id).lower().strip()
    if key not in PLATFORMS:
        raise ValueError(f"Nền tảng '{platform_id}' không hợp lệ. Hỗ trợ: {list(PLATFORMS.keys())}")
    return PLATFORMS[key]  # type: ignore[index]


def list_platforms() -> List[PlatformPreset]:
    """Danh sách toàn bộ các platform presets hỗ trợ."""
    return list(PLATFORMS.values())


def fit_strategy(
    src_w: int,
    src_h: int,
    target_w: int,
    target_h: int,
    strategy: FitStrategyType = "cover",
) -> Dict[str, Any]:
    """Tính toán thông số biến đổi kích thước khung hình (scale, crop, pad, blur-pad).

    Args:
        src_w: Chiều rộng gốc.
        src_h: Chiều cao gốc.
        target_w: Chiều rộng đích.
        target_h: Chiều cao đích.
        strategy: 'cover', 'contain', hoặc 'blur-pad'.

    Returns:
        Dict chứa các thông số căn chỉnh và chuỗi filter FFmpeg tương ứng.
    """
    if src_w <= 0 or src_h <= 0 or target_w <= 0 or target_h <= 0:
        raise ValueError("Kích thước video phải lớn hơn 0.")

    if strategy == "cover":
        scale = max(target_w / src_w, target_h / src_h)
        scaled_w = int(round(src_w * scale))
        scaled_h = int(round(src_h * scale))
        # Đảm bảo chia hết cho 2
        scaled_w = scaled_w if scaled_w % 2 == 0 else scaled_w + 1
        scaled_h = scaled_h if scaled_h % 2 == 0 else scaled_h + 1

        crop_x = max(0, (scaled_w - target_w) // 2)
        crop_y = max(0, (scaled_h - target_h) // 2)

        ffmpeg_filter = (
            f"scale={scaled_w}:{scaled_h}:flags=lanczos,"
            f"crop={target_w}:{target_h}:{crop_x}:{crop_y}"
        )
        return {
            "strategy": "cover",
            "scale": scale,
            "scaled_w": scaled_w,
            "scaled_h": scaled_h,
            "crop_x": crop_x,
            "crop_y": crop_y,
            "pad_x": 0,
            "pad_y": 0,
            "target_w": target_w,
            "target_h": target_h,
            "ffmpeg_filter": ffmpeg_filter,
        }

    elif strategy == "contain":
        scale = min(target_w / src_w, target_h / src_h)
        scaled_w = int(round(src_w * scale))
        scaled_h = int(round(src_h * scale))
        scaled_w = scaled_w if scaled_w % 2 == 0 else scaled_w + 1
        scaled_h = scaled_h if scaled_h % 2 == 0 else scaled_h + 1

        pad_x = max(0, (target_w - scaled_w) // 2)
        pad_y = max(0, (target_h - scaled_h) // 2)

        ffmpeg_filter = (
            f"scale={scaled_w}:{scaled_h}:flags=lanczos,"
            f"pad={target_w}:{target_h}:{pad_x}:{pad_y}:color=black"
        )
        return {
            "strategy": "contain",
            "scale": scale,
            "scaled_w": scaled_w,
            "scaled_h": scaled_h,
            "crop_x": 0,
            "crop_y": 0,
            "pad_x": pad_x,
            "pad_y": pad_y,
            "target_w": target_w,
            "target_h": target_h,
            "ffmpeg_filter": ffmpeg_filter,
        }

    elif strategy == "blur-pad":
        # Background: cover + blur; Foreground: contain + overlay center
        ffmpeg_filter = (
            f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
            f"crop={target_w}:{target_h},boxblur=20:5[bg];"
            f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )
        return {
            "strategy": "blur-pad",
            "target_w": target_w,
            "target_h": target_h,
            "ffmpeg_filter": ffmpeg_filter,
        }

    else:
        raise ValueError(f"Chiến lược '{strategy}' không hỗ trợ. Chọn cover, contain, hoặc blur-pad.")
