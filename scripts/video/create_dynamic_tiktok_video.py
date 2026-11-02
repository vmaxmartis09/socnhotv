"""
=============================================================================
VMAX AUTO AFFILIATE VIDEO GENERATOR
Tự động hóa 100% quy trình sản xuất video TikTok Affiliate.
Tích hợp trực tiếp VMaxVideoEngine & Concat Document Model.
Không dùng bất kỳ file .bat nào - Vận hành hoàn toàn bằng Python trong hệ sinh thái.
=============================================================================
"""

import os
import sys
import argparse

sys.stdout.reconfigure(encoding="utf-8")

import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "src"))  # repo src/ -> gobi.*
from gobi.services.media.video_engine import VMaxVideoEngine

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_DIR = os.path.join(PROJECT_ROOT, "assets", "samples", "sample_video")
IMAGES_DIR = os.path.join(SAMPLE_DIR, "images")
AUDIO_DIR = os.path.join(SAMPLE_DIR, "audio")
OUTPUT_DIR = os.path.join(SAMPLE_DIR, "output")

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


def main():
    parser = argparse.ArgumentParser(description="VMAX Autonomous Affiliate Video Generator")
    parser.add_argument("--preview", action="store_true", help="Tự động mở Concat Studio GUI để xem/chỉnh sửa")
    args = parser.parse_args()

    print("==================================================================")
    print("🚀 VMAX NATIVE VIDEO ENGINE: TỰ ĐỘNG HÓA SẢN XUẤT VIDEO AFFILIATE")
    print("==================================================================")
    
    engine = VMaxVideoEngine()
    print(f"[*] Concat Engine Status: {'Ready (Tích hợp cục bộ)' if engine.is_concat_available() else 'FFmpeg Render Only'}")
    print(f"[*] Thư mục đầu ra: {OUTPUT_DIR}")

    print("\n[1/3] Đang phân tích âm thanh & xây dựng Timeline Concat (concat.json)...")
    res = engine.auto_handle_affiliate_video(
        scenes=scenes,
        audio_path=audio_path,
        output_dir=OUTPUT_DIR,
        video_filename="cardigan_affiliate_auto.mp4",
        preview=args.preview
    )

    print("\n[2/3] Đã biên tập dự án Concat:")
    print(f"      -> {res['project_file']}")

    print("\n[3/3] Đã tự động render video TikTok hoàn chỉnh (9:16):")
    print(f"      -> {res['video_file']}")

    if "studio_preview" in res:
        print("\n[+] Đã tự động mở Concat Studio trực tiếp trên màn hình theo yêu cầu --preview.")
    else:
        print("\n[i] Video đã sẵn sàng tải lên TikTok Shop (không cần mở thêm công cụ nào).")
        print("    (Nếu muốn xem giao diện chỉnh sửa trên Concat Studio, thêm cờ: --preview)")

    print("\n🎉 HOÀN TẤT TỰ ĐỘNG 100% TRONG HỆ SINH THÁI PYTHON CỦA VMAX!")


if __name__ == "__main__":
    main()
