import os
import sys
import json
import math
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_DIR = os.path.join(PROJECT_ROOT, "assets", "samples", "sample_video")
IMAGES_DIR = os.path.join(SAMPLE_DIR, "images")
AUDIO_DIR = os.path.join(SAMPLE_DIR, "audio")
OUTPUT_DIR = os.path.join(SAMPLE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def build_video():
    """
    Tự động ghép 4 ảnh AI với file voiceover 19.6s tạo thành video MP4 1080x1920 chuẩn TikTok
    """
    print("="*60)
    print("🎬 VMAX AUTO VIDEO PIPELINE: BẮT ĐẦU DỰNG VIDEO MP4...")
    print("="*60)

    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"[+] Tìm thấy FFmpeg Engine: {ffmpeg_exe}")
    except ImportError:
        print("[!] Chưa có imageio_ffmpeg, vui lòng cài đặt.")
        return False

    audio_path = os.path.join(AUDIO_DIR, "cardigan_voiceover.mp3")
    if not os.path.exists(audio_path):
        print(f"[!] Không tìm thấy file audio: {audio_path}")
        return False

    # Tìm danh sách ảnh trong thư mục images
    supported_exts = (".png", ".jpg", ".jpeg", ".webp")
    image_files = [
        os.path.join(IMAGES_DIR, f) for f in os.listdir(IMAGES_DIR)
        if f.lower().endswith(supported_exts)
    ]
    image_files.sort()

    if not image_files:
        print(f"[!] Chưa có ảnh trong {IMAGES_DIR}. Chờ subagent tạo ảnh...")
        return False

    print(f"[+] Tìm thấy {len(image_files)} ảnh sản phẩm/người mẫu:")
    for img in image_files:
        print(f"  - {os.path.basename(img)}")

    # Tính thời lượng mỗi ảnh dựa trên độ dài audio (19.6s / số ảnh)
    import mutagen.mp3
    audio = mutagen.mp3.MP3(audio_path)
    total_duration = audio.info.length
    clip_duration = total_duration / len(image_files)
    print(f"[+] Tổng thời lượng: {total_duration:.2f}s | Mỗi ảnh hiển thị: {clip_duration:.2f}s")

    # Chuẩn hóa ảnh về đúng tỷ lệ dọc 1080x1920 (TikTok 9:16)
    TARGET_W, TARGET_H = 1080, 1920
    normalized_images = []
    
    for idx, img_path in enumerate(image_files):
        with Image.open(img_path) as im:
            im = im.convert("RGB")
            # Resize fit target aspect ratio
            w, h = im.size
            scale = max(TARGET_W / w, TARGET_H / h)
            new_w, new_h = int(w * scale), int(h * scale)
            im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Crop to center 1080x1920
            left = (new_w - TARGET_W) // 2
            top = (new_h - TARGET_H) // 2
            im_cropped = im_resized.crop((left, top, left + TARGET_W, top + TARGET_H))
            
            norm_path = os.path.join(OUTPUT_DIR, f"norm_scene_{idx+1}.jpg")
            im_cropped.save(norm_path, quality=95)
            normalized_images.append(norm_path)

    # Tạo file danh sách input cho FFmpeg concat
    concat_txt_path = os.path.join(OUTPUT_DIR, "concat_list.txt")
    with open(concat_txt_path, "w", encoding="utf-8") as f:
        for p in normalized_images:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
            f.write(f"duration {clip_duration:.3f}\n")
        # Lặp lại frame cuối theo quy tắc của FFmpeg concat demuxer
        f.write(f"file '{normalized_images[-1].replace(os.sep, '/')}'\n")

    output_video_path = os.path.join(OUTPUT_DIR, "cardigan_review_tiktok.mp4")

    # Lệnh FFmpeg ghép ảnh + audio thành video MP4 h264/aac
    import subprocess
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_video_path
    ]

    print("[*] Đang render video MP4 qua FFmpeg...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0 and os.path.exists(output_video_path):
        size_mb = os.path.getsize(output_video_path) / (1024 * 1024)
        print("="*60)
        print("🎉 XUẤT VIDEO TIKTOK THÀNH CÔNG 100%!")
        print(f"[*] Đường dẫn: {output_video_path}")
        print(f"[*] Kích thước: {size_mb:.2f} MB")
        print(f"[*] Thời lượng: {total_duration:.2f} giây")
        print(f"[*] Chuẩn: 1080x1920 (9:16) 30 FPS")
        print("="*60)
        return output_video_path
    else:
        print("[!] FFmpeg Error:", res.stderr[-500:])
        return False

if __name__ == "__main__":
    build_video()
