"""
Demo Concat Integration for VMAX TikTok Affiliate Video
Assembles the cardigan review scenes into a native Concat project (concat.json)
and demonstrates editor launching and timeline validation.
"""

import os
import sys
import json
import time

sys.stdout.reconfigure(encoding="utf-8")

import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "src"))  # repo src/ -> gobi.*
from gobi.services.media.concat_bridge import (
    ConcatEngine,
    ConcatProjectBuilder,
    create_affiliate_tiktok_concat_project
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_DIR = os.path.join(PROJECT_ROOT, "assets", "samples", "sample_video")
IMAGES_DIR = os.path.join(SAMPLE_DIR, "images")
AUDIO_DIR = os.path.join(SAMPLE_DIR, "audio")
CONCAT_PROJ_DIR = os.path.join(SAMPLE_DIR, "concat_project")

scenes = [
    {
        "img": os.path.join(IMAGES_DIR, "01_hook_model_cafe.jpg"),
        "sub": "Mấy bà đang tìm áo cardigan mặc đi học, đi làm vừa ấm vừa tôn dáng thì xem ngay em này nha!"
    },
    {
        "img": os.path.join(IMAGES_DIR, "02_texture_fabric_buttons.jpg"),
        "sub": "Chất len dệt kim mềm mịn, dày dặn mà không hề dặm ngứa."
    },
    {
        "img": os.path.join(IMAGES_DIR, "03_fullbody_korean_ootd.jpg"),
        "sub": "Form rộng chuẩn Hàn Quốc giấu dáng cực đỉnh, phối chân váy hay quần suông đều xinh xỉu."
    },
    {
        "img": os.path.join(IMAGES_DIR, "04_cta_pointing_cart.jpg"),
        "sub": "Giá đang sale hời dưới 100 cành ở giỏ hàng góc trái, săn ngay kẻo hết nha!"
    }
]

audio_path = os.path.join(AUDIO_DIR, "cardigan_voiceover.mp3")

def run():
    print("==================================================")
    print("🚀 VMAX VIDEO ENGINE: TÍCH HỢP CONCAT CHO AFFILIATE")
    print("==================================================")
    
    engine = ConcatEngine()
    print(f"[*] Concat binary: {engine.concat_exe}")
    print(f"[*] Concat sẵn sàng: {engine.is_available()}")
    
    print("\n[*] 1. Đang tự động dựng Timeline TikTok 9:16 (1080x1920)...")
    project_file = create_affiliate_tiktok_concat_project(
        scenes=scenes,
        audio_path=audio_path,
        output_project_dir=CONCAT_PROJ_DIR
    )
    print(f"[+] Dự án Concat đã được tạo thành công tại:\n    -> {project_file}")
    
    # Verify file content
    with open(project_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    timeline = data["timelines"][0]
    print(f"\n[*] Thông tin Timeline:")
    print(f"    - Tên Timeline: {timeline['name']}")
    print(f"    - Độ phân giải: {timeline['video']['width']}x{timeline['video']['height']} (Chuẩn TikTok 9:16)")
    print(f"    - Frame rate:   {timeline['video']['rate_num']} fps")
    print(f"    - Số lượng Track: {len(timeline['tracks'])} tracks (Visual, Audio, Subtitles)")
    print(f"    - Số lượng Clip:  {len(timeline['clips'])} clips")
    
    print("\n[*] 2. Danh sách các Clips trên Timeline:")
    for c in timeline["clips"]:
        kind = c["kind"]
        st = c["start"]
        dur = c["duration"]
        name = c["name"]
        print(f"    - [{kind.upper():6s}] {st:5.2f}s -> {st+dur:5.2f}s: {name}")

    print("\n[+] Hoàn thành cấu hình Timeline Concat tự động cho VMAX!")
    print("[*] Bạn có thể mở trực tiếp Concat để xem, kéo thả chỉnh sửa hoặc render video.")

if __name__ == "__main__":
    run()
