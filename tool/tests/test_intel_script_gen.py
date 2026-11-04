from __future__ import annotations

from socnhotv.intelligence.compliance import check_and_clean_script
from socnhotv.intelligence.products import Product
from socnhotv.intelligence.script_gen import (
    generate_complete_script,
    generate_koc_review_script,
    generate_tiktok_sales_script,
)


def test_compliance_blocks_medical_and_adds_affiliate():
    bad_text = "Sản phẩm này cam kết chữa khỏi 100% bệnh đau đầu và là số 1 Việt Nam."
    res = check_and_clean_script(bad_text, is_affiliate=True)

    assert not res.passed
    assert any("chữa khỏi" in w for w in res.warnings)
    assert "chữa khỏi 100%" not in res.modified_text
    # Auto inserted affiliate disclosure
    assert "#affiliate" in res.modified_text


def test_script_generation_koc_and_sales():
    prod = Product(
        id="prod_test_01",
        name="Kem Dưỡng Da Sóc Nhỏ",
        brand="Sóc Nhỏ Organic",
        price=189000,
        usp=["thành phần tự nhiên 100%", "thấm nhanh không bết dính"],
        pain_points=["da khô nứt nẻ mùa đông"],
    )

    # 1. KOC review
    koc_res = generate_complete_script(
        project_id="soc-nho-tv",
        product=prod,
        generator_type="koc_review",
        character_name="LyLy",
    )
    assert koc_res["template_id"] == "koc-review-v1"
    assert len(koc_res["lines"]) == 5
    assert koc_res["content_idea_id"].startswith("idea_")
    assert "Kem Dưỡng Da Sóc Nhỏ" in koc_res["full_text"]

    # 2. TikTok sales
    sales_res = generate_complete_script(
        project_id="soc-nho-tv",
        product=prod,
        generator_type="tiktok_sales",
    )
    assert sales_res["template_id"] == "tiktok-sales-v1"
    assert sales_res["render_request"]["data"]["product_name"] == "Kem Dưỡng Da Sóc Nhỏ"
