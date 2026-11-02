"""
=============================================================================
KOC AI VIDEO AUTOMATION TOOLKIT (Theo quy trình W5G Martech / Steve W)
Tự động hóa sản xuất video ngắn TikTok / Reels / Shorts từ kịch bản hoặc sản phẩm.
=============================================================================
"""

import os
import sys
import json
import argparse
import subprocess
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"

def generate_voice(text, out_path, lang='vi'):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(out_path)
    # Get duration
    res = subprocess.run([FFMPEG, "-i", out_path], stderr=subprocess.PIPE, text=True)
    import re
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", res.stderr)
    if m:
        return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
    return 6.0

def create_gradient_mask(w, h, top_fade=420, bot_fade=560):
    gradient = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)
    for y in range(top_fade):
        alpha = int(180 * (1.0 - (y / top_fade) ** 1.5))
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    for y in range(h - bot_fade, h):
        progress = (y - (h - bot_fade)) / bot_fade
        alpha = int(210 * (progress ** 1.3))
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    return gradient

def render_scene(scene_data, out_path, fps=30):
    duration = scene_data['duration'] + 0.3
    total_frames = int(duration * fps)
    w, h = 1080, 1920
    
    img = Image.open(scene_data['image']).convert('RGB')
    img_w, img_h = img.size
    target_ratio = w / h
    img_ratio = img_w / img_h
    
    if img_ratio > target_ratio:
        new_w = int(img_h * target_ratio)
        offset = (img_w - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, img_h))
    else:
        new_h = int(img_w / target_ratio)
        offset = (img_h - new_h) // 2
        img = img.crop((0, offset, img_w, offset + new_h))
        
    img = img.resize((w, h), Image.Resampling.LANCZOS)
    gradient_mask = create_gradient_mask(w, h)
    
    font_badge = ImageFont.truetype(FONT_BOLD, 36)
    font_title = ImageFont.truetype(FONT_BOLD, 70)
    font_sub = ImageFont.truetype(FONT_BOLD, 44)
    
    cmd = [
        FFMPEG, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{w}x{h}", "-pix_fmt", "rgb24", "-r", str(fps),
        "-i", "-",
        "-i", scene_data['audio'],
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        out_path
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    b_color = scene_data.get('badge_color', (239, 68, 68))
    badge_text = scene_data.get('badge', '★ HOT DEAL ★')
    title_text = scene_data.get('hook_title', '')
    sub1 = scene_data.get('sub1', '')
    sub2 = scene_data.get('sub2', '')
    
    for i in range(total_frames):
        if proc.poll() is not None:
            break
        progress = i / max(1, total_frames - 1)
        scale = 1.0 + 0.12 * progress
        scaled_w, scaled_h = int(w * scale), int(h * scale)
        crop_x, crop_y = (scaled_w - w) // 2, (scaled_h - h) // 2
        
        scaled_img = img.resize((scaled_w, scaled_h), Image.Resampling.BILINEAR)
        frame = scaled_img.crop((crop_x, crop_y, crop_x + w, crop_y + h))
        frame.paste(gradient_mask, (0, 0), gradient_mask)
        draw = ImageDraw.Draw(frame, 'RGBA')
        
        # Badge
        b_bbox = font_badge.getbbox(badge_text)
        bw = (b_bbox[2] - b_bbox[0]) + 60
        bx = (w - bw) // 2
        draw.rounded_rectangle([bx, 130, bx + bw, 194], radius=32, fill=(*b_color, 240))
        draw.text((bx + 30, 140), badge_text, font=font_badge, fill=(255, 255, 255, 255))
        
        # Title
        t_bbox = font_title.getbbox(title_text)
        tw = t_bbox[2] - t_bbox[0]
        tx = (w - tw) // 2
        for off in [(3, 3), (-3, -3), (3, -3), (-3, 3)]:
            draw.text((tx + off[0], 225 + off[1]), title_text, font=font_title, fill=(0, 0, 0, 200))
        draw.text((tx, 225), title_text, font=font_title, fill=(255, 230, 0, 255))
        
        # Subtitle
        cur_sub = sub1 if progress < 0.52 else sub2
        s_bbox = font_sub.getbbox(cur_sub)
        sw = (s_bbox[2] - s_bbox[0]) + 64
        sx = (w - sw) // 2
        draw.rounded_rectangle([sx, h - 380, sx + sw, h - 288], radius=26, fill=(15, 23, 42, 240))
        draw.rounded_rectangle([sx, h - 380, sx + sw, h - 288], radius=26, outline=(255, 215, 0, 230), width=4)
        draw.text((sx + 32, h - 361), cur_sub, font=font_sub, fill=(255, 255, 255, 255))
        
        # Progress Bar
        draw.rectangle([0, h - 20, int(w * progress), h], fill=(236, 72, 153, 255))
        
        try:
            proc.stdin.write(frame.tobytes())
        except (BrokenPipeError, OSError):
            break
            
    try:
        proc.stdin.close()
    except Exception:
        pass
    proc.wait()

def build_video_from_config(config_file, output_file, bgm_file="assets/audio/bgm.mp3"):
    with open(config_file, 'r', encoding='utf-8') as f:
        scenes = json.load(f)
        
    os.makedirs('temp_clips', exist_ok=True)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    clips = []
    for s in scenes:
        clip_path = f"temp_clips/{s['id']}.mp4"
        print(f"-> Processing scene: {s['id']}")
        render_scene(s, clip_path)
        clips.append(clip_path)
        
    concat_list = "temp_clips/list.txt"
    with open(concat_list, 'w', encoding='utf-8') as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c).replace('\\', '/')}'\n")
            
    concat_raw = "temp_clips/raw.mp4"
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", concat_raw], check=True)
    
    # Mix BGM
    res = subprocess.run([FFMPEG, "-i", concat_raw], stderr=subprocess.PIPE, text=True)
    import re
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", res.stderr)
    total_dur = 45.0
    if m:
        total_dur = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
        
    fade_st = max(0, total_dur - 2.5)
    filter_complex = f"[1:a]volume=0.14,afade=t=out:st={fade_st:.2f}:d=2.5[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    
    cmd_mix = [
        FFMPEG, "-y", "-i", concat_raw, "-i", bgm_file,
        "-filter_complex", filter_complex,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-t", str(total_dur),
        output_file
    ]
    subprocess.run(cmd_mix, check=True)
    print(f"\n[DONE] Video exported successfully to: {output_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="KOC AI Video Automation")
    parser.add_argument("--config", default="configs/scenes_config.json", help="Path to scenes config JSON")
    parser.add_argument("--out", default="output/final_video.mp4", help="Output MP4 file path")
    args = parser.parse_args()
    build_video_from_config(args.config, args.out)
