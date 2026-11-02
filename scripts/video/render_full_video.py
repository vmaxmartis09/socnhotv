import os
import sys
import json
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT_REGULAR = "C:/Windows/Fonts/arial.ttf"

font_badge = ImageFont.truetype(FONT_BOLD, 36)
font_title = ImageFont.truetype(FONT_BOLD, 70)
font_sub = ImageFont.truetype(FONT_BOLD, 44)

# Create smooth gradient overlay
def create_gradient_mask(w, h, top_fade=420, bot_fade=560):
    gradient = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)
    
    # Top fade down
    for y in range(top_fade):
        alpha = int(180 * (1.0 - (y / top_fade) ** 1.5))
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
        
    # Bottom fade up
    for y in range(h - bot_fade, h):
        progress = (y - (h - bot_fade)) / bot_fade
        alpha = int(210 * (progress ** 1.3))
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
        
    return gradient

def render_scene_clip(scene, out_path, fps=30):
    duration = scene['duration']
    total_frames = int(duration * fps)
    w, h = 1080, 1920
    
    print(f"\n>>> Rendering {scene['id']} ({duration}s, {total_frames} frames)...")
    
    # Load and fit base image
    img = Image.open(scene['image']).convert('RGB')
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
    
    # ffmpeg streaming command
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{w}x{h}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-i", f"assets/audio/{scene['id']}.mp3",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        out_path
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    badge_text = scene.get('badge', '★ HOT DEAL ★')
    title_text = scene.get('hook_title', '')
    sub1 = scene.get('subtitle_1', '')
    sub2 = scene.get('subtitle_2', '')
    
    badge_colors = {
        'scene1': (239, 68, 68),    # Red
        'scene2': (245, 158, 11),   # Amber
        'scene3': (16, 185, 129),   # Emerald
        'scene4': (99, 102, 241),   # Indigo
        'scene5': (236, 72, 153)    # Pink
    }
    b_color = badge_colors.get(scene['id'], (239, 68, 68))
    
    for i in range(total_frames):
        if proc.poll() is not None:
            break
            
        progress = i / max(1, total_frames - 1)
        
        # Ken burns motion
        if scene['id'] in ['scene1', 'scene3', 'scene5']:
            scale = 1.0 + 0.12 * progress
            scaled_w = int(w * scale)
            scaled_h = int(h * scale)
            crop_x = (scaled_w - w) // 2
            crop_y = (scaled_h - h) // 2
        else:
            scale = 1.10
            scaled_w = int(w * scale)
            scaled_h = int(h * scale)
            max_pan_x = scaled_w - w
            crop_x = int(max_pan_x * progress)
            crop_y = (scaled_h - h) // 2
            
        scaled_img = img.resize((scaled_w, scaled_h), Image.Resampling.BILINEAR)
        frame = scaled_img.crop((crop_x, crop_y, crop_x + w, crop_y + h))
        
        # Composite smooth gradient
        frame.paste(gradient_mask, (0, 0), gradient_mask)
        draw = ImageDraw.Draw(frame, 'RGBA')
        
        # 1. Category Pill Badge at Top
        badge_bbox = font_badge.getbbox(badge_text)
        b_w = (badge_bbox[2] - badge_bbox[0]) + 60
        b_h = 64
        b_x = (w - b_w) // 2
        b_y = 130
        draw.rounded_rectangle([b_x, b_y, b_x + b_w, b_y + b_h], radius=32, fill=(*b_color, 240))
        draw.text((b_x + 30, b_y + 10), badge_text, font=font_badge, fill=(255, 255, 255, 255))
        
        # 2. Main Title Headline with Glow & Drop Shadow
        title_bbox = font_title.getbbox(title_text)
        t_w = title_bbox[2] - title_bbox[0]
        t_x = (w - t_w) // 2
        t_y = 225
        
        # Drop shadow
        for offset in [(3, 3), (-3, -3), (3, -3), (-3, 3)]:
            draw.text((t_x + offset[0], t_y + offset[1]), title_text, font=font_title, fill=(0, 0, 0, 200))
        draw.text((t_x, t_y), title_text, font=font_title, fill=(255, 230, 0, 255))
        
        # 3. Dynamic Subtitles with Highlight
        current_sub = sub1 if progress < 0.52 else sub2
        sub_bbox = font_sub.getbbox(current_sub)
        sub_w = (sub_bbox[2] - sub_bbox[0]) + 64
        sub_h = 92
        sub_x = (w - sub_w) // 2
        sub_y = h - 380
        
        # Backdrop container
        draw.rounded_rectangle([sub_x, sub_y, sub_x + sub_w, sub_y + sub_h], radius=26, fill=(15, 23, 42, 240))
        draw.rounded_rectangle([sub_x, sub_y, sub_x + sub_w, sub_y + sub_h], radius=26, outline=(255, 215, 0, 230), width=4)
        
        # Subtitle Text
        sub_text_x = sub_x + 32
        sub_text_y = sub_y + 19
        draw.text((sub_text_x, sub_text_y), current_sub, font=font_sub, fill=(255, 255, 255, 255))
        
        # 4. Animated Progress Bar
        line_w = int(w * progress)
        draw.rectangle([0, h - 20, line_w, h], fill=(236, 72, 153, 255))
        
        try:
            proc.stdin.write(frame.tobytes())
        except (BrokenPipeError, OSError):
            break
            
        if (i + 1) % 60 == 0 or i == total_frames - 1:
            print(f"  Frame {i+1}/{total_frames} ({int((i+1)/total_frames*100)}%)")
            
    try:
        proc.stdin.close()
    except Exception:
        pass
    proc.wait()
    print(f"Done clip: {out_path} ({os.path.getsize(out_path):,} bytes)")

def assemble_master_video():
    with open('configs/scenes_config.json', 'r', encoding='utf-8') as f:
        scenes = json.load(f)
        
    os.makedirs('temp_clips', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    
    # 1. Render all clips
    clip_files = []
    for s in scenes:
        clip_path = f"temp_clips/{s['id']}.mp4"
        render_scene_clip(s, clip_path)
        clip_files.append(clip_path)
        
    # 2. Create ffmpeg concat list
    concat_list_path = "temp_clips/concat_list.txt"
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for cf in clip_files:
            abs_p = os.path.abspath(cf).replace('\\', '/')
            f.write(f"file '{abs_p}'\n")
            
    # Concatenate video clips
    concat_video_path = "temp_clips/concat_raw.mp4"
    cmd_concat = [
        ffmpeg_exe,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        concat_video_path
    ]
    print("\n>>> Concatenating all scenes...")
    subprocess.run(cmd_concat, check=True)
    
    # 3. Add background music with auto ducking and fade out
    final_output = "output/KOC_AI_Tai_Nghe_Viral_Review.mp4"
    bgm_path = "assets/audio/bgm.mp3"
    
    # Get total duration of concat video
    res = subprocess.run([ffmpeg_exe, "-i", concat_video_path], stderr=subprocess.PIPE, text=True)
    import re
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", res.stderr)
    total_dur = 46.0
    if m:
        total_dur = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
        
    fade_start = max(0, total_dur - 2.5)
    
    print(f"\n>>> Final Master Export (Duration: {total_dur:.2f}s)...")
    
    # Filter complex to mix voiceover from video with ducked BGM
    # [1:a] volume=0.14, afade=t=out:st={fade_start}:d=2.5 [bgm];
    # [0:a][bgm] amix=inputs=2:duration=first:dropout_transition=2 [aout]
    filter_complex = f"[1:a]volume=0.14,afade=t=out:st={fade_start:.2f}:d=2.5[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    
    cmd_mix = [
        ffmpeg_exe,
        "-y",
        "-i", concat_video_path,
        "-i", bgm_path,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(total_dur),
        final_output
    ]
    subprocess.run(cmd_mix, check=True)
    
    print("\n" + "="*60)
    print("SUCCESS: Master KOC AI Video Created!")
    print(f"Path: {os.path.abspath(final_output)}")
    print(f"Size: {os.path.getsize(final_output):,} bytes")
    print("="*60)

if __name__ == '__main__':
    assemble_master_video()
