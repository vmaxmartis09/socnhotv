"""
VMAX Video Engine Bridge - Integration with jub0t/Concat
Provides automated timeline creation, project generation (concat.json),
auto-captions, and direct execution with Concat engine for TikTok Affiliate Videos.
"""

import os
import sys
import json
import subprocess
from typing import List, Dict, Optional, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
DEFAULT_CONCAT_EXE = os.path.join(PROJECT_ROOT, "bin", "concat_engine", "concat.exe")

class ConcatProjectBuilder:
    """
    Builds native Concat project documents (concat.json) compliant with jub0t/Concat model.
    """
    def __init__(self, project_name: str = "TikTok_Affiliate_Video", width: int = 1080, height: int = 1920, fps: int = 30):
        self.project_name = project_name
        self.width = width
        self.height = height
        self.fps = fps
        self.timeline_id = "TL1"
        
        self.media_items: List[Dict[str, Any]] = []
        self.tracks = [
            {"id": "T1", "visible": True, "muted": False},  # Visuals / Products / KOC
            {"id": "T2", "visible": True, "muted": False},  # Audio / Voiceover
            {"id": "T3", "visible": True, "muted": False},  # Subtitles / Kinetic Captions / CTA
        ]
        self.clips: List[Dict[str, Any]] = []
        self._media_counter = 0
        self._clip_counter = 0

    def _next_media_id(self) -> str:
        self._media_counter += 1
        return f"m{self._media_counter}"

    def _next_clip_id(self) -> str:
        self._clip_counter += 1
        return f"c{self._clip_counter}"

    def add_media(self, file_path: str, kind: str = "image", duration: Optional[float] = None) -> str:
        """Register a media item into the project media bin."""
        abs_path = os.path.abspath(file_path).replace("\\", "/")
        # Avoid duplicate media entries
        for item in self.media_items:
            if item["path"] == abs_path:
                return item["id"]

        media_id = self._next_media_id()
        base_name = os.path.basename(abs_path)
        item = {
            "id": media_id,
            "path": abs_path,
            "name": base_name,
            "kind": kind,
            "hasAudio": (kind in ["video", "audio"]),
            "has_audio": (kind in ["video", "audio"]),
        }
        if duration is not None:
            item["duration"] = round(float(duration), 3)
        self.media_items.append(item)
        return media_id

    def add_image_clip(self, image_path: str, start: float, duration: float, scale: float = 1.0, offset_y: float = 0.0) -> str:
        """Add an image clip on Track 1 (Visual Track)."""
        media_id = self.add_media(image_path, kind="image")
        clip_id = self._next_clip_id()
        clip = {
            "id": clip_id,
            "trackId": "T1",
            "track_id": "T1",
            "mediaId": media_id,
            "media_id": media_id,
            "name": os.path.basename(image_path),
            "kind": "image",
            "start": round(start, 3),
            "duration": round(duration, 3),
            "sourceStart": 0.0,
            "source_start": 0.0,
            "volume": 1.0,
            "fadeIn": 0.0,
            "fade_in": 0.0,
            "fadeOut": 0.0,
            "fade_out": 0.0,
            "scale": scale,
            "offsetX": 0.0,
            "offset_x": 0.0,
            "offsetY": offset_y,
            "offset_y": offset_y,
            "rotation": 0.0,
            "opacity": 1.0,
            "speed": 1.0,
            "preservePitch": True,
            "preserve_pitch": True,
            "filters": [],
            "videoEffects": [],
            "video_effects": []
        }
        self.clips.append(clip)
        return clip_id

    def add_audio_clip(self, audio_path: str, start: float = 0.0, duration: Optional[float] = None, volume: float = 1.0) -> str:
        """Add a voiceover or background music clip on Track 2 (Audio Track)."""
        media_id = self.add_media(audio_path, kind="audio", duration=duration)
        clip_id = self._next_clip_id()
        clip = {
            "id": clip_id,
            "trackId": "T2",
            "track_id": "T2",
            "mediaId": media_id,
            "media_id": media_id,
            "name": os.path.basename(audio_path),
            "kind": "audio",
            "start": round(start, 3),
            "duration": round(duration, 3) if duration else 10.0,
            "sourceStart": 0.0,
            "source_start": 0.0,
            "volume": volume,
            "fadeIn": 0.2,
            "fade_in": 0.2,
            "fadeOut": 0.5,
            "fade_out": 0.5,
            "scale": 1.0,
            "offsetX": 0.0,
            "offset_x": 0.0,
            "offsetY": 0.0,
            "offset_y": 0.0,
            "rotation": 0.0,
            "opacity": 1.0,
            "speed": 1.0,
            "preservePitch": True,
            "preserve_pitch": True,
            "filters": [],
            "videoEffects": [],
            "video_effects": []
        }
        self.clips.append(clip)
        return clip_id

    def add_text_caption(self, text: str, start: float, duration: float, font_size: float = 0.065,
                         color: str = "#FFFC00", stroke_color: str = "#000000", bg_color: str = "#000000AA",
                         offset_y: float = 0.32) -> str:
        """Add styled TikTok caption / subtitle overlay on Track 3."""
        clip_id = self._next_clip_id()
        clip = {
            "id": clip_id,
            "trackId": "T3",
            "track_id": "T3",
            "mediaId": "",
            "media_id": "",
            "name": text[:20] + "..." if len(text) > 20 else text,
            "kind": "text",
            "start": round(start, 3),
            "duration": round(duration, 3),
            "sourceStart": 0.0,
            "source_start": 0.0,
            "volume": 1.0,
            "fadeIn": 0.0,
            "fade_in": 0.0,
            "fadeOut": 0.0,
            "fade_out": 0.0,
            "scale": 1.0,
            "offsetX": 0.0,
            "offset_x": 0.0,
            "offsetY": offset_y,
            "offset_y": offset_y,
            "rotation": 0.0,
            "opacity": 1.0,
            "speed": 1.0,
            "preservePitch": True,
            "preserve_pitch": True,
            "filters": [],
            "videoEffects": [],
            "video_effects": [],
            "text": {
                "content": text,
                "fontFamily": "\"Cabinet Grotesk\"",
                "fontSize": font_size,
                "fontWeight": 800.0,
                "italic": False,
                "color": color,
                "align": "center",
                "opacity": 1.0,
                "strokeWidth": 0.012,
                "strokeColor": stroke_color,
                "shadow": True,
                "background": bg_color,
                "backgroundRadius": 0.02,
                "backgroundPaddingX": 0.04,
                "backgroundPaddingY": 0.02,
                "lineHeight": 1.25,
                "tracking": 0.0,
                "maxWidth": 0.85,
                "maxHeight": 0.0
            }
        }
        self.clips.append(clip)
        return clip_id

    def to_dict(self) -> Dict[str, Any]:
        """Generate the full Concat document structure compliant with Concat 0.2.7."""
        video_spec = {
            "width": self.width,
            "height": self.height,
            "rateNum": self.fps,
            "rateDen": 1,
            "rate_num": self.fps,
            "rate_den": 1
        }
        timeline = {
            "id": self.timeline_id,
            "name": self.project_name,
            "video": video_spec,
            "tracks": self.tracks,
            "clips": self.clips
        }
        return {
            "concat": "0.2.7",
            "name": self.project_name,
            "video": video_spec,
            "tracks": self.tracks,
            "clips": self.clips,
            "media": self.media_items,
            "fonts": [],
            "timelines": [timeline],
            "activeTimelineId": self.timeline_id,
            "active_timeline_id": self.timeline_id
        }

    def save_project(self, target_folder: str) -> str:
        """Save project file concat.json in the specified folder."""
        os.makedirs(target_folder, exist_ok=True)
        json_path = os.path.join(target_folder, "concat.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        return json_path


class ConcatEngine:
    """
    High-level engine controller to launch Concat, preview, and build affiliate video projects.
    """
    def __init__(self, concat_exe: str = DEFAULT_CONCAT_EXE):
        self.concat_exe = concat_exe

    def is_available(self) -> bool:
        return os.path.isfile(self.concat_exe)

    def launch_editor(self, project_path: str) -> subprocess.Popen:
        """Launch Concat GUI with the project loaded."""
        if not self.is_available():
            raise FileNotFoundError(f"Concat binary not found at: {self.concat_exe}")
        
        abs_proj = os.path.abspath(project_path)
        cmd = [self.concat_exe, "--project", abs_proj]
        print(f"Launching Concat with project: {abs_proj}")
        process = subprocess.Popen(cmd, cwd=os.path.dirname(self.concat_exe))
        return process


def create_affiliate_tiktok_concat_project(scenes: List[Dict[str, Any]], audio_path: str, output_project_dir: str) -> str:
    """
    Assembles a full TikTok affiliate review video project for Concat:
    - 9:16 vertical resolution (1080x1920)
    - Aligned image cutaways
    - Audio track with voiceover
    - Synchronized styled TikTok subtitles
    """
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    
    # Get audio duration via ffprobe/ffmpeg
    cmd = [ff, "-i", audio_path]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
    duration = 15.0 # fallback
    for line in res.stderr.splitlines():
        if "Duration" in line:
            parts = line.strip().split(",")[0].split("Duration: ")[1].split(":")
            duration = float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
            break

    scene_dur = duration / len(scenes)
    builder = ConcatProjectBuilder("Affiliate_Cardigan_Review", width=1080, height=1920, fps=30)
    
    # 1. Add Audio
    builder.add_audio_clip(audio_path, start=0.0, duration=duration, volume=1.0)

    # 2. Add Visuals & Subtitles
    current_time = 0.0
    for idx, sc in enumerate(scenes):
        img_file = sc["img"]
        subtitle_text = sc["sub"]
        
        # Add visual image
        builder.add_image_clip(img_file, start=current_time, duration=scene_dur, scale=1.05)
        
        # Add styled caption
        builder.add_text_caption(
            text=subtitle_text,
            start=current_time,
            duration=scene_dur,
            font_size=0.058,
            color="#FFF500" if idx % 2 == 0 else "#FFFFFF",
            stroke_color="#000000",
            bg_color="#000000B0",
            offset_y=0.32
        )
        current_time += scene_dur

    saved_file = builder.save_project(output_project_dir)
    return saved_file
