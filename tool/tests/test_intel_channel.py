import json
import pytest
from pathlib import Path
from socnhotv.intelligence.channel_analyze import (
    abstract_title_pattern,
    analyze_channel,
    cluster_pillars,
)
from socnhotv.intelligence.ideas import (
    generate_ideas_batch,
    promote_idea,
    update_idea_status,
)
from socnhotv.intelligence.strategy import (
    generate_channel_strategy,
    validate_title_guardrail,
)
from socnhotv.workspace import project_path


@pytest.fixture
def mock_channel_fixture(tmp_path, monkeypatch):
    """Create a mock channel with 50 videos in videos.jsonl."""
    proj_id = "test_channel_proj"
    channel_id = "ch_competitor_test"

    # Override workspace paths to tmp_path
    def mock_project_path(project_id, *parts, ensure=False):
        p = tmp_path / project_id / Path(*parts)
        if ensure:
            p.parent.mkdir(parents=True, exist_ok=True)
        return p

    monkeypatch.setattr("socnhotv.intelligence.channel_analyze.project_path", mock_project_path)
    monkeypatch.setattr("socnhotv.intelligence.strategy.project_path", mock_project_path)
    monkeypatch.setattr("socnhotv.intelligence.ideas.project_path", mock_project_path)
    monkeypatch.setattr("socnhotv.intelligence.contracts.project_path", mock_project_path)
    monkeypatch.setattr("socnhotv.intelligence.products.project_path", mock_project_path)
    monkeypatch.setattr("socnhotv.intelligence.script_gen.project_path", mock_project_path)

    channel_dir = mock_project_path(proj_id, "knowledge", "channels", channel_id, ensure=True)
    channel_dir.mkdir(parents=True, exist_ok=True)

    # 50 mock videos
    videos = []
    for i in range(50):
        # Views: majority 10k, outlier video 0 has 500k
        view_cnt = 500000 if i == 0 else 10000 + (i * 200)
        videos.append({
            "id": f"vid_{i:03d}",
            "title": f"Mẹo vặt {i} cách sử dụng sản phẩm hiệu quả cho người mới" if i % 2 == 0 else f"Thử thách ngày {i} cùng bạn thân",
            "duration": 45.0 if i % 3 == 0 else 120.0,
            "upload_date": "20261015",
            "view_count": view_cnt,
            "like_count": int(view_cnt * 0.05),
            "comment_count": int(view_cnt * 0.01),
            "thumbnail": f"https://img.test/thumb_{i}.jpg",
            "url": f"https://youtube.com/watch?v=vid_{i:03d}",
            "views_per_day": float(view_cnt),
        })

    with open(channel_dir / "videos.jsonl", "w", encoding="utf-8") as f:
        for v in videos:
            f.write(json.dumps(v) + "\n")

    with open(channel_dir / "channel.json", "w", encoding="utf-8") as f:
        json.dump({
            "id": channel_id,
            "url": f"https://youtube.com/{channel_id}",
            "name": "Kênh Đối Thủ Mẫu",
            "video_count": 50,
        }, f)

    return proj_id, channel_id


def test_channel_analysis_stats_and_outliers(mock_channel_fixture):
    proj_id, channel_id = mock_channel_fixture

    analysis = analyze_channel(proj_id, channel_id)

    stats = analysis["stats"]
    assert stats["total_videos"] == 50
    # Median should be ~14900
    assert stats["median_views"] > 10000
    assert stats["median_views"] < 20000

    # Top outlier should be vid_000 with huge outlier score
    top_outliers = analysis["top_outliers"]
    assert len(top_outliers) > 0
    assert top_outliers[0]["id"] == "vid_000"
    assert top_outliers[0]["outlier_score"] > 20.0  # 500k / ~15k > 30

    # Heatmap dimensions
    heatmap = analysis["schedule_heatmap"]
    assert len(heatmap) == 7  # 7 days
    assert len(heatmap[0]) == 24  # 24 hours

    # Pillars
    pillars = analysis["pillars"]
    assert len(pillars) >= 2


def test_abstract_title_pattern():
    raw_1 = "Tôi đã thử 30 ngày tập thể dục và giảm 5kg"
    res_1 = abstract_title_pattern(raw_1)
    assert "[Thời gian]" in res_1 or "[Số]" in res_1

    raw_2 = "Top 5 sai lầm khi mua kem chống nắng 350k"
    res_2 = abstract_title_pattern(raw_2)
    assert "[Số]" in res_2
    assert "[Giá tiền]" in res_2 or "[Số]" in res_2


def test_title_guardrail():
    source_titles = [
        "Tôi Đã Thử 30 Ngày Uống Nước Ép Cần Tây Và Cái Kết",
        "Top 5 Món Đồ Gia Dụng Thông Minh Đáng Mua Nhất",
    ]

    # Similar title (>70% match) should be BLOCKED (return False)
    plagiarized = "Tôi Đã Thử 30 Ngày Uống Nước Ép Cần Tây Và Cái Kết Bất Ngờ"
    assert validate_title_guardrail(plagiarized, source_titles, max_similarity=70.0) is False

    # Original distinct title should PASS (return True)
    original = "Sóc Nhỏ và Bí Mật Vườn Trái Cây Thần Kỳ Của Koala"
    assert validate_title_guardrail(original, source_titles, max_similarity=70.0) is True


def test_ideas_generation_and_promotion(mock_channel_fixture):
    proj_id, channel_id = mock_channel_fixture

    # Generate strategy
    strat = generate_channel_strategy(proj_id, [channel_id])
    assert len(strat["our_pillars"]) == 4

    # Generate 30 ideas
    ideas = generate_ideas_batch(proj_id, count=30)
    assert len(ideas) == 30
    assert all(i.status == "new" for i in ideas)

    # Test update status (kanban)
    first_id = ideas[0].id
    updated = update_idea_status(proj_id, first_id, status="rendered", priority=5)
    assert updated.status == "rendered"
    assert updated.priority == 5

    # Test promote idea
    second_id = ideas[1].id
    promoted = promote_idea(proj_id, second_id, character_name="LyLy")
    assert promoted["idea"]["status"] == "scripted"
    assert "script_result" in promoted
    assert "render_request" in promoted["script_result"]
