"""Tạo video mẫu 3 cảnh (đỏ, xanh lá, xanh dương, mỗi cảnh 3s) bằng ffmpeg lavfi để thử scene-cut.
Dùng: python make_sample.py <ffmpeg.exe> <out.mp4>"""
import subprocess
import sys

ffmpeg, out = sys.argv[1], sys.argv[2]
args = [ffmpeg, "-y", "-v", "error"]
for color in ("red", "green", "blue"):
    args += ["-f", "lavfi", "-i", f"color=c={color}:s=640x360:r=30:d=3"]
args += ["-filter_complex", "[0][1][2]concat=n=3:v=1:a=0[v]", "-map", "[v]", "-pix_fmt", "yuv420p", out]
subprocess.run(args, check=True)
print(out)
