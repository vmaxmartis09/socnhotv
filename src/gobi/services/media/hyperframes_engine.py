"""
=============================================================================
🎬 GOBI HYPERFRAMES VIDEO ENGINE (TẦNG 2: SERVICES - PRIMARY VIDEO ENGINE)
Động cơ dựng và biên tập video CHÍNH THỨC của hệ sinh thái Gobi Social.
Sử dụng HeyGen HyperFrames (HTML5, CSS3, GSAP, SVG) làm công cụ render cốt lõi:
- Chuẩn tỉ lệ 9:16 dọc (1080x1920) tối ưu cho TikTok / Reels / Shorts.
- Khớp Safe Zone chuẩn xác: Top Header Pill, Bottom CTA Giỏ hàng & Controls.
- Phụ đề tương tác (Karaoke / Kinetic Pill) chống flop và giữ chân người xem.
- Hiệu ứng camera Ken Burns mượt mà hoặc chèn Video Clip thực tế (Flow/Veo/Kling).
- Đa luồng âm thanh: Voiceover (LyLy / OmniVoice) + BGM lồng thông minh.
- Xuất bản video MP4 tất định (deterministic) với chất lượng chuẩn studio.
=============================================================================
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any

from gobi.adapters.integrations.hyperframes_adapter import HyperFramesAdapter

PROJECT_ROOT = Path("/Volumes/Data/gobi-social")


class HyperFramesEngine:
    """
    Primary Video Editing and Rendering Engine for Gobi Social using HyperFrames.
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or PROJECT_ROOT
        self.adapter = HyperFramesAdapter(self.workspace_root)
        self.default_output_dir = self.workspace_root / "output" / "videos"
        self.default_output_dir.mkdir(parents=True, exist_ok=True)

    def get_audio_duration(self, audio_path: str | Path) -> float:
        """Đo thời lượng file audio chính xác bằng ffprobe."""
        audio_file = Path(audio_path).resolve()
        if not audio_file.exists():
            return 15.0

        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_file)
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(res.stdout.strip())
        except Exception:
            return 15.0

    def generate_html_composition(
        self,
        scenes: List[Dict[str, Any]],
        audio_voiceover_path: str | Path,
        title_badge: str = "GÔ BI FASHION REVIEW",
        bgm_path: Optional[str | Path] = None,
        total_duration: Optional[float] = None,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
        voiceover_src: Optional[str] = None,
        bgm_src: Optional[str] = None
    ) -> str:
        """
        Sinh mã nguồn HTML5 hoàn chỉnh tuân thủ tiêu chuẩn HyperFrames Composition.

        `voiceover_src`/`bgm_src` là đường dẫn TƯƠNG ĐỐI ("assets/...") đã được
        localize để nhúng vào thẻ <audio src="...">. `audio_voiceover_path`/`bgm_path`
        vẫn dùng để đo thời lượng file (ffprobe cần đường dẫn thật trên đĩa).
        """
        voice_path = Path(audio_voiceover_path).resolve()
        dur = total_duration or self.get_audio_duration(voice_path)
        voiceover_src = voiceover_src or str(voice_path)
        num_scenes = max(1, len(scenes))
        scene_duration = dur / num_scenes

        # Chuẩn bị HTML các phân cảnh (Visuals & Ken Burns / Videos)
        scene_html_blocks = []
        gsap_tweens = []

        current_time = 0.0
        for idx, sc in enumerate(scenes):
            sc_dur = sc.get("duration", scene_duration)
            media_src = sc.get("img") or sc.get("video") or sc.get("src")
            # [GOBI FIX] Không resolve thành path tuyệt đối — HyperFrames yêu cầu đường dẫn
            # TƯƠNG ĐỐI từ index.html ("assets/..."), path tuyệt đối khiến ảnh/video không load được.
            is_video = media_src and Path(media_src).suffix.lower() in [".mp4", ".mov", ".webm"]
            sub_text = sc.get("sub", "")
            sc_id = f"scene-{idx + 1}"

            # Visual layer
            if is_video:
                # Video Clip (Flow AI / Kling / Source clip)
                visual_markup = f"""
        <video id="vid-{sc_id}" class="clip media-clip"
               src="{media_src}"
               playsinline muted
               data-start="{current_time:.3f}"
               data-duration="{sc_dur:.3f}"
               data-track-index="1"></video>"""
            else:
                # Ken Burns Image
                img_path_str = media_src or ""
                visual_markup = f"""
        <div id="wrapper-{sc_id}" class="clip media-wrapper"
             data-start="{current_time:.3f}"
             data-duration="{sc_dur:.3f}"
             data-track-index="1">
            <img id="img-{sc_id}" class="kenburns-img" src="{img_path_str}" alt="Scene {idx + 1}" />
        </div>"""
                # GSAP Ken Burns animation
                zoom_dir = 1.12 if idx % 2 == 0 else 1.0
                start_scale = 1.0 if idx % 2 == 0 else 1.12
                end_scale = zoom_dir
                pan_y = 15 if idx % 2 == 0 else -15
                gsap_tweens.append(
                    f'tl.fromTo("#img-{sc_id}", {{ scale: {start_scale}, y: 0 }}, {{ scale: {end_scale}, y: {pan_y}, duration: {sc_dur:.3f}, ease: "none" }}, {current_time:.3f});'
                )

            # Subtitle pill layer (TikTok Styled Safe Zone: Y = ~1380px)
            sub_markup = f"""
        <div id="sub-wrap-{sc_id}" class="clip subtitle-wrapper"
             data-start="{current_time:.3f}"
             data-duration="{sc_dur:.3f}"
             data-track-index="3">
            <div id="sub-box-{sc_id}" class="subtitle-pill">
                <span class="sub-text">{sub_text}</span>
            </div>
        </div>"""
            gsap_tweens.append(
                f'tl.fromTo("#sub-box-{sc_id}", {{ opacity: 0, scale: 0.9, y: 15 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.25, ease: "power2.out" }}, {current_time:.3f});'
            )

            scene_html_blocks.append(visual_markup)
            scene_html_blocks.append(sub_markup)
            current_time += sc_dur

        # Âm thanh (Audio Layer)
        audio_markup = f"""
    <!-- Voiceover Audio Track -->
    <audio id="voiceover-audio"
           src="{voiceover_src}"
           data-start="0"
           data-duration="{dur:.3f}"
           data-volume="1.0"
           data-track-index="4"></audio>"""

        if bgm_path and Path(bgm_path).exists():
            bgm_src = bgm_src or str(Path(bgm_path).resolve())
            audio_markup += f"""
    <!-- BGM Bed with Smart Ducking -->
    <audio id="bgm-audio"
           src="{bgm_src}"
           data-start="0"
           data-duration="{dur:.3f}"
           data-volume="0.16"
           data-track-index="5"></audio>"""

        # Tổng hợp toàn bộ HTML document
        html_content = f"""<!doctype html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={width}, height={height}" />
    <title>Gobi Social - HyperFrames TikTok Review</title>
    <!-- GSAP for seekable deterministic animations -->
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }}
      html, body {{
        margin: 0;
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
        display: flex;
        flex-direction: column;
      }}
      
      /* Visual Media Layer */
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

      /* Dark Vignette Overlay for Contrast */
      .vignette-overlay {{
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at center, rgba(0,0,0,0) 40%, rgba(0,0,0,0.65) 100%);
        pointer-events: none;
        z-index: 2;
      }}

      /* Top Safe Zone Badge (Y: 200px - 280px) */
      .top-badge-wrapper {{
        position: absolute;
        top: 210px;
        left: 0;
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10;
      }}
      .top-badge-pill {{
        background: rgba(18, 18, 22, 0.78);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1.5px solid rgba(255, 230, 0, 0.65);
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
        background: #ffe600;
        border-radius: 50%;
        box-shadow: 0 0 12px #ffe600;
      }}
      .top-badge-text {{
        color: #ffffff;
        font-size: 32px;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
      }}

      /* Subtitle Safe Zone (Y: 1360px - 1500px, tránh che giỏ hàng TikTok) */
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
        background: rgba(0, 0, 0, 0.78);
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
        color: #fffb00;
        font-size: 46px;
        font-weight: 800;
        line-height: 1.35;
        letter-spacing: -0.01em;
        text-shadow: 0 3px 12px rgba(0, 0, 0, 0.95);
      }}

      /* Bottom Safe Zone Indicator / TikTok Cart Anchor Hint */
      .bottom-cart-hint {{
        position: absolute;
        bottom: 220px;
        left: 60px;
        background: rgba(254, 44, 85, 0.9);
        border-radius: 12px;
        padding: 10px 22px;
        color: #ffffff;
        font-size: 26px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 8px;
        z-index: 10;
        box-shadow: 0 6px 20px rgba(254, 44, 85, 0.45);
      }}
    </style>
  </head>
  <body>
    <div id="root"
         data-composition-id="main"
         data-start="0"
         data-duration="{dur:.3f}"
         data-width="{width}"
         data-height="{height}">

      <!-- Static Top Safe Zone Badge -->
      <div id="top-badge" class="top-badge-wrapper clip"
           data-start="0"
           data-duration="{dur:.3f}"
           data-track-index="2">
        <div class="top-badge-pill">
          <div class="badge-dot"></div>
          <span class="top-badge-text">{title_badge}</span>
        </div>
      </div>

      <!-- Vignette Overlay -->
      <div class="vignette-overlay clip"
           data-start="0"
           data-duration="{dur:.3f}"
           data-track-index="2"></div>

      <!-- Bottom Cart Callout Hint -->
      <div id="bottom-cart" class="bottom-cart-hint clip"
           data-start="0"
           data-duration="{dur:.3f}"
           data-track-index="2">
        <span>🛒 Nhấn góc trái để xem ưu đãi</span>
      </div>

      <!-- Dynamic Scene Clips -->
      {"".join(scene_html_blocks)}

      {audio_markup}
    </div>

    <script>
      // Khởi tạo Timeline GSAP tất định cho HyperFrames
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});

      // Top badge & Cart entrance
      tl.fromTo("#top-badge", {{ y: -40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.5, ease: "power2.out" }}, 0.1);
      tl.fromTo("#bottom-cart", {{ x: -30, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.5, ease: "power2.out" }}, 0.3);

      // Kịch bản chuyển động phân cảnh
      {"".join(gsap_tweens)}

      // Gắn timeline vào runtime HyperFrames
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>"""
        return html_content

    def _localize_scene_assets(self, scenes: List[Dict[str, Any]], proj_path: Path) -> List[Dict[str, Any]]:
        """
        Copy ảnh/video của từng scene vào <proj_path>/assets/ và trả về scene dict mới
        với đường dẫn tương đối ("assets/..."), đúng quy ước HyperFrames yêu cầu.
        """
        assets_dir = proj_path / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        localized = []

        for idx, sc in enumerate(scenes):
            sc = dict(sc)
            for key in ("img", "video", "src"):
                media_path = sc.get(key)
                if not media_path:
                    continue
                src = Path(media_path)
                if not src.exists():
                    continue
                dest_name = f"scene{idx + 1:02d}_{src.name}"
                dest = assets_dir / dest_name
                if not dest.exists():
                    shutil.copy2(src, dest)
                sc[key] = f"assets/{dest_name}"
            localized.append(sc)

        return localized

    def _localize_audio_asset(self, audio_path: Optional[str | Path], proj_path: Path, dest_name: str) -> Optional[str]:
        """
        Copy một file audio (voiceover/BGM) vào <proj_path>/assets/ và trả về
        đường dẫn tương đối ("assets/...") để nhúng trong <audio src="...">.
        """
        if not audio_path:
            return None
        src = Path(audio_path)
        if not src.exists():
            return None
        assets_dir = proj_path / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        dest = assets_dir / dest_name
        if not dest.exists():
            shutil.copy2(src, dest)
        return f"assets/{dest_name}"

    def create_project(
        self,
        project_dir: str | Path,
        scenes: List[Dict[str, Any]],
        audio_voiceover_path: str | Path,
        title_badge: str = "GÔ BI FASHION REVIEW",
        bgm_path: Optional[str | Path] = None,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30
    ) -> Path:
        """
        Tạo thư mục project hoàn chỉnh cho HyperFrames với index.html và cấu hình.
        """
        proj_path = Path(project_dir).resolve()
        proj_path.mkdir(parents=True, exist_ok=True)

        # [GOBI FIX] HyperFrames yêu cầu asset dùng đường dẫn TƯƠNG ĐỐI từ index.html
        # (quy ước "assets/..." — xem .agent/skills/remotion-to-hyperframes/references/media.md).
        # Dùng path tuyệt đối ngoài project_dir khiến ảnh không load được khi render (màn hình đen).
        scenes = self._localize_scene_assets(scenes, proj_path)

        # [GOBI FIX] Voiceover/BGM cũng phải dùng đường dẫn tương đối "assets/..."
        # trong index.html, cùng lý do với ảnh/video phân cảnh ở trên.
        voiceover_src = self._localize_audio_asset(audio_voiceover_path, proj_path, "voiceover_full.mp3")
        bgm_src = self._localize_audio_asset(bgm_path, proj_path, f"bgm_{Path(bgm_path).name}") if bgm_path else None

        html_content = self.generate_html_composition(
            scenes=scenes,
            audio_voiceover_path=audio_voiceover_path,
            title_badge=title_badge,
            bgm_path=bgm_path,
            width=width,
            height=height,
            fps=fps,
            voiceover_src=voiceover_src,
            bgm_src=bgm_src
        )

        index_file = proj_path / "index.html"
        index_file.write_text(html_content, encoding="utf-8")

        # hyperframes.json cấu hình căn bản
        hf_config = {
            "name": proj_path.name,
            "version": "1.0.0",
            "fps": fps,
            "width": width,
            "height": height
        }
        (proj_path / "hyperframes.json").write_text(json.dumps(hf_config, indent=2), encoding="utf-8")

        return proj_path

    def render_project(
        self,
        project_dir: str | Path,
        output_file: Optional[str | Path] = None,
        quality: str = "looks",
        fps: int = 30
    ) -> Path:
        """
        Render project HyperFrames thành video MP4 hoàn thiện.
        """
        proj_path = Path(project_dir).resolve()
        out_file = Path(output_file) if output_file else self.default_output_dir / f"{proj_path.name}.mp4"
        return self.adapter.render(proj_path, out_file, quality=quality, fps=fps)

    def create_and_render_video(
        self,
        scenes: List[Dict[str, Any]],
        audio_voiceover_path: str | Path,
        output_mp4: Optional[str | Path] = None,
        title_badge: str = "GÔ BI FASHION REVIEW",
        bgm_path: Optional[str | Path] = None,
        temp_project_name: str = "gobi_hyperframes_job",
        quality: str = "looks",
        fps: int = 30
    ) -> Path:
        """
        Hàm bao toàn diện (All-in-one Entry Point):
        1. Tạo project HyperFrames tự động từ dữ liệu cảnh quay.
        2. Render ra file MP4 chất lượng cao.
        """
        temp_proj_dir = self.workspace_root / "output" / "hyperframes_projects" / temp_project_name
        self.create_project(
            project_dir=temp_proj_dir,
            scenes=scenes,
            audio_voiceover_path=audio_voiceover_path,
            title_badge=title_badge,
            bgm_path=bgm_path,
            width=1080,
            height=1920,
            fps=fps
        )

        out_path = Path(output_mp4) if output_mp4 else self.default_output_dir / f"{temp_project_name}.mp4"
        return self.render_project(temp_proj_dir, out_path, quality=quality, fps=fps)

    def preview(self, project_dir: str | Path) -> subprocess.Popen:
        """Mở Studio xem trước composition trên trình duyệt."""
        return self.adapter.preview(project_dir, background=True)
