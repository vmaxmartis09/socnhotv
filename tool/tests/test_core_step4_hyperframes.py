from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
import pytest

from socnhotv.core.adapters.hyperframes_adapter import HyperFramesAdapter
from socnhotv.core.adapters.voice_adapter import VoiceAdapter
from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    Edge,
    Graph,
    GraphRunRequest,
    NodeInstance,
    NodeState,
    RunMode,
)
from socnhotv.core.engine.graph_runner import GraphRunner
from socnhotv.core.nodes.registry import NodeRegistry
from socnhotv.core.providers.mock_provider import create_minimal_png_bytes
from socnhotv.core.storage.project_store import ProjectStore


@pytest.fixture(autouse=True)
def setup_registry():
    NodeRegistry.initialize_defaults()


def test_hyperframes_html_generation():
    """Kiểm tra sinh mã nguồn HTML5/GSAP chuẩn Safe Zone TikTok 9:16."""
    store = ProjectStore("soc-nho-tv")
    adapter = HyperFramesAdapter(store)

    scenes = [
        {
            "sceneNumber": 1,
            "img": "assets/scene_01.png",
            "durationSec": 4.5,
            "dialogue": "Chào mừng các bạn nhỏ!",
        },
        {
            "sceneNumber": 2,
            "video": "assets/scene_02.mp4",
            "durationSec": 5.5,
            "dialogue": "Hôm nay Bi sẽ kể một câu chuyện thật vui nhé!",
        },
    ]

    html = adapter.generate_html_composition(
        scenes=scenes,
        voiceover_rel_path="assets/voiceover.mp3",
        total_duration=10.0,
        title_badge="SÓC NHỎ TV • TẬP 1",
        width=1080,
        height=1920,
        fps=30,
    )

    # 1. Kiểm tra kích thước và Safe Zone TikTok
    assert "width=1080, height=1920" in html
    assert "top: 200px" in html  # Header Safe Zone
    assert "top: 1360px" in html  # Subtitle Safe Zone
    assert "SÓC NHỎ TV • TẬP 1" in html

    # 2. Kiểm tra GSAP seekable timeline
    assert "gsap.timeline" in html
    assert 'window.__timelines["main"] = tl;' in html
    assert "tl.seek(0);" in html

    # 3. Kiểm tra các clips và phụ đề
    assert "Chào mừng các bạn nhỏ!" in html
    assert "assets/scene_01.png" in html
    assert "assets/scene_02.mp4" in html
    assert "assets/voiceover.mp3" in html


def test_hyperframes_project_bundle():
    """Kiểm tra đóng gói bundle dự án HyperFrames với đường dẫn tương đối."""
    store = ProjectStore("soc-nho-tv")
    adapter = HyperFramesAdapter(store)

    with tempfile.TemporaryDirectory() as tmp_dir:
        bundle_dir = Path(tmp_dir) / "hf_bundle"
        mock_audio = Path(tmp_dir) / "dummy_voice.mp3"

        # Tạo file audio giả lập
        from socnhotv.core.providers.mock_provider import create_minimal_wav_bytes
        mock_audio.write_bytes(create_minimal_wav_bytes(duration_sec=3.0))

        scenes = [
            {"image": str(mock_audio), "durationSec": 3.0, "dialogue": "Hello Bi"}
        ]

        adapter.build_project_bundle(
            target_dir=bundle_dir,
            scenes=scenes,
            audio_voiceover_path=mock_audio,
            title_badge="SÓC NHỎ TEST",
            width=1080,
            height=1920,
            fps=30,
        )

        assert (bundle_dir / "index.html").exists()
        assert (bundle_dir / "hyperframes.json").exists()
        assert (bundle_dir / "assets").exists()
        assert (bundle_dir / "assets" / "voiceover.mp3").exists()

        # Kiểm tra nội dung hyperframes.json
        config = json.loads((bundle_dir / "hyperframes.json").read_text())
        assert config["width"] == 1080
        assert config["height"] == 1920
        assert config["fps"] == 30


def test_hyperframes_render_fallback_ffmpeg():
    """Kiểm tra render video MP4 9:16 bằng FFmpeg Compositor."""
    store = ProjectStore("soc-nho-tv")
    adapter = HyperFramesAdapter(store)

    with tempfile.TemporaryDirectory() as tmp_dir:
        bundle_dir = Path(tmp_dir) / "hf_render_proj"
        assets_dir = bundle_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Tạo ảnh phân cảnh mẫu PNG 1080x1920
        png_bytes = create_minimal_png_bytes(width=1080, height=1920)
        (assets_dir / "scene_01_frame.png").write_bytes(png_bytes)

        # Tạo audio mẫu
        from socnhotv.core.providers.mock_provider import create_minimal_wav_bytes
        (assets_dir / "voiceover.mp3").write_bytes(create_minimal_wav_bytes(duration_sec=2.0))

        out_mp4 = Path(tmp_dir) / "rendered_output.mp4"
        res_mp4 = adapter.render_fallback_ffmpeg(
            project_dir=bundle_dir,
            output_mp4=out_mp4,
            fps=24,
        )

        assert res_mp4.exists()
        assert res_mp4.stat().st_size > 0
        assert res_mp4.suffix == ".mp4"


def test_hyperframes_render_from_artifacts():
    """Kiểm tra render từ các Artifacts trong ProjectStore."""
    async def _test():
        store = ProjectStore("soc-nho-tv")
        adapter = HyperFramesAdapter(store)
        voice_adapter = VoiceAdapter(store)

        # 1. Tạo artifact voice
        voice_art = await voice_adapter.synthesize(
            text="Sóc Nhỏ chào cả nhà!",
            voice_id="soc-nho",
            node_id="voice_hf",
            run_id="run_hf_test",
        )

        # 2. Tạo artifact ảnh
        png_data = create_minimal_png_bytes(1080, 1920)
        from socnhotv.core.contracts.types import ArtifactProvenance, ArtifactMeta
        prov = ArtifactProvenance(
            node_id="img_hf",
            provider="test",
            model="test-img",
            cost_usd=0.0,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        img_art = store.store_bytes(
            data=png_data,
            ext="png",
            kind=ArtifactKind.IMAGE,
            provenance=prov,
            meta=ArtifactMeta(width=1080, height=1920),
        )

        scenes = [
            {"image": str(store.project_dir / img_art.uri), "dialogue": "Sóc Nhỏ chào cả nhà!", "durationSec": 3.0}
        ]

        # 3. Render video
        video_art = await adapter.render_from_artifacts(
            scenes=scenes,
            voice_artifact=voice_art,
            title_badge="SÓC NHỎ BI TV",
            node_id="hf_node",
            run_id="run_hf_test",
        )

        assert isinstance(video_art, Artifact)
        assert video_art.kind == ArtifactKind.VIDEO
        assert video_art.meta.aspect == "9:16"
        assert video_art.meta.width == 1080
        assert video_art.meta.height == 1920
        assert video_art.size > 0

        # Kiểm tra file vật lý tồn tại
        physical_file = store.project_dir / video_art.uri
        assert physical_file.exists()
        assert physical_file.stat().st_size == video_art.size

    asyncio.run(_test())


def test_end_to_end_hyperframes_dag():
    """Kiểm tra chạy toàn diện DAG: Text -> Voice TTS -> HyperFrames Render -> MP4 9:16."""
    async def _test():
        store = ProjectStore("soc-nho-tv")
        runner = GraphRunner(store=store)

        node_text = NodeInstance(
            id="node_script_text",
            type="text",
            params={"content": "Chào các bạn, mình là Sóc Nhỏ Bi!"},
        )
        node_voice = NodeInstance(
            id="node_tts_voice",
            type="voice_tts",
            params={"voiceId": "soc-nho", "tempo": 1.10},
        )
        node_render = NodeInstance(
            id="node_final_render",
            type="hyperframes_render",
            params={"titleBadge": "SÓC NHỎ TV • TẬP ĐẶC BIỆT"},
        )

        edges = [
            Edge(
                id="e1",
                source_node_id="node_script_text",
                source_port="text",
                target_node_id="node_tts_voice",
                target_port="text",
            ),
            Edge(
                id="e2",
                source_node_id="node_tts_voice",
                source_port="audio",
                target_node_id="node_final_render",
                target_port="audio",
            ),
        ]

        graph = Graph(
            id="graph_hyperframes_pipeline",
            project_id="soc-nho-tv",
            nodes=[node_text, node_voice, node_render],
            edges=edges,
            updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        # Chạy DAG thật không dùng mock
        req = GraphRunRequest(
            project_id="soc-nho-tv",
            mode=RunMode.ALL,
            mock_mode=False,
        )

        summary = await runner.run(graph, req)

        assert summary.is_success is True
        assert len(summary.failed_nodes) == 0
        assert "node_final_render" in summary.executed_nodes

        # Kiểm tra node render có ghim generation video MP4
        render_node = next(n for n in graph.nodes if n.id == "node_final_render")
        assert render_node.state == NodeState.COMPLETED
        assert render_node.pinned_generation_id is not None

        pinned_gen = next(g for g in render_node.generations if g.id == render_node.pinned_generation_id)
        art = store.get_artifact(pinned_gen.artifact_id)
        assert art is not None
        assert art.kind == ArtifactKind.VIDEO
        assert art.meta.aspect == "9:16"

    asyncio.run(_test())
