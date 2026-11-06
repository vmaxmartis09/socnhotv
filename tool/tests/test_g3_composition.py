import asyncio
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
    NodeInstance,
)
from socnhotv.core.storage.project_store import ProjectStore
from socnhotv.video.craft.camera import (
    parse_camera_move,
    build_shot_camera_gsap,
    get_camera_preset,
    CAMERA_PRESETS,
)
from socnhotv.video.hyperframes_engine import HyperFramesEngine, find_hyperframes_bin
from socnhotv.core.adapters.hyperframes_adapter import HyperFramesAdapter


def test_camera_presets_and_parsing():
    """Kiểm tra mapping các trường camera kịch bản sang camera preset chuẩn."""
    assert parse_camera_move("smooth push-in") == "push-in"
    assert parse_camera_move("eye-level, 50mm, push-in") == "push-in"
    assert parse_camera_move("eye-level, 35mm, static") == "static"
    assert parse_camera_move("slow pan left") == "pan-left"
    assert parse_camera_move("pan right") == "pan-right"
    assert parse_camera_move("tilt up") == "tilt-up"
    assert parse_camera_move("tilt down") == "tilt-down"
    assert parse_camera_move("dolly-out") == "dolly-out"
    assert parse_camera_move("ken-burns") == "ken-burns"
    assert parse_camera_move("punch-in") == "punch-in"
    assert parse_camera_move("") == "push-in"


def test_camera_gsap_shot_duration_behaviors():
    """Kiểm tra sinh mã GSAP cho shot ngắn (1 nhịp) và shot dài 20s (3 nhịp)."""
    # Shot ngắn (4s)
    snippet_short = build_shot_camera_gsap(
        target_selector="#img_scene_1",
        start_time=0.0,
        duration_sec=4.0,
        camera_name="pan-left",
        is_video=False,
    )
    assert "Short Shot" in snippet_short
    assert "tl.fromTo" in snippet_short
    assert "x: 35.0" in snippet_short
    assert "x: -35.0" in snippet_short

    # Shot dài 20s (hoạt hình Sóc Nhỏ chuẩn)
    snippet_long = build_shot_camera_gsap(
        target_selector="#img_scene_2",
        start_time=20.0,
        duration_sec=20.0,
        camera_name="push-in",
        is_video=False,
    )
    assert "3-Beat Long Shot 20.0s" in snippet_long
    assert "Nhịp 1: Xuất hiện & Mở đầu cú máy" in snippet_long
    assert "Nhịp 2: Giữ & Trôi góc nhẹ tự nhiên" in snippet_long
    assert "Nhịp 3: Định hình đích & Chuẩn bị chuyển cảnh" in snippet_long
    # Kiểm tra tính tất định: các mốc thời gian đều được nội suy theo timeline
    assert "20.000" in snippet_long
    assert "27.000" in snippet_long  # 20 + 20*0.35 = 27
    assert "35.000" in snippet_long  # 27 + 20*0.40 = 35


def test_html_composition_different_cameras_and_transitions(tmp_path: Path):
    """Kiểm tra composition HTML sinh ra có tween khác nhau cho các camera và ghi nhận transition."""
    engine = HyperFramesEngine()
    scenes = [
        {
            "id": "S01",
            "sceneIndex": 1,
            "durationSec": 20.0,
            "image": "assets/s01.png",
            "camera": "smooth push-in",
            "dialogue": "Chào các bạn nhỏ!",
        },
        {
            "id": "S02",
            "sceneIndex": 1,
            "durationSec": 20.0,
            "image": "assets/s02.png",
            "camera": "eye-level, 35mm, static",
            "dialogue": "Mun mang quả bóng sang nè!",
        },
        {
            "id": "S03",
            "sceneIndex": 2,  # Đổi sceneIndex sang cảnh 2 -> kích hoạt transition foresight
            "durationSec": 20.0,
            "image": "assets/s03.png",
            "camera": "slow pan left",
            "dialogue": "Bụng Bi nóng ran...",
        },
    ]

    html = engine.generate_composition_html(
        scenes=scenes,
        voiceover_rel_path="assets/voiceover.mp3",
        total_duration=60.0,
        title_badge="TẬP 01: NÚI LỬA TRONG BỤNG BI",
    )

    # 1. Có camera push-in cho S01
    assert "Shot SCENE_1 (push-in" in html
    # 2. Có camera static cho S02
    assert "Shot SCENE_2 (static" in html
    # 3. Có camera pan-left cho S03
    assert "Shot SCENE_3 (pan-left" in html
    # 4. Có Transition foresight khi sceneIndex chuyển từ 1 sang 2
    assert "Transition foresight: Scene 1 -> 2" in html
    # 5. Đảm bảo các scene container có visibility control
    assert 'tl.set("#scene_1", { opacity: 1, pointerEvents: "auto" }, 0.000);' in html
    assert 'tl.set("#scene_1", { opacity: 0, pointerEvents: "none" }, 20.000);' in html


def test_find_hyperframes_binary():
    """Kiểm tra định vị binary HyperFrames ghim sẵn."""
    bin_path = find_hyperframes_bin()
    assert bin_path is not None
    assert "hyperframes" in str(bin_path)


@pytest.mark.anyio
async def test_hyperframes_render_failure_does_not_call_generate_video(tmp_path: Path):
    """Kiểm tra khi HyperFrames render lỗi, hệ thống raise lỗi và TUYỆT ĐỐI KHÔNG gọi generate_video."""
    from socnhotv.core.engine.graph_runner import GraphRunner

    # Tạo mock provider có spy đếm số lần gọi generate_video
    mock_provider = MagicMock()
    mock_provider.generate_video = AsyncMock()

    # Tạo store tạm trong tmp_path
    store = ProjectStore(project_id="test_proj", repo_root=tmp_path)
    store.project_dir.mkdir(parents=True, exist_ok=True)

    runner = GraphRunner(store=store, provider=mock_provider)

    # Mock adapter để ép render_from_artifacts văng lỗi
    with patch("socnhotv.core.engine.graph_runner.HyperFramesAdapter") as mock_adapter_cls:
        instance = mock_adapter_cls.return_value
        instance.render_from_artifacts = AsyncMock(side_effect=RuntimeError("HyperFrames CLI crashed"))
        instance.last_cli_error = "Chrome headless launch error"

        node = NodeInstance(
            id="n_render",
            type="hyperframes_render",
            title="Dựng HyperFrames",
            params={"requireHyperFrames": True},
        )

        audio_art = store.store_bytes(
            data=b"dummy audio content",
            ext="mp3",
            kind=ArtifactKind.AUDIO,
            provenance=ArtifactProvenance(
                node_id="n_voice",
                run_id="r1",
                provider="local",
                model="mock",
                cost_usd=0.0,
                created_at="2026-11-06T00:00:00Z",
            ),
        )

        resolved_inputs = {
            "scenes": [{"image": "assets/s1.png", "durationSec": 5.0}],
            "audio": audio_art,
        }

        with pytest.raises(RuntimeError) as exc_info:
            await runner._execute_node_handler(
                node=node,
                resolved_inputs=resolved_inputs,
                run_id="run_test",
                is_mock=False,
            )

        assert "HyperFrames render thất bại" in str(exc_info.value)
        # Bằng chứng cốt lõi: mock_provider.generate_video KHÔNG HỀ ĐƯỢC GỌI!
        assert mock_provider.generate_video.call_count == 0
