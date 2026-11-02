"""
GOBI SOCIAL - VIDEO TYPE CLASSIFIER (TẦNG 2: SERVICES - MEDIA)
===============================================================
Phân loại video tham khảo: "talking_head" (KOC nói trực diện, cần kịch bản +
ghép ảnh Gô Bi) hay "product_only" (chỉ khoe sản phẩm, lookbook/outfit đi dạo,
không nói trực diện — chỉ cần edit tối giản, giữ nguyên hình ảnh/âm thanh gốc).

Đây là heuristic cục bộ (không gọi cloud), có thể sai ở các ca khó (vd: mặt
nghiêng liên tục, giọng nói lẫn nhạc to). Dùng --force-type ở CLI để ghi đè
khi cần.
"""

from pathlib import Path
from typing import Any, Dict

import cv2

# Ngưỡng phân loại — điều chỉnh tại đây nếu test thực tế cho kết quả sai nhiều
FACE_PRESENCE_RATIO_THRESHOLD = 0.5   # >= 50% frame mẫu phải có mặt
FACE_AREA_RATIO_THRESHOLD = 0.01      # mặt phải chiếm >= 1% diện tích khung hình (đủ gần, không phải người nền xa)
# [Hiệu chỉnh thực tế] Video "nói trực diện" dạng medium-shot 9:16 thường chỉ ~0.015-0.03,
# không phải cận mặt sát — ngưỡng quá cao (0.03) sẽ phân loại nhầm sang product_only.
MIN_TRANSCRIPT_LENGTH = 20            # ký tự — transcript quá ngắn coi như không có lời thoại thật

FACE_DETECT_PROVIDERS = ["CoreMLExecutionProvider", "CPUExecutionProvider"]


def _sample_frame_indices(total_frames: int, num_samples: int = 8) -> list[int]:
    if total_frames <= num_samples:
        return list(range(max(total_frames, 1)))
    step = total_frames / num_samples
    return [int(i * step) for i in range(num_samples)]


def classify_reference_video(video_path: Path, transcript: str = "") -> Dict[str, Any]:
    """
    Lấy mẫu ~8 frame cách đều trong video, chạy InsightFace để đo tỉ lệ
    frame có mặt + tỉ lệ diện tích mặt/khung hình, kết hợp với độ dài
    transcript để phân loại video_type.
    """
    import insightface
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(name="buffalo_l", providers=FACE_DETECT_PROVIDERS)
    app.prepare(ctx_id=0, det_size=(320, 320))

    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1
    frame_area = frame_w * frame_h

    indices = _sample_frame_indices(total_frames)
    frames_with_face = 0
    face_area_ratios = []

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        faces = app.get(frame)
        if faces:
            frames_with_face += 1
            largest = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            face_area = (largest.bbox[2] - largest.bbox[0]) * (largest.bbox[3] - largest.bbox[1])
            face_area_ratios.append(face_area / frame_area)

    cap.release()

    num_sampled = len(indices) if indices else 1
    face_presence_ratio = frames_with_face / num_sampled
    avg_face_area_ratio = float(sum(face_area_ratios) / len(face_area_ratios)) if face_area_ratios else 0.0
    has_speech = len(transcript.strip()) >= MIN_TRANSCRIPT_LENGTH

    is_talking_head = (
        face_presence_ratio >= FACE_PRESENCE_RATIO_THRESHOLD
        and avg_face_area_ratio >= FACE_AREA_RATIO_THRESHOLD
        and has_speech
    )

    return {
        "video_type": "talking_head" if is_talking_head else "product_only",
        "face_presence_ratio": round(face_presence_ratio, 3),
        "avg_face_area_ratio": round(avg_face_area_ratio, 4),
        "has_speech": has_speech,
    }
