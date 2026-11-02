import os
import sys
import subprocess
import imageio_ffmpeg

sys.stdout.reconfigure(encoding="utf-8")
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

OUTPUT_DIR = os.path.abspath(r"assets/samples/sample_video/output")
INPUT_VIDEO = os.path.join(OUTPUT_DIR, "koc_model_real_ai_motion.mp4")
FINAL_TIKTOK_VIDEO = os.path.join(OUTPUT_DIR, "koc_model_tiktok_9_16_subtitled.mp4")

# Tạo file phụ đề SRT khớp với từng động tác của mẫu
# 00:00 -> 00:03: Mẫu xoay người tạo dáng khoe váy trắng
# 00:03 -> 00:06: Mẫu quay lại cười tươi, vuốt tóc
# 00:06 -> 00:09: Mẫu bước nhẹ, mỉm cười chốt dáng
SRT_CONTENT = """1
00:00:00,000 --> 00:00:03,000
Chiếc đầm trắng tiểu thư diện đi tiệc cực sang

2
00:00:03,000 --> 00:00:06,000
Chất lụa mềm mát, tôn dáng và cực kỳ hack tuổi

3
00:00:06,000 --> 00:00:09,500
Săn ngay ở góc trái giỏ hàng để nhận giá ưu đãi nha!
"""

srt_file = os.path.join(OUTPUT_DIR, "koc_subs.srt")
with open(srt_file, "w", encoding="utf-8") as f:
    f.write(SRT_CONTENT)

# Cắt crop video về chuẩn 9:16 (1080x1920) ở giữa và gắn phụ đề vàng viền đen chuẩn TikTok
escaped_srt = srt_file.replace("\\", "/").replace(":", "\\:")
style = (
    "FontName=Arial,"
    "FontSize=12,"
    "PrimaryColour=&H0000F5FF,"
    "OutlineColour=&H00000000,"
    "Bold=1,"
    "BorderStyle=1,"
    "Outline=2.5,"
    "Shadow=1.5,"
    "Alignment=2,"
    "MarginV=220"
)

# Filter: Crop 16:9 to 9:16 centered + Subtitles
vf_filter = (
    f"crop=ih*(9/16):ih:(iw-ih*(9/16))/2:0,"
    f"scale=1080:1920,"
    f"subtitles='{escaped_srt}':force_style='{style}'"
)

cmd = [
    ffmpeg, "-y",
    "-i", INPUT_VIDEO,
    "-vf", vf_filter,
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-r", "30",
    FINAL_TIKTOK_VIDEO
]

print("Rendering final 9:16 TikTok KOC AI Video...")
res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
if res.returncode == 0:
    print(f"🎉 THÀNH CÔNG: {FINAL_TIKTOK_VIDEO} ({os.path.getsize(FINAL_TIKTOK_VIDEO)} bytes)")
else:
    print("FFmpeg error:", res.stderr[-400:])
