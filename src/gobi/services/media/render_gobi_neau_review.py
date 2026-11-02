"""
VMAX Gobi KOC Production Engine
Official Review Video: NEAU NuNu Áo Thun Nữ Dài Tay BodyFit Chống UV (NU221)
- Resolution: 1080x1920 (9:16 Vertical HD)
- Frame Rate: 30 FPS
- Multi-Scene Dynamic Ken Burns Motion
- TikTok Safe Zone Compliant Graphic Badges & Subtitles
- Mastered KOC Voiceover + Ducked Commercial BGM (12% volume)
"""

import os
import sys
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = "/Volumes/Data/gobi-social"
VOICEOVER = os.path.join(PROJECT_ROOT, "assets", "datasets", "koc", "campaign_neau", "voice_mastered.wav")
BGM = os.path.join(PROJECT_ROOT, "assets", "audio", "bgm.mp3")
OUTPUT_VIDEO = os.path.join(PROJECT_ROOT, "output", "videos", "gobi_neau_review_master.mp4")

IMG_DIR = os.path.join(PROJECT_ROOT, "assets", "datasets", "koc", "campaign_neau")
SCENE_1_IMG = os.path.join(IMG_DIR, "shot_01_hook.jpg")
SCENE_2_IMG = os.path.join(IMG_DIR, "shot_02_walk.jpg")
SCENE_3_IMG = os.path.join(IMG_DIR, "shot_03_fabric.jpg")
SCENE_4_IMG = os.path.join(IMG_DIR, "shot_04_blazer.jpg")
SCENE_5_IMG = os.path.join(IMG_DIR, "shot_01_hook.jpg")

TARGET_W = 1080
TARGET_H = 1920
FPS = 30
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

# Scene Timing (Total: 24.45s matching voiceover)
SCENES = [
    {
        "id": 1,
        "image": SCENE_1_IMG,
        "start": 0.0,
        "end": 5.2,
        "badge": "★ ÁO THUN CHỐNG UV MÁT LỊM ★",
        "sub": "Ai bảo áo thun ôm dài tay là bị bí bách nóng nực? Quên đi nha!",
        "motion": "zoom_in"
    },
    {
        "id": 2,
        "image": SCENE_2_IMG,
        "start": 5.2,
        "end": 10.8,
        "badge": "★ SIÊU CO GIÃN - SIẾT EO TÔN DÁNG ★",
        "sub": "Chất vải Micro-Mesh co giãn đàn hồi, form bodyfit hack dáng cực đỉnh!",
        "motion": "pan_down"
    },
    {
        "id": 3,
        "image": SCENE_3_IMG,
        "start": 10.8,
        "end": 16.2,
        "badge": "★ VẢI MICRO-MESH KHÔNG ĐƯỜNG MAY ★",
        "sub": "Mùa hè cản nắng đạp xe bao mát, cản 99% tia cực tím độc hại",
        "motion": "zoom_in"
    },
    {
        "id": 4,
        "image": SCENE_4_IMG,
        "start": 16.2,
        "end": 20.8,
        "badge": "★ 1 MÓN ĐỒ PHỐI ĐỦ 4 MÙA ★",
        "sub": "Mùa đông khoác thêm chiếc blazer ngoài là thành outfit sang xịn mịn",
        "motion": "pan_horizontal"
    },
    {
        "id": 5,
        "image": SCENE_5_IMG,
        "start": 20.8,
        "end": 24.45,
        "badge": "★ GIỎ HÀNG TIKTOK SHOP GÓC TRÁI ★",
        "sub": "Đang có đủ màu xinh trong giỏ hàng góc trái, bấm ngay kẻo hết size nha!",
        "motion": "cta_pulse"
    }
]

TOTAL_DURATION = 24.45
TOTAL_FRAMES = int(round(TOTAL_DURATION * FPS))

def get_font(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf"
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()

font_badge = get_font(36)
font_sub = get_font(32)
font_watermark = get_font(26)

def load_and_prep_image(path):
    img = Image.open(path).convert("RGB")
    if img.size != (TARGET_W, TARGET_H):
        w, h = img.size
        scale = max(TARGET_W / w, TARGET_H / h)
        nw, nh = int(round(w * scale)), int(round(h * scale))
        img = img.resize((nw, nh), Image.Resampling.LANCZOS)
        left = (nw - TARGET_W) // 2
        top = (nh - TARGET_H) // 2
        img = img.crop((left, top, left + TARGET_W, top + TARGET_H))
    return img

print("[1] Loading and preparing scene images...")
loaded_images = [load_and_prep_image(s["image"]) for s in SCENES]

def draw_text_with_outline(draw, pos, text, font, fill_color, outline_color, outline_width=3):
    x, y = pos
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx * dx + dy * dy <= outline_width * outline_width:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text((x, y), text, font=font, fill=fill_color)

def render_frame(frame_idx):
    cur_time = frame_idx / FPS
    scene_idx = 0
    for idx, sc in enumerate(SCENES):
        if sc["start"] <= cur_time < sc["end"]:
            scene_idx = idx
            break
        if cur_time >= SCENES[-1]["start"]:
            scene_idx = len(SCENES) - 1

    sc = SCENES[scene_idx]
    base_img = loaded_images[scene_idx]
    sc_dur = sc["end"] - sc["start"]
    progress = min(max((cur_time - sc["start"]) / sc_dur, 0.0), 1.0)
    ease = progress * progress * (3.0 - 2.0 * progress)

    w, h = TARGET_W, TARGET_H
    if sc["motion"] == "zoom_in":
        zoom = 1.00 + 0.08 * ease
        cw, ch = int(w / zoom), int(h / zoom)
        cx, cy = w // 2, int(h * (0.42 - 0.04 * ease))
        x1 = max(0, min(w - cw, cx - cw // 2))
        y1 = max(0, min(h - ch, cy - ch // 2))
        crop_box = (x1, y1, x1 + cw, y1 + ch)
        frame = base_img.crop(crop_box).resize((w, h), Image.Resampling.BILINEAR)

    elif sc["motion"] == "pan_down":
        zoom = 1.06
        cw, ch = int(w / zoom), int(h / zoom)
        cx = w // 2
        cy = int(h * (0.34 + 0.14 * ease))
        x1 = max(0, min(w - cw, cx - cw // 2))
        y1 = max(0, min(h - ch, cy - ch // 2))
        crop_box = (x1, y1, x1 + cw, y1 + ch)
        frame = base_img.crop(crop_box).resize((w, h), Image.Resampling.BILINEAR)

    elif sc["motion"] == "pan_horizontal":
        zoom = 1.05
        cw, ch = int(w / zoom), int(h / zoom)
        cx = int(w * (0.47 + 0.06 * ease))
        cy = int(h * 0.40)
        x1 = max(0, min(w - cw, cx - cw // 2))
        y1 = max(0, min(h - ch, cy - ch // 2))
        crop_box = (x1, y1, x1 + cw, y1 + ch)
        frame = base_img.crop(crop_box).resize((w, h), Image.Resampling.BILINEAR)

    else:  # cta_pulse
        pulse = 0.03 * math.sin(progress * math.pi * 4)
        zoom = 1.02 + pulse
        cw, ch = int(w / zoom), int(h / zoom)
        cx, cy = w // 2, int(h * 0.42)
        x1 = max(0, min(w - cw, cx - cw // 2))
        y1 = max(0, min(h - ch, cy - ch // 2))
        crop_box = (x1, y1, x1 + cw, y1 + ch)
        frame = base_img.crop(crop_box).resize((w, h), Image.Resampling.BILINEAR)

    # Overlays
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    # 1. Top Safe Zone: Channel Badge (y = 260)
    badge_text = sc["badge"]
    bbox = font_badge.getbbox(badge_text)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    bx = (w - bw) // 2
    by = 260

    pad_x, pad_y = 26, 12
    odraw.rounded_rectangle(
        [bx - pad_x, by - pad_y, bx + bw + pad_x, by + bh + pad_y],
        radius=16,
        fill=(0, 0, 0, 190),
        outline=(254, 44, 85, 230),  # TikTok Red Outline
        width=2
    )

    chan_tag = "GOBI KOC | 1m62 - 48kg | Review Chân Thật"
    tbox = font_watermark.getbbox(chan_tag)
    tw = tbox[2] - tbox[0]
    odraw.text(((w - tw) // 2, by - 38), chan_tag, font=font_watermark, fill=(255, 255, 255, 220))
    draw_text_with_outline(odraw, (bx, by), badge_text, font_badge, (255, 225, 80, 255), (0, 0, 0, 255), 2)

    # 2. Lower Safe Zone: Subtitles (y = 1420)
    sub_text = sc["sub"]
    sbox = font_sub.getbbox(sub_text)
    sw, sh = sbox[2] - sbox[0], sbox[3] - sbox[1]
    if sw > 900:
        words = sub_text.split()
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        sb1 = font_sub.getbbox(line1)
        sb2 = font_sub.getbbox(line2)
        w1, h1 = sb1[2] - sb1[0], sb1[3] - sb1[1]
        w2, h2 = sb2[2] - sb2[0], sb2[3] - sb2[1]
        max_w = max(w1, w2)
        total_h = h1 + h2 + 10
        sy = 1420
        odraw.rounded_rectangle(
            [(w - max_w) // 2 - 24, sy - 14, (w + max_w) // 2 + 24, sy + total_h + 14],
            radius=14,
            fill=(0, 0, 0, 190)
        )
        draw_text_with_outline(odraw, ((w - w1) // 2, sy), line1, font_sub, (255, 255, 255, 255), (0, 0, 0, 255), 2)
        draw_text_with_outline(odraw, ((w - w2) // 2, sy + h1 + 10), line2, font_sub, (255, 255, 255, 255), (0, 0, 0, 255), 2)
    else:
        sx = (w - sw) // 2
        sy = 1430
        odraw.rounded_rectangle(
            [sx - 24, sy - 12, sx + sw + 24, sy + sh + 12],
            radius=14,
            fill=(0, 0, 0, 190)
        )
        draw_text_with_outline(odraw, (sx, sy), sub_text, font_sub, (255, 255, 255, 255), (0, 0, 0, 255), 2)

    # 3. Bottom Left CTA Pointer for Final Scene
    if scene_idx == 4:
        cta_glow = int(190 + 65 * math.sin(cur_time * 7))
        cta_txt = "BẤM GIỎ HÀNG NHẬN VOUCHER"
        cbox = font_watermark.getbbox(cta_txt)
        cw, ch = cbox[2] - cbox[0], cbox[3] - cbox[1]
        odraw.rounded_rectangle(
            [80, 1550, 80 + cw + 32, 1550 + ch + 20],
            radius=12,
            fill=(254, 44, 85, cta_glow),
            outline=(255, 255, 255, 255),
            width=2
        )
        odraw.text((96, 1560), cta_txt, font=font_watermark, fill=(255, 255, 255, 255))

    final_frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")
    return np.array(final_frame)

print(f"[2] Initializing FFmpeg pipe ({TOTAL_FRAMES} frames @ 30 FPS)...")
temp_video = os.path.join(PROJECT_ROOT, "output", "videos", "temp_visual_neau.mp4")

pipe_cmd = [
    ffmpeg_exe, "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{TARGET_W}x{TARGET_H}",
    "-pix_fmt", "rgb24",
    "-r", str(FPS),
    "-i", "-",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    temp_video
]

proc = subprocess.Popen(pipe_cmd, stdin=subprocess.PIPE)

print("[3] Rendering cinematic frames...")
for f in range(TOTAL_FRAMES):
    arr = render_frame(f)
    proc.stdin.write(arr.tobytes())
    if (f + 1) % 150 == 0 or f == TOTAL_FRAMES - 1:
        print(f"    Progress: {f+1}/{TOTAL_FRAMES} ({(f+1)/TOTAL_FRAMES*100:.1f}%)")

proc.stdin.close()
proc.wait()
print(f"[+] Visual track rendered: {temp_video}")

# Mix Master Audio: Mastered Voiceover + Ducked BGM
print("[4] Mixing Voiceover with ducked BGM...")
mix_cmd = [
    ffmpeg_exe, "-y",
    "-i", temp_video,
    "-i", VOICEOVER,
    "-i", BGM,
    "-filter_complex",
    "[2:a]volume=0.12,afade=t=in:st=0:d=1,afade=t=out:st=22:d=2.45[bgm];"
    "[1:a]volume=1.25[vox];"
    "[vox][bgm]amix=inputs=2:duration=first[aout]",
    "-map", "0:v",
    "-map", "[aout]",
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    OUTPUT_VIDEO
]

res = subprocess.run(mix_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
if os.path.exists(temp_video):
    os.remove(temp_video)

if os.path.exists(OUTPUT_VIDEO):
    size_mb = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
    print(f"\n[SUCCESS] Gobi NEAU Review Video #1 rendered successfully!")
    print(f"File: {OUTPUT_VIDEO}")
    print(f"Size: {size_mb:.2f} MB")
else:
    print("[-] Error mixing video:", res.stderr)
