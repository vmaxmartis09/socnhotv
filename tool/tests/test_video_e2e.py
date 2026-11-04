from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from socnhotv.core.api.app import app
from socnhotv.video.episode.assemble import assemble_episode
from socnhotv.video.episode.assets import estimate_episode_cost, generate_scene_assets
from socnhotv.video.episode.planner import DialogueLine, EpisodePlan, ScenePlan, plan_episode
from socnhotv.video.episode.shorts import extract_and_assemble_shorts
from socnhotv.video.episode.voice import synthesize_episode_voice
from socnhotv.video.queue import RenderQueue
from socnhotv.workspace.paths import project_path

SAMPLE_SCRIPT = """Cảnh 1: Phòng khám Bác sĩ Koala
Bi: Bác sĩ Koala ơi, răng của em bị sâu đau quá!
Koala: Để bác xem nào, em ăn nhiều kẹo ngọt mà quên đánh răng đúng không?

Cảnh 2: Hướng dẫn chăm sóc răng miệng
Koala: Mỗi ngày em phải đánh răng 2 lần, sáng và tối nhé!
Bi: Dạ, em nhớ rồi ạ, em sẽ chăm chỉ đánh răng!

Cảnh 3: Kết thúc vui vẻ
Bi: Răng em hết đau rồi, cảm ơn Bác sĩ Koala!
Koala: Chúc Bi luôn vui khỏe và có nụ cười thật tươi!"""


def test_plan_episode_scale_lock():
    """Kiểm tra kịch bản phân cảnh đảm bảo Scale Lock 100cm / 150cm."""
    plan = plan_episode(SAMPLE_SCRIPT, episode_id="ep_test_01", title="Sóc Nhỏ và Chiếc Răng Sâu")

    assert len(plan.scenes) == 3
    assert plan.episode_id == "ep_test_01"
    assert plan.title == "Sóc Nhỏ và Chiếc Răng Sâu"
    assert plan.total_duration_est > 0
    assert plan.estimated_cost_usd > 0

    # Kiểm tra phân cảnh 1 có cả Bi và Koala
    sc1 = plan.scenes[0]
    assert "soc_nho" in sc1.characters
    assert "koala" in sc1.characters
    assert "100cm" in sc1.scale_lock_prompt
    assert "150cm" in sc1.scale_lock_prompt
    assert "two-thirds" in sc1.scale_lock_prompt.lower() or "100cm vs 150cm" in sc1.scale_lock_prompt


@pytest.mark.anyio
async def test_assets_and_voice_pipeline(tmp_path):
    """Kiểm tra sinh key-frame, voiceover đa nhân vật và TikTok mastering."""
    pid = "soc-nho-tv"
    eid = "ep_test_assets"
    plan = plan_episode(SAMPLE_SCRIPT, episode_id=eid)

    # 1. Assets
    assets = generate_scene_assets(pid, eid, plan.scenes, use_mock=True)
    assert len(assets) == 3
    for a in assets:
        assert Path(a["image"]).exists()
        assert a["durationSec"] > 0

    # 2. Voice
    master_voice, durations = await synthesize_episode_voice(pid, eid, plan.scenes, use_mock=True)
    assert master_voice.exists()
    assert len(durations) == 3


def test_assemble_and_shorts_generation(tmp_path):
    """Kiểm tra dựng RenderRequest YouTube 16:9 và 3 Shorts 9:16 kèm chapters.txt & youtube_meta.json."""
    pid = "soc-nho-tv"
    eid = "ep_test_assemble"
    plan = plan_episode(SAMPLE_SCRIPT, episode_id=eid, title="Sóc Nhỏ và Chiếc Răng Sâu")
    assets = generate_scene_assets(pid, eid, plan.scenes, use_mock=True)
    voice_path = project_path(pid, "output", eid, "audio", "episode_master_voice.mp3")
    voice_path.parent.mkdir(parents=True, exist_ok=True)
    from socnhotv.core.providers.mock_provider import create_minimal_wav_bytes
    voice_path.write_bytes(create_minimal_wav_bytes(duration_sec=1.0))

    # Main Episode Assemble
    main_req = assemble_episode(pid, eid, plan.title, plan.scenes, assets, voice_path)
    assert main_req.template_id == "yt-animation-episode-v1"
    assert main_req.platforms == ["youtube"]
    assert main_req.data["auto_draft"] is True
    assert "100cm" in main_req.data["character_scale_lock"]

    # Verify chapters.txt and youtube_meta.json
    ep_dir = project_path(pid, "output", eid)
    chapters_file = ep_dir / "chapters.txt"
    meta_file = ep_dir / "youtube_meta.json"
    assert chapters_file.exists()
    assert "00:00 Mở đầu" in chapters_file.read_text(encoding="utf-8")

    assert meta_file.exists()
    meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
    assert "Chiếc Răng Sâu" in meta_data["title"]
    assert len(meta_data["tags"]) > 0

    # Shorts extraction
    shorts_reqs = extract_and_assemble_shorts(pid, eid, plan.scenes, assets, voice_path)
    assert len(shorts_reqs) == 3
    for sr in shorts_reqs:
        assert set(sr.platforms) == {"shorts", "tiktok", "reels"}
        assert sr.data["auto_draft"] is True


@pytest.mark.anyio
async def test_e2e_queue_and_auto_draft(tmp_path):
    """Nghiệm thu E2E: 1 YouTube + 3 Shorts hoàn tất và gọi create_draft_post 4 lần."""
    pid = "soc-nho-tv"
    eid = "ep_e2e_draft_test"
    plan = plan_episode(SAMPLE_SCRIPT, episode_id=eid, title="Sóc Nhỏ và Chiếc Răng Sâu")
    assets = generate_scene_assets(pid, eid, plan.scenes, use_mock=True)
    voice_path = project_path(pid, "output", eid, "audio", "episode_master_voice.mp3")
    voice_path.parent.mkdir(parents=True, exist_ok=True)
    from socnhotv.core.providers.mock_provider import create_minimal_wav_bytes
    voice_path.write_bytes(create_minimal_wav_bytes(duration_sec=1.0))

    main_req = assemble_episode(pid, eid, plan.title, plan.scenes, assets, voice_path)
    shorts_reqs = extract_and_assemble_shorts(pid, eid, plan.scenes, assets, voice_path)

    queue = RenderQueue(max_parallel=2)

    # Mock render thực thi nhanh để test luồng queue & auto-draft
    def fast_mock_render(bundle_dir, out_path, platform, **kwargs):
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(b"fake_mp4_video")
        return str(out_path)

    queue.engine.render = MagicMock(side_effect=fast_mock_render)

    draft_mock = MagicMock(return_value={"post_id": "draft_123", "status": "draft"})
    with patch("socnhotv.social.contracts.create_draft_post", draft_mock):
        main_job = queue.submit(main_req)
        s_jobs = [queue.submit(sr) for sr in shorts_reqs]

        # Chờ các background workers xử lý hoàn tất cả 4 jobs
        if queue._queue is not None:
            await queue._queue.join()

        main_job = queue.get(pid, main_job.job_id)
        assert main_job.status == "done"
        for sj in s_jobs:
            sj_updated = queue.get(pid, sj.job_id)
            assert sj_updated.status == "done"

        # Khẳng định create_draft_post được gọi đúng 4 lần
        assert draft_mock.call_count == 4


def test_api_video_episodes(tmp_path):
    """Kiểm tra bộ API /projects/{pid}/video/episodes/{eid}/..."""
    client = TestClient(app)
    pid = "soc-nho-tv"
    eid = "ep_api_test"

    # 1. POST plan
    resp = client.post(
        f"/projects/{pid}/video/episodes/{eid}/plan",
        json={"script": SAMPLE_SCRIPT, "title": "Tập Kiểm Tra API"},
    )
    assert resp.status_code == 200, resp.text
    plan_data = resp.json()
    assert plan_data["episode_id"] == eid
    assert len(plan_data["scenes"]) == 3

    # 2. POST build with mock
    with patch("socnhotv.social.contracts.create_draft_post", MagicMock()):
        resp_build = client.post(
            f"/projects/{pid}/video/episodes/{eid}/build",
            json={"use_mock": True},
        )
        assert resp_build.status_code == 200, resp_build.text
        build_data = resp_build.json()
        assert build_data["episode_id"] == eid
        assert "main_job_id" in build_data
        assert len(build_data["shorts_job_ids"]) == 3

    # 3. GET status
    resp_status = client.get(f"/projects/{pid}/video/episodes/{eid}/status")
    assert resp_status.status_code == 200, resp_status.text
    st = resp_status.json()
    assert st["episode_id"] == eid
    assert "chapters" in st
    assert "youtube_meta" in st
