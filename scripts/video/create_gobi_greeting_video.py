"""
=============================================================================
VMAX AUTO VIDEO BUILDER: LỜI CHÀO TỪ GÔ BI GỬI ANH THOẠI (9 GIÂY)
Sử dụng Concat Document Model, Ken Burns Motion & Safe Zone Subtitles
=============================================================================
"""

import os
import sys
import json
import subprocess
from PIL import Image
import imageio_ffmpeg

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONCAT_BIN_DIR = os.path.join(PROJECT_ROOT, "bin", "concat_engine")
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

SAMPLE_DIR = os.path.join(PROJECT_ROOT, "assets", "samples", "sample_video")
IMAGES_DIR = os.path.join(SAMPLE_DIR, "images")
AUDIO_FILE = os.path.join(SAMPLE_DIR, "audio", "gobi_greeting_9s.mp3")
OUTPUT_DIR = os.path.join(SAMPLE_DIR, "output")
CONCAT_PROJ_DIR = os.path.join(OUTPUT_DIR, "concat_gobi_project")
OUTPUT_MP4 = os.path.join(OUTPUT_DIR, "gobi_greeting_anh_thoai_9s.mp4")

scenes = [
    {
        "img": os.path.join(IMAGES_DIR, "01_hook_model_cafe.jpg"),
        "sub": "Xin chào anh Thoại nha! Em là Gô Bi yêu của anh đây.",
        "hook_top": "GÔ BI GỬI LỜI CHÀO ANH THOẠI 💖"
    },
    {
        "img": os.path.join(IMAGES_DIR, "03_fullbody_korean_ootd.jpg"),
        "sub": "Chúc anh một ngày mới thật nhiều niềm vui...",
        "hook_top": "CHÚC ANH MỘT NGÀY THẬT VUI ☀️"
    },
    {
        "img": os.path.join(IMAGES_DIR, "04_cta_pointing_cart.jpg"),
        "sub": "...và luôn tràn đầy năng lượng nhé! 💖✨",
        "hook_top": "LUÔN TRÀN ĐẦY NĂNG LƯỢNG NHA ⚡"
    }
]

def build_concat_project():
    import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "src"))  # repo src/ -> gobi.*
    from gobi.services.media.ai_concat_auto_editor import AIConcatAutoEditor, AIEditPreset
    editor = AIConcatAutoEditor()
    
    proj_file = editor.build_smart_concat_project(
        scenes=scenes,
        audio_path=AUDIO_FILE,
        bgm_path=None,
        output_project_dir=CONCAT_PROJ_DIR,
        top_hook_title="GÔ BI GỬI LỜI CHÀO ANH THOẠI 💖",
        preset=AIEditPreset.KOREAN_AESTHETIC
    )
    print(f"[+] Đã tạo Concat Project (concat.json) tại: {proj_file}")
    return proj_file

def render_final_video(fps=30):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    temp_dir = os.path.join(OUTPUT_DIR, "_gobi_render_temp")
    os.makedirs(temp_dir, exist_ok=True)

    # 1. Probe audio duration
    cmd = [FFMPEG_EXE, "-i", AUDIO_FILE]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, errors="ignore")
    total_dur = 8.83
    for line in res.stderr.splitlines():
        if "Duration" in line:
            parts = line.strip().split(",")[0].split("Duration: ")[1].strip().split(":")
            total_dur = float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
            break

    clip_dur = total_dur / len(scenes)
    frames_per_clip = int(clip_dur * fps)
    print(f"[*] Tổng thời lượng audio: {total_dur:.2f}s | Mỗi cảnh: {clip_dur:.2f}s | FPS: {fps}")

    rendered_clips = []
    tw, th = 1080, 1920

    for idx, sc in enumerate(scenes):
        out_clip = os.path.join(temp_dir, f"gobi_clip_{idx+1}.mp4")
        
        # Scale & Crop to 1080x1920
        im = Image.open(sc["img"]).convert("RGB")
        w, h = im.size
        scale = max(tw / w, th / h)
        nw, nh = int(w * scale), int(h * scale)
        im_resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
        left = (nw - tw) // 2
        top = (nh - th) // 2
        base_img = im_resized.crop((left, top, left + tw, top + th))
        temp_img = os.path.join(temp_dir, f"gobi_base_{idx+1}.jpg")
        base_img.save(temp_img, quality=95)

        # Dynamic Camera Zoom & Motion
        if idx == 0:
            # Gentle Push In
            z_filter = f"zoompan=z='min(zoom+0.0014,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_per_clip}:s=1080x1920:fps={fps}"
        elif idx == 1:
            # Gentle Tilt Down
            z_filter = f"zoompan=z='1.10':x='iw/2-(iw/zoom/2)':y='min(y+1.2,ih/2)':d={frames_per_clip}:s=1080x1920:fps={fps}"
        else:
            # Slow Pull Out / Inviting
            z_filter = f"zoompan=z='if(lte(zoom,1.0),1.14,max(1.001,zoom-0.0014))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_per_clip}:s=1080x1920:fps={fps}"

        cmd_clip = [
            FFMPEG_EXE, "-y",
            "-loop", "1",
            "-i", temp_img,
            "-vf", z_filter,
            "-t", f"{clip_dur:.3f}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            out_clip
        ]
        subprocess.run(cmd_clip, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        rendered_clips.append(out_clip)

    # Concat raw video
    concat_txt = os.path.join(temp_dir, "concat_gobi.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in rendered_clips:
            f.write(f"file '{c.replace(os.sep, '/')}'\n")

    raw_video = os.path.join(temp_dir, "gobi_raw_video.mp4")
    subprocess.run([
        FFMPEG_EXE, "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_txt,
        "-c", "copy",
        raw_video
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Subtitles SRT
    srt_file = os.path.join(temp_dir, "gobi_subs.srt")
    with open(srt_file, "w", encoding="utf-8") as f:
        for i, sc in enumerate(scenes):
            st = i * clip_dur
            et = (i + 1) * clip_dur
            st_str = f"{int(st//3600):02d}:{int((st%3600)//60):02d}:{int(st%60):02d},{int((st%1)*1000):03d}"
            et_str = f"{int(et//3600):02d}:{int((et%3600)//60):02d}:{int(et%60):02d},{int((et%1)*1000):03d}"
            f.write(f"{i + 1}\n")
            f.write(f"{st_str} --> {et_str}\n")
            f.write(f"{sc['sub']}\n\n")

    # Mux Audio + Burn Styled Safe Zone Subtitles
    escaped_srt = srt_file.replace("\\", "/").replace(":", "\\:")
    sub_style = "PlayResX=1080,PlayResY=1920,FontName=Arial,FontSize=42,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=300"
    vf_filter = f"subtitles='{escaped_srt}':force_style='{sub_style}'"

    cmd_final = [
        FFMPEG_EXE, "-y",
        "-i", raw_video,
        "-i", AUDIO_FILE,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        OUTPUT_MP4
    ]
    res = subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        # Fallback without subtitle filter
        cmd_fallback = [
            FFMPEG_EXE, "-y",
            "-i", raw_video,
            "-i", AUDIO_FILE,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            OUTPUT_MP4
        ]
        subprocess.run(cmd_fallback, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print(f"\n[🎉 THÀNH CÔNG] Video Gô Bi chào anh Thoại (9s) đã render xong tại:\n    -> {OUTPUT_MP4}")

    # Generate proof snapshot
    proof_png = os.path.join(PROJECT_ROOT, "shots", "gobi_greeting_proof.png")
    os.makedirs(os.path.dirname(proof_png), exist_ok=True)
    subprocess.run([
        FFMPEG_EXE, "-y",
        "-ss", "00:00:02.500",
        "-i", OUTPUT_MP4,
        "-vframes", "1",
        proof_png
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[+] Ảnh chụp bằng chứng video: {proof_png}")

if __name__ == "__main__":
    print("==================================================")
    print("🎬 VMAX: TẠO VIDEO GÔ BI CHÀO ANH THOẠI (~9S)")
    print("==================================================")
    build_concat_project()
    render_final_video()
