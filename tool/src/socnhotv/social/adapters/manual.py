"""Manual Export Package Adapter for all social platforms.

Generates a ready-to-upload manual publication bundle under:
data/projects/<project_id>/publishing/packages/<post_id>/<platform>/
- video.mp4
- cover.jpg
- caption.txt
- hashtags.txt
- checklist.md
- meta.json
"""
from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from socnhotv.social.adapters.base import Capabilities, Issue, PublishAdapter, PublishResult
from socnhotv.social.models import PostMedia, PostTarget, SocialAccount
from socnhotv.workspace.paths import project_path


class ManualAdapter(PublishAdapter):
    def __init__(self, platform: str = "manual"):
        self.platform = platform  # type: ignore

    def capabilities(self) -> Capabilities:
        return Capabilities(
            direct_post=False,
            draft_upload=True,
            schedule_native=False,
            thumbnail=True,
            first_comment=True,
            product_link=True,
        )

    def connect_url(self, account: SocialAccount, redirect_uri: str) -> str:
        return ""

    def exchange_code(self, account: SocialAccount, code: str, redirect_uri: str) -> Dict[str, Any]:
        return {"mode": "manual", "status": "active"}

    def refresh(self, account: SocialAccount) -> Dict[str, Any]:
        return {"mode": "manual", "status": "active"}

    def validate(self, target: PostTarget, media: Optional[PostMedia]) -> List[Issue]:
        issues: List[Issue] = []
        if not target.caption:
            issues.append(Issue(level="warning", code="empty_caption", message="Bài viết chưa có caption"))
        return issues

    def publish(
        self,
        account: SocialAccount,
        target: PostTarget,
        media: Optional[PostMedia],
        project_id: str = "soc-nho-tv",
        post_id: str = "post_unknown",
    ) -> PublishResult:
        """Export manual package bundle to publishing/packages/<post_id>/<platform>/."""
        pkg_dir = project_path(
            project_id,
            "publishing",
            "packages",
            post_id,
            target.platform,
            ensure=True,
        )
        pkg_dir.mkdir(parents=True, exist_ok=True)

        # 1. Caption & Hashtags
        caption_path = pkg_dir / "caption.txt"
        caption_path.write_text(target.caption or "", encoding="utf-8")

        tags_path = pkg_dir / "hashtags.txt"
        tags_str = " ".join([h if h.startswith("#") else f"#{h}" for h in target.hashtags])
        tags_path.write_text(tags_str, encoding="utf-8")

        # 2. Video file
        video_dest = pkg_dir / "video.mp4"
        if media and media.path and os.path.exists(media.path):
            try:
                # Try hardlink or copy
                if video_dest.exists():
                    video_dest.unlink()
                try:
                    os.link(media.path, video_dest)
                except Exception:
                    shutil.copy2(media.path, video_dest)
            except Exception:
                pass
        else:
            video_dest.write_text("DUMMY_VIDEO_FILE", encoding="utf-8")

        # 3. Cover image
        cover_dest = pkg_dir / "cover.jpg"
        if media and media.thumb and os.path.exists(media.thumb):
            try:
                shutil.copy2(media.thumb, cover_dest)
            except Exception:
                cover_dest.write_text("DUMMY_COVER", encoding="utf-8")
        else:
            cover_dest.write_text("DUMMY_COVER", encoding="utf-8")

        # 4. Meta JSON
        meta_dest = pkg_dir / "meta.json"
        meta_data = {
            "post_id": post_id,
            "target_id": target.id,
            "account": account.model_dump(),
            "platform": target.platform,
            "title": target.title,
            "caption": target.caption,
            "hashtags": target.hashtags,
            "product_link": target.product_link,
            "disclosure_ad": target.disclosure_ad,
            "privacy": target.privacy,
            "scheduled_at": target.scheduled_at,
        }
        meta_dest.write_text(json.dumps(meta_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # 5. Checklist markdown
        checklist_dest = pkg_dir / "checklist.md"
        chk_content = f"""# Hướng dẫn đăng bài thủ công: {target.platform.upper()}

- **Tài khoản:** {account.display_name} ({account.handle})
- **Tiêu đề:** {target.title or '(Không có)'}
- **Giờ đăng đề xuất:** {target.scheduled_at or 'Đăng ngay'}

## Các bước thực hiện:
1. Mở ứng dụng hoặc trang quản trị {target.platform.upper()}.
2. Đính kèm tệp `video.mp4` và chọn ảnh bìa `cover.jpg`.
3. Dán nội dung từ `caption.txt` và `hashtags.txt`.
{"4. Thêm liên kết sản phẩm: " + target.product_link if target.product_link else ""}
{"5. Bật tuỳ chọn 'Nội dung trả phí / Quảng cáo' (Affiliate disclosure)" if target.disclosure_ad else ""}
6. Bấm ĐĂNG.
7. Sau khi đăng xong, quay lại Social Manager và bấm 'Tôi đã đăng' để dán link URL thực tế.
"""
        checklist_dest.write_text(chk_content, encoding="utf-8")

        return PublishResult(
            external_id=f"pkg_{post_id}_{target.platform}",
            url=str(pkg_dir),
            status="published",
            raw_response={"package_dir": str(pkg_dir)},
        )

    def fetch_status(self, account: SocialAccount, external_id: str) -> PublishResult:
        return PublishResult(external_id=external_id, status="published")


def export_package_zip(project_id: str, post_id: str, platform: str) -> Path:
    """Pack manual publishing package into a downloadable .zip archive."""
    pkg_dir = project_path(project_id, "publishing", "packages", post_id, platform)
    if not pkg_dir.exists():
        raise FileNotFoundError(f"Package directory not found: {pkg_dir}")

    zip_path = pkg_dir.parent / f"{platform}_package_{post_id}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(pkg_dir):
            for file in files:
                file_full = Path(root) / file
                arcname = file_full.relative_to(pkg_dir)
                zipf.write(file_full, arcname)

    return zip_path
