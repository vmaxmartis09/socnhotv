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
AUDIO_FILE = os.path.join(PROJECT_ROOT, "assets", "samples", "sample_video", "audio", "cardigan_45s_mastered.mp3")
PANEL_DIR = os.path.join(PROJECT_ROOT, "assets", "datasets", "koc", "ethereal_koc_panels_v3")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "assets", "samples", "sample_video", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_VIDEO = os.path.join(OUTPUT_DIR, "koc_broll_fashion_review_45s.mp4")

TARGET_W = 1080
TARGET_H = 1920
FPS = 30

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

# Read audio info
audio_info = MP3(AUDIO_FILE).info
TOTAL_DURATION = audio_info.length
TOTAL_FRAMES = int(round(TOTAL_DURATION * FPS))

print(f"[*] Total duration: {TOTAL_DURATION:.2f}s | Total frames: {TOTAL_FRAMES} | FPS: {FPS}")

# Fonts
try:
    font_title = ImageFont.truetype("arialbd.ttf", 30)
    font_badge = ImageFont.truetype("arialbd.ttf", 26)
    font_main = ImageFont.truetype("arialbd.ttf", 44)
    font_cta = ImageFont.truetype("arialbd.ttf", 34)
except Exception:
    font_title = ImageFont.load_default()
    font_badge = ImageFont.load_default()
    font_main = ImageFont.load_default()
    font_cta = ImageFont.load_default()

# 10 Segments
SEGMENTS = [
    {
        "start": 0.0, "end": 3.8,
        "panel": "panel_03_can_mat_chinh_dien.jpg",
        "badge": "DỪNG LẠI 3 GIÂY", "color": (255, 71, 87),
        "sub": "MẤY BÀ ƠI, DỪNG LẠI BA GIÂY!",
        "zoom_start": 1.00, "zoom_end": 1.08, "pan": (0.0, 0.0)
    },
    {
        "start": 3.8, "end": 8.2,
        "panel": "panel_01_chinh_dien_toan_than.jpg",
        "badge": "TRENDING 2026", "color": (255, 107, 129),
        "sub": "ÁO CARDIGAN HÀN QUỐC CỰC HOT NÈ!",
        "zoom_start": 1.07, "zoom_end": 1.00, "pan": (0.0, -0.03)
    },
    {
        "start": 8.2, "end": 13.0,
        "panel": "panel_05_goc_3_4_trung_canh.jpg",
        "badge": "BEST SELLER", "color": (241, 196, 15),
        "sub": "ĐỐ BIẾT TẠI SAO VỪA LÊN KỆ ĐÃ CHÁY HÀNG?",
        "zoom_start": 1.00, "zoom_end": 1.07, "pan": (0.0, 0.02)
    },
    {
        "start": 13.0, "end": 18.0,
        "panel": "panel_25_can_canh_chat_lieu.jpg",
        "badge": "THẨM ĐỊNH VẢI", "color": (46, 213, 115),
        "sub": "CẬN CẢNH LEN DỆT KIM SIÊU MỀM MỊN",
        "zoom_start": 1.02, "zoom_end": 1.08, "pan": (0.05, 0.0)
    },
    {
        "start": 18.0, "end": 23.0,
        "panel": "panel_20_can_canh_goc_rong.jpg",
        "badge": "CHẤT LƯỢNG 100%", "color": (52, 152, 219),
        "sub": "DÀY DẶN, GIẶT MÁY KHÔNG BAI DÃO",
        "zoom_start": 1.06, "zoom_end": 1.00, "pan": (0.0, 0.0)
    },
    {
        "start": 23.0, "end": 28.0,
        "panel": "panel_26_buoc_di_tu_nhien.jpg",
        "badge": "HACK DÁNG ĐỈNH", "color": (255, 159, 26),
        "sub": "FORM SUÔNG RỘNG GIẤU BỤNG CỰC ĐỈNH",
        "zoom_start": 1.00, "zoom_end": 1.08, "pan": (0.0, -0.04)
    },
    {
        "start": 28.0, "end": 33.0,
        "panel": "panel_10_nhin_lai_qua_vai.jpg",
        "badge": "OOTD AESTHETIC", "color": (155, 89, 182),
        "sub": "ĐI HỌC, ĐI LÀM PHỐI ĐỒ XINH XỈU",
        "zoom_start": 1.00, "zoom_end": 1.07, "pan": (0.02, 0.0)
    },
    {
        "start": 33.0, "end": 38.0,
        "panel": "panel_06_can_mat_3_4.jpg",
        "badge": "TÔN DA PASTEL", "color": (255, 107, 129),
        "sub": "BẢNG MÀU PASTEL TÔN DA HÀN QUỐC",
        "zoom_start": 1.01, "zoom_end": 1.08, "pan": (0.0, 0.02)
    },
    {
        "start": 38.0, "end": 43.0,
        "panel": "panel_35_chinh_toc.jpg",
        "badge": "CHUẨN TIỂU THƯ", "color": (52, 152, 219),
        "sub": "TRỜI SE LẠNH MẶC VỪA ĐỦ ẤM ÁP",
        "zoom_start": 1.07, "zoom_end": 1.00, "pan": (0.0, -0.02)
    },
    {
        "start": 43.0, "end": TOTAL_DURATION,
        "panel": "panel_02_chinh_dien_trung_canh.jpg",
        "badge": "SĂN DEAL NGAY", "color": (255, 71, 87),
        "sub": "GIÁ SALE DƯỚI 100 CÀNH Ở GIỎ HÀNG!",
        "zoom_start": 1.00, "zoom_end": 1.09, "pan": (0.0, 0.0)
    }
]

# Pre-load and clean panel images (strip bottom banner: 0 to 458)
print("[*] Pre-processing clean panel assets...")
loaded_panels = {}
for seg in SEGMENTS:
    p_name = seg["panel"]
    if p_name not in loaded_panels:
        full_p = os.path.join(PANEL_DIR, p_name)
        img = Image.open(full_p).convert("RGB")
        # Crop out bottom caption banner
        w, h = img.size
        clean_img = img.crop((0, 0, w, int(h * 0.895)))
        loaded_panels[p_name] = clean_img

# Pre-create rounded mask for the card
card_w = 960
card_h = 1200
card_mask = Image.new("L", (card_w, card_h), 0)
draw_mask = ImageDraw.Draw(card_mask)
draw_mask.rounded_rectangle([(0, 0), (card_w, card_h)], radius=36, fill=255)

card_shadow = Image.new("RGBA", (card_w + 40, card_h + 40), (0, 0, 0, 0))
draw_shadow = ImageDraw.Draw(card_shadow)
draw_shadow.rounded_rectangle([(15, 15), (card_w + 25, card_h + 25)], radius=36, fill=(0, 0, 0, 150))
card_shadow = card_shadow.filter(ImageFilter.GaussianBlur(radius=16))

card_x = (TARGET_W - card_w) // 2
card_y = 220

# Launch FFmpeg subprocess
print(f"[*] Launching FFmpeg encoder -> {OUTPUT_VIDEO}")
cmd = [
    ffmpeg_exe, "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{TARGET_W}x{TARGET_H}",
    "-pix_fmt", "rgb24",
    "-r", str(FPS),
    "-i", "-",
    "-i", AUDIO_FILE,
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-preset", "faster",
    "-crf", "19",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    OUTPUT_VIDEO
]

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

print("[*] Rendering frames with Ken Burns camera motion & dynamic overlays...")

last_seg_idx = -1
cached_bg = None

for frame_idx in range(TOTAL_FRAMES):
    current_time = frame_idx / FPS
    
    # Find active segment
    seg = SEGMENTS[-1]
    seg_idx = len(SEGMENTS) - 1
    for i, s in enumerate(SEGMENTS):
        if s["start"] <= current_time < s["end"]:
            seg = s
            seg_idx = i
            break
            
    # Interpolate motion
    seg_duration = max(seg["end"] - seg["start"], 0.1)
    seg_progress = min(max((current_time - seg["start"]) / seg_duration, 0.0), 1.0)
    
    # Smooth easing (smoothstep)
    ease_p = seg_progress * seg_progress * (3.0 - 2.0 * seg_progress)
    zoom = seg["zoom_start"] + (seg["zoom_end"] - seg["zoom_start"]) * ease_p
    pan_x = seg["pan"][0] * ease_p
    pan_y = seg["pan"][1] * ease_p
    
    clean_p = loaded_panels[seg["panel"]]
    pw, ph = clean_p.size
    
    # Cache ambient background per segment
    if seg_idx != last_seg_idx:
        last_seg_idx = seg_idx
        bg_raw = clean_p.resize((TARGET_W, TARGET_H), Image.Resampling.BILINEAR)
        bg_blur = bg_raw.filter(ImageFilter.GaussianBlur(radius=35))
        dimmer = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 110))
        bg_blur.paste(dimmer, (0, 0), dimmer)
        cached_bg = bg_blur
        
    frame = cached_bg.copy()
    
    # Crop foreground card with zoom & pan
    crop_w = int(pw / zoom)
    crop_h = int((pw / zoom) * (card_h / card_w))
    if crop_h > ph:
        crop_h = ph
        crop_w = int(ph * (card_w / card_h))
        
    center_x = pw // 2 + int(pw * pan_x)
    center_y = ph // 2 + int(ph * pan_y)
    
    left = max(0, min(center_x - crop_w // 2, pw - crop_w))
    top = max(0, min(center_y - crop_h // 2, ph - crop_h))
    
    crop_box = (left, top, left + crop_w, top + crop_h)
    card_img = clean_p.crop(crop_box).resize((card_w, card_h), Image.Resampling.LANCZOS)
    
    # Paste card shadow and card
    frame.paste(card_shadow, (card_x - 20, card_y - 20), card_shadow)
    frame.paste(card_img, (card_x, card_y), card_mask)
    
    # Overlay graphics
    overlay = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Card subtle white border
    draw.rounded_rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], radius=36, outline=(255, 255, 255, 80), width=2)
    
    # Header KOC channel pill
    chan_text = "• Mây Mây Review | 1m58 - 46kg •"
    tb = draw.textbbox((0, 0), chan_text, font=font_title)
    tb_w = tb[2] - tb[0]
    pill_w = tb_w + 48
    pill_h = 56
    pill_x = (TARGET_W - pill_w) // 2
    pill_y = 70
    draw.rounded_rectangle([(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)], radius=28, fill=(15, 15, 25, 210), outline=(255, 255, 255, 100), width=1)
    draw.text((pill_x + 24, pill_y + 11), chan_text, font=font_title, fill=(255, 255, 255, 240))
    
    # Badge Pill (top-left inside card)
    badge_text = seg["badge"]
    badge_color = seg["color"]
    bb = draw.textbbox((0, 0), badge_text, font=font_badge)
    bb_w = bb[2] - bb[0]
    b_pill_w = bb_w + 36
    b_pill_h = 44
    b_pill_x = card_x + 36
    b_pill_y = card_y + 36
    draw.rounded_rectangle([(b_pill_x, b_pill_y), (b_pill_x + b_pill_w, b_pill_y + b_pill_h)], radius=22, fill=(badge_color[0], badge_color[1], badge_color[2], 235))
    draw.text((b_pill_x + 18, b_pill_y + 8), badge_text, font=font_badge, fill=(255, 255, 255, 255))
    
    # Subtitle Card (Safe Zone: y = 1480)
    sub_text = seg["sub"]
    sub_y = 1480
    sb = draw.textbbox((0, 0), sub_text, font=font_main)
    sb_w = sb[2] - sb[0]
    sub_card_w = max(sb_w + 64, 600)
    sub_card_h = 100
    sub_card_x = (TARGET_W - sub_card_w) // 2
    
    draw.rounded_rectangle([(sub_card_x, sub_y), (sub_card_x + sub_card_w, sub_y + sub_card_h)], radius=26, fill=(10, 10, 18, 220), outline=(255, 255, 255, 65), width=2)
    # Shadow text
    draw.text((sub_card_x + (sub_card_w - sb_w) // 2 + 2, sub_y + 24 + 2), sub_text, font=font_main, fill=(0, 0, 0, 220))
    # Glowing yellow text
    draw.text((sub_card_x + (sub_card_w - sb_w) // 2, sub_y + 24), sub_text, font=font_main, fill=(255, 235, 80, 255))
    
    # CTA Callout (Last 6 seconds with gentle pulse)
    if current_time >= 42.5:
        pulse = math.sin((current_time - 42.5) * 7.0) * 6.0
        cta_x = 70
        cta_y = 1630 + int(pulse)
        cta_text = "▼ SĂN DEAL GIỎ HÀNG GÓC TRÁI"
        cb = draw.textbbox((0, 0), cta_text, font=font_cta)
        cb_w = cb[2] - cb[0]
        draw.rounded_rectangle([(cta_x, cta_y), (cta_x + cb_w + 48, cta_y + 74)], radius=37, fill=(255, 71, 87, 245), outline=(255, 255, 255, 230), width=2)
        draw.text((cta_x + 24, cta_y + 17), cta_text, font=font_cta, fill=(255, 255, 255, 255))
        
    frame.paste(overlay, (0, 0), overlay)
    
    # Write raw bytes to ffmpeg stdin
    proc.stdin.write(frame.tobytes())
    
    if frame_idx % 150 == 0 or frame_idx == TOTAL_FRAMES - 1:
        percent = (frame_idx + 1) / TOTAL_FRAMES * 100.0
        print(f"[Render Progress] {frame_idx + 1}/{TOTAL_FRAMES} frames ({percent:.1f}%) | {current_time:.1f}s")

proc.stdin.close()
proc.wait()

print("\n" + "="*70)
print(f"🎉 RENDER SUCCESS: {OUTPUT_VIDEO}")
print(f"File size: {os.path.getsize(OUTPUT_VIDEO) / (1024*1024):.2f} MB")
print("="*70)
