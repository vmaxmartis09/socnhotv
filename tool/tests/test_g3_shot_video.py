from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
    NodeInstance,
)
from socnhotv.core.storage.project_store import ProjectStore
from socnhotv.core.engine.shot_video import (
    ShotVideoEngine,
    select_shots_for_video,
    find_manual_clip,
    inject_manual_clips,
)


def test_select_shots_max_clips_and_priority():
    """Kiểm tra chọn shot theo maxClips và sắp xếp ưu tiên (đầu cảnh, bài hát/cao trào, cuối tập)."""
    scenes = [
        {"id": "S01", "sceneIndex": 1, "dialogue": "Chào các bạn"},
        {"id": "S02", "sceneIndex": 1, "dialogue": "Chơi bóng nè"},
        {"id": "S03", "sceneIndex": 2, "dialogue": "Cảnh 2 bắt đầu"},
        {"id": "S04", "sceneIndex": 2, "dialogue": "Bi tức giận, núi lửa trong bụng, thở 5 ngón tay"},  # highlight
        {"id": "S05", "sceneIndex": 3, "dialogue": "Cảnh 3 bắt đầu"},
        {"id": "S06", "sceneIndex": 3, "dialogue": "Tập phim kết thúc rồi, tạm biệt các bạn!"},  # last shot
    ]

    # Chọn tối đa 3 shot
    selected = select_shots_for_video(scenes, max_clips=3)
    assert len(selected) == 3
    selected_ids = [sc["id"] for sc in selected]
    # S01 (đầu cảnh 1), S03 (đầu cảnh 2), S05 (đầu cảnh 3) hoặc S04 (cao trào thở 5 ngón tay)
    assert "S01" in selected_ids
    assert "S03" in selected_ids


def test_manual_clip_priority_and_injection(tmp_path: Path):
    """Kiểm tra ưu tiên clip tay ở thư mục content/episodes/<ep>/clips/<shotId>.mp4."""
    store = ProjectStore(project_id="test_ep_proj", repo_root=tmp_path)
    clips_dir = store.project_dir / "content" / "episodes" / "ep01" / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    s01_clip = clips_dir / "S01.mp4"
    s01_clip.write_bytes(b"dummy manual clip content S01")

    scenes = [
        {"id": "S01", "image": "assets/s01.png"},
        {"id": "S02", "image": "assets/s02.png"},
    ]

    injected = inject_manual_clips(scenes, store.project_dir, episode_id="ep01")
    assert injected[0]["video"] == str(s01_clip.resolve())
    assert injected[0]["videoSource"] == "manual"
    assert injected[1].get("video") is None


@pytest.mark.anyio
async def test_shot_video_auto_mode_uses_manual_if_exists_else_calls_ai(tmp_path: Path):
    """Kiểm tra chế độ auto: có clip tay thì dùng, không có thì gọi AI."""
    store = ProjectStore(project_id="test_ep_proj", repo_root=tmp_path)
    clips_dir = store.project_dir / "content" / "episodes" / "ep01" / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    (clips_dir / "S01.mp4").write_bytes(b"manual S01 bytes")

    engine = ShotVideoEngine(store)

    # Mock provider sinh clip cho S02
    ai_clip_art = store.store_bytes(
        data=b"ai generated video bytes",
        ext="mp4",
        kind=ArtifactKind.VIDEO,
        provenance=ArtifactProvenance(
            node_id="video_gen",
            run_id="r1",
            provider="mock-ai",
            model="mock-video",
            cost_usd=0.0,
            created_at="2026-11-06T00:00:00Z",
        ),
    )
    mock_provider = MagicMock()
    mock_provider.generate_video = AsyncMock(return_value=ai_clip_art)

    scenes = [
        {"id": "S01", "sceneIndex": 1, "image": "assets/s01.png"},
        {"id": "S02", "sceneIndex": 1, "image": "assets/s02.png"},
    ]

    out_scenes, arts = await engine.generate_per_shot_videos(
        scenes=scenes,
        provider=mock_provider,
        episode_id="ep01",
        max_clips=2,
        clip_source="auto",
        model="mock-video",
    )

    assert out_scenes[0]["videoSource"] == "manual"
    assert "S01.mp4" in out_scenes[0]["video"]
    assert out_scenes[1]["videoSource"] == "ai"
    # mock_provider chỉ được gọi 1 lần cho S02, S01 dùng clip tay!
    assert mock_provider.generate_video.call_count == 1


@pytest.mark.anyio
async def test_shot_video_ai_quota_error_keeps_image(tmp_path: Path):
    """Kiểm tra khi AI văng lỗi (QUOTA/AUTH...), hệ thống không sập mà giữ nguyên ảnh tĩnh."""
    store = ProjectStore(project_id="test_ep_proj", repo_root=tmp_path)
    engine = ShotVideoEngine(store)

    mock_provider = MagicMock()
    mock_provider.generate_video = AsyncMock(side_effect=RuntimeError("429 ResourceExhausted: Quota exceeded"))

    scenes = [
        {"id": "S01", "sceneIndex": 1, "image": "assets/s01.png", "dialogue": "Xin chào"},
    ]

    out_scenes, arts = await engine.generate_per_shot_videos(
        scenes=scenes,
        provider=mock_provider,
        episode_id="ep01",
        max_clips=1,
        clip_source="ai",
        model="veo-2",
    )

    assert len(out_scenes) == 1
    # Video là None vì AI lỗi
    assert out_scenes[0]["video"] is None
    # Giữ nguyên ảnh tĩnh gốc
    assert out_scenes[0]["image"] == "assets/s01.png"
    # Ghi nhận warning
    assert "Quota exceeded" in out_scenes[0]["videoWarning"]


@pytest.mark.anyio
async def test_shot_video_cache_hit_on_second_run(tmp_path: Path):
    """Kiểm tra cache: lần 1 gọi provider, lần 2 trúng cache (0 lần gọi provider)."""
    store = ProjectStore(project_id="test_ep_proj", repo_root=tmp_path)
    engine = ShotVideoEngine(store)

    ai_clip_art = store.store_bytes(
        data=b"ai clip test bytes",
        ext="mp4",
        kind=ArtifactKind.VIDEO,
        provenance=ArtifactProvenance(
            node_id="video_gen",
            run_id="r1",
            provider="mock-ai",
            model="mock-video",
            cost_usd=0.0,
            created_at="2026-11-06T00:00:00Z",
        ),
    )
    mock_provider = MagicMock()
    mock_provider.generate_video = AsyncMock(return_value=ai_clip_art)

    scenes = [
        {"id": "S01", "sceneIndex": 1, "image": "assets/s01.png", "videoPrompt": "Bi waves hand"},
    ]

    # Lần chạy 1
    out_1, _ = await engine.generate_per_shot_videos(
        scenes=scenes,
        provider=mock_provider,
        episode_id="ep01",
        max_clips=1,
        clip_source="ai",
        model="mock-video",
    )
    assert mock_provider.generate_video.call_count == 1
    assert out_1[0]["videoSource"] == "ai"

    # Lần chạy 2 cùng tham số
    mock_provider.generate_video.reset_mock()
    out_2, _ = await engine.generate_per_shot_videos(
        scenes=scenes,
        provider=mock_provider,
        episode_id="ep01",
        max_clips=1,
        clip_source="ai",
        model="mock-video",
    )
    # Trúng cache: 0 lần gọi provider!
    assert mock_provider.generate_video.call_count == 0
    assert out_2[0]["cached"] is True
    assert out_2[0]["video"] == out_1[0]["video"]
