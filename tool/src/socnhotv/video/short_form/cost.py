from __future__ import annotations

from typing import Any, Dict


# Bảng giá chuẩn tham chiếu từ models.yaml & các nhà cung cấp
MODEL_COST_PER_SECOND = {
    "mock-video": 0.0,
    "fal-ltx-video": 0.05,
    "fal-kling-v3-std": 0.084,
    "google-veo-2": 0.15,
    "google-veo-3.1-fast": 0.40,
}


def estimate_short_video_cost(
    mode: str = "static",
    shot_count: int = 5,
    duration_sec: float = 30.0,
    video_model: str = "google-veo-2",
    image_model: str = "pollinations-flux",
    max_clips: int = 5,
) -> Dict[str, Any]:
    """Ước tính chi phí chi tiết theo quy tắc SpendGuard và Session H.
    
    Chế độ 'static' (ảnh tĩnh):
      - Ảnh: Nguồn miễn phí (Pollinations / local) = $0.00
      - Thoại: OmniVoice chạy trực tiếp trên máy = $0.00
      - Video AI: $0.00 (dùng ảnh tĩnh kết hợp GSAP camera motion)
      - Dựng: HyperFrames render nội bộ trên máy = $0.00
      - Tổng: $0.00 (Hoàn toàn miễn phí)
      
    Chế độ 'ai_clip' (clip AI qua video_gen perShot của G3):
      - Sinh tối đa `min(shot_count, max_clips)` clip AI
      - Đơn giá lấy theo model video (Veo / Kling / LTX)
      - Bắt buộc cảnh báo SpendGuard và xác nhận người dùng trước khi gọi API thật.
    """
    image_cost = 0.0  # pollinations-flux hoặc local $0
    voice_cost = 0.0  # OmniVoice trên máy $0
    render_cost = 0.0 # HyperFrames cục bộ $0

    if mode == "static":
        video_cost = 0.0
        total_cost = 0.0
        is_free = True
        spend_guard_required = False
        note = "Chế độ ảnh tĩnh: Miễn phí 100% ($0.00). Sử dụng ảnh keyframe, giọng OmniVoice và camera điện ảnh GSAP."
    else:
        # Chế độ clip AI
        clips_to_generate = min(shot_count, max_clips)
        # Giả định mỗi clip AI dài ~5 giây (chuẩn model Kling/Veo)
        clip_duration = min(6.0, duration_sec / max(1, shot_count))
        rate_per_sec = MODEL_COST_PER_SECOND.get(video_model, 0.15)
        video_cost = round(clips_to_generate * clip_duration * rate_per_sec, 3)
        total_cost = round(image_cost + voice_cost + video_cost + render_cost, 3)
        is_free = (total_cost == 0.0)
        spend_guard_required = not is_free
        note = (
            f"Chế độ clip AI: Ước tính ${total_cost:.2f} ({clips_to_generate} clips qua {video_model} @ ${rate_per_sec}/s). "
            "Bắt buộc qua SpendGuard và hỏi người dùng trước khi gọi API trả phí thật."
        )

    return {
        "mode": mode,
        "total_cost_usd": total_cost,
        "breakdown": {
            "image_cost_usd": image_cost,
            "voice_cost_usd": voice_cost,
            "video_ai_cost_usd": video_cost,
            "render_cost_usd": render_cost,
        },
        "is_free": is_free,
        "spend_guard_required": spend_guard_required,
        "video_model": video_model if mode == "ai_clip" else "none",
        "clips_count": min(shot_count, max_clips) if mode == "ai_clip" else 0,
        "note": note,
    }
