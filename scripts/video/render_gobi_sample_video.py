import os
import sys
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg
from mutagen.mp3 import MP3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIO_FILE = os.path.join(PROJECT_ROOT, "assets", "samples", "sample_video", "audio", "gobi_thui_9s.mp3")
BGM_FILE = os.path.join(PROJECT_ROOT, "assets", "audio", "bgm.mp3")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "assets", "samples", "sample_video", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_VIDEO = os.path.join(OUTPUT_DIR, "gobi_thui_koc_9s.mp4")

# Master Image Asset (100% locked Master KOC DNA)
MASTER_DNA_PATH = os.path.join(PROJECT_ROOT, "assets", "datasets", "koc", "MASTER_KOC_DNA.jpg")

TARGET_W = 1080
TARGET_H = 1920
FPS = 30
TOTAL_DURATION = 9.0  # exactly 9.0 seconds
TOTAL_FRAMES = int(TOTAL_DURATION * FPS)

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

# Font setup with fallback
try:
    font_main = ImageFont.truetype("arialbd.ttf", 46)
    font_badge = ImageFont.truetype("arialbd.ttf", 26)
    font_watermark = ImageFont.truetype("arialbd.ttf", 28)
except Exception:
    font_main = ImageFont.load_default()
    font_badge = ImageFont.load_default()
    font_watermark = ImageFont.load_default()

# Prepare Ultra-Res Master Image (2x Lanczos super-sampling + delicate unsharp mask)
print("[*] Loading and super-sampling Master KOC DNA...")
master_raw = Image.open(MASTER_DNA_PATH).convert("RGB")
mw, mh = master_raw.size
# 2x super-sampling gives 1536x2752 for flawless downscaling at all zoom levels
super_master = master_raw.resize((mw * 2, mh * 2), Image.Resampling.LANCZOS)
super_master = super_master.filter(ImageFilter.UnsharpMask(radius=1.2, percent=50, threshold=1))
SW, SH = super_master.size
print(f"[+] Master DNA ready: {SW}x{SH}")

# Clean, professional subtitle track (zero missing glyphs, accurate timings)
SUBTITLE_TRACK = [
    (0.0, 1.4, "HELLO ÔNG KẸ!", "Gobi Thúi", (255, 107, 129)),
    (1.4, 3.2, "EM LÀ GOBI THÚI CỦA ANH ĐÂY!", "KOC AI VMAX", (255, 71, 87)),
    (3.2, 5.8, "HÔM NAY CÙNG EM LÊN ĐỒ THẬT XINH", "Cozy Silk & Knit OOTD", (241, 196, 15)),
    (5.8, 7.4, "VÀ DẠO PHỐ NHA...", "Lookbook Aesthetic", (46, 213, 115)),
    (7.4, 9.0, "YÊU ANH NHIỀU!", "Gobi Thúi", (255, 107, 129))
]

def render_camera_frame(progress_in_scene, scene_type="intro"):
    """
    Renders smooth, living cinematic camera movements from the Master DNA.
    Guarantees 100% identity lock across all 9 seconds with zero face distortion.
    """
    # Smooth easing curve (smoothstep)
    t = progress_in_scene
    ease = t * t * (3.0 - 2.0 * t)

    # Base scale: fit image height to 1920 with breathing room
    fit_scale = (TARGET_H / SH) * 1.05

    if scene_type == "intro":
        # Scene 1: Medium portrait hook (0.0s - 3.2s)
        # Slow, seductive push-in to Gobi's eyes and smile
        zoom = 1.00 + (1.12 - 1.00) * ease
        cy_ratio = 0.32 + (0.30 - 0.32) * ease  # Focus on face
        cx_ratio = 0.50

    elif scene_type == "ootd":
        # Scene 2: OOTD outfit showcase (3.2s - 5.8s)
        # Smooth vertical tilt from silk camisole/cardigan up to collarbone & face
        zoom = 1.10 - (1.10 - 1.04) * ease
        cy_ratio = 0.44 - (0.44 - 0.32) * ease  # Pan upward along body
        cx_ratio = 0.50 + 0.015 * math.sin(ease * math.pi)

    else:
        # Scene 3: Emotional close-up & outro (5.8s - 9.0s)
        # Intimate beauty portrait with gentle organic drift
        zoom = 1.15 - (1.15 - 1.06) * ease
        cy_ratio = 0.29 + 0.02 * ease
        cx_ratio = 0.50 - 0.015 * math.sin(ease * math.pi)

    current_scale = fit_scale * zoom
    cw = int(round(TARGET_W / current_scale))
    ch = int(round(TARGET_H / current_scale))

    cx = SW * cx_ratio
    cy = SH * cy_ratio

    x1 = int(round(cx - cw / 2.0))
    y1 = int(round(cy - ch / 2.0))
    x1 = max(0, min(SW - cw, x1))
    y1 = max(0, min(SH - ch, y1))

    crop = super_master.crop((x1, y1, x1 + cw, y1 + ch))
    return crop.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)

def draw_decorations(frame, current_time):
    overlay = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Subtle top & bottom cinematic vignettes for contrast
    # Top-left Watermark Pill
    wm_text = "GOBI THÚI • KOC AI"
    w_box = draw.textbbox((0, 0), wm_text, font=font_watermark)
    w_tw = w_box[2] - w_box[0]
    pill_w = w_tw + 44
    pill_h = 52
    draw.rounded_rectangle([(40, 60), (40 + pill_w, 60 + pill_h)], radius=26, fill=(10, 10, 15, 175), outline=(255, 255, 255, 60), width=1)
    # Glowing dot
    draw.ellipse([(56, 81), (68, 93)], fill=(255, 107, 129, 240))
    draw.text((78, 72), wm_text, font=font_watermark, fill=(255, 245, 235, 240))

    # 2. Subtitle Card
    active_sub = None
    for sub in SUBTITLE_TRACK:
        if sub[0] <= current_time <= sub[1]:
            active_sub = sub
            break

    if active_sub:
        start_t, end_t, main_txt, badge_txt, badge_col = active_sub
        duration = end_t - start_t
        sub_progress = (current_time - start_t) / duration

        # Smooth pop-in
        alpha_mult = min(1.0, sub_progress / 0.12)
        card_alpha = int(225 * alpha_mult)

        # Dynamic measurement of text widths to avoid any overflow
        m_box = draw.textbbox((0, 0), main_txt, font=font_main)
        m_tw = m_box[2] - m_box[0]
        m_th = m_box[3] - m_box[1]

        b_box = draw.textbbox((0, 0), badge_txt, font=font_badge)
        b_tw = b_box[2] - b_box[0]

        card_w = max(m_tw + 110, 600)
        card_w = min(card_w, 1000)  # Safe bounds
        card_h = 160
        card_x = (TARGET_W - card_w) // 2
        card_y = 1380  # TikTok safe zone

        # Frosted dark glass container
        draw.rounded_rectangle(
            [(card_x, card_y), (card_x + card_w, card_y + card_h)],
            radius=32,
            fill=(12, 12, 18, card_alpha),
            outline=(255, 255, 255, int(90 * alpha_mult)),
            width=2
        )

        # Accent badge
        badge_w = b_tw + 48
        badge_h = 40
        badge_x = card_x + (card_w - badge_w) // 2
        badge_y = card_y - 20
        draw.rounded_rectangle(
            [(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)],
            radius=20,
            fill=badge_col + (int(255 * alpha_mult),),
            outline=(255, 255, 255, int(120 * alpha_mult)),
            width=1
        )
        draw.text((badge_x + (badge_w - b_tw) // 2, badge_y + 6), badge_txt, font=font_badge, fill=(255, 255, 255, int(255 * alpha_mult)))

        # Main subtitle text
        m_tx = card_x + (card_w - m_tw) // 2
        m_ty = card_y + 62

        # Crisp shadow
        draw.text((m_tx + 2, m_ty + 2), main_txt, font=font_main, fill=(0, 0, 0, int(220 * alpha_mult)))
        # Main white text
        draw.text((m_tx, m_ty), main_txt, font=font_main, fill=(255, 255, 255, int(255 * alpha_mult)))

    frame_rgba = frame.convert("RGBA")
    combined = Image.alpha_composite(frame_rgba, overlay)
    return combined.convert("RGB")

print(f"[*] Rendering 9.0s TikTok video ({TOTAL_FRAMES} frames @ {FPS}fps)...")

cmd = [
    ffmpeg_exe,
    "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{TARGET_W}x{TARGET_H}",
    "-pix_fmt", "rgb24",
    "-r", str(FPS),
    "-i", "-",  # stdin raw video frames
    "-i", AUDIO_FILE,
]

if os.path.exists(BGM_FILE):
    cmd.extend([
        "-i", BGM_FILE,
        "-filter_complex",
        "[1:a]volume=1.0[v];[2:a]volume=0.18,afade=t=out:st=8.0:d=1.0[b];[v][b]amix=inputs=2:duration=first[aout]",
        "-map", "0:v",
        "-map", "[aout]",
    ])
else:
    cmd.extend([
        "-map", "0:v",
        "-map", "1:a",
    ])

cmd.extend([
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-preset", "medium",
    "-crf", "17",
    "-c:a", "aac",
    "-b:a", "192k",
    "-t", str(TOTAL_DURATION),
    OUTPUT_VIDEO
])

pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)

for f_idx in range(TOTAL_FRAMES):
    t = f_idx / FPS

    # 3 cinematic acts:
    # Act 1: 0.0s - 3.2s (Greeting & Hook)
    # Act 2: 3.2s - 5.8s (OOTD showcase)
    # Act 3: 5.8s - 9.0s (Emotional close-up & outro)
    if t < 3.2:
        prog = t / 3.2
        frame = render_camera_frame(prog, scene_type="intro")
    elif t < 5.8:
        prog = (t - 3.2) / 2.6
        frame = render_camera_frame(prog, scene_type="ootd")
    else:
        prog = (t - 5.8) / 3.2
        frame = render_camera_frame(prog, scene_type="outro")

    frame = draw_decorations(frame, t)
    pipe.stdin.write(frame.tobytes())

    if f_idx % 45 == 0 or f_idx == TOTAL_FRAMES - 1:
        print(f"Rendered frame {f_idx+1}/{TOTAL_FRAMES} ({(f_idx+1)/TOTAL_FRAMES*100:.1f}%) - time {t:.2f}s")

pipe.stdin.close()
pipe.wait()

if pipe.returncode == 0 and os.path.exists(OUTPUT_VIDEO):
    size_mb = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
    print("="*60)
    print("🎉 RENDER VIDEO 9S HOÀN TOÀN THÀNH CÔNG!")
    print(f"[*] File xuất: {OUTPUT_VIDEO}")
    print(f"[*] Dung lượng: {size_mb:.2f} MB")
    print(f"[*] Độ phân giải: {TARGET_W}x{TARGET_H} (9:16) 30 FPS")
    print("="*60)
else:
    print("Error rendering video")
