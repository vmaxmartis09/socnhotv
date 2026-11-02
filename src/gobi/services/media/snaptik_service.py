"""SnapTik Service - High-level media ingestion and download orchestrator."""

import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable

from gobi.adapters.scrapers.snaptik_scraper import SnaptikScraper
from gobi.domain.snaptik_models import (
    SnaptikVideoItem,
    SnaptikDownloadResult,
)

logger = logging.getLogger(__name__)


def sanitize_filename(name: str, max_length: int = 60) -> str:
    """Sanitize string to be safe for filenames across OS platforms (ASCII slug)."""
    # Normalize unicode diacritics (e.g. 'Áo Khoác' -> 'Ao Khoac')
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_text = nfkd.encode("ASCII", "ignore").decode("utf-8")
    # Replace non-alphanumeric chars with underscore
    clean = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", ascii_text)
    clean = re.sub(r"_+", "_", clean).strip("._")
    if not clean:
        clean = "tiktok_video"
    return clean[:max_length]


class SnaptikService:
    """Orchestrates video extraction, stream downloading, and asset storage."""

    def __init__(self, scraper: Optional[SnaptikScraper] = None):
        self.scraper = scraper or SnaptikScraper()

    def get_info(self, url: str) -> SnaptikVideoItem:
        """Extract video metadata without downloading files."""
        return self.scraper.extract(url)

    def download(
        self,
        url: str,
        output_dir: str = "output/videos",
        filename: Optional[str] = None,
        watermark: bool = False,
        hd: bool = True,
        download_audio: bool = False,
        download_cover: bool = False,
        save_metadata: bool = True,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> SnaptikDownloadResult:
        """Download TikTok source video, audio, cover, and metadata to project."""
        target_dir = Path(output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            info = self.get_info(url)
        except Exception as e:
            logger.error(f"Failed to extract video info for {url}: {e}")
            return SnaptikDownloadResult(
                success=False,
                error=f"Extraction error: {str(e)}",
            )

        # Base stem for output files
        if filename:
            custom_path = Path(filename)
            if custom_path.suffix.lower() == ".mp4":
                stem = sanitize_filename(custom_path.stem)
                # If custom filename specified directory
                if len(custom_path.parts) > 1:
                    target_dir = custom_path.parent
                    target_dir.mkdir(parents=True, exist_ok=True)
            else:
                stem = sanitize_filename(filename)
        else:
            author_tag = info.author.unique_id or "tiktok"
            title_tag = sanitize_filename(info.title or "video", max_length=40)
            stem = f"{author_tag}_{info.id}_{title_tag}"

        video_path = None
        audio_path = None
        cover_path = None
        metadata_path = None
        image_paths = []

        # 1. Handle Photo Slideshow if present
        if info.is_slideshow and info.media.images:
            slides_dir = target_dir / f"{stem}_slides"
            slides_dir.mkdir(parents=True, exist_ok=True)
            for i, img_url in enumerate(info.media.images, 1):
                img_file = slides_dir / f"slide_{i:02d}.jpg"
                try:
                    self.scraper.download_stream(img_url, img_file)
                    image_paths.append(str(img_file))
                except Exception as img_err:
                    logger.warning(f"Failed to download slide {i}: {img_err}")

        # 2. Download Video Stream
        # Select appropriate video stream: HD -> clean video -> watermarked video
        target_video_url = None
        if watermark and info.media.watermark_video_url:
            target_video_url = info.media.watermark_video_url
        elif hd and info.media.video_hd_url:
            target_video_url = info.media.video_hd_url
        elif info.media.video_url:
            target_video_url = info.media.video_url

        if target_video_url:
            v_dest = target_dir / f"{stem}.mp4"
            try:
                self.scraper.download_stream(target_video_url, v_dest, on_progress=on_progress)
                video_path = str(v_dest)
            except Exception as e:
                # If HD stream fails, fallback to standard clean video
                if hd and info.media.video_url and target_video_url != info.media.video_url:
                    try:
                        self.scraper.download_stream(info.media.video_url, v_dest, on_progress=on_progress)
                        video_path = str(v_dest)
                    except Exception as e_fallback:
                        return SnaptikDownloadResult(
                            success=False,
                            info=info,
                            error=f"Video download failed: {e_fallback}",
                        )
                else:
                    return SnaptikDownloadResult(
                        success=False,
                        info=info,
                        error=f"Video download failed: {e}",
                    )

        # 3. Download Audio MP3 if requested
        if download_audio and info.media.audio_url:
            a_dir = Path("output/audio") if output_dir == "output/videos" else target_dir
            a_dir.mkdir(parents=True, exist_ok=True)
            a_dest = a_dir / f"{stem}_audio.mp3"
            try:
                self.scraper.download_stream(info.media.audio_url, a_dest)
                audio_path = str(a_dest)
            except Exception as e:
                logger.warning(f"Could not download audio stream: {e}")

        # 4. Download Cover Image if requested
        if download_cover and info.media.cover_url:
            c_dest = target_dir / f"{stem}_cover.jpg"
            try:
                self.scraper.download_stream(info.media.cover_url, c_dest)
                cover_path = str(c_dest)
            except Exception as e:
                logger.warning(f"Could not download cover image: {e}")

        # 5. Save JSON Metadata
        if save_metadata:
            m_dest = target_dir / f"{stem}.json"
            try:
                meta_data = {
                    "id": info.id,
                    "original_url": info.original_url,
                    "title": info.title,
                    "duration": info.duration,
                    "is_slideshow": info.is_slideshow,
                    "author": info.author.model_dump(),
                    "stats": info.stats.model_dump(),
                    "source_engine": info.source_engine,
                    "saved_files": {
                        "video": video_path,
                        "audio": audio_path,
                        "cover": cover_path,
                        "slides": image_paths,
                    },
                }
                with open(m_dest, "w", encoding="utf-8") as f:
                    json.dump(meta_data, f, ensure_ascii=False, indent=2)
                metadata_path = str(m_dest)
            except Exception as e:
                logger.warning(f"Could not save metadata JSON: {e}")

        return SnaptikDownloadResult(
            success=True,
            video_path=video_path,
            audio_path=audio_path,
            cover_path=cover_path,
            metadata_path=metadata_path,
            image_paths=image_paths,
            info=info,
        )

    def download_batch(
        self,
        urls: List[str],
        output_dir: str = "output/videos",
        **kwargs,
    ) -> List[SnaptikDownloadResult]:
        """Download multiple TikTok videos in batch."""
        results = []
        for url in urls:
            u = url.strip()
            if not u or u.startswith("#"):
                continue
            logger.info(f"Processing batch download for: {u}")
            res = self.download(u, output_dir=output_dir, **kwargs)
            results.append(res)
        return results
