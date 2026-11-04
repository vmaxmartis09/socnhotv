from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, List, Literal, Optional

from socnhotv.intelligence.compliance import check_and_clean_script
from socnhotv.intelligence.contracts import ContentIdea, VideoBlueprint, save_content_idea
from socnhotv.intelligence.products import Product
from socnhotv.video.contracts import Platform, RenderRequest, VoiceSpec
from socnhotv.workspace import project_path

logger = logging.getLogger(__name__)

GeneratorType = Literal["koc_review", "tiktok_sales", "affiliate_compare"]


def generate_koc_review_script(
    product: Product,
    blueprint: Optional[VideoBlueprint] = None,
    character_name: str = "LyLy",
) -> List[Dict[str, Any]]:
    """Generate authentic KOC review script with pros + 1 honest con and rating."""
    usp_text = product.usp[0] if product.usp else "chất lượng vượt mong đợi"
    pain_text = product.pain_points[0] if product.pain_points else "tìm kiếm sản phẩm ưng ý"
    
    lines = [
        {
            "role": "hook",
            "duration_s": 3.5,
            "text": f"Đừng mua {product.name} nếu mọi người chưa nghe qua trải nghiệm thực tế này của {character_name} nha!",
        },
        {
            "role": "problem",
            "duration_s": 4.0,
            "text": f"Trước đây {character_name} cũng rất đau đầu vì {pain_text}, thử qua nhiều loại nhưng không ăn thua.",
        },
        {
            "role": "demo",
            "duration_s": 6.0,
            "text": f"Nhưng từ lúc đổi sang {product.name} của nhà {product.brand or 'này'}, điểm ưng ý nhất là {usp_text}.",
        },
        {
            "role": "proof",
            "duration_s": 5.0,
            "text": f"Tuy nhiên, có một điểm trừ nhỏ là sản phẩm quá hot nên thường xuyên hết màu đẹp. {character_name} chấm em này 9/10 nha!",
        },
        {
            "role": "cta",
            "duration_s": 4.0,
            "text": f"Giá đang được sale chỉ còn {product.price:,.0f}{product.currency}. Link chính hãng {character_name} gắn ngay góc trái giỏ hàng nhé!",
        },
    ]
    return lines


def generate_tiktok_sales_script(
    product: Product,
    blueprint: Optional[VideoBlueprint] = None,
) -> List[Dict[str, Any]]:
    """Generate high-conversion TikTok Shop sales script."""
    usp_text = ", ".join(product.usp[:2]) if product.usp else "công năng vượt trội"
    pain_text = product.pain_points[0] if product.pain_points else "sự bất tiện hàng ngày"

    lines = [
        {
            "role": "hook",
            "duration_s": 3.0,
            "text": f"Ai đang gặp tình trạng {pain_text} thì xem ngay video này nhé!",
        },
        {
            "role": "agitate",
            "duration_s": 4.0,
            "text": f"Chỉ với một thao tác đơn giản cùng {product.name}, mọi rắc rối đều được giải quyết gọn gàng.",
        },
        {
            "role": "demo",
            "duration_s": 6.0,
            "text": f"Cận cảnh chi tiết đây ạ: thiết kế thông minh, tích hợp {usp_text}.",
        },
        {
            "role": "offer",
            "duration_s": 4.0,
            "text": f"Đặc biệt hôm nay trên livestream giá ưu đãi chỉ {product.price:,.0f} {product.currency}.",
        },
        {
            "role": "cta",
            "duration_s": 4.0,
            "text": "Nhanh tay nhấn vào giỏ hàng màu vàng góc dưới màn hình để chốt deal ngay hôm nay!",
        },
    ]
    return lines


def generate_affiliate_compare_script(
    products: List[Product],
    blueprint: Optional[VideoBlueprint] = None,
) -> List[Dict[str, Any]]:
    """Generate product comparison script for affiliate commission."""
    p1 = products[0]
    p2 = products[1] if len(products) > 1 else products[0]

    lines = [
        {
            "role": "hook",
            "duration_s": 3.5,
            "text": f"So sánh thực tế: Nên chọn {p1.name} hay {p2.name} cho nhu cầu của bạn?",
        },
        {
            "role": "compare",
            "duration_s": 7.0,
            "text": f"Về thiết kế và tính năng: {p1.name} nổi bật với {p1.usp[0] if p1.usp else 'sự nhỏ gọn'}, còn {p2.name} lại tập trung vào {p2.usp[0] if p2.usp else 'độ bền cao'}.",
        },
        {
            "role": "proof",
            "duration_s": 5.0,
            "text": f"Nếu ưu tiên ngân sách vừa phải thì {p1.name} là lựa chọn số 1. Còn muốn cao cấp hơn thì chọn {p2.name}.",
        },
        {
            "role": "cta",
            "duration_s": 4.5,
            "text": "Cả hai sản phẩm chính hãng mình đều đã gắn link trong giỏ hàng và phần bio cho mọi người dễ chọn nha!",
        },
    ]
    return lines


def generate_complete_script(
    project_id: str,
    product: Product,
    generator_type: GeneratorType = "koc_review",
    blueprint: Optional[VideoBlueprint] = None,
    character_name: str = "LyLy",
    voice_id: str = "soc-nho",
    platforms: Optional[List[Platform]] = None,
) -> Dict[str, Any]:
    """Generate, compliance-clean, and package script + RenderRequest + ContentIdea."""
    target_platforms: List[Platform] = platforms or ["tiktok", "reels", "shorts"]
    script_id = f"script_{uuid.uuid4().hex[:10]}"

    # 1. Generate lines based on generator type
    if generator_type == "tiktok_sales":
        raw_lines = generate_tiktok_sales_script(product, blueprint)
        template_id = "tiktok-sales-v1"
    elif generator_type == "affiliate_compare":
        raw_lines = generate_affiliate_compare_script([product], blueprint)
        template_id = "affiliate-compare-v1"
    else:
        raw_lines = generate_koc_review_script(product, blueprint, character_name)
        template_id = "koc-review-v1"

    # 2. Run compliance filter on each line
    cleaned_lines = []
    all_warnings = []
    full_text_chunks = []

    for l in raw_lines:
        res = check_and_clean_script(l["text"], is_affiliate=False)
        cleaned_lines.append({
            "role": l["role"],
            "duration_s": l["duration_s"],
            "text": res.modified_text,
        })
        all_warnings.extend(res.warnings)
        full_text_chunks.append(res.modified_text)

    # 3. Add affiliate disclosure at the end
    full_copy = "\n".join(full_text_chunks)
    comp_full = check_and_clean_script(full_copy, is_affiliate=True)
    all_warnings.extend(comp_full.warnings)

    # 4. Save script to content/scripts/<script_id>.json
    script_file = project_path(project_id, "content", "scripts", f"{script_id}.json", ensure=True)
    with open(script_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_lines, f, ensure_ascii=False, indent=2)

    # 5. Create ContentIdea for Session C
    idea = ContentIdea(
        id=f"idea_{script_id}",
        project_id=project_id,
        title=f"Review {product.name} ({generator_type})",
        platform_targets=target_platforms,
        template_id=template_id,
        blueprint_ref=blueprint.id if blueprint else None,
        priority=1,
        status="scripted",
    )
    save_content_idea(project_id, idea)

    # 6. Package RenderRequest
    render_req = RenderRequest(
        project_id=project_id,
        template_id=template_id,
        platforms=target_platforms,
        data={
            "product_id": product.id,
            "product_name": product.name,
            "price": product.price,
            "currency": product.currency,
            "images": product.images,
            "script_id": script_id,
            "generator_type": generator_type,
            "character_name": character_name,
        },
        voice=VoiceSpec(voice_id=voice_id, script="\n".join([c["text"] for c in cleaned_lines])),
        source_ref=blueprint.source_ref if blueprint else None,
        output_name=f"prod_{product.id}_{generator_type}",
    )

    return {
        "script_id": script_id,
        "content_idea_id": idea.id,
        "template_id": template_id,
        "lines": cleaned_lines,
        "full_text": comp_full.modified_text,
        "compliance_warnings": list(set(all_warnings)),
        "render_request": render_req.model_dump(),
    }
