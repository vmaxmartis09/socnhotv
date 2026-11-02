import os
import sys
import subprocess
import imageio_ffmpeg

sys.stdout.reconfigure(encoding="utf-8")

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_DIR = os.path.join(PROJECT_ROOT, "assets", "samples", "sample_video")
OUTPUT_DIR = os.path.join(SAMPLE_DIR, "output")
AUDIO_DIR = os.path.join(SAMPLE_DIR, "audio")

raw_video = os.path.join(OUTPUT_DIR, "motion_video_raw.mp4")
audio_path = os.path.join(AUDIO_DIR, "cardigan_voiceover.mp3")

# Chia nhỏ phụ đề theo nhịp nói (mỗi đoạn 2 - 2.5 giây) chuẩn style TikTok
subtitles = [
    # Cảnh 1 (0.0s - 4.9s)
    {"start": "00:00:00,000", "end": "00:00:02,400", "text": "Mấy bà tìm cardigan mặc đi học, đi làm"},
    {"start": "00:00:02,400", "end": "00:00:04,900", "text": "Vừa ấm vừa tôn dáng thì xem ngay nha!"},
    # Cảnh 2 (4.9s - 9.8s)
    {"start": "00:00:04,900", "end": "00:00:07,300", "text": "Chất len dệt kim mềm mịn, dày dặn"},
    {"start": "00:00:07,300", "end": "00:00:09,800", "text": "Đặc biệt không hề dặm ngứa chút nào"},
    # Cảnh 3 (9.8s - 14.7s)
    {"start": "00:00:09,800", "end": "00:00:12,300", "text": "Form rộng chuẩn Hàn Quốc giấu dáng cực đỉnh"},
    {"start": "00:00:12,300", "end": "00:00:14,700", "text": "Phối chân váy hay quần suông đều xinh xỉu"},
    # Cảnh 4 (14.7s - 19.6s)
    {"start": "00:00:14,700", "end": "00:00:17,200", "text": "Giá đang sale hời dưới 100 cành"},
    {"start": "00:00:17,200", "end": "00:00:19,630", "text": "Ở giỏ hàng góc trái, săn ngay kẻo hết nha!"}
]

srt_path = os.path.join(OUTPUT_DIR, "tiktok_styled_subs.srt")
with open(srt_path, "w", encoding="utf-8") as f:
    for idx, s in enumerate(subtitles):
        f.write(f"{idx+1}\n")
        f.write(f"{s['start']} --> {s['end']}\n")
        f.write(f"{s['text']}\n\n")

# Định dạng phụ đề chuẩn CapCut: Font to rõ ràng (size 11-13 pt tương đương ~65px), chữ vàng hoặc trắng viền đen đậm, đặt ở 1/4 phía dưới (MarginV=260)
escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")
# PrimaryColour=&H0000FFFF (Màu vàng rực TikTok) hoặc &H00FFFFFF (Trắng)
# OutlineColour=&H00000000 (Đen)
style = (
    "FontName=Arial,"
    "FontSize=12,"
    "PrimaryColour=&H0000F5FF,"  # Màu vàng nghệ sáng chuẩn TikTok
    "SecondaryColour=&H00000000,"
    "OutlineColour=&H00000000,"  # Viền đen dày rõ nét
    "BackColour=&H80000000,"
    "Bold=1,"
    "Italic=0,"
    "BorderStyle=1,"             # Outline + Shadow viền chữ, không che mặt
    "Outline=2.5,"
    "Shadow=1.5,"
    "Alignment=2,"               # Căn giữa phía dưới
    "MarginV=240"                # Cách đáy 240px (trên thanh giỏ hàng TikTok một chút)
)

final_video = os.path.join(OUTPUT_DIR, "review_cardigan_tiktok_chuan.mp4")

cmd = [
    ffmpeg_exe, "-y",
    "-i", raw_video,
    "-i", audio_path,
    "-vf", f"subtitles='{escaped_srt}':force_style='{style}'",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    final_video
]

print("Rendering video with CapCut-style subtitles...")
res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
if res.returncode == 0:
    print(f"🎉 HOÀN THÀNH VIDEO CHUẨN ĐẸP: {final_video}")
else:
    print("Error:", res.stderr[-500:])
