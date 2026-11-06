from __future__ import annotations

import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from socnhotv.intelligence.compliance import check_and_clean_script
from socnhotv.intelligence.products import Product
from socnhotv.intelligence.script_gen import (
    generate_affiliate_compare_script,
    generate_koc_review_script,
    generate_tiktok_sales_script,
)
from socnhotv.video.craft.camera import parse_camera_move
from socnhotv.video.craft.depth import enrich_3layer_prompt
from socnhotv.video.craft.hooks import score_hook
from socnhotv.video.short_form.cost import estimate_short_video_cost
from socnhotv.video.short_form.types import (
    ShortVideoConfig,
    ShortVideoResult,
    ShortVideoShot,
    slugify,
)

logger = logging.getLogger(__name__)


def _extract_product_from_prompt(prompt: str) -> Product:
    """Tự động phân tích prompt ý tưởng của người dùng thành đối tượng Product hợp lệ."""
    clean_p = prompt.strip()
    words = clean_p.split()

    # Nhận diện tên chủ đề/sản phẩm
    title = clean_p
    if len(words) > 10:
        title = " ".join(words[:8]) + "..."

    usp = []
    pain_points = []

    # Khám phá các từ khoá điểm nhấn hoặc khó khăn trong prompt
    lower_p = clean_p.lower()
    if any(k in lower_p for k in ["hạt dẻ", "rừng", "cây", "món ăn", "bánh", "kẹo"]):
        usp = ["hương vị thơm bùi tuyệt hảo", "dinh dưỡng tự nhiên từ rừng xanh"]
        pain_points = ["tìm kiếm món ăn vặt lành mạnh", "mệt mỏi sau ngày dài khám phá"]
    elif any(k in lower_p for k in ["áo", "váy", "đầm", "thời trang", "giày"]):
        usp = ["chất liệu cao cấp thoáng mát", "tôn dáng thanh lịch và hiện đại"]
        pain_points = ["khó chọn đồ phù hợp đi chơi và đi làm"]
    elif any(k in lower_p for k in ["sách", "truyện", "học", "bài học", "chia sẻ"]):
        usp = ["bài học ý nghĩa sâu sắc", "hình ảnh minh họa sống động trực quan"]
        pain_points = ["tìm phương pháp rèn luyện thói quen tốt cho trẻ"]
    else:
        usp = ["thiết kế thông minh và tinh tế", "chất lượng vượt trội so với phân khúc"]
        pain_points = ["những bất tiện thường nhật chưa có giải pháp ưng ý"]

    product_id = slugify(title)[:32] or "san-pham-doc-dao"
    return Product(
        id=product_id,
        name=title,
        brand="SocNhoTV",
        usp=usp,
        pain_points=pain_points,
        price=99000.0,
        currency="VND",
    )


def _determine_shot_count(target_duration_sec: float) -> int:
    """Xác định số shot (từ 4 đến 10 shot) dựa trên thời lượng yêu cầu 30–90s."""
    # 30s: 4–5 shot (~6-7s/shot)
    # 45s: 5–6 shot (~7-8s/shot)
    # 60s: 6–8 shot (~7-8s/shot)
    # 90s: 8–10 shot (~9s/shot)
    if target_duration_sec <= 35.0:
        return 5
    elif target_duration_sec <= 50.0:
        return 6
    elif target_duration_sec <= 70.0:
        return 7
    else:
        return 9


def _assign_camera_presets(shot_index: int, total_shots: int, role: str) -> str:
    """Gán chuyển động camera GSAP chuẩn điện ảnh từ video-craft camera.py."""
    if shot_index == 0:
        return "push-in"      # Hook mở đầu: đẩy nhẹ thu hút thị giác
    elif shot_index == 1:
        return "pan-left"     # Vấn đề: lia ngang tạo cảm giác băn khoăn
    elif shot_index == total_shots - 1:
        return "push-in"      # CTA kết: cận cảnh chốt hạ kêu gọi hành động
    elif role in ("demo", "solution", "discovery"):
        return "dolly-out"    # Trưng bày/khám phá: mở rộng góc nhìn
    elif role in ("proof", "detail", "compare"):
        return "ken-burns"    # Bằng chứng/so sánh: trôi chuyển động chậm
    else:
        # Xoay vòng các preset camera đã kiểm định trong camera.py
        rot = ["tilt-up", "pan-right", "ken-burns", "dolly-out"]
        return rot[shot_index % len(rot)]


def generate_short_video_script(config: ShortVideoConfig) -> ShortVideoResult:
    """Sinh kịch bản video ngắn 30–90 giây từ 1 prompt duy nhất.
    
    Quy trình tuân thủ triệt để:
    1. Gọi script_gen.py (không sửa đổi tệp gốc)
    2. Chạy compliance filter làm sạch ngôn từ
    3. Đánh giá Hook 3 giây đầu qua craft.hooks
    4. Mở rộng/phân bổ thành 4–10 shots đạt đúng thời lượng target_duration_sec
    5. Tạo prompt 3 tầng (Tiền cảnh - Nhân vật DNA - Hậu cảnh) qua craft.depth
    6. Gán camera moves điện ảnh từ craft.camera
    7. Ước tính chi phí theo SpendGuard (0$ cho chế độ ảnh tĩnh)
    """
    product = _extract_product_from_prompt(config.prompt)

    # 1. Gọi intelligence/script_gen.py
    if config.generator_type == "tiktok_sales":
        raw_lines = generate_tiktok_sales_script(product)
    elif config.generator_type == "affiliate_compare":
        raw_lines = generate_affiliate_compare_script([product])
    else:
        raw_lines = generate_koc_review_script(product, character_name=config.character_name)

    # 2. Làm sạch ngôn từ qua compliance filter
    cleaned_lines = []
    for l in raw_lines:
        res = check_and_clean_script(l["text"], is_affiliate=False)
        cleaned_lines.append({
            "role": l["role"],
            "duration_s": float(l.get("duration_s", 5.0)),
            "text": res.modified_text,
        })

    # 3. Đánh giá và tối ưu Hook 3 giây đầu
    hook_score = score_hook(cleaned_lines[0]["text"])
    if hook_score.has_greeting_penalty:
        # Loại bỏ lời chào rườm rà để giữ chân 3s đầu
        cleaned_lines[0]["text"] = re.sub(
            r"^(xin\s+)?chào(\s+cả\s+nhà|\s+mọi\s+người|\s+các\s+bạn)?[,!.\s]*",
            "",
            cleaned_lines[0]["text"],
            flags=re.IGNORECASE,
        ).strip()
        if not cleaned_lines[0]["text"].startswith(("Đừng", "Bí mật", "Sự thật", "Bạn có biết")):
            cleaned_lines[0]["text"] = f"Bí mật đây: {cleaned_lines[0]['text']}"

    target_shot_count = _determine_shot_count(config.target_duration_sec)

    # 4. Mở rộng/ghép các shot thành đúng target_shot_count
    roles_sequence = []
    if target_shot_count == 5:
        roles_sequence = ["hook", "problem", "demo", "proof", "cta"]
    elif target_shot_count == 6:
        roles_sequence = ["hook", "problem", "solution", "demo", "proof", "cta"]
    elif target_shot_count == 7:
        roles_sequence = ["hook", "problem", "agitate", "solution", "demo", "proof", "cta"]
    elif target_shot_count == 8:
        roles_sequence = ["hook", "problem", "agitate", "solution", "demo", "review", "proof", "cta"]
    else:  # 9-10
        roles_sequence = ["hook", "problem", "agitate", "context", "solution", "demo", "review", "proof", "cta"]

    # Xây dựng danh sách kịch bản shot với nội dung tương ứng
    base_text_by_role = {item["role"]: item["text"] for item in cleaned_lines}
    usp_primary = product.usp[0] if product.usp else "trải nghiệm tuyệt hảo"

    expanded_shots_data: List[Tuple[str, str, str]] = []  # (role, title, text)
    for r in roles_sequence:
        if r in base_text_by_role:
            txt = base_text_by_role[r]
            title = f"Phân đoạn {r.upper()}"
        elif r == "agitate":
            txt = f"Nếu không biết điều này sớm, {config.character_name} và các bạn nhỏ sẽ bỏ lỡ những khoảnh khắc quý giá nhất!"
            title = "Điểm nghẽn cần tháo gỡ"
        elif r == "solution":
            txt = f"Và đây chính là giải pháp mà {config.character_name} khám phá ra: {product.name} với {usp_primary}!"
            title = "Khám phá giải pháp"
        elif r == "context":
            txt = f"Cùng theo chân {config.character_name} quan sát kỹ từng chi tiết dưới ánh nắng sớm nhé!"
            title = "Bối cảnh mở rộng"
        elif r == "review":
            txt = f"Cảm giác thực tế khi trải nghiệm vô cùng dễ chịu và chắc chắn, đúng như kỳ vọng!"
            title = "Đánh giá chi tiết"
        else:
            txt = f"Hãy đồng hành cùng {config.character_name} để đón nhận thêm nhiều điều thú vị mỗi ngày nha!"
            title = "Thông điệp hành động"
        expanded_shots_data.append((r, title, txt))

    # Cân chỉnh thời lượng từng shot sao cho tổng thời lượng đúng target_duration_sec
    shot_durations = []
    total_shots = len(expanded_shots_data)
    dur_per_shot = round(config.target_duration_sec / total_shots, 1)
    
    # Tạo nhịp điệu sinh động: Shot đầu (Hook) ngắn hơn (~3.5-4s), Shot demo dài hơn
    for i, (r, _, _) in enumerate(expanded_shots_data):
        if r == "hook":
            shot_durations.append(max(3.0, min(4.0, dur_per_shot - 1.0)))
        elif r in ("demo", "solution"):
            shot_durations.append(dur_per_shot + 1.2)
        elif r == "cta":
            shot_durations.append(max(3.5, dur_per_shot - 0.5))
        else:
            shot_durations.append(dur_per_shot)

    # Chuẩn hoá tổng chính xác
    current_sum = sum(shot_durations)
    diff = round(config.target_duration_sec - current_sum, 1)
    if diff != 0 and shot_durations:
        shot_durations[-1] = round(shot_durations[-1] + diff, 1)

    # 5. Xây dựng từng Shot với Depth 3-layer & Camera presets
    shots: List[ShortVideoShot] = []
    scenes: List[Dict[str, Any]] = []
    lines: List[Dict[str, Any]] = []
    raw_script_blocks: List[str] = []

    char_key = config.character_id if config.character_id in ("soc_nho", "koala", "gobi_koc") else "soc_nho"
    env_key = config.environment if config.environment in ("forest", "rainbow_sky", "studio_indoor") else "forest"

    for idx, ((role, title, text), dur) in enumerate(zip(expanded_shots_data, shot_durations), start=1):
        shot_id = f"S{idx:02d}"
        cam_preset = _assign_camera_presets(idx - 1, total_shots, role)

        # Mô tả hành động theo vai trò của shot
        if role == "hook":
            action_desc = f"{config.character_name} ngạc nhiên mở to mắt nhìn thẳng vào ống kính máy quay, biểu cảm hào hứng hé lộ bí mật"
        elif role in ("problem", "agitate"):
            action_desc = f"{config.character_name} đứng suy tư gãi đầu, biểu cảm băn khoăn tìm cách giải quyết vấn đề"
        elif role in ("demo", "solution"):
            action_desc = f"{config.character_name} vui sướng cầm trên tay {product.name}, khoe điểm nổi bật {usp_primary} dưới ánh nắng ấm"
        elif role in ("proof", "review"):
            action_desc = f"{config.character_name} mỉm cười gật gù hài lòng, giơ ngón tay cái chấm điểm tuyệt đối"
        else:
            action_desc = f"{config.character_name} tươi cười vẫy tay chào khán giả, chỉ tay về phía góc dưới màn hình kêu gọi tương tác"

        # Sinh prompt 3 tầng từ video-craft depth.py
        depth_prompt_res = enrich_3layer_prompt(
            action_or_core=action_desc,
            character_key=char_key,
            environment_key=env_key,
        )
        image_prompt = depth_prompt_res.combined_prompt
        video_prompt = f"Camera {cam_preset} mượt mà theo chuẩn 9:16 TikTok, diễn hoạt tự nhiên sinh động cho {action_desc}"

        dialogue_line = f"{config.character_name}: {text}"

        shot_obj = ShortVideoShot(
            shot_id=shot_id,
            scene_number=idx,
            title=f"{shot_id}: {title}",
            role=role,
            speaker=config.character_name,
            speaker_id=config.character_id,
            dialogue=text,
            duration_sec=dur,
            image_prompt=image_prompt,
            video_prompt=video_prompt,
            camera=cam_preset,
            safe_zone="tiktok_9_16" if config.aspect_ratio == "9:16" else "standard_16_9",
        )
        shots.append(shot_obj)

        scenes.append({
            "sceneNumber": idx,
            "shotId": shot_id,
            "title": f"{shot_id}: {title}",
            "imagePrompt": image_prompt,
            "videoPrompt": video_prompt,
            "dialogue": dialogue_line,
            "speaker": config.character_name,
            "speakerId": config.character_id,
            "characterIds": [config.character_id],
            "durationSec": dur,
            "camera": cam_preset,
            "safeZone": shot_obj.safe_zone,
        })

        lines.append({
            "id": f"c{idx}-1",
            "order": idx - 1,
            "speaker": config.character_name,
            "characterId": config.character_id,
            "text": text,
            "durationSec": dur,
            "shotId": shot_id,
        })

        raw_script_blocks.append(
            f"Cảnh {idx}: {title}\n"
            f"(Camera: {cam_preset})\n"
            f"Hình ảnh: {image_prompt}\n"
            f"{dialogue_line}\n"
        )

    raw_script_text = "\n".join(raw_script_blocks)

    # 6. Ước tính chi phí
    cost_info = estimate_short_video_cost(
        mode=config.mode,
        shot_count=len(shots),
        duration_sec=config.target_duration_sec,
        video_model=config.video_model,
        image_model=config.image_model,
        max_clips=config.max_clips,
    )

    return ShortVideoResult(
        config=config,
        shots=shots,
        scenes=scenes,
        lines=lines,
        raw_script=raw_script_text,
        total_duration_sec=sum(s.duration_sec for s in shots),
        shot_count=len(shots),
        cost_estimate=cost_info,
    )
