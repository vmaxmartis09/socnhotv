"""Unit tests for Hook Lab generation and heuristic scoring."""
from socnhotv.video.craft.hooks import score_hook, generate_hook_variants

def test_greeting_penalty():
    bad_hook = "Xin chào các bạn, hôm nay mình sẽ chia sẻ về cầu vồng"
    score = score_hook(bad_hook)
    assert score.has_greeting_penalty is True
    assert score.total_score < 60.0
    assert any("lời chào" in p for p in score.penalties)

def test_good_concise_hook():
    good_hook = "Đố bạn biết bí mật đằng sau chiếc cầu vồng 7 sắc?"
    score = score_hook(good_hook)
    assert score.has_greeting_penalty is False
    assert score.has_surprise_element is True
    assert score.total_score >= 80.0
    assert score.word_count <= 12

def test_long_hook_penalty():
    long_hook = (
        "Trong buổi chiều ngày hôm nay khi mà trời mưa xong thì bỗng nhiên xuất hiện "
        "một chiếc cầu vồng cực kỳ to lớn và lung linh nhiều màu sắc khác nhau"
    )
    score = score_hook(long_hook)
    assert score.word_count > 16
    assert any("quá dài" in p for p in score.penalties)

def test_generate_hook_variants():
    result = generate_hook_variants(topic="Cầu vồng sau mưa", character="soc-nho")
    assert len(result.variants) == 3
    assert result.best_variant_id in {"A", "B", "C"}
    assert len(result.selected_hook) > 0
    # Every variant should have valid scores
    for v in result.variants:
        assert 0.0 <= v.score.total_score <= 100.0
        assert v.score.estimated_duration_sec > 0
