"""Unit tests for Creative QA / Lint rules."""
from socnhotv.video.craft.lint import lint_script, lint_caption, lint_composition

def test_lint_script_clean():
    clean_script = (
        "Đố các bạn biết tại sao cầu vồng lại có 7 màu kỳ diệu?\n"
        "Mỗi giọt mưa như một lăng kính tí hon tách ánh sáng mặt trời.\n"
        "Hãy bình luận bên dưới xem bạn thích màu nào nhất nhé!"
    )
    report = lint_script(clean_script, duration_sec=25.0)
    assert report.error_count == 0
    assert report.passed is True

def test_lint_script_violations():
    bad_script = (
        "Xin chào các bạn và cả nhà yêu quý, hôm nay mình xin chia sẻ câu chuyện dài...\n"
        "Không có lời kêu gọi hành động nào cả."
    )
    report = lint_script(bad_script, duration_sec=75.0)
    assert report.error_count >= 1
    rule_ids = [i.rule_id for i in report.issues]
    assert "RULE_NO_GREETINGS" in rule_ids
    assert "RULE_HAS_CTA" in rule_ids
    assert "RULE_PLATFORM_DURATION" in rule_ids

def test_lint_caption():
    bad_caption = "Mua ngay tại https://shopee.vn/sp123 nha các bạn ơi!"
    report = lint_caption(bad_caption, has_affiliate=True)
    assert report.error_count >= 1
    rule_ids = [i.rule_id for i in report.issues]
    assert "RULE_NO_LINK_IN_CAPTION" in rule_ids
    assert "RULE_AFFILIATE_DISCLOSURE" in rule_ids

    good_caption = (
        "Bé thích màu nào nhất trong video này? Để lại bình luận nhé!\n"
        "📌 Chi tiết và link quà tặng mình ghim ở bình luận đầu tiên nha!\n"
        "*(Bài viết có chứa liên kết tiếp thị - Affiliate link)*"
    )
    report_good = lint_caption(good_caption, has_affiliate=True)
    assert report_good.error_count == 0
    assert report_good.passed is True

def test_lint_composition_safe_zones():
    comp_meta = {
        "scenes": [{"duration": 6.5}],  # too long
        "elements": [
            {"type": "subtitle", "y": 100},  # too high (y < 180)
            {"type": "button", "y": 1700}    # too low (y > 1600)
        ]
    }
    report = lint_composition(comp_meta)
    rule_ids = [i.rule_id for i in report.issues]
    assert "RULE_SCENE_TOO_LONG" in rule_ids
    assert "RULE_SAFE_ZONE_TOP" in rule_ids
    assert "RULE_SAFE_ZONE_BOTTOM" in rule_ids
