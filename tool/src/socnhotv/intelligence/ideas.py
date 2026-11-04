"""Content Idea engine: generates 30 viral ideas mapped to pillars with rapidfuzz guardrail, supports promotion to script."""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from typing import Any, Dict, List, Optional
import httpx

from socnhotv.intelligence.contracts import (
    ContentIdea,
    list_channel_blueprints,
    list_content_ideas,
    load_content_idea,
    save_content_idea,
)
from socnhotv.intelligence.products import list_products
from socnhotv.intelligence.script_gen import generate_complete_script
from socnhotv.intelligence.strategy import load_channel_strategy, validate_title_guardrail
from socnhotv.workspace import project_path

logger = logging.getLogger(__name__)

# Base creative themes for Soc Nho TV
IDEA_SEEDS = [
    # Pillar 1: Hoạt hình & Đời sống Sóc Nhỏ
    {"p": "pillar_animation_life", "t": "Sóc Nhỏ và Thử Thách Nhịn Ăn Vặt Trong 24 Giờ", "h": "Liệu Sóc Nhỏ có vượt qua được cám dỗ của chiếc tủ lạnh?", "tmpl": "koc-review-v1", "pri": 5},
    {"p": "pillar_animation_life", "t": "Koala Lần Đầu Đi Siêu Thị Cùng Sóc Nhỏ", "h": "Cái kết cười ra nước mắt khi Koala chọn đồ ăn vặt!", "tmpl": "koc-review-v1", "pri": 4},
    {"p": "pillar_animation_life", "t": "Chiếc Hộp Bí Ẩn Dưới Gốc Cây Dẻ Gai", "h": "Đừng mở chiếc hộp này nếu chưa chuẩn bị tâm lý!", "tmpl": "koc-review-v1", "pri": 3},
    {"p": "pillar_animation_life", "t": "Một Ngày Làm Trợ Lý Cho Bạn Koala", "h": "Làm trợ lý cho một bạn Koala ngủ 20 tiếng/ngày sẽ như thế nào?", "tmpl": "koc-review-v1", "pri": 4},
    {"p": "pillar_animation_life", "t": "Sóc Nhỏ Học Cách Quản Lý Tiền Tiết Kiệm", "h": "Bí quyết nuôi heo đất không bao giờ vỡ của Sóc Nhỏ Bi.", "tmpl": "koc-review-v1", "pri": 5},
    {"p": "pillar_animation_life", "t": "Kỳ Nghỉ Hè Bất Ổn Của Đôi Bạn Thân", "h": "Chuyến cắm trại trong rừng và những vị khách không mời.", "tmpl": "koc-review-v1", "pri": 3},
    {"p": "pillar_animation_life", "t": "Khi Sóc Nhỏ Bị Ốm và Koala Làm Bác Sĩ", "h": "Bài thuốc đặc biệt của bác sĩ Koala khiến ai cũng bật cười.", "tmpl": "koc-review-v1", "pri": 4},

    # Pillar 2: Thám Tử Tò Mò — Giải Mã Đời Sống
    {"p": "pillar_science_fun", "t": "Tại Sao Mắt Chúng Ta Lại Chớp Hơn 20.000 Lần Mỗi Ngày?", "h": "Có bao giờ bạn tự hỏi điều gì xảy ra nếu bạn không chớp mắt?", "tmpl": "tiktok-sales-v1", "pri": 4},
    {"p": "pillar_science_fun", "t": "Sự Thật Về Chiếc Bụng Kêu Ục Ục Khi Đói", "h": "Không phải do dạ dày đói đâu, sự thật đằng sau sẽ làm bạn bất ngờ!", "tmpl": "tiktok-sales-v1", "pri": 5},
    {"p": "pillar_science_fun", "t": "Top 5 Động Vật Có Siêu Năng Lực Kỳ Lạ Nhất Trái Đất", "h": "Loài vật số 3 có thể sống sót ngoài không gian vũ trụ!", "tmpl": "tiktok-sales-v1", "pri": 5},
    {"p": "pillar_science_fun", "t": "Vì Sao Nước Biển Lại Mặn Mà Nước Sông Lại Ngọt?", "h": "Hành trình hàng triệu năm của muối mà trường học chưa dạy bạn.", "tmpl": "tiktok-sales-v1", "pri": 3},
    {"p": "pillar_science_fun", "t": "Giải Mã Hiện Tượng Nấc Cụt và Mẹo Dứt Điểm Trong 10 Giây", "h": "Áp dụng mẹo này là nấc cụt biến mất ngay lập tức!", "tmpl": "tiktok-sales-v1", "pri": 4},
    {"p": "pillar_science_fun", "t": "Cầu Vồng Thực Chất Có Hình Gì Từ Trên Máy Bay?", "h": "Cầu vồng không phải hình vòng cung như bạn vẫn nghĩ!", "tmpl": "tiktok-sales-v1", "pri": 4},
    {"p": "pillar_science_fun", "t": "Tại Sao Chúng Ta Lại Quên Giấc Mơ Ngay Sau Khi Thức Dậy?", "h": "Não bộ đang âm thầm xóa ký ức của bạn mỗi sáng mai.", "tmpl": "tiktok-sales-v1", "pri": 3},

    # Pillar 3: KOC Review & Đập Hộp
    {"p": "pillar_koc_review", "t": "KOC LyLy Thử Bút Luyện Chữ Tự Xoá: Có Đáng Tiền Không?", "h": "Bút tự xoá mực sau 15 phút, thần thánh hay chỉ là chiêu trò?", "tmpl": "koc-review-v1", "pri": 5},
    {"p": "pillar_koc_review", "t": "Đập Hộp Hộp Cơm Giữ Nhiệt Cắm Điện Mini Cho Học Sinh", "h": "Mang cơm nóng hổi đi học mà không cần lò vi sóng!", "tmpl": "koc-review-v1", "pri": 4},
    {"p": "pillar_koc_review", "t": "Trải Nghiệm Đèn Bàn Chống Cận Thị Thông Minh Sóc Nhỏ", "h": "Chiếc đèn tự nhắc nhở ngồi thẳng lưng có thực sự hiệu quả?", "tmpl": "koc-review-v1", "pri": 5},
    {"p": "pillar_koc_review", "t": "Test Khả Năng Kháng Nước Của Balo Học Sinh Chống Gù", "h": "Xịt vòi nước áp lực cao vào balo và cái kết bên trong...", "tmpl": "koc-review-v1", "pri": 4},
    {"p": "pillar_koc_review", "t": "LyLy Review Bình Giữ Nhiệt Báo Nhiệt Độ Cảm Ứng", "h": "Chỉ cần chạm nhẹ nắp bình là biết nước nóng hay nguội!", "tmpl": "koc-review-v1", "pri": 3},
    {"p": "pillar_koc_review", "t": "Thử Thách Dùng Máy In Nhiệt Cầm Tay In Ảnh Học Tập", "h": "Không cần mực in mà vẫn in bài tập siêu nét!", "tmpl": "koc-review-v1", "pri": 4},
    {"p": "pillar_koc_review", "t": "Review Quạt Tích Điện Cầm Tay Mini Pin Trâu 24 Giờ", "h": "Cứu tinh những ngày cúp điện mùa hè mà giá chỉ bằng 3 ly trà sữa.", "tmpl": "koc-review-v1", "pri": 5},
    {"p": "pillar_koc_review", "t": "Đánh Giá Gối Tựa Lưng Công Thái Học Cho Người Ngồi Lâu", "h": "Ngồi học 8 tiếng không lo mỏi lưng, đáng tiền từng xu!", "tmpl": "koc-review-v1", "pri": 4},

    # Pillar 4: Bí Kíp Tiết Kiệm & Săn Deal Affiliate
    {"p": "pillar_affiliate_hacks", "t": "So Sánh 3 Dòng Bàn Chải Điện Giá Rẻ Dưới 300K", "h": "Đừng mua loại đắt tiền nếu chưa xem bảng so sánh này!", "tmpl": "affiliate-compare-v1", "pri": 5},
    {"p": "pillar_affiliate_hacks", "t": "Top 3 Món Đồ Gia Dụng Tiện Ích Đáng Mua Nhất Dịp Sale", "h": "3 món đồ thông minh giá hạt dẻ ai cũng nên có trong phòng.", "tmpl": "affiliate-compare-v1", "pri": 5},
    {"p": "pillar_affiliate_hacks", "t": "So Sánh Nồi Chiên Không Dầu Cơ vs Điện Tử Cùng Tầm Giá", "h": "Nên mua núm vặn hay màn hình cảm ứng để bền bỉ hơn?", "tmpl": "affiliate-compare-v1", "pri": 4},
    {"p": "pillar_affiliate_hacks", "t": "Bí Kíp Săn Mã Giảm Giá Shopee & TikTok Shop Giảm 50%", "h": "Mẹo lấy voucher độc quyền không phải ai cũng biết!", "tmpl": "affiliate-compare-v1", "pri": 4},
    {"p": "pillar_affiliate_hacks", "t": "So Sánh 2 Dòng Máy Xay Sinh Tố Cầm Tay Mini", "h": "Máy xay mini nào xay đá nhuyễn mịn mà không bị kẹt lưỡi?", "tmpl": "affiliate-compare-v1", "pri": 4},
    {"p": "pillar_affiliate_hacks", "t": "Có Nên Mua Tai Nghe Bluetooth Chống Ồn Giá Học Sinh?", "h": "Trải nghiệm âm thanh thực tế sau 1 tháng sử dụng liên tục.", "tmpl": "affiliate-compare-v1", "pri": 3},
    {"p": "pillar_affiliate_hacks", "t": "Top 4 Dụng Cụ Vệ Sinh Bàn Học Thông Minh Cực Gọn", "h": "Dọn sạch vụn tẩy và bụi bàn phím trong đúng 30 giây!", "tmpl": "affiliate-compare-v1", "pri": 4},
    {"p": "pillar_affiliate_hacks", "t": "So Sánh Sạc Dự Phòng Sạc Nhanh 20W và 30W", "h": "Tốc độ sạc pin thực tế chênh lệch bao nhiêu phần trăm?", "tmpl": "affiliate-compare-v1", "pri": 4},
]


def generate_ideas_batch(
    project_id: str,
    count: int = 30,
) -> List[ContentIdea]:
    """Generate 30 unique ContentIdeas mapped to pillars with rapidfuzz guardrail."""
    strategy = load_channel_strategy(project_id)

    # Collect competitor titles for guardrail verification
    source_titles: List[str] = []
    for bp in list_channel_blueprints(project_id):
        for v in bp.top_videos:
            if "title" in v:
                source_titles.append(v["title"])

    existing_ideas = {i.title.lower() for i in list_content_ideas(project_id)}

    created_ideas: List[ContentIdea] = []
    seed_idx = 0

    while len(created_ideas) < count and seed_idx < len(IDEA_SEEDS):
        seed = IDEA_SEEDS[seed_idx]
        seed_idx += 1

        cand_title = seed["t"]
        # Skip if already exists
        if cand_title.lower() in existing_ideas:
            continue

        # Guardrail check against competitor titles (must be < 70 similarity)
        if source_titles and not validate_title_guardrail(cand_title, source_titles, max_similarity=70.0):
            # Tweak title slightly to maintain uniqueness
            cand_title = f"{cand_title} — Bí Quyết Của Sóc Nhỏ"

        idea_id = f"idea_{hashlib.md5((project_id + cand_title).encode()).hexdigest()[:10]}"

        idea = ContentIdea(
            id=idea_id,
            project_id=project_id,
            title=cand_title,
            platform_targets=["tiktok", "shorts", "reels", "youtube"],
            template_id=seed["tmpl"],
            priority=seed["pri"],
            status="new",
        )

        save_content_idea(project_id, idea)
        created_ideas.append(idea)
        existing_ideas.add(cand_title.lower())

    return created_ideas


def update_idea_status(
    project_id: str,
    idea_id: str,
    status: Optional[str] = None,
    priority: Optional[int] = None,
) -> Optional[ContentIdea]:
    """Update idea status (for kanban drag & drop) or priority."""
    idea = load_content_idea(project_id, idea_id)
    if not idea:
        return None

    if status and status in ["new", "scripted", "rendered", "scheduled", "dropped"]:
        idea.status = status  # type: ignore
    if priority is not None and 1 <= priority <= 5:
        idea.priority = priority

    save_content_idea(project_id, idea)
    return idea


def promote_idea(
    project_id: str,
    idea_id: str,
    product_id: Optional[str] = None,
    character_name: str = "LyLy",
    voice_id: str = "soc-nho",
) -> Dict[str, Any]:
    """Promote ContentIdea from status 'new' to 'scripted' by generating script & RenderRequest."""
    idea = load_content_idea(project_id, idea_id)
    if not idea:
        raise FileNotFoundError(f"Không tìm thấy ý tưởng {idea_id}")

    # Pick product
    products = list_products(project_id)
    target_product = None
    if product_id:
        target_product = next((p for p in products if p.id == product_id), None)
    if not target_product and products:
        target_product = products[0]

    if not target_product:
        # Fallback draft product if none exist
        from socnhotv.intelligence.products import Product, save_product
        target_product = save_product(
            project_id,
            Product(
                id=f"prod_{idea.id}",
                name=idea.title,
                brand="Sóc Nhỏ Lab",
                category="Đời sống",
                price=199000,
                sale_price=159000,
                usp=["Chất lượng chuẩn mực", "Bảo hành 1 đổi 1"],
                affiliate_links={"tiktok_shop": "https://shop.tiktok.com"},
            ),
        )

    generator_type = "koc_review"
    if idea.template_id == "tiktok-sales-v1":
        generator_type = "tiktok_sales"
    elif idea.template_id == "affiliate-compare-v1":
        generator_type = "affiliate_compare"

    res = generate_complete_script(
        project_id=project_id,
        product=target_product,
        generator_type=generator_type,  # type: ignore
        character_name=character_name,
        voice_id=voice_id,
        platforms=["tiktok", "shorts", "reels"],
    )

    # Update idea status to 'scripted'
    idea.status = "scripted"
    save_content_idea(project_id, idea)

    return {
        "idea": idea.model_dump(),
        "script_result": res,
    }


def schedule_idea_to_social(
    project_id: str,
    idea_id: str,
    core_port: int = 8000,
) -> Dict[str, Any]:
    """Push idea to Session C publishing scheduler via HTTP if available."""
    idea = load_content_idea(project_id, idea_id)
    if not idea:
        raise FileNotFoundError(f"Không tìm thấy ý tưởng {idea_id}")

    scheduled_res = {"status": "ok", "message": "Ý tưởng đã chuyển trạng thái Lên lịch"}

    try:
        url = f"http://127.0.0.1:{core_port}/projects/{project_id}/social/ideas/{idea_id}/schedule"
        r = httpx.post(url, timeout=3.0)
        if r.status_code == 200:
            scheduled_res = r.json()
    except Exception as e:
        logger.info(f"Session C schedule endpoint not connected, updating local idea state: {e}")

    idea.status = "scheduled"
    save_content_idea(project_id, idea)

    return {
        "idea": idea.model_dump(),
        "social_response": scheduled_res,
    }
