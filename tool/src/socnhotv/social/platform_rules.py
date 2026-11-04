from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field

from socnhotv.social.models import PlatformType, PostTarget, SocialAccount


class Issue(BaseModel):
    level: Literal["error", "warn"]
    code: str
    message_vi: str


class PlatformRule(BaseModel):
    platform: PlatformType
    name_vi: str
    recommended_aspect_ratios: List[str]
    max_duration_s: float
    min_duration_s: float = 1.0
    max_size_mb: float
    max_title_length: int
    max_caption_length: int
    max_hashtags: int
    required_fields: List[str] = Field(default_factory=list)
    daily_quota_limit: int = 20


PLATFORM_RULES: Dict[str, PlatformRule] = {
    "youtube": PlatformRule(
        platform="youtube",
        name_vi="YouTube",
        recommended_aspect_ratios=["16:9", "9:16"],
        max_duration_s=43200.0,
        max_size_mb=256000.0,
        max_title_length=100,
        max_caption_length=5000,
        max_hashtags=15,
        required_fields=["title", "privacy", "category", "made_for_kids"],
        daily_quota_limit=6,  # 1600 units * 6 = 9600 units (free tier max 10k)
    ),
    "tiktok": PlatformRule(
        platform="tiktok",
        name_vi="TikTok",
        recommended_aspect_ratios=["9:16"],
        max_duration_s=600.0,
        max_size_mb=4000.0,
        max_title_length=150,
        max_caption_length=2200,
        max_hashtags=10,
        required_fields=["privacy", "comment", "duet", "stitch", "ai_generated_label"],
        daily_quota_limit=10,
    ),
    "facebook": PlatformRule(
        platform="facebook",
        name_vi="Facebook",
        recommended_aspect_ratios=["4:5", "9:16", "16:9"],
        max_duration_s=14400.0,
        max_size_mb=4000.0,
        max_title_length=255,
        max_caption_length=5000,
        max_hashtags=30,
        required_fields=["first_comment"],
        daily_quota_limit=25,
    ),
    "instagram": PlatformRule(
        platform="instagram",
        name_vi="Instagram",
        recommended_aspect_ratios=["9:16", "4:5", "1:1"],
        max_duration_s=900.0,
        max_size_mb=4000.0,
        max_title_length=150,
        max_caption_length=2200,
        max_hashtags=30,
        required_fields=["first_comment"],
        daily_quota_limit=50,
    ),
    "threads": PlatformRule(
        platform="threads",
        name_vi="Threads",
        recommended_aspect_ratios=["9:16", "1:1", "16:9"],
        max_duration_s=300.0,
        max_size_mb=1000.0,
        max_title_length=100,
        max_caption_length=500,
        max_hashtags=5,
        required_fields=[],
        daily_quota_limit=20,
    ),
    "x": PlatformRule(
        platform="x",
        name_vi="X (Twitter)",
        recommended_aspect_ratios=["16:9", "1:1", "9:16"],
        max_duration_s=140.0,
        max_size_mb=512.0,
        max_title_length=100,
        max_caption_length=280,
        max_hashtags=4,
        required_fields=[],
        daily_quota_limit=20,
    ),
}

# Default fallback rule
DEFAULT_RULE = PlatformRule(
    platform="youtube",
    name_vi="Thủ công",
    recommended_aspect_ratios=["9:16", "16:9", "4:5", "1:1"],
    max_duration_s=86400.0,
    max_size_mb=10000.0,
    max_title_length=255,
    max_caption_length=5000,
    max_hashtags=30,
    required_fields=[],
    daily_quota_limit=999,
)


def get_platform_rule(platform: str) -> PlatformRule:
    return PLATFORM_RULES.get(platform.lower(), DEFAULT_RULE)


def pick_best_variant(variants: Dict[str, str], platform: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (variant_key, path) that best matches platform aspect ratio requirements."""
    if not variants:
        return None, None
    plat = platform.lower()
    # Preferred mapping order
    priority_map: Dict[str, List[str]] = {
        "tiktok": ["tiktok", "shorts", "9:16", "reels", "vertical", "youtube"],
        "instagram": ["reels", "tiktok", "shorts", "9:16", "vertical", "youtube"],
        "threads": ["shorts", "tiktok", "reels", "9:16", "vertical", "youtube"],
        "facebook": ["reels", "facebook", "tiktok", "shorts", "youtube", "16:9"],
        "youtube": ["youtube", "16:9", "horizontal", "shorts", "tiktok"],
        "x": ["x", "twitter", "youtube", "16:9", "shorts", "tiktok"],
    }
    candidates = priority_map.get(plat, [plat])
    for cand in candidates:
        for k, v in variants.items():
            if k.lower() == cand:
                return k, v
    # Fallback to any variant
    k, v = next(iter(variants.items()))
    return k, v


def validate(
    video: Optional[Dict[str, Any]],
    target: Dict[str, Any] | PostTarget,
    account: Optional[SocialAccount | Dict[str, Any]] = None,
) -> List[Issue]:
    """Validate video and target against platform rules.
    
    Returns a list of Issue objects (level: 'error' or 'warn').
    """
    issues: List[Issue] = []

    # Normalize target data
    if isinstance(target, PostTarget):
        platform = target.platform
        title = target.title
        caption = target.caption
        hashtags = target.hashtags
    else:
        platform = target.get("platform", "youtube")
        title = target.get("title", "")
        caption = target.get("caption", "")
        hashtags = target.get("hashtags", [])

    rule = get_platform_rule(platform)

    # 1. Validate Account Status
    if account:
        status = account.status if isinstance(account, SocialAccount) else account.get("status")
        display_name = account.display_name if isinstance(account, SocialAccount) else account.get("display_name", "")
        if status == "expired":
            issues.append(
                Issue(
                    level="error",
                    code="account_expired",
                    message_vi=f"Tài khoản {display_name} đã hết hạn xác thực OAuth, cần kết nối lại.",
                )
            )
        elif status == "disabled":
            issues.append(
                Issue(
                    level="error",
                    code="account_disabled",
                    message_vi=f"Tài khoản {display_name} đang bị tạm khoá/vô hiệu hoá.",
                )
            )

    # 2. Validate Video Properties
    if video:
        duration_s = float(video.get("duration_s", 0.0))
        size_mb = float(video.get("size_mb", 0.0))
        width = int(video.get("width", 0))
        height = int(video.get("height", 0))
        variants = video.get("variants", {})

        # Duration check
        if duration_s > rule.max_duration_s:
            issues.append(
                Issue(
                    level="error",
                    code="duration_exceeded",
                    message_vi=f"Thời lượng video ({duration_s:.0f}s) vượt quá giới hạn {rule.max_duration_s:.0f}s của {rule.name_vi}.",
                )
            )

        # Size check
        if size_mb > rule.max_size_mb:
            issues.append(
                Issue(
                    level="error",
                    code="size_exceeded",
                    message_vi=f"Dung lượng video ({size_mb:.1f}MB) vượt quá giới hạn {rule.max_size_mb:.0f}MB của {rule.name_vi}.",
                )
            )

        # Aspect ratio check
        aspect_ratio = video.get("aspect_ratio", "")
        if not aspect_ratio and width > 0 and height > 0:
            aspect_ratio = "9:16" if height > width else "16:9"

        # Check if platform strictly recommends 9:16
        if rule.recommended_aspect_ratios == ["9:16"]:
            has_916_variant = any(k in ["tiktok", "shorts", "reels", "9:16"] for k in variants)
            if aspect_ratio == "16:9" and not has_916_variant:
                issues.append(
                    Issue(
                        level="warn",
                        code="ratio_mismatch",
                        message_vi=f"Video tỉ lệ 16:9 ngang không tối ưu cho {rule.name_vi} (khuyên dùng 9:16 dọc). Đề xuất: dùng bản blur-pad hoặc render lại biến thể 9:16.",
                    )
                )
        elif "16:9" in rule.recommended_aspect_ratios and platform == "youtube" and duration_s > 60:
            if aspect_ratio == "9:16":
                issues.append(
                    Issue(
                        level="warn",
                        code="ratio_mismatch",
                        message_vi="Video tỉ lệ dọc (9:16) dài hơn 60s sẽ hiển thị viền đen 2 bên trên YouTube màn hình rộng.",
                    )
                )

    # 3. Validate Text Lengths
    if title and len(title) > rule.max_title_length:
        issues.append(
            Issue(
                level="error",
                code="title_too_long",
                message_vi=f"Tiêu đề ({len(title)} ký tự) vượt quá giới hạn {rule.max_title_length} ký tự của {rule.name_vi}.",
            )
        )

    if caption and len(caption) > rule.max_caption_length:
        issues.append(
            Issue(
                level="error",
                code="caption_too_long",
                message_vi=f"Nội dung caption ({len(caption)} ký tự) vượt quá giới hạn {rule.max_caption_length} ký tự của {rule.name_vi}.",
            )
        )

    if len(hashtags) > rule.max_hashtags:
        issues.append(
            Issue(
                level="warn",
                code="too_many_hashtags",
                message_vi=f"Số lượng hashtag ({len(hashtags)}) vượt khuyến nghị {rule.max_hashtags} của {rule.name_vi}.",
            )
        )

    return issues
