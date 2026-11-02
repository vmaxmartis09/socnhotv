"""
GOBI SOCIAL - VIDEO INGEST (TẦNG 2: SERVICES - MEDIA)
======================================================
Tiện ích dùng chung: tải/nạp video tham khảo (file nội bộ hoặc URL TikTok/YouTube),
đọc metadata (ffprobe), và tách audio (ffmpeg). Dùng chung bởi MotionMimicWorkflow
và ContentRemixWorkflow — tránh trùng lặp logic.
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict


def get_video_metadata(video_path: str | Path) -> Dict[str, Any]:
    """Lấy thông tin duration, fps, resolution của video bằng ffprobe."""
    vid = Path(video_path).resolve()
    meta = {"duration": 15.0, "width": 1080, "height": 1920, "fps": 30.0}
    if not vid.exists():
        return meta

    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration",
        "-show_entries", "format=duration",
        "-of", "json",
        str(vid)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(res.stdout)
        fmt = data.get("format", {})
        streams = data.get("streams", [{}])
        stream = streams[0] if streams else {}

        dur = float(fmt.get("duration") or stream.get("duration") or 15.0)
        meta["duration"] = round(dur, 2)
        meta["width"] = int(stream.get("width") or 1080)
        meta["height"] = int(stream.get("height") or 1920)
    except Exception:
        pass
    return meta


def ingest_reference_video(source: str, job_dir: Path, workspace_root: Path) -> Path:
    """
    Tiếp nhận video mẫu: Có thể là đường dẫn file nội bộ hoặc URL TikTok / YouTube.
    """
    source_str = str(source).strip()
    local_path = Path(source_str)

    if local_path.exists() and local_path.is_file():
        dest = job_dir / f"ref_video{local_path.suffix}"
        shutil.copy2(local_path, dest)
        return dest

    # Nếu là URL: Ưu tiên dùng SnaptikService cho TikTok, fallback sang yt-dlp
    if source_str.startswith("http://") or source_str.startswith("https://"):
        dest = job_dir / "downloaded_reference.mp4"
        print(f"[*] Đang tải reference video từ URL: {source_str}...")

        # 1. Thử SnaptikService nếu là link TikTok
        if "tiktok.com" in source_str:
            try:
                from gobi.services.media.snaptik_service import SnaptikService
                service = SnaptikService()
                res = service.download(
                    source_str,
                    output_dir=str(job_dir),
                    filename="downloaded_reference.mp4",
                    hd=True
                )
                if res.video_path and Path(res.video_path).exists():
                    # Kiểm tra xem có video stream không
                    meta = get_video_metadata(res.video_path)
                    if meta.get("width", 0) > 0 and meta.get("height", 0) > 0:
                        return Path(res.video_path)
            except Exception as ex:
                print(f"[!] SnaptikService gặp lỗi: {ex}. Chuyển sang fallback...")

        # 2. Fallback qua yt-dlp với cờ ép buộc tải video stream
        cmd = [
            str(workspace_root / ".venv" / "bin" / "yt-dlp"),
            source_str,
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "-o", str(dest)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return dest

    raise FileNotFoundError(f"Không tìm thấy reference video tại: {source}")


def extract_audio(video_path: Path, output_audio_path: Path) -> Path:
    """Trích xuất file audio từ video phục vụ ghép nhạc và đồng bộ khẩu hình."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn", "-acodec", "libmp3lame", "-q:a", "2",
        str(output_audio_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return output_audio_path
