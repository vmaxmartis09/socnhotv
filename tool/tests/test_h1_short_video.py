import asyncio
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
    Graph,
    GraphRunRequest,
    NodeInstance,
    RunMode,
)
from socnhotv.core.providers.mock_provider import MockProvider
from socnhotv.core.storage.project_store import ProjectStore
from socnhotv.video.craft.camera import CAMERA_PRESETS
from socnhotv.video.short_form import (
    ShortVideoConfig,
    SHORT_VIDEO_PRESET_ID,
    SHORT_VIDEO_PRESET_NAME,
    build_short_video_graph,
    estimate_short_video_cost,
    generate_short_video_script,
    run_short_video_pipeline,
)


def test_h1_generator_script_and_shots():
    """Kiểm tra sinh kịch bản ngắn 4–10 shot từ 1 prompt, tuân thủ 30s và video craft."""
    cfg = ShortVideoConfig(
        prompt="Sóc Nhỏ tìm thấy quả thông khổng lồ phát sáng",
        target_duration_sec=30.0,
        aspect_ratio="9:16",
        mode="static",
        character_id="soc_nho",
        character_name="Sóc Nhỏ",
    )
    result = generate_short_video_script(cfg)

    # 1. Số shot nằm trong khoảng 4–10 shot (30s = 5 shot)
    assert 4 <= result.shot_count <= 10
    assert len(result.shots) == result.shot_count
    assert len(result.scenes) == result.shot_count
    assert len(result.lines) == result.shot_count

    # 2. Tổng thời lượng kịch bản khớp mục tiêu 30 giây (± 0.5s)
    assert abs(result.total_duration_sec - 30.0) <= 0.5

    # 3. Cấu trúc vai trò shot: có hook mở đầu và cta kết
    assert result.shots[0].role == "hook"
    assert result.shots[-1].role == "cta"

    # 4. Kiểm tra camera presets hợp lệ từ video-craft camera.py
    for s in result.shots:
        assert s.camera in CAMERA_PRESETS

    # 5. Kiểm tra prompt ảnh 3 tầng (DNA nhân vật và không gian)
    for s in result.shots:
        assert "soc_nho" in s.image_prompt.lower() or "squirrel" in s.image_prompt.lower()
        assert len(s.image_prompt) > 40

    # 6. Kịch bản thô raw_script chứa định dạng chuẩn
    assert "Cảnh 1:" in result.raw_script
    assert "Camera:" in result.raw_script
    assert "Hình ảnh:" in result.raw_script
    assert "Sóc Nhỏ:" in result.raw_script


def test_h1_scaling_durations():
    """Kiểm tra co giãn thời lượng từ 30 đến 90 giây."""
    for dur in (30.0, 45.0, 60.0, 90.0):
        cfg = ShortVideoConfig(
            prompt="Chuyến thám hiểm rừng rậm của Sóc Nhỏ",
            target_duration_sec=dur,
            aspect_ratio="9:16",
        )
        res = generate_short_video_script(cfg)
        assert 4 <= res.shot_count <= 10
        assert abs(res.total_duration_sec - dur) <= 0.5


def test_h1_cost_estimation_rules():
    """Kiểm tra ước tính chi phí minh bạch theo SpendGuard."""
    # 1. Chế độ ảnh tĩnh: hoàn toàn miễn phí ($0)
    cost_static = estimate_short_video_cost(mode="static", shot_count=5, duration_sec=30.0)
    assert cost_static["total_cost_usd"] == 0.0
    assert cost_static["is_free"] is True
    assert cost_static["spend_guard_required"] is False
    assert cost_static["breakdown"]["video_ai_cost_usd"] == 0.0

    # 2. Chế độ clip AI: tính theo đơn giá perShot
    cost_ai = estimate_short_video_cost(
        mode="ai_clip",
        shot_count=5,
        duration_sec=30.0,
        video_model="google-veo-2",
        max_clips=5,
    )
    assert cost_ai["total_cost_usd"] > 0.0
    assert cost_ai["is_free"] is False
    assert cost_ai["spend_guard_required"] is True
    assert cost_ai["clips_count"] == 5

    # 3. Model Kling v3
    cost_kling = estimate_short_video_cost(
        mode="ai_clip",
        shot_count=5,
        duration_sec=30.0,
        video_model="fal-kling-v3-std",
        max_clips=5,
    )
    assert cost_kling["total_cost_usd"] == round(5 * 6.0 * 0.084, 3)


def test_h1_graph_builder_structure():
    """Kiểm tra xây dựng đồ thị Graph 7 node, 11 edge chuẩn Core Engine."""
    cfg = ShortVideoConfig(
        prompt="Sóc Nhỏ học cách chia sẻ",
        target_duration_sec=30.0,
        aspect_ratio="9:16",
        mode="static",
    )
    result = generate_short_video_script(cfg)
    graph = build_short_video_graph(cfg, result)

    assert isinstance(graph, Graph)
    assert len(graph.nodes) == 7
    assert len(graph.edges) == 11

    node_map = {n.id: n for n in graph.nodes}
    assert "n_script" in node_map
    assert "n_cast" in node_map
    assert "n_quality" in node_map
    assert "n_keyframes" in node_map
    assert "n_video" in node_map
    assert "n_render" in node_map
    assert "n_export" in node_map

    # Kiểm tra params node video_gen ở chế độ tĩnh
    assert node_map["n_video"].params["clipSource"] == "manual"
    assert node_map["n_video"].params["maxClips"] == 0

    # Kiểm tra params dựng HyperFrames 9:16 TikTok
    assert node_map["n_render"].params["aspectRatio"] == "9:16"
    assert node_map["n_render"].params["platform"] == "tiktok"
    assert node_map["n_render"].params["template"] == "tiktok_safe_zone"


def test_h1_graph_builder_ai_clip_mode():
    """Kiểm tra đồ thị ở chế độ clip AI: video_gen chuyển sang auto perShot."""
    cfg = ShortVideoConfig(
        prompt="Sóc Nhỏ học cách chia sẻ",
        target_duration_sec=30.0,
        aspect_ratio="9:16",
        mode="ai_clip",
        video_model="google-veo-2",
        max_clips=5,
    )
    result = generate_short_video_script(cfg)
    graph = build_short_video_graph(cfg, result)

    node_map = {n.id: n for n in graph.nodes}
    assert node_map["n_video"].params["clipSource"] == "auto"
    assert node_map["n_video"].params["maxClips"] == 5
    assert node_map["n_video"].params["model"] == "google-veo-2"


@pytest.mark.anyio
async def test_h1_pipeline_execution_mock(tmp_path: Path):
    """Kiểm tra thực thi toàn bộ pipeline đồ thị Video ngắn với mock store."""
    store = ProjectStore(project_id="test_h1_proj", repo_root=tmp_path)
    store.project_dir.mkdir(parents=True, exist_ok=True)
    store.output_dir.mkdir(parents=True, exist_ok=True)

    # Chuẩn bị dummy voice mp3 để test không gọi TTS tốn thời gian
    voice_dir = tmp_path / "data" / "shared" / "voice_vault" / "soc-nho"
    voice_dir.mkdir(parents=True, exist_ok=True)
    (voice_dir / "sample.mp3").write_bytes(b"ID3dummy")

    cfg = ShortVideoConfig(
        prompt="Sóc Nhỏ khám phá hang đá bí mật",
        project_id="test_h1_proj",
        target_duration_sec=30.0,
        aspect_ratio="9:16",
        mode="static",
        output_slug="test-short-video",
    )

    mock_prov = MockProvider(store=store)

    # Mock adapter render_from_artifacts để test logic đồ thị nhanh trong unit test
    fake_video = store.output_dir / "test-short-video" / "test-short-video.mp4"
    fake_video.parent.mkdir(parents=True, exist_ok=True)
    fake_video.write_bytes(b"dummy_mp4_bytes")

    fake_art = Artifact(
        id="art_video_short",
        kind=ArtifactKind.VIDEO,
        uri=str(fake_video.relative_to(store.project_dir)),
        mime="video/mp4",
        size=15,
        hash="dummyhash123",
        provenance=ArtifactProvenance(
            node_id="n_render",
            run_id="run_h1",
            provider="local",
            model="hyperframes",
            params={},
            cost_usd=0.0,
            created_at="2026-11-06T12:00:00Z",
        ),
        meta=ArtifactMeta(duration=30.0),
    )

    with patch("socnhotv.core.engine.graph_runner.HyperFramesAdapter") as mock_adapter_cls:
        inst = mock_adapter_cls.return_value
        inst.render_from_artifacts = AsyncMock(return_value=fake_art)

        result = await run_short_video_pipeline(
            config=cfg,
            store=store,
            provider=mock_prov,
        )

        assert result["slug"] == "test-short-video"
        assert result["shots_count"] == 5
        assert result["cost_estimate"]["total_cost_usd"] == 0.0
        assert result["metrics"]["total_time_sec"] > 0
