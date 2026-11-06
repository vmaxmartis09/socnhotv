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
from socnhotv.workspace.paths import project_path, repo_root


def resolve_media_file(project_id: str, raw_path: Optional[str]) -> Optional[Path]:
    """Resolves media path whether absolute, relative to project, or repo-relative."""
    if not raw_path:
        return None
    p = Path(raw_path)
    if p.is_absolute() and p.exists():
        return p
    try:
        proj_p = project_path(project_id, raw_path)
        if proj_p.exists():
            return proj_p
    except Exception:
        pass
    if p.exists():
        return p.resolve()
    try:
        repo_p = repo_root() / raw_path
        if repo_p.exists():
            return repo_p
    except Exception:
        pass
    return None


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
        resolved_vid = resolve_media_file(project_id, media.path) if media and media.path else None
        if resolved_vid and resolved_vid.exists():
            try:
                if video_dest.exists():
                    video_dest.unlink()
                try:
                    os.link(resolved_vid, video_dest)
                except Exception:
                    shutil.copy2(resolved_vid, video_dest)
            except Exception:
                pass
        else:
            video_dest.write_text("DUMMY_VIDEO_FILE", encoding="utf-8")

        # 3. Cover image
        cover_dest = pkg_dir / "cover.jpg"
        resolved_cover = resolve_media_file(project_id, media.thumb) if media and media.thumb else None
        if resolved_cover and resolved_cover.exists():
            try:
                shutil.copy2(resolved_cover, cover_dest)
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


def create_manual_package(
    project_id: str,
    post_id: str,
    platform: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Builds the complete manual publishing package for a post.
    Resolves post from SocialStore, picks target, writes bundle, generates .zip,
    and returns package metadata.
    """
    from socnhotv.social.store import SocialStore
    store = SocialStore(project_id)
    post = store.get_post(post_id)
    if not post:
        raise ValueError(f"Post '{post_id}' not found in project '{project_id}'")

    target: Optional[PostTarget] = None
    if platform:
        target = next((t for t in post.targets if t.platform == platform), None)
    if not target and post.targets:
        target = post.targets[0]
    if not target:
        target = PostTarget(
            id=f"tgt_{post_id[:8]}",
            account_id="manual_default",
            platform=platform or "youtube",
            title=post.title,
            caption=post.title,
        )

    acc = store.get_account(target.account_id) or SocialAccount(
        id=target.account_id,
        platform=target.platform,
        handle=f"@{target.platform}",
        display_name=f"{target.platform.upper()} Channel",
    )

    media = post.media[0] if post.media else None
    adapter = ManualAdapter(platform=target.platform)
    res = adapter.publish(
        account=acc,
        target=target,
        media=media,
        project_id=project_id,
        post_id=post.id,
    )

    pkg_dir = Path(res.url)
    zip_path = export_package_zip(project_id, post.id, target.platform)

    video_file = pkg_dir / "video.mp4"
    has_real_video = (
        video_file.exists()
        and video_file.stat().st_size > 0
        and video_file.read_bytes() != b"DUMMY_VIDEO_FILE"
    )

    return {
        "post_id": post.id,
        "target_id": target.id,
        "platform": target.platform,
        "package_dir": str(pkg_dir),
        "zip_path": str(zip_path),
        "zip_filename": zip_path.name,
        "has_real_video": has_real_video,
        "caption": (pkg_dir / "caption.txt").read_text(encoding="utf-8") if (pkg_dir / "caption.txt").exists() else "",
        "hashtags": (pkg_dir / "hashtags.txt").read_text(encoding="utf-8") if (pkg_dir / "hashtags.txt").exists() else "",
        "checklist": (pkg_dir / "checklist.md").read_text(encoding="utf-8") if (pkg_dir / "checklist.md").exists() else "",
    }


def get_manual_package_info(
    project_id: str,
    post_id: str,
    platform: str,
) -> Optional[Dict[str, Any]]:
    """Returns metadata of an existing package or None."""
    pkg_dir = project_path(project_id, "publishing", "packages", post_id, platform)
    if not pkg_dir.exists():
        return None
    zip_path = pkg_dir.parent / f"{platform}_package_{post_id}.zip"
    caption = (pkg_dir / "caption.txt").read_text(encoding="utf-8") if (pkg_dir / "caption.txt").exists() else ""
    hashtags = (pkg_dir / "hashtags.txt").read_text(encoding="utf-8") if (pkg_dir / "hashtags.txt").exists() else ""
    checklist = (pkg_dir / "checklist.md").read_text(encoding="utf-8") if (pkg_dir / "checklist.md").exists() else ""
    video_file = pkg_dir / "video.mp4"
    has_real_video = (
        video_file.exists()
        and video_file.stat().st_size > 0
        and video_file.read_bytes() != b"DUMMY_VIDEO_FILE"
    )

    return {
        "post_id": post_id,
        "platform": platform,
        "package_dir": str(pkg_dir),
        "zip_path": str(zip_path) if zip_path.exists() else None,
        "zip_filename": zip_path.name if zip_path.exists() else None,
        "has_real_video": has_real_video,
        "caption": caption,
        "hashtags": hashtags,
        "checklist": checklist,
    }
