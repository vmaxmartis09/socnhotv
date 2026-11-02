"""
=============================================================================
VMAX CORE VIDEO ENGINE (Autonomous & Headless Pipeline)
Integrates Concat Document Model (concat.json) with Autonomous Rendering
Eliminates any external .bat files - Fully native to VMAX Python Ecosystem.
=============================================================================
"""

import os
import sys
import json
import time
import subprocess
from typing import List, Dict, Optional, Any
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
CONCAT_BIN_DIR = os.path.join(PROJECT_ROOT, "bin", "concat_engine")
CONCAT_EXE = os.path.join(CONCAT_BIN_DIR, "concat.exe")
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


class VMaxVideoEngine:
    """
    Autonomous Video Engine for VMAX Affiliate & KOC Video Automation.
    Handles timeline generation, subtitles, motion, and headless export.
    """
    def __init__(self, concat_bin_dir: str = CONCAT_BIN_DIR):
        self.bin_dir = os.path.abspath(concat_bin_dir)
        self.concat_exe = os.path.join(self.bin_dir, "concat.exe")
        self.ffmpeg_exe = FFMPEG_EXE

    def is_concat_available(self) -> bool:
        return os.path.isfile(self.concat_exe)

    def get_audio_duration(self, audio_path: str) -> float:
        """Probe audio file duration accurately via ffmpeg."""
        cmd = [self.ffmpeg_exe, "-i", audio_path]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
        for line in res.stderr.splitlines():
            if "Duration" in line:
                try:
                    time_str = line.strip().split(",")[0].split("Duration: ")[1].strip()
                    parts = time_str.split(":")
                    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                except Exception:
                    pass
        return 15.0

    def build_project(self, scenes: List[Dict[str, Any]], audio_path: str, output_project_dir: str) -> str:
        """
        Builds a compliant Concat 0.2.7 document (concat.json) for the project.
        """
        os.makedirs(output_project_dir, exist_ok=True)
        total_dur = self.get_audio_duration(audio_path)
        scene_dur = total_dur / len(scenes)

        media_items = []
        # Register audio
        abs_audio = os.path.abspath(audio_path).replace("\\", "/")
        media_items.append({
            "id": "m1",
            "path": abs_audio,
            "name": os.path.basename(abs_audio),
            "kind": "audio",
            "hasAudio": True,
            "duration": round(total_dur, 3)
        })

        # Register images
        for idx, sc in enumerate(scenes):
            abs_img = os.path.abspath(sc["img"]).replace("\\", "/")
            media_items.append({
                "id": f"m{idx + 2}",
                "path": abs_img,
                "name": os.path.basename(abs_img),
                "kind": "image",
                "hasAudio": False
            })

        tracks = [
            {"id": "T1", "visible": True, "muted": False},
            {"id": "T2", "visible": True, "muted": False},
            {"id": "T3", "visible": True, "muted": False}
        ]

        clips = []
        # Audio clip
        clips.append({
            "id": "c1",
            "trackId": "T2",
            "mediaId": "m1",
            "name": os.path.basename(audio_path),
            "kind": "audio",
            "start": 0.0,
            "duration": round(total_dur, 3),
            "sourceStart": 0.0,
            "volume": 1.0,
            "fadeIn": 0.2,
            "fadeOut": 0.5,
            "scale": 1.0,
            "offsetX": 0.0,
            "offsetY": 0.0,
            "rotation": 0.0,
            "opacity": 1.0,
            "speed": 1.0,
            "preservePitch": True,
            "filters": [],
            "videoEffects": []
        })

        clip_counter = 1
        current_time = 0.0
        for idx, sc in enumerate(scenes):
            # Visual clip on T1
            clip_counter += 1
            clips.append({
                "id": f"c{clip_counter}",
                "trackId": "T1",
                "mediaId": f"m{idx + 2}",
                "name": os.path.basename(sc["img"]),
                "kind": "image",
                "start": round(current_time, 3),
                "duration": round(scene_dur, 3),
                "sourceStart": 0.0,
                "volume": 1.0,
                "fadeIn": 0.0,
                "fadeOut": 0.0,
                "scale": 1.05,
                "offsetX": 0.0,
                "offsetY": 0.0,
                "rotation": 0.0,
                "opacity": 1.0,
                "speed": 1.0,
                "preservePitch": True,
                "filters": [],
                "videoEffects": []
            })

            # Subtitle clip on T3
            clip_counter += 1
            clips.append({
                "id": f"c{clip_counter}",
                "trackId": "T3",
                "mediaId": "",
                "name": sc["sub"][:20] + "...",
                "kind": "text",
                "start": round(current_time, 3),
                "duration": round(scene_dur, 3),
                "sourceStart": 0.0,
                "volume": 1.0,
                "fadeIn": 0.0,
                "fadeOut": 0.0,
                "scale": 1.0,
                "offsetX": 0.0,
                "offsetY": 0.32,
                "rotation": 0.0,
                "opacity": 1.0,
                "speed": 1.0,
                "preservePitch": True,
                "filters": [],
                "videoEffects": [],
                "text": {
                    "content": sc["sub"],
                    "fontFamily": "\"Cabinet Grotesk\"",
                    "fontSize": 0.058,
                    "fontWeight": 800.0,
                    "italic": False,
                    "color": "#FFF500" if idx % 2 == 0 else "#FFFFFF",
                    "align": "center",
                    "opacity": 1.0,
                    "strokeWidth": 0.012,
                    "strokeColor": "#000000",
                    "shadow": True,
                    "background": "#000000B0",
                    "backgroundRadius": 0.02,
                    "backgroundPaddingX": 0.04,
                    "backgroundPaddingY": 0.02,
                    "lineHeight": 1.25,
                    "tracking": 0.0,
                    "maxWidth": 0.85,
                    "maxHeight": 0.0
                }
            })
            current_time += scene_dur

        video_spec = {
            "width": 1080,
            "height": 1920,
            "rateNum": 30,
            "rateDen": 1,
            "rate_num": 30,
            "rate_den": 1
        }
        timeline = {
            "id": "TL1",
            "name": "Affiliate_Video_Project",
            "video": video_spec,
            "tracks": tracks,
            "clips": clips
        }
        doc = {
            "concat": "0.2.7",
            "name": "Affiliate_Video_Project",
            "video": video_spec,
            "tracks": tracks,
            "clips": clips,
            "media": media_items,
            "fonts": [],
            "timelines": [timeline],
            "activeTimelineId": "TL1",
            "active_timeline_id": "TL1"
        }

        json_path = os.path.join(output_project_dir, "concat.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        return json_path

    def render_video(self, scenes: List[Dict[str, Any]], audio_path: str, output_mp4: str, fps: int = 30) -> str:
        """
        Headlessly renders the final TikTok video:
        - 1080x1920 9:16 vertical ratio
        - Smooth dynamic Ken Burns camera motion on product shots
        - High-contrast styled TikTok subtitles
        - Voiceover audio track synced
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_mp4)), exist_ok=True)
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(output_mp4)), "_vmax_temp_render")
        os.makedirs(temp_dir, exist_ok=True)

        total_dur = self.get_audio_duration(audio_path)
        clip_dur = total_dur / len(scenes)
        frames_per_clip = int(clip_dur * fps)

        rendered_clips = []
        for idx, sc in enumerate(scenes):
            out_clip = os.path.join(temp_dir, f"scene_{idx + 1}.mp4")
            
            # Prepare scaled base image (1080x1920)
            im = Image.open(sc["img"]).convert("RGB")
            tw, th = 1080, 1920
            w, h = im.size
            scale = max(tw / w, th / h)
            nw, nh = int(w * scale), int(h * scale)
            im_resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
            left = (nw - tw) // 2
            top = (nh - th) // 2
            base_img = im_resized.crop((left, top, left + tw, top + th))
            temp_img = os.path.join(temp_dir, f"temp_base_{idx + 1}.jpg")
            base_img.save(temp_img, quality=95)

            # Camera motion filter
            if idx == 0:
                z_filter = f"zoompan=z='min(zoom+0.0012,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_per_clip}:s=1080x1920:fps={fps}"
            elif idx == 1:
                z_filter = f"zoompan=z='1.12':x='iw/2-(iw/zoom/2)':y='min(y+1.2,ih/2)':d={frames_per_clip}:s=1080x1920:fps={fps}"
            elif idx == 2:
                z_filter = f"zoompan=z='if(lte(zoom,1.0),1.12,max(1.001,zoom-0.0012))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_per_clip}:s=1080x1920:fps={fps}"
            else:
                z_filter = f"zoompan=z='min(zoom+0.0010,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_per_clip}:s=1080x1920:fps={fps}"

            cmd = [
                self.ffmpeg_exe, "-y",
                "-loop", "1",
                "-i", temp_img,
                "-vf", z_filter,
                "-t", f"{clip_dur:.3f}",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", str(fps),
                out_clip
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            rendered_clips.append(out_clip)

        # Concatenate scenes
        concat_txt = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for c in rendered_clips:
                f.write(f"file '{c.replace(os.sep, '/')}'\n")

        raw_video = os.path.join(temp_dir, "raw_assembled.mp4")
        subprocess.run([
            self.ffmpeg_exe, "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_txt,
            "-c", "copy",
            raw_video
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Generate styled subtitles (SRT)
        srt_file = os.path.join(temp_dir, "subtitles.srt")
        with open(srt_file, "w", encoding="utf-8") as f:
            for i, sc in enumerate(scenes):
                st = i * clip_dur
                et = (i + 1) * clip_dur
                
                # Format SRT timestamp 00:00:00,000
                st_str = f"{int(st//3600):02d}:{int((st%3600)//60):02d}:{int(st%60):02d},{int((st%1)*1000):03d}"
                et_str = f"{int(et//3600):02d}:{int((et%3600)//60):02d}:{int(et%60):02d},{int((et%1)*1000):03d}"
                
                f.write(f"{i + 1}\n")
                f.write(f"{st_str} --> {et_str}\n")
                f.write(f"{sc['sub']}\n\n")

        # Burn subtitles and mux audio
        escaped_srt = srt_file.replace("\\", "/").replace(":", "\\:")
        sub_style = "FontName=Arial,FontSize=16,PrimaryColour=&H00FFFF00,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=140"
        vf_filter = f"subtitles='{escaped_srt}':force_style='{sub_style}'"

        cmd_final = [
            self.ffmpeg_exe, "-y",
            "-i", raw_video,
            "-i", audio_path,
            "-vf", vf_filter,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "19",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_mp4
        ]
        res = subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            # Fallback mux without burned subtitles filter if font rendering lacks filter
            cmd_fallback = [
                self.ffmpeg_exe, "-y",
                "-i", raw_video,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                output_mp4
            ]
            subprocess.run(cmd_fallback, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        return os.path.abspath(output_mp4)

    def open_in_studio(self, project_dir: str) -> subprocess.Popen:
        """Opens project directly in Concat Studio GUI via Python."""
        if not self.is_concat_available():
            raise FileNotFoundError(f"Concat binary not found at: {self.concat_exe}")
        
        abs_proj = os.path.abspath(project_dir)
        cmd = [self.concat_exe, "--project", abs_proj]
        proc = subprocess.Popen(cmd, cwd=self.bin_dir)
        return proc

    def auto_handle_affiliate_video(self, scenes: List[Dict[str, Any]], audio_path: str, output_dir: str,
                                    video_filename: str = "affiliate_review_tiktok.mp4",
                                    preview: bool = False) -> Dict[str, str]:
        """
        Unified Autonomous Entry Point:
        1. Builds Concat project model (concat.json)
        2. Automatically renders final MP4 TikTok video
        3. Optionally opens in Concat Studio if preview=True
        """
        project_dir = os.path.join(output_dir, "concat_project")
        project_file = self.build_project(scenes, audio_path, project_dir)

        output_mp4 = os.path.join(output_dir, video_filename)
        rendered_mp4 = self.render_video(scenes, audio_path, output_mp4)

        result = {
            "status": "success",
            "project_file": project_file,
            "video_file": rendered_mp4
        }

        if preview and self.is_concat_available():
            self.open_in_studio(project_dir)
            result["studio_preview"] = "opened"

        return result
