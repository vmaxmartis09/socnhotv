import os
import sys
import json
import asyncio
import subprocess
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import edge_tts

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

SCENES = [
    {
        "id": 1,
        "panel": os.path.join(PROJECT_ROOT, "assets", "samples", "sample_video", "koc_matrix_panels", "panel_03_can_mat_chinh_dien.jpg"),
        "text": "Thời tiết thu se lạnh thế này, đố các nàng tìm được set đồ nào xinh hơn set 2 dây kèm cardigan len mỏng này!",
        "subtitle": "ĐỐ CÁC NÀNG TÌM ĐƯỢC SET ĐỒ NÀY 🍂",
        "motion": "zoom_in"
    },
    {
        "id": 2,
        "panel": os.path.join(PROJECT_ROOT, "assets", "samples", "sample_video", "koc_matrix_panels", "panel_25_can_canh_chat_lieu.jpg"),
        "text": "Chất len dệt kim mềm mướt, thoáng khí, mặc vào cực kỳ tôn dáng và che trọn bắp tay luôn.",
        "subtitle": "CHẤT LEN DỆT KIM MỀM MƯỚT ✨",
        "motion": "pan_down"
    },
    {
        "id": 3,
        "panel": os.path.join(PROJECT_ROOT, "assets", "samples", "sample_video", "koc_matrix_panels", "panel_26_buoc_di_tu_nhien.jpg"),
        "text": "Đi làm, đi học hay đi cafe chụp hình thì chuẩn gu nàng thơ Hàn Quốc trong veo nha.",
        "subtitle": "CHUẨN GU NÀNG THƠ HÀN QUỐC ☕",
        "motion": "zoom_out"
    },
    {
        "id": 4,
        "panel": os.path.join(PROJECT_ROOT, "assets", "samples", "sample_video", "koc_matrix_panels", "panel_02_chinh_dien_trung_canh.jpg"),
        "text": "Đang trợ giá chỉ 139 cành ở giỏ hàng góc trái! Nàng nào cần bộ câu lệnh AI tạo video này comment prom Gobi gửi ngay nha!",
        "subtitle": "SĂN DEAL 139K - COMMENT PROM NHẬN PROMPT 👇",
        "motion": "zoom_in"
    }
]

TEMP_DIR = os.path.join(PROJECT_ROOT, "output", "_build_temp")
OUTPUT_VIDEO = os.path.join(PROJECT_ROOT, "output", "koc_ai_google_flow_showcase.mp4")

async def generate_voiceovers():
    os.makedirs(TEMP_DIR, exist_ok=True)
    voice_files = []
    for sc in SCENES:
        v_path = os.path.join(TEMP_DIR, f"voice_{sc['id']}.mp3")
        clean_text = sc["text"].replace("'", "").replace('"', "").replace("&", " và ")
        for attempt in range(3):
            try:
                comm = edge_tts.Communicate(clean_text, "vi-VN-HoaiMyNeural", rate="+6%")
                await comm.save(v_path)
                break
            except Exception as e:
                if attempt == 2:
                    raise e
                await asyncio.sleep(1)
        voice_files.append(v_path)
        print(f"[+] Da tao voiceover canh {sc['id']}")
    return voice_files

def get_duration(file_path):
    cmd = [FFMPEG_EXE, "-i", file_path]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, errors="ignore")
    for line in res.stderr.splitlines():
        if "Duration" in line:
            try:
                t = line.split("Duration: ")[1].split(",")[0].strip()
                h, m, s = t.split(":")
                return float(h)*3600 + float(m)*60 + float(s)
            except Exception:
                pass
    return 5.0

def build_scene_clip(sc, duration, fps=30):
    clip_path = os.path.join(TEMP_DIR, f"clip_{sc['id']}.mp4")
    frames = int(duration * fps)
    
    # 1. Resize & Crop base image to 1080x1920
    im = Image.open(sc["panel"]).convert("RGB")
    tw, th = 1080, 1920
    w, h = im.size
    scale = max(tw / w, th / h)
    nw, nh = int(w * scale), int(h * scale)
    im_resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    base_img = im_resized.crop((left, top, left + tw, top + th))
    
    temp_img = os.path.join(TEMP_DIR, f"base_{sc['id']}.jpg")
    base_img.save(temp_img, quality=95)
    
    # 2. Camera filter (One-Move Rule)
    if sc["motion"] == "zoom_in":
        z_filter = f"zoompan=z='min(zoom+0.0012,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps={fps}"
    elif sc["motion"] == "pan_down":
        z_filter = f"zoompan=z='1.10':x='iw/2-(iw/zoom/2)':y='min(y+1.0,ih/2)':d={frames}:s=1080x1920:fps={fps}"
    elif sc["motion"] == "zoom_out":
        z_filter = f"zoompan=z='if(lte(zoom,1.0),1.12,max(1.001,zoom-0.0012))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps={fps}"
    else:
        z_filter = f"zoompan=z='min(zoom+0.0008,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps={fps}"
        
    cmd = [
        FFMPEG_EXE, "-y",
        "-loop", "1",
        "-i", temp_img,
        "-vf", z_filter,
        "-t", f"{duration:.3f}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        clip_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return clip_path

def main():
    print("=== BAT DAU QUY TRINH SAN XUAT VIDEO KOC AI THEO GOOGLE FLOW WORKFLOW ===")
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)
    
    # 1. Sinh Voiceover
    voice_files = asyncio.run(generate_voiceovers())
    
    durations = [get_duration(v) + 0.3 for v in voice_files] # Them 0.3s breath room
    total_dur = sum(durations)
    print(f"[*] Tong thoi luong video: {total_dur:.2f} giay")
    
    # 2. Render tung scene video
    clip_files = []
    for sc, d in zip(SCENES, durations):
        print(f"[*] Dang render Scene {sc['id']} (thoi luong {d:.2f}s, motion {sc['motion']})...")
        c = build_scene_clip(sc, d)
        clip_files.append(c)
        
    # 3. Ghep video thanh pham
    concat_txt = os.path.join(TEMP_DIR, "clips.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in clip_files:
            f.write(f"file '{c.replace(os.sep, '/')}'\n")
            
    visual_video = os.path.join(TEMP_DIR, "visual_assembled.mp4")
    subprocess.run([
        FFMPEG_EXE, "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_txt,
        "-c", "copy",
        visual_video
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 4. Ghep audio voiceover thanh 1 file
    audio_concat_txt = os.path.join(TEMP_DIR, "voices.txt")
    with open(audio_concat_txt, "w", encoding="utf-8") as f:
        for v in voice_files:
            f.write(f"file '{v.replace(os.sep, '/')}'\n")
            
    full_voice = os.path.join(TEMP_DIR, "full_voice.mp3")
    subprocess.run([
        FFMPEG_EXE, "-y",
        "-f", "concat", "-safe", "0",
        "-i", audio_concat_txt,
        "-c", "copy",
        full_voice
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 5. Tao Subtitle SRT voi Safe Zone
    srt_file = os.path.join(TEMP_DIR, "subtitles.srt")
    current_time = 0.0
    with open(srt_file, "w", encoding="utf-8") as f:
        for i, (sc, d) in enumerate(zip(SCENES, durations)):
            start_s = current_time
            end_s = current_time + d
            
            def fmt_time(sec):
                hrs = int(sec // 3600)
                mins = int((sec % 3600) // 60)
                secs = int(sec % 60)
                ms = int((sec - int(sec)) * 1000)
                return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"
                
            f.write(f"{i + 1}\n")
            f.write(f"{fmt_time(start_s)} --> {fmt_time(end_s)}\n")
            f.write(f"{sc['subtitle']}\n\n")
            current_time += d
            
    # 6. Mix Video + Voiceover + BGM + Subtitle Burn-in
    bgm_path = os.path.join(PROJECT_ROOT, "assets", "audio", "bgm.mp3")
    
    # Format Subtitle filter using relative path
    rel_srt = os.path.relpath(srt_file, PROJECT_ROOT).replace("\\", "/")
    sub_style = f"subtitles='{rel_srt}':force_style='FontName=Arial,FontSize=15,Bold=1,PrimaryColour=&H0000F5FF,BackColour=&H80000000,BorderStyle=4,Outline=2,Shadow=0,MarginV=120,Alignment=2'"
    
    print("[*] Dang mix am thanh, nhac nen ducking va burn-in phu de TikTok...")
    if os.path.exists(bgm_path):
        # Audio filter: duck bgm to 12% (-18dB)
        cmd_final = [
            FFMPEG_EXE, "-y",
            "-i", visual_video,
            "-i", full_voice,
            "-i", bgm_path,
            "-filter_complex",
            f"[0:v]{sub_style}[v];[2:a]volume=0.12[bgm];[1:a][bgm]amix=inputs=2:duration=first[a]",
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-shortest",
            OUTPUT_VIDEO
        ]
    else:
        cmd_final = [
            FFMPEG_EXE, "-y",
            "-i", visual_video,
            "-i", full_voice,
            "-vf", sub_style,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-shortest",
            OUTPUT_VIDEO
        ]
        
    subprocess.run(cmd_final, check=True)
    print(f"\n[SUCCESS] DA XUAT BAN VIDEO HOAN CHINH: {OUTPUT_VIDEO}")
    file_size = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
    print(f"[*] Dung luong file: {file_size:.2f} MB")

if __name__ == "__main__":
    main()
