from __future__ import annotations

import tempfile
from pathlib import Path
from socnhotv.video.contracts import RenderRequest, submit_render, get_render, list_templates
from socnhotv.intelligence.contracts import (
    Beat,
    VideoBlueprint,
    ChannelBlueprint,
    ContentIdea,
    save_video_blueprint,
    load_video_blueprint,
    list_video_blueprints,
    save_channel_blueprint,
    load_channel_blueprint,
    list_channel_blueprints,
    save_content_idea,
    load_content_idea,
    list_content_ideas,
)
from socnhotv.social.contracts import create_draft_post


def test_video_contracts():
    req = RenderRequest(
        project_id="soc-nho-tv",
        template_id="tiktok-sales-v1",
        platforms=["tiktok", "reels"],
        data={"headline": "Test Video"},
        output_name="test_video_1",
    )
    job = submit_render(req)
    assert job.job_id.startswith("render_")
    assert job.status == "queued"
    
    fetched = get_render("soc-nho-tv", job.job_id)
    assert fetched.job_id == job.job_id
    assert fetched.status == "queued"

    templates = list_templates()
    assert isinstance(templates, list)


def test_intelligence_contracts():
    # VideoBlueprint
    vbp = VideoBlueprint(
        id="vbp_123",
        source_ref="yt_xyz",
        duration_s=45.0,
        platform="tiktok",
        hook="Ban co biet?",
        beats=[Beat(t_start=0.0, t_end=3.0, role="hook", summary="Hook beat")],
        cta="Follow ngay",
    )
    saved_path = save_video_blueprint("soc-nho-tv", vbp)
    assert saved_path.exists()
    loaded_vbp = load_video_blueprint("soc-nho-tv", "vbp_123")
    assert loaded_vbp is not None
    assert loaded_vbp.id == "vbp_123"
    assert loaded_vbp.hook == "Ban co biet?"

    # ChannelBlueprint
    cbp = ChannelBlueprint(
        id="cbp_123",
        channel_url="https://youtube.com/@test",
        niche="kids",
        pillars=["education", "story"],
    )
    saved_cbp = save_channel_blueprint("soc-nho-tv", cbp)
    assert saved_cbp.exists()
    loaded_cbp = load_channel_blueprint("soc-nho-tv", "cbp_123")
    assert loaded_cbp is not None
    assert loaded_cbp.niche == "kids"

    # ContentIdea
    idea = ContentIdea(
        id="idea_123",
        project_id="soc-nho-tv",
        title="5 meo cho soc nho",
        platform_targets=["tiktok", "youtube"],
    )
    saved_idea = save_content_idea("soc-nho-tv", idea)
    assert saved_idea.exists()
    loaded_idea = load_content_idea("soc-nho-tv", "idea_123")
    assert loaded_idea is not None
    assert loaded_idea.title == "5 meo cho soc nho"


def test_social_contracts():
    post_id = create_draft_post(
        project_id="soc-nho-tv",
        media_path="output/test.mp4",
        title="Video moi",
        caption="Cung xem soc nho",
        platforms=["tiktok", "youtube"],
    )
    assert post_id.startswith("post_")
