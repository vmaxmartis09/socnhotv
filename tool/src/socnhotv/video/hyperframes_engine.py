from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional, Union

import imageio_ffmpeg
import soundfile as sf

# Audio mastering lazily imported to avoid circular import with adapters package
from socnhotv.video.fallback_ffmpeg import render_fallback_ffmpeg, get_audio_duration
from socnhotv.video.platforms import PlatformPreset, get_platform

logger = logging.getLogger("socnhotv.video.engine")
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


class HyperFramesEngine:
    """HyperFrames deterministic video composition and rendering engine.
    Hỗ trợ preset đa nền tảng, render qua HyperFrames CLI, fallback FFmpeg,
    kiểm tra check bundle, audio mastering -14 LUFS và sinh thumbnail 1.0s.
    """

    def __init__(self, ffmpeg_exe: str = FFMPEG_EXE):
        self.ffmpeg = ffmpeg_exe
        self._audio_mastering = None
        self.last_engine: str = "none"
        self.last_cli_error: str = ""

    @property
    def audio_mastering(self):
        if self._audio_mastering is None:
            from socnhotv.core.adapters.audio_mastering import AudioMastering
            self._audio_mastering = AudioMastering(ffmpeg_exe=self.ffmpeg)
        return self._audio_mastering

    def get_audio_duration(self, audio_path: str | Path) -> float:
        return get_audio_duration(audio_path, self.ffmpeg)

    def generate_composition_html(
        self,
        scenes: List[Dict[str, Any]],
        voiceover_rel_path: str,
        total_duration: float,
        title_badge: str = "SÓC NHỎ TV",
        bgm_rel_path: Optional[str] = None,
        platform: str | PlatformPreset = "tiktok",
    ) -> str:
        """Sinh mã nguồn HTML5/CSS/GSAP composition tuân thủ quy chuẩn HyperFrames
        và Safe Zone của nền tảng tương ứng.
        """
        preset = get_platform(platform) if isinstance(platform, str) else platform
        num_scenes = max(1, len(scenes))
        scene_duration = total_duration / num_scenes

        scene_html_blocks = []
        gsap_tweens = []
        current_time = 0.0

        for idx, sc in enumerate(scenes):
            sc_dur = float(sc.get("durationSec", sc.get("duration", scene_duration)))
            media_src = sc.get("video") or sc.get("img") or sc.get("image") or sc.get("src", "")
            is_video = str(media_src).lower().endswith((".mp4", ".mov", ".webm"))
            sub_text = sc.get("dialogue") or sc.get("sub", "")
            sc_id = f"scene_{idx + 1}"

            if is_video:
                visual_markup = f"""
        <video id="vid_{sc_id}" class="clip media-clip"
               src="{media_src}"
               data-start="{current_time:.3f}"
               data-duration="{sc_dur:.3f}"
               data-track-index="0"
               playsinline muted preload="auto"></video>"""
            else:
                visual_markup = f"""
        <img id="img_{sc_id}" class="clip media-clip"
             src="{media_src}"
             data-start="{current_time:.3f}"
             data-duration="{sc_dur:.3f}"
             data-track-index="0" />"""

            scene_html_blocks.append(f"""
      <!-- {sc_id.upper()} -->
      <div id="{sc_id}" class="scene-container">
        {visual_markup}
        <div id="sub_{sc_id}" class="subtitle-wrapper clip"
             data-start="{current_time:.3f}"
             data-duration="{sc_dur:.3f}"
             data-track-index="1">
          <div class="subtitle-pill">
            <span class="sub-text">{sub_text}</span>
          </div>
        </div>
      </div>""")

            # GSAP animation timeline
            media_elem = f"#vid_{sc_id}" if is_video else f"#img_{sc_id}"
            gsap_tweens.append(f"""
      // Tween {sc_id}
      tl.fromTo("{media_elem}", {{ scale: 1.05, opacity: 0 }}, {{ scale: 1.0, opacity: 1, duration: 0.45, ease: "power2.out" }}, {current_time:.3f});
      tl.to("{media_elem}", {{ scale: 1.03, duration: {sc_dur - 0.45:.3f}, ease: "none" }}, {current_time + 0.45:.3f});
      tl.fromTo("#sub_{sc_id}", {{ y: 25, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.35, ease: "back.out(1.4)" }}, {current_time + 0.1:.3f});
      tl.to("#sub_{sc_id}", {{ opacity: 0, duration: 0.2 }}, {current_time + sc_dur - 0.2:.3f});""")

            current_time += sc_dur

        audio_markup = f"""
      <audio id="audio-voiceover" class="clip"
             src="{voiceover_rel_path}"
             data-start="0"
             data-duration="{total_duration:.3f}"
             data-track-index="3"></audio>"""

        if bgm_rel_path:
            audio_markup += f"""
      <audio id="audio-bgm" class="clip"
             src="{bgm_rel_path}"
             data-start="0"
             data-duration="{total_duration:.3f}"
             data-track-index="4"
             data-volume="0.18"></audio>"""

        # Tính toán tọa độ CSS Safe Zone theo preset
        top_offset = preset.safe_zone.top
        bottom_offset = preset.safe_zone.bottom
        left_offset = preset.safe_zone.left
        right_offset = preset.safe_zone.right

        # Vị trí subtitle: cách đáy một khoảng bottom_offset + 30px
        subtitle_top = max(100, preset.height - bottom_offset - 180)
        if preset.width == 1080 and preset.height == 1920:
            top_offset = 200
            subtitle_top = 1360

        html_content = f"""<!DOCTYPE html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={preset.width}, height={preset.height}, initial-scale=1.0" />
    <title>{title_badge}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
    <style>
      * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        user-select: none;
      }}
      body, html {{
        width: {preset.width}px;
        height: {preset.height}px;
        overflow: hidden;
        background: #000000;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      }}
      #root {{
        position: relative;
        width: {preset.width}px;
        height: {preset.height}px;
        overflow: hidden;
      }}
      .scene-container {{
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
      }}
      .media-clip {{
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center;
      }}
      .vignette-overlay {{
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at center, transparent 40%, rgba(0, 0, 0, 0.45) 100%),
                    linear-gradient(180deg, rgba(0,0,0,0.65) 0%, transparent 22%, transparent 75%, rgba(0,0,0,0.85) 100%);
        pointer-events: none;
        z-index: 5;
      }}
      /* Header Safe Zone */
      .top-badge-wrapper {{
        position: absolute;
        top: {top_offset}px;
        left: {left_offset}px;
        z-index: 10;
        display: flex;
        align-items: center;
      }}
      .top-badge-pill {{
        display: inline-flex;
        align-items: center;
        gap: 12px;
        background: rgba(15, 23, 42, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1.5px solid rgba(255, 255, 255, 0.2);
        padding: 10px 24px;
        border-radius: 9999px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
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
        font-size: 28px;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
      }}
      /* Subtitle Safe Zone */
      .subtitle-wrapper {{
        position: absolute;
        top: {subtitle_top}px;
        left: 0;
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 0 {max(30, left_offset)}px {max(30, right_offset)}px;
        z-index: 10;
      }}
      .subtitle-pill {{
        background: rgba(0, 0, 0, 0.82);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1.5px solid rgba(255, 255, 255, 0.22);
        border-radius: 26px;
        padding: 18px 36px;
        max-width: {preset.width - left_offset - right_offset}px;
        text-align: center;
        box-shadow: 0 12px 35px rgba(0,0,0,0.6);
      }}
      .sub-text {{
        color: #ffe600;
        font-size: 44px;
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
         data-width="{preset.width}"
         data-height="{preset.height}">

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

    def build(
        self,
        composition_html: str,
        assets: Dict[str, Union[str, Path]],
        platform: str | PlatformPreset = "tiktok",
        target_dir: Optional[Path] = None,
        duration: Optional[float] = None,
    ) -> Path:
        """Đóng gói bundle HyperFrames hợp lệ theo hyperframes-core:
        index.html, hyperframes.json, thư mục assets/ chứa các file media.
        """
        preset = get_platform(platform) if isinstance(platform, str) else platform
        if target_dir is None:
            tmp = tempfile.mkdtemp(prefix="hf_bundle_")
            target_dir = Path(tmp)
        else:
            target_dir = Path(target_dir).resolve()

        target_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = target_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Sao chép các assets vào bundle
        for rel_name, src_path in assets.items():
            src = Path(src_path).resolve()
            if src.exists():
                dest = assets_dir / Path(rel_name).name
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists():
                    shutil.copy2(src, dest)

        # Đảm bảo có voiceover.mp3 trong assets nếu index.html nhắc đến
        voice_dest = assets_dir / "voiceover.mp3"
        if "assets/voiceover.mp3" in composition_html and not voice_dest.exists():
            from socnhotv.core.providers.mock_provider import create_minimal_wav_bytes
            voice_dest.write_bytes(create_minimal_wav_bytes(duration_sec=duration or 5.0))

        # Ghi index.html
        (target_dir / "index.html").write_text(composition_html, encoding="utf-8")

        # Ghi hyperframes.json
        hf_config = {
            "name": target_dir.name,
            "version": "1.0.0",
            "fps": preset.fps,
            "width": preset.width,
            "height": preset.height,
            "duration": duration or 10.0,
        }
        (target_dir / "hyperframes.json").write_text(json.dumps(hf_config, indent=2), encoding="utf-8")

        return target_dir

    def build_from_scenes(
        self,
        scenes: List[Dict[str, Any]],
        audio_voiceover_path: str | Path,
        platform: str | PlatformPreset = "tiktok",
        target_dir: Optional[Path] = None,
        title_badge: str = "SÓC NHỎ TV",
        bgm_path: Optional[str | Path] = None,
    ) -> Path:
        """Helper xây dựng bundle hoàn chỉnh từ danh sách scenes và audio."""
        preset = get_platform(platform) if isinstance(platform, str) else platform
        if target_dir is None:
            target_dir = Path(tempfile.mkdtemp(prefix="hf_bundle_"))
        else:
            target_dir = Path(target_dir).resolve()

        target_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = target_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        voice_file = Path(audio_voiceover_path).resolve()
        total_duration = self.get_audio_duration(voice_file)

        # Localize Audio
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

        # Localize Scenes Assets
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

        html = self.generate_composition_html(
            scenes=localized_scenes,
            voiceover_rel_path=voice_rel,
            total_duration=total_duration,
            title_badge=title_badge,
            bgm_rel_path=bgm_rel,
            platform=preset,
        )

        assets_map: Dict[str, Union[str, Path]] = {}
        for f in assets_dir.iterdir():
            if f.is_file():
                assets_map[f.name] = f

        return self.build(
            composition_html=html,
            assets=assets_map,
            platform=preset,
            target_dir=target_dir,
            duration=total_duration,
        )

    def check(self, bundle_dir: Path) -> Dict[str, Any]:
        """Chạy `npx hyperframes check` trước khi render; fail -> trả lỗi chi tiết."""
        bundle_dir = Path(bundle_dir).resolve()
        cmd = ["npx", "hyperframes", "check", "--json"]

        try:
            res = subprocess.run(
                cmd,
                cwd=str(bundle_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
            )
            # Thử parse JSON
            stdout = res.stdout.strip()
            # Bỏ các dòng log đầu như [hyperframes]...
            json_start = stdout.find("{")
            if json_start != -1:
                try:
                    data = json.loads(stdout[json_start:])
                    return {"ok": res.returncode == 0, "details": data}
                except Exception:
                    pass

            if res.returncode != 0:
                return {
                    "ok": False,
                    "error": res.stderr or res.stdout,
                    "returncode": res.returncode,
                }
            return {"ok": True, "output": res.stdout}
        except FileNotFoundError:
            return {"ok": False, "error": "HyperFrames CLI không tồn tại."}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "HyperFrames check timeout (60s)."}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def extract_thumbnail(
        self,
        video_path: Path,
        thumb_path: Optional[Path] = None,
        timestamp: float = 1.0,
    ) -> Path:
        """Trích frame ở timestamp (mặc định 1.0s) -> file JPEG thumbnail."""
        video_path = Path(video_path).resolve()
        if thumb_path is None:
            thumb_path = video_path.with_suffix(".jpg")
        else:
            thumb_path = Path(thumb_path).resolve()

        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            self.ffmpeg,
            "-y",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(video_path),
            "-vframes",
            "1",
            "-q:v",
            "2",
            str(thumb_path),
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, timeout=15)
        except Exception as e:
            logger.warning(f"Lỗi trích xuất thumbnail ({e}), thử fallback ss 0.0s")
            cmd[3] = "0.000"
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, timeout=15)

        return thumb_path

    def post_process_audio(
        self,
        video_path: Path,
        target_lufs: float = -14.0,
    ) -> Path:
        """Mastering audio trong file video đạt chuẩn target_lufs (-14 LUFS)."""
        video_path = Path(video_path).resolve()
        with tempfile.TemporaryDirectory() as tmp_dir:
            extracted_wav = Path(tmp_dir) / "extracted.wav"
            mastered_wav = Path(tmp_dir) / "mastered.wav"
            temp_output_mp4 = Path(tmp_dir) / "remuxed.mp4"

            # 1. Trích xuất audio
            extract_cmd = [
                self.ffmpeg,
                "-y",
                "-i",
                str(video_path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "44100",
                str(extracted_wav),
            ]
            res = subprocess.run(extract_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0 or not extracted_wav.exists() or extracted_wav.stat().st_size == 0:
                # Video không có âm thanh hoặc trích xuất lỗi -> giữ nguyên video
                return video_path

            # 2. Xử lý mastering chuẩn -14 LUFS
            try:
                self.audio_mastering.master_tiktok(
                    input_audio_path=str(extracted_wav),
                    output_audio_path=str(mastered_wav),
                    target_lufs=target_lufs,
                )
            except Exception as e:
                logger.warning(f"Audio mastering thất bại, giữ âm thanh gốc: {e}")
                return video_path

            # 3. Remux lại vào video
            remux_cmd = [
                self.ffmpeg,
                "-y",
                "-i",
                str(video_path),
                "-i",
                str(mastered_wav),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                str(temp_output_mp4),
            ]
            remux_res = subprocess.run(remux_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            if remux_res.returncode == 0 and temp_output_mp4.exists() and temp_output_mp4.stat().st_size > 0:
                shutil.copy2(temp_output_mp4, video_path)

        return video_path

    def render(
        self,
        bundle_dir: Path,
        out_path: Path,
        platform: str | PlatformPreset = "tiktok",
        quality: str = "looks",
        log_file: Optional[Path] = None,
        timeout_sec: int = 900,
    ) -> Path:
        """Render video chính thức qua HyperFrames CLI; nếu không có hoặc lỗi, fallback qua FFmpeg."""
        preset = get_platform(platform) if isinstance(platform, str) else platform
        bundle_dir = Path(bundle_dir).resolve()
        out_path = Path(out_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if log_file:
            log_file = Path(log_file).resolve()
            log_file.parent.mkdir(parents=True, exist_ok=True)

        self.last_engine = "ffmpeg_fallback"
        self.last_cli_error = ""

        # 1. Thử render bằng HyperFrames CLI nếu được kích hoạt
        use_cli = os.environ.get("HYPERFRAMES_USE_CLI", "1") == "1"

        if use_cli:
            try:
                # Kiểm tra npx hyperframes
                cli_cmd = [
                    "npx",
                    "-y",
                    "hyperframes",
                    "render",
                    "--quality",
                    quality,
                    "--fps",
                    str(preset.fps),
                    "--output",
                    str(out_path),
                ]
                logger.info(f"Khởi chạy render HyperFrames CLI: {' '.join(cli_cmd)}")
                proc = subprocess.run(
                    cli_cmd,
                    cwd=str(bundle_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout_sec,
                )

                if log_file:
                    with open(log_file, "a", encoding="utf-8") as lf:
                        lf.write(f"--- HyperFrames CLI Render (code: {proc.returncode}) ---\n")
                        lf.write(f"STDOUT:\n{proc.stdout}\n")
                        lf.write(f"STDERR:\n{proc.stderr}\n")

                if proc.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0:
                    self.last_engine = "hyperframes"
                    # Audio mastering + thumbnail
                    self.post_process_audio(out_path, target_lufs=preset.loudness_lufs)
                    self.extract_thumbnail(out_path)
                    return out_path

                self.last_cli_error = (proc.stderr or proc.stdout or "")[-500:]
                logger.warning(f"HyperFrames CLI render thất bại: {self.last_cli_error}")
            except Exception as e:
                self.last_cli_error = str(e)
                logger.warning(f"Không thể thực thi HyperFrames CLI: {e}")
                if log_file:
                    with open(log_file, "a", encoding="utf-8") as lf:
                        lf.write(f"HyperFrames CLI Exception: {e}\n")

        # 2. Fallback FFmpeg khi CLI thất bại hoặc tắt
        logger.warning(f"Chuyển sang Fallback FFmpeg Compositor cho preset {preset.id}")
        render_fallback_ffmpeg(
            project_dir=bundle_dir,
            output_mp4=out_path,
            platform=preset,
            fps=preset.fps,
            ffmpeg_exe=self.ffmpeg,
        )

        if log_file:
            with open(log_file, "a", encoding="utf-8") as lf:
                lf.write(f"FALLBACK_USED: rendered via FFmpeg fallback to {out_path}\n")

        # 3. Mastering audio & Thumbnail
        self.post_process_audio(out_path, target_lufs=preset.loudness_lufs)
        self.extract_thumbnail(out_path)

        return out_path
