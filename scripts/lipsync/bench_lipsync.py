#!/usr/bin/env python3
"""Benchmark and Feasibility Measurement Script for LipSync Options (Luồng H5).

Chạy đo lường thực tế trên môi trường Mac M4 16GB:
1. Đánh giá tất cả các lựa chọn (a, b, c).
2. Kiểm tra tính tương thích hình thái nhân vật 3D hoạt hình (Sóc Bi, Dê Mun).
3. Đo hiệu năng thực tế của Lựa chọn (a) Narrative Alignment trên clip và giọng thật.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Đảm bảo đường dẫn import socnhotv
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tool" / "src"))

from socnhotv.video.lipsync import (
    AlignmentMode,
    CharacterType,
    LipSyncEvaluator,
    NarrativeAligner,
    LIPSYNC_REGISTRY,
)


def run_benchmark():
    print("=" * 80)
    print("BÁO CÁO ĐO LƯỜNG & KHẢO SÁT CÁC LỰA CHỌN LIP-SYNC (LUỒNG H5)")
    print("Môi trường: Apple Silicon Mac M4, 16GB Unified Memory, macOS 15+")
    print("=" * 80)

    # 1. Bảng so sánh các công cụ
    print("\n1. BẢNG TỔNG HỢP CÁC LỰA CHỌN ĐÃ KHẢO SÁT:")
    print("-" * 105)
    print(f"{'Mã tool':<18} | {'Nhóm':<15} | {'Giá/phút (USD)':<14} | {'Phần cứng':<16} | {'Độ hợp 3D hoạt hình':<22} | {'Upload ảnh ngoài?'}")
    print("-" * 105)

    for tool in LIPSYNC_REGISTRY.values():
        comp = tool.character_compatibility.get(CharacterType.ANTHROPOMORPHIC_3D)
        comp_str = comp.value if comp else "N/A"
        upload_str = "CÓ (Vi phạm nếu chưa duyệt)" if tool.requires_external_upload else "KHÔNG ($0 Offline)"
        print(f"{tool.tool_id:<18} | {tool.category.value:<15} | ${tool.cost_per_minute_usd:<13.2f} | {tool.hardware.value:<16} | {comp_str:<22} | {upload_str}")

    print("-" * 105)

    # 2. Đo thật Lựa chọn (a) trên tệp thật
    video_real = Path("data/projects/soc-nho-tv/content/episodes/soc-nho-sau-rang/scenes/canh_01.mp4")
    audio_real = Path("data/projects/soc-nho-tv/content/episodes/soc-nho-sau-rang/voice_bi/canh_01.mp3")

    if not video_real.exists() or not audio_real.exists():
        print(f"\n[CẢNH BÁO] Không tìm thấy file thật ({video_real} hoặc {audio_real}) để đo thời gian.")
        return

    print("\n2. ĐO THẬT HIỆU NĂNG LỰA CHỌN (a) NARRATIVE ALIGNMENT:")
    temp_dir = Path("/tmp/socnhotv_h5")
    temp_dir.mkdir(parents=True, exist_ok=True)
    out_aligned = temp_dir / "bench_canh_01_aligned.mp4"

    aligner = NarrativeAligner()

    t0 = time.time()
    res = aligner.align_shot(
        shot_id="bench_canh_01",
        video_path=video_real,
        audio_path=audio_real,
        output_path=out_aligned,
        mode=AlignmentMode.STRIP_ORIGINAL,
        audio_start_offset_sec=0.4,
    )
    t1 = time.time()

    print(f"  - Trạng thái: {'THÀNH CÔNG' if res.success else 'THẤT BÀI'}")
    print(f"  - Thời gian xử lý: {res.execution_time_sec:.4f} giây")
    print(f"  - Chi phí tài chính: ${res.cost_usd:.2f}")
    print(f"  - Tệp kết quả: {res.output_video_path} ({res.metadata.get('output_size_bytes', 0):,} bytes)")
    print(f"  - Thời lượng video: {res.metadata.get('video_duration')}s | Thoại OmniVoice: {res.metadata.get('audio_duration')}s")
    print(f"  - Tốc độ xử lý: {res.metadata.get('video_duration', 8.0) / max(0.001, res.execution_time_sec):.1f}x Realtime")

    # 3. Kế hoạch đề xuất tối ưu
    print("\n3. KHUYẾN NGHỊ TỐI ƯU CỦA EVALUATOR:")
    plan = LipSyncEvaluator.recommend_plan(
        shot_id="canh_01",
        character_type=CharacterType.ANTHROPOMORPHIC_3D,
        audio_duration_sec=4.22,
        video_duration_sec=8.0,
        allow_paid=False,
        allow_external_upload=False,
    )
    print(f"  - Phương pháp được chọn: {plan.method.value} ({plan.tool_id})")
    print(f"  - Chi phí ước tính: ${plan.estimated_cost_usd:.2f}")
    print("  - Lý do:")
    for r in plan.reasons:
        print(f"    * {r}")


if __name__ == "__main__":
    run_benchmark()
