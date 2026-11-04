"""End-to-end Session B integration test: link -> source -> blueprint -> script KOC -> submit_render -> ContentIdea scripted."""
import json
import pytest
from pathlib import Path

from socnhotv.intelligence.analyzer import analyze_video
from socnhotv.intelligence.contracts import load_content_idea, load_video_blueprint
from socnhotv.intelligence.ideas import generate_ideas_batch, promote_idea
from socnhotv.intelligence.products import Product, save_product
from socnhotv.intelligence.script_gen import generate_complete_script
from socnhotv.sources.models import IngestRequest, SourceItem
from socnhotv.workspace import project_path


@pytest.fixture
def e2e_project_env(tmp_path, monkeypatch):
    pid = "e2e_session_b_proj"

    def mock_project_path(project_id, *parts, ensure=False):
        p = tmp_path / project_id / Path(*parts)
        if ensure:
            p.parent.mkdir(parents=True, exist_ok=True)
        return p

    # Patch workspace resolution across all modules
    for mod in [
        "socnhotv.sources.service",
        "socnhotv.sources.scenes",
        "socnhotv.intelligence.analyzer",
        "socnhotv.intelligence.products",
        "socnhotv.intelligence.script_gen",
        "socnhotv.intelligence.ideas",
        "socnhotv.intelligence.strategy",
        "socnhotv.intelligence.contracts",
    ]:
        monkeypatch.setattr(f"{mod}.project_path", mock_project_path)

    # 1. Ingest Mock Source
    source_id = "youtube_e2e_test_123"
    raw_dir = mock_project_path(pid, "raw", source_id, ensure=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy video & audio files
    (raw_dir / "video.mp4").write_bytes(b"dummy mp4 video bytes")
    (raw_dir / "audio.wav").write_bytes(b"RIFF dummy wav bytes")
    (raw_dir / "thumb.jpg").write_bytes(b"dummy thumb jpg")

    # Create scenes.json
    scenes = [
        {"scene_idx": 0, "start_s": 0.0, "end_s": 3.0, "thumb": "scenes/s_0.jpg"},
        {"scene_idx": 1, "start_s": 3.0, "end_s": 12.0, "thumb": "scenes/s_1.jpg"},
        {"scene_idx": 2, "start_s": 12.0, "end_s": 24.0, "thumb": "scenes/s_2.jpg"},
        {"scene_idx": 3, "start_s": 24.0, "end_s": 30.0, "thumb": "scenes/s_3.jpg"},
    ]
    with open(raw_dir / "scenes.json", "w", encoding="utf-8") as f:
        json.dump(scenes, f)

    # Create transcript.orig.json
    with open(raw_dir / "transcript.orig.json", "w", encoding="utf-8") as f:
        json.dump([
            {"start": 0.0, "end": 3.0, "text": "Mọi người đừng bao giờ mua kem chống nắng này nếu chưa xem video này nha!"},
            {"start": 3.0, "end": 12.0, "text": "Da dầu mụn rất hay bị bết dính và vón cục khi bôi kem."},
            {"start": 12.0, "end": 24.0, "text": "Nhưng thử em này xong là mê ngay, kiềm dầu cực đỉnh suốt 12 tiếng."},
            {"start": 24.0, "end": 30.0, "text": "Bấm vào giỏ hàng góc trái để nhận ưu đãi sale 30% hôm nay nhé!"},
        ], f)

    source_item = SourceItem(
        id=source_id,
        project_id=pid,
        url="https://youtube.com/watch?v=e2e_test_123",
        platform="youtube",
        title="Video Review Mỹ Phẩm Viral Mẫu",
        duration_s=30.0,
        rights="reference_only",
        rights_note="Nguồn học tập cấu trúc",
        files={
            "video": "video.mp4",
            "audio": "audio.wav",
            "thumb": "thumb.jpg",
            "scenes": "scenes.json",
        },
    )
    with open(raw_dir / "meta.json", "w", encoding="utf-8") as f:
        f.write(source_item.model_dump_json(indent=2))

    return pid, source_id


def test_session_b_full_e2e_pipeline(e2e_project_env):
    pid, source_id = e2e_project_env

    # Step 1: Analyze source into VideoBlueprint
    bp = analyze_video(pid, source_id)
    assert bp.id == f"bp_{source_id}"
    assert len(bp.beats) == 4
    # Pacing cuts per 10s = (3 cuts / 30s) * 10 = 1.0 cut/10s
    assert bp.pacing_cuts_per_10s == 1.0
    assert bp.beats[0].role == "hook"
    assert bp.beats[-1].role == "cta"

    # Step 2: Create Product
    product = Product(
        id="prod_e2e_serum",
        name="Tinh Chất Tràm Trà Trị Mụn Sóc Nhỏ",
        brand="Sóc Nhỏ Lab",
        category="Mỹ phẩm",
        price=299000,
        sale_price=219000,
        usp=["Giảm sưng mụn 24h", "Chiết xuất tràm trà hữu cơ"],
        pain_points=["Mụn viêm sưng đau", "Để lại thâm dai dẳng"],
        affiliate_links={"tiktok_shop": "https://shop.tiktok.com/p/123"},
        compliance_notes="Không cam kết chữa khỏi 100% vĩnh viễn",
    )
    saved_prod = save_product(pid, product)
    assert saved_prod.id == "prod_e2e_serum"

    # Step 3: Generate KOC Script + RenderRequest
    script_res = generate_complete_script(
        project_id=pid,
        product=saved_prod,
        generator_type="koc_review",
        blueprint=bp,
        character_name="LyLy",
        voice_id="soc-nho",
        platforms=["tiktok", "shorts", "reels"],
    )
    assert script_res["template_id"] == "koc-review-v1"
    assert len(script_res["lines"]) >= 4
    assert script_res["render_request"]["template_id"] == "koc-review-v1"
    assert script_res["render_request"]["voice"]["voice_id"] == "soc-nho"
    # Affiliate disclosure automatically added to compliance warnings
    assert any("affiliate" in w.lower() for w in script_res["compliance_warnings"])

    # Step 4: Generate Ideas & Promote Idea
    ideas = generate_ideas_batch(pid, count=5)
    assert len(ideas) == 5
    assert ideas[0].status == "new"

    # Promote first idea
    promoted = promote_idea(pid, ideas[0].id, product_id="prod_e2e_serum", character_name="LyLy")
    assert promoted["idea"]["status"] == "scripted"

    # Verify idea status in storage
    loaded = load_content_idea(pid, ideas[0].id)
    assert loaded is not None
    assert loaded.status == "scripted"
