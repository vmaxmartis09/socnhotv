#!/usr/bin/env python3
"""1-Shot Demo Script for LipSync & Voice-Mouth Alignment (Luồng H5).

Tạo bản demo 1 shot hoàn chỉnh so sánh trước và sau khi áp dụng Narrative Alignment (Lựa chọn a).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Đảm bảo đường dẫn import socnhotv
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tool" / "src"))

from socnhotv.video.lipsync import (
    AlignmentMode,
    NarrativeAligner,
)


def make_demo_shot():
    input_video = Path("data/projects/soc-nho-tv/content/episodes/soc-nho-sau-rang/scenes/canh_01.mp4")
    input_audio = Path("data/projects/soc-nho-tv/content/episodes/soc-nho-sau-rang/voice_bi/canh_01.mp3")

    if not input_video.exists() or not input_audio.exists():
        print(f"Lỗi: Không tìm thấy tệp đầu vào ({input_video} hoặc {input_audio})")
        sys.exit(1)

    output_dir = Path("/tmp/socnhotv_h5")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "demo_canh_01_aligned.mp4"

    print("=" * 70)
    print("DEMO 1 SHOT: KHẮC PHỤC LỖI KHẨU HÌNH BẰNG NARRATIVE ALIGNMENT")
    print(f"Video gốc (Veo clip, mồm nhép tự do): {input_video}")
    print(f"Thoại OmniVoice (Giọng Sóc Bi chuẩn):  {input_audio}")
    print(f"Video đầu ra (Đã tắt tiếng gốc, đồng bộ): {output_file}")
    print("=" * 70)

    aligner = NarrativeAligner()
    result = aligner.align_shot(
        shot_id="canh_01_demo",
        video_path=input_video,
        audio_path=input_audio,
        output_path=output_file,
        mode=AlignmentMode.STRIP_ORIGINAL,
        audio_start_offset_sec=0.4,
    )

    if not result.success:
        print(f"Thất bại: {result.error_message}")
        sys.exit(1)

    print("\n[KẾT QUẢ THÀNH CÔNG]")
    print(f"- Thời gian xử lý: {result.execution_time_sec:.4f} giây")
    print(f"- Chi phí: ${result.cost_usd:.2f} ($0)")
    print(f"- Dung lượng file: {result.metadata.get('output_size_bytes', 0):,} bytes")

    # Kiểm tra với ffprobe
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=codec_name,width,height",
        "-of", "default=noprint_wrappers=1",
        str(output_file),
    ]
    probe = subprocess.run(cmd, capture_output=True, text=True, check=False)
    print("\n[THÔNG SỐ KỸ THUẬT KIỂM ĐỊNH BẰNG FFPROBE]")
    print(probe.stdout.strip())
    print("\nDemo 1 shot hoàn tất. Đạt chuẩn H5!")


if __name__ == "__main__":
    make_demo_shot()
