from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import imageio_ffmpeg
import soundfile as sf

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
)
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


class HyperFramesAdapter:
    """Tool Adapter HeyGen HyperFrames:
    - Biên tập video chuẩn TikTok 9:16 (1080x1920, 30fps).
    - Khóa Safe Zone TikTok: Header 180-260px, Subtitle 1360-1500px, Bottom cart anchor.
    - Tạo HTML5/CSS/GSAP timeline tất định (deterministic).
    - Hỗ trợ Render kép: HyperFrames CLI (npx hyperframes) và Fallback FFmpeg Compositor.
    - Không hardcode đường dẫn tuyệt đối (Zero Hardcoded Paths).
    """

    def __init__(self, store: ProjectStore):
        self.store = store
        self.repo_root = get_repo_root()
        self.ffmpeg = FFMPEG_EXE

    def get_audio_duration(self, audio_path: str | Path) -> float:
        """Đo thời lượng file audio chính xác."""
        audio_file = Path(audio_path).resolve()
        if not audio_file.exists():
            return 10.0

        try:
            with sf.SoundFile(str(audio_file)) as f:
                return round(len(f) / f.samplerate, 3)
        except Exception:
            pass

        # Fallback ffprobe
        cmd = [
            self.ffmpeg,
            "-i",
            str(audio_file),
            "-f",
            "null",
            "-",
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in res.stderr.splitlines():
                if "Duration:" in line:
                    parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
                    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        except Exception:
            pass

        return 10.0

    def generate_html_composition(
        self,
        scenes: List[Dict[str, Any]],
        voiceover_rel_path: str,
        total_duration: float,
        title_badge: str = "SÓC NHỎ TV • HOẠT HÌNH 3D",
        bgm_rel_path: Optional[str] = None,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
    ) -> str:
        """Sinh mã nguồn HTML5/CSS/GSAP composition tuân thủ quy chuẩn HyperFrames."""
        num_scenes = max(1, len(scenes))
        scene_duration = total_duration / num_scenes

        scene_html_blocks = []
        gsap_tweens = []
        current_time = 0.0

        for idx, sc in enumerate(scenes):
            sc_dur = float(sc.get("durationSec", sc.get("duration", scene_duration)))
            media_src = sc.get("video") or sc.get("img") or sc.get("image") or sc.get("src", "")
            is_video = media_src.lower().endswith((".mp4", ".mov", ".webm"))
            sub_text = sc.get("dialogue") or sc.get("sub", "")
            sc_id = f"scene_{idx + 1}"

            if is_video:
                visual_markup = f"""
        <video id="vid_{sc_id}" class="clip media-clip"
               src="{media_src}"
               playsinline muted
               data-start="{current_time:.3f}"
               data-duration="{sc_dur:.3f}"
               data-track-index="1"></video>"""
            else:
                visual_markup = f"""
        <div id="wrapper_{sc_id}" class="clip media-wrapper"
             data-start="{current_time:.3f}"
             data-duration="{sc_dur:.3f}"
             data-track-index="1">
            <img id="img_{sc_id}" class="kenburns-img" src="{media_src}" alt="Scene {idx + 1}" />
        </div>"""
                # GSAP Ken Burns animation mượt mà
                start_scale = 1.0 if idx % 2 == 0 else 1.12
                end_scale = 1.12 if idx % 2 == 0 else 1.0
                pan_y = 15 if idx % 2 == 0 else -15
                gsap_tweens.append(
                    f'tl.fromTo("#img_{sc_id}", {{ scale: {start_scale}, y: 0 }}, '
                    f'{{ scale: {end_scale}, y: {pan_y}, duration: {sc_dur:.3f}, ease: "none" }}, {current_time:.3f});'
                )

            # Subtitle pill trong Safe Zone TikTok (Y: 1360px - 1500px)
            if sub_text:
                sub_markup = f"""
        <div id="sub_wrap_{sc_id}" class="clip subtitle-wrapper"
             data-start="{current_time:.3f}"
             data-duration="{sc_dur:.3f}"
             data-track-index="3">
            <div id="sub_box_{sc_id}" class="subtitle-pill">
                <span class="sub-text">{sub_text}</span>
            </div>
        </div>"""
                gsap_tweens.append(
                    f'tl.fromTo("#sub_box_{sc_id}", {{ opacity: 0, scale: 0.9, y: 15 }}, '
                    f'{{ opacity: 1, scale: 1, y: 0, duration: 0.25, ease: "power2.out" }}, {current_time:.3f});'
                )
                scene_html_blocks.append(sub_markup)

            scene_html_blocks.append(visual_markup)
            current_time += sc_dur

        # Âm thanh
        audio_markup = f"""
    <!-- Voiceover Mastered Track -->
    <audio id="voiceover-audio"
           src="{voiceover_rel_path}"
           data-start="0"
           data-duration="{total_duration:.3f}"
           data-volume="1.0"
           data-track-index="4"></audio>"""

        if bgm_rel_path:
            audio_markup += f"""
    <!-- BGM Bed Track -->
    <audio id="bgm-audio"
           src="{bgm_rel_path}"
           data-start="0"
           data-duration="{total_duration:.3f}"
           data-volume="0.16"
           data-track-index="5"></audio>"""

        html_content = f"""<!doctype html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={width}, height={height}" />
    <title>Sóc Nhỏ TV - HyperFrames TikTok Episode</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{
        width: {width}px;
        height: {height}px;
        overflow: hidden;
        background: #0d0e12;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      }}
      #root {{
        width: 100%;
        height: 100%;
        position: relative;
        overflow: hidden;
      }}
      .media-wrapper, .media-clip {{
        position: absolute;
        top: 0;
        left: 0;
        width: {width}px;
        height: {height}px;
        object-fit: cover;
      }}
      .kenburns-img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        transform-origin: center center;
      }}
      .vignette-overlay {{
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.65) 100%);
        pointer-events: none;
        z-index: 2;
      }}
      /* TikTok Top Safe Zone Badge */
      .top-badge-wrapper {{
        position: absolute;
        top: 200px;
        left: 0;
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10;
      }}
      .top-badge-pill {{
        background: rgba(18, 18, 22, 0.82);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1.5px solid rgba(255, 180, 0, 0.85);
        border-radius: 9999px;
        padding: 14px 38px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.45);
        display: flex;
        align-items: center;
        gap: 12px;
      }}
      .badge-dot {{
        width: 14px;
        height: 14px;
        background: #ffb400;
        border-radius: 50%;
        box-shadow: 0 0 12px #ffb400;
      }}
      .top-badge-text {{
        color: #ffffff;
        font-size: 32px;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
      }}
      /* TikTok Subtitle Safe Zone */
      .subtitle-wrapper {{
        position: absolute;
        top: 1360px;
        left: 0;
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 0 50px;
        z-index: 10;
      }}
      .subtitle-pill {{
        background: rgba(0, 0, 0, 0.82);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1.5px solid rgba(255, 255, 255, 0.22);
        border-radius: 26px;
        padding: 18px 36px;
        max-width: 980px;
        text-align: center;
        box-shadow: 0 12px 35px rgba(0,0,0,0.6);
      }}
      .sub-text {{
        color: #ffe600;
        font-size: 46px;
        font-weight: 800;
        line-height: 1.35;
        letter-spacing: -0.01em;
        text-shadow: 0 3px 12px rgba(0, 0, 0, 0.95);
      }}
    </style>
  </head>
  <body>
    <div id="root"
         data-composition-id="main"
         data-start="0"
         data-duration="{total_duration:.3f}"
         data-width="{width}"
         data-height="{height}">

      <!-- Header Top Safe Zone -->
      <div id="top-badge" class="top-badge-wrapper clip"
           data-start="0"
           data-duration="{total_duration:.3f}"
           data-track-index="2">
        <div class="top-badge-pill">
          <div class="badge-dot"></div>
          <span class="top-badge-text">{title_badge}</span>
        </div>
      </div>

      <!-- Vignette Overlay -->
      <div class="vignette-overlay clip"
           data-start="0"
           data-duration="{total_duration:.3f}"
           data-track-index="2"></div>

      <!-- Scene Visuals & Subtitles -->
      {"".join(scene_html_blocks)}

      {audio_markup}
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#top-badge", {{ y: -40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.5, ease: "power2.out" }}, 0.1);
      {"".join(gsap_tweens)}
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>"""
        return html_content

    def build_project_bundle(
        self,
        target_dir: Path,
        scenes: List[Dict[str, Any]],
        audio_voiceover_path: str | Path,
        title_badge: str = "SÓC NHỎ TV • HOẠT HÌNH 3D",
        bgm_path: Optional[str | Path] = None,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
    ) -> Path:
        """Đóng gói toàn bộ cấu trúc dự án HyperFrames vào target_dir:
        target_dir/
          ├── index.html
          ├── hyperframes.json
          └── assets/
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = target_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        voice_file = Path(audio_voiceover_path).resolve()
        total_duration = self.get_audio_duration(voice_file)

        # 1. Localize Audio
        voice_dest = assets_dir / "voiceover.mp3"
        if voice_file.exists():
            shutil.copy2(voice_file, voice_dest)
        voice_rel = "assets/voiceover.mp3"

        bgm_rel = None
        if bgm_path:
            bgm_src = Path(bgm_path).resolve()
            if bgm_src.exists():
                bgm_dest = assets_dir / "bgm.mp3"
                shutil.copy2(bgm_src, bgm_dest)
                bgm_rel = "assets/bgm.mp3"

        # 2. Localize Scenes Assets
        localized_scenes = []
        for idx, sc in enumerate(scenes):
            sc_dict = dict(sc)
            for k in ("video", "img", "image", "src"):
                media_path = sc_dict.get(k)
                if not media_path:
                    continue
                src = Path(media_path)
                if src.exists():
                    dest_name = f"scene_{idx + 1:02d}_{src.name}"
                    dest = assets_dir / dest_name
                    if not dest.exists():
                        shutil.copy2(src, dest)
                    sc_dict[k] = f"assets/{dest_name}"
            localized_scenes.append(sc_dict)

        # 3. Tạo index.html
        html = self.generate_html_composition(
            scenes=localized_scenes,
            voiceover_rel_path=voice_rel,
            total_duration=total_duration,
            title_badge=title_badge,
            bgm_rel_path=bgm_rel,
            width=width,
            height=height,
            fps=fps,
        )
        (target_dir / "index.html").write_text(html, encoding="utf-8")

        # 4. Tạo hyperframes.json
        hf_config = {
            "name": target_dir.name,
            "version": "1.0.0",
            "fps": fps,
            "width": width,
            "height": height,
            "duration": total_duration,
        }
        (target_dir / "hyperframes.json").write_text(json.dumps(hf_config, indent=2), encoding="utf-8")

        return target_dir

    def render_fallback_ffmpeg(
        self,
        project_dir: Path,
        output_mp4: Path,
        fps: int = 30,
    ) -> Path:
        """Render tốc độ cao bằng ffmpeg compositor:
        Nối các hình ảnh/clip phân cảnh + audio voiceover + nhạc nền thành MP4 9:16 chuẩn xác.
        """
        output_mp4.parent.mkdir(parents=True, exist_ok=True)
        assets_dir = project_dir / "assets"
        voice_file = assets_dir / "voiceover.mp3"

        # Tìm các video clip hoặc ảnh trong assets/
        media_files = sorted(
            [f for f in assets_dir.iterdir() if f.name.startswith("scene_")],
            key=lambda p: p.name,
        )

        total_dur = self.get_audio_duration(voice_file) if voice_file.exists() else 4.0
        dur_per_scene = total_dur / max(1, len(media_files))

        if not media_files:
            # Tạo dummy test video 9:16 nếu assets rỗng
            cmd = [
                self.ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c=0x111625:s=1080x1920:d={total_dur}",
            ]
            if voice_file.exists():
                cmd.extend(["-i", str(voice_file), "-c:a", "aac", "-b:a", "192k"])
            cmd.extend([
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(fps),
                "-t",
                f"{total_dur:.3f}",
                str(output_mp4),
            ])
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, timeout=25)
            return output_mp4

        # Dựng filter_complex ghép các scenes với tốc độ cao
        inputs = []
        filter_parts = []
        for i, m in enumerate(media_files):
            is_img = m.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
            if is_img:
                inputs.extend(["-loop", "1", "-framerate", str(fps), "-t", f"{dur_per_scene:.3f}"])
            else:
                inputs.extend(["-t", f"{dur_per_scene:.3f}"])
            inputs.extend(["-i", str(m)])
            filter_parts.append(
                f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920,setsar=1[v{i}];"
            )

        concat_in = "".join(f"[v{i}]" for i in range(len(media_files)))
        filter_parts.append(f"{concat_in}concat=n={len(media_files)}:v=1:a=0[vout]")

        cmd = [self.ffmpeg, "-y"]
        cmd.extend(inputs)
        if voice_file.exists():
            cmd.extend(["-i", str(voice_file)])

        cmd.extend([
            "-filter_complex",
            "".join(filter_parts),
            "-map",
            "[vout]",
        ])

        if voice_file.exists():
            voice_idx = len(media_files)
            cmd.extend(["-map", f"{voice_idx}:a", "-c:a", "aac", "-b:a", "192k"])

        cmd.extend([
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-shortest",
            str(output_mp4),
        ])

        try:
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=25)
            if res.returncode != 0:
                raise RuntimeError(res.stderr)
        except Exception:
            # Fallback đơn giản với cảnh đầu tiên nếu concat gặp lỗi codec hoặc timeout
            simple_cmd = [
                self.ffmpeg,
                "-y",
                "-loop",
                "1",
                "-framerate",
                str(fps),
                "-t",
                f"{total_dur:.3f}",
                "-i",
                str(media_files[0]),
            ]
            if voice_file.exists():
                simple_cmd.extend(["-i", str(voice_file), "-c:a", "aac", "-b:a", "192k"])
            simple_cmd.extend([
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-pix_fmt",
                "yuv420p",
                "-vf",
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                "-shortest",
                str(output_mp4),
            ])
            subprocess.run(simple_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, timeout=25)

        return output_mp4

    def render(
        self,
        project_dir: Path,
        output_mp4: Path,
        quality: str = "looks",
        fps: int = 30,
    ) -> Path:
        """Render video: HyperFrames CLI là engine chính (chuẩn project); ffmpeg chỉ là dự phòng khi CLI lỗi.
        Engine thực sự đã dùng nằm ở self.last_engine ("hyperframes" hoặc "ffmpeg_fallback")."""
        output_mp4 = Path(output_mp4).resolve()
        output_mp4.parent.mkdir(parents=True, exist_ok=True)
        self.last_engine = "ffmpeg_fallback"
        self.last_cli_error = ""

        if os.environ.get("HYPERFRAMES_USE_CLI", "1") == "1":
            try:
                cli_cmd = [
                    "npx",
                    "-y",
                    "hyperframes",
                    "render",
                    "--quality",
                    quality,
                    "--fps",
                    str(fps),
                    "--output",
                    str(output_mp4),
                ]
                res = subprocess.run(
                    cli_cmd,
                    cwd=str(project_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=int(os.environ.get("HYPERFRAMES_TIMEOUT_SEC", "900")),
                )
                if res.returncode == 0 and output_mp4.exists() and output_mp4.stat().st_size > 0:
                    self.last_engine = "hyperframes"
                    return output_mp4
                self.last_cli_error = (res.stderr or res.stdout or "")[-500:]
            except Exception as e:
                self.last_cli_error = str(e)[:500]

        # Fallback siêu tốc và ổn định tuyệt đối
        return self.render_fallback_ffmpeg(project_dir, output_mp4, fps=fps)

    async def render_from_artifacts(
        self,
        scenes: List[Dict[str, Any]],
        voice_artifact: Optional[Artifact] = None,
        captions_artifact: Optional[Artifact] = None,
        title_badge: str = "SÓC NHỎ TV • TẬP MỚI",
        node_id: str = "unknown",
        run_id: str = "run_default",
    ) -> Artifact:
        """Đầu vào là Artifacts (từ các node trước trong DAG), trả về Video Artifact MP4."""
        run_session_dir = self.store.runs_dir / run_id
        run_session_dir.mkdir(parents=True, exist_ok=True)
        hf_project_dir = run_session_dir / f"hf_composition_{node_id}"

        voice_path = (
            str(self.store.project_dir / voice_artifact.uri)
            if voice_artifact
            else ""
        )

        # Xây dựng bundle
        self.build_project_bundle(
            target_dir=hf_project_dir,
            scenes=scenes,
            audio_voiceover_path=voice_path,
            title_badge=title_badge,
            width=1080,
            height=1920,
            fps=30,
        )

        output_mp4_temp = run_session_dir / f"{node_id}_rendered.mp4"
        final_mp4 = self.render(
            project_dir=hf_project_dir,
            output_mp4=output_mp4_temp,
            fps=30,
        )

        with open(final_mp4, "rb") as f:
            mp4_bytes = f.read()

        total_dur = self.get_audio_duration(final_mp4)

        provenance = ArtifactProvenance(
            node_id=node_id,
            run_id=run_id,
            provider=getattr(self, "last_engine", "hyperframes"),
            model="hyperframes-v0.9.8" if getattr(self, "last_engine", "") == "hyperframes" else "ffmpeg-compositor",
            params={
                "aspectRatio": "9:16",
                "width": 1080,
                "height": 1920,
                "fps": 30,
                "sceneCount": len(scenes),
            },
            input_hashes=[art.hash for art in (voice_artifact, captions_artifact) if art],
            cost_usd=0.0,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        meta = ArtifactMeta(
            width=1080,
            height=1920,
            duration=total_dur,
            fps=30.0,
            aspect="9:16",
        )

        return self.store.store_bytes(
            data=mp4_bytes,
            ext="mp4",
            kind=ArtifactKind.VIDEO,
            provenance=provenance,
            meta=meta,
        )
