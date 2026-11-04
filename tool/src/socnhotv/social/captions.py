from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from socnhotv.social.platform_rules import get_platform_rule
from socnhotv.social.store import SocialStore
from socnhotv.social.video_library import VideoLibrary
from socnhotv.workspace.paths import project_path


class CaptionGenerateRequest(BaseModel):
    video_id: str
    platforms: List[str]
    tone: Optional[str] = "friendly"  # "friendly", "humorous", "expert", "exciting"
    goal: Optional[str] = "story"  # "story", "sales", "education"
    include_affiliate: bool = False
    affiliate_link: Optional[str] = None
    vary_per_account: bool = False
    account_ids: Optional[List[str]] = None


class PlatformCaptionResult(BaseModel):
    platform: str
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    hook: str
    caption: str
    hashtags: List[str]
    cta: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    disclosure_ad: bool = False
    disclosure_text: str = ""


# High quality smart templates for fallback & deterministic generation
HOOK_TEMPLATES = {
    "story": [
        "Chuyện gì sẽ xảy ra khi Sóc Bi gặp bác sĩ Koala khám răng?",
        "Bí mật đằng sau nụ cười rạng rỡ của Sóc Nhỏ hôm nay!",
        "Đừng bao giờ ăn kẹo trước khi đi ngủ nếu chưa xem video này!",
        "Khoảnh khắc hài hước nhất trong ngày của bé Sóc Bi!",
    ],
    "education": [
        "3 bài học bổ ích cho bé từ câu chuyện của Sóc Nhỏ!",
        "Ba mẹ đã biết cách giúp bé tự giác đánh răng mỗi ngày chưa?",
        "Khám phá kiến thức thú vị về thế giới tự nhiên cùng Sóc Nhỏ!",
        "Mẹo nhỏ giúp bé vui học đánh răng chuẩn y khoa cực dễ hiểu!",
    ],
    "sales": [
        "Món quà đặc biệt mà bé nào cũng mê mẩn từ cái nhìn đầu tiên!",
        "Review chân thực bàn chải điện hình Sóc Nhỏ cho các bé yêu!",
        "Bé sợ đánh răng? Xem ngay giải pháp thần kỳ của mẹ bỉm sữa!",
        "Ưu đãi độc quyền hôm nay: Tặng kèm quà xinh xắn cho bé!",
    ],
}

CTA_TEMPLATES = {
    "story": "👉 Nhấn Follow kênh để đón xem những tập phim hoạt hình mới nhất mỗi ngày nhé!",
    "education": "👉 Đừng quên chia sẻ video này đến các bậc phụ huynh để cùng nhau chăm sóc bé thật tốt!",
    "sales": "👉 Link sản phẩm chính hãng có ngay trong bio/phần mô tả. Đặt ngay kẻo hết quà!",
}

HASHTAG_POOLS = {
    "youtube": ["#SocNhoTV", "#HoatHinh3D", "#ThieuNhi", "#GiaoDucSom", "#SocBi", "#Koala"],
    "tiktok": ["#socnhotv", "#hoathinh3d", "#learnontiktok", "#mebimsua", "#embe", "#phimhoathinh"],
    "facebook": ["#SocNhoTV", "#HoatHinhThieuNhi", "#NuoiDayCon", "#KienThucChoBe", "#GiaDinh"],
    "instagram": ["#socnhotv", "#cartoon3d", "#kidstv", "#parenting", "#animation", "#family"],
    "threads": ["#socnhotv", "#hoathinh", "#giadinh"],
    "x": ["#SocNhoTV", "#Animation", "#Kids"],
}


class CaptionGenerator:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.library = VideoLibrary(project_id)
        self.store = SocialStore(project_id)

    def _get_video_context(self, video_id: str) -> Dict[str, Any]:
        videos = self.library.list_videos()
        for v in videos:
            if v["id"] == video_id:
                return v

        # Fallback reading from files directly
        req_file = project_path(self.project_id, "runs", "render_queue", f"{video_id}.req.json", ensure=False)
        if req_file.exists():
            try:
                with open(req_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {
                        "id": video_id,
                        "title": data.get("data", {}).get("title") or "Video hoạt hình Sóc Nhỏ",
                        "script_excerpt": data.get("data", {}).get("book_page_text", ""),
                    }
            except Exception:
                pass

        return {
            "id": video_id,
            "title": f"Video {video_id[:8]}",
            "script_excerpt": "",
        }

    def generate(self, req: CaptionGenerateRequest) -> List[PlatformCaptionResult]:
        video = self._get_video_context(req.video_id)
        title = video.get("title", "Video hoạt hình Sóc Nhỏ TV")
        script = video.get("script_excerpt", "")
        goal = req.goal if req.goal in HOOK_TEMPLATES else "story"

        all_accounts = {a.id: a for a in self.store.list_accounts()}
        selected_accounts = [all_accounts[aid] for aid in (req.account_ids or []) if aid in all_accounts]

        results: List[PlatformCaptionResult] = []

        # Affiliate text
        disclosure_text = ""
        if req.include_affiliate or req.affiliate_link:
            disclosure_text = "(Video có gắn liên kết tiếp thị liên kết / quảng cáo sản phẩm tài trợ #quangcao)"

        cta = CTA_TEMPLATES.get(goal, CTA_TEMPLATES["story"])
        if req.affiliate_link:
            cta += f"\n🔗 Link sản phẩm: {req.affiliate_link}"

        # If accounts are given and vary_per_account is True, generate for each account
        if req.vary_per_account and selected_accounts:
            for idx, acc in enumerate(selected_accounts):
                rule = get_platform_rule(acc.platform)
                hooks = HOOK_TEMPLATES[goal]
                hook = hooks[idx % len(hooks)]

                # Build body
                body_lines = [hook]
                if script:
                    body_lines.append(f"\n{script[:150]}...")
                body_lines.append(f"\n{cta}")
                if disclosure_text:
                    body_lines.append(f"\n{disclosure_text}")

                full_caption = "\n".join(body_lines)

                # Hashtags
                base_hashtags = list(acc.default_hashtags or HASHTAG_POOLS.get(acc.platform, []))
                # Rotate hashtags for variation
                if len(base_hashtags) > 1 and idx > 0:
                    base_hashtags = base_hashtags[idx % len(base_hashtags):] + base_hashtags[:idx % len(base_hashtags)]
                final_hashtags = base_hashtags[:rule.max_hashtags]

                # Append hashtags to caption if platform requires
                tag_str = " ".join(final_hashtags)
                if acc.platform in ["tiktok", "instagram", "threads", "x", "facebook"]:
                    if len(f"{full_caption}\n\n{tag_str}") <= rule.max_caption_length:
                        full_caption = f"{full_caption}\n\n{tag_str}"

                # Trim to limit
                full_caption = full_caption[:rule.max_caption_length]

                # YouTube specific
                yt_title = f"{hook} - Sóc Nhỏ TV"[:rule.max_title_length]
                yt_desc = f"{hook}\n\n{script or title}\n\n{cta}\n\n{disclosure_text}\n\n{tag_str}".strip()[:rule.max_caption_length]

                results.append(
                    PlatformCaptionResult(
                        platform=acc.platform,
                        account_id=acc.id,
                        account_name=acc.display_name or acc.handle,
                        hook=hook,
                        caption=full_caption,
                        hashtags=final_hashtags,
                        cta=cta,
                        title=yt_title if acc.platform == "youtube" else title[:rule.max_title_length],
                        description=yt_desc if acc.platform == "youtube" else None,
                        tags=final_hashtags if acc.platform == "youtube" else None,
                        disclosure_ad=bool(req.include_affiliate or req.affiliate_link),
                        disclosure_text=disclosure_text,
                    )
                )
            return results

        # Otherwise generate per platform in req.platforms
        for idx, plat in enumerate(req.platforms):
            rule = get_platform_rule(plat)
            hooks = HOOK_TEMPLATES[goal]
            hook = hooks[idx % len(hooks)]

            body_lines = [hook]
            if script:
                body_lines.append(f"\n{script[:150]}...")
            body_lines.append(f"\n{cta}")
            if disclosure_text:
                body_lines.append(f"\n{disclosure_text}")

            full_caption = "\n".join(body_lines)
            base_hashtags = HASHTAG_POOLS.get(plat, ["#socnhotv", f"#{plat}"])
            final_hashtags = base_hashtags[:rule.max_hashtags]
            tag_str = " ".join(final_hashtags)

            if plat in ["tiktok", "instagram", "threads", "x", "facebook"]:
                if len(f"{full_caption}\n\n{tag_str}") <= rule.max_caption_length:
                    full_caption = f"{full_caption}\n\n{tag_str}"

            full_caption = full_caption[:rule.max_caption_length]

            yt_title = f"{hook} - Sóc Nhỏ TV"[:rule.max_title_length]
            yt_desc = f"{hook}\n\n{script or title}\n\n{cta}\n\n{disclosure_text}\n\n{tag_str}".strip()[:rule.max_caption_length]

            results.append(
                PlatformCaptionResult(
                    platform=plat,
                    hook=hook,
                    caption=full_caption,
                    hashtags=final_hashtags,
                    cta=cta,
                    title=yt_title if plat == "youtube" else title[:rule.max_title_length],
                    description=yt_desc if plat == "youtube" else None,
                    tags=final_hashtags if plat == "youtube" else None,
                    disclosure_ad=bool(req.include_affiliate or req.affiliate_link),
                    disclosure_text=disclosure_text,
                )
            )

        return results
