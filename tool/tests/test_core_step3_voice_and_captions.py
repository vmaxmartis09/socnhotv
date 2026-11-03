from __future__ import annotations

import asyncio
import os
import tempfile
import time
import pytest

from socnhotv.core.adapters.audio_mastering import AudioMastering
from socnhotv.core.adapters.caption_adapter import (
    CaptionAdapter,
    format_timestamp_srt,
    format_timestamp_vtt,
)
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
from socnhotv.core.providers.mock_provider import create_minimal_wav_bytes
from socnhotv.core.storage.project_store import ProjectStore


@pytest.fixture(autouse=True)
def setup_registry():
    NodeRegistry.initialize_defaults()


def test_timestamp_formatters():
    """Kiểm tra độ chính xác của hàm format timestamp SRT và VTT."""
    # 0 giây
    assert format_timestamp_srt(0.0) == "00:00:00,000"
    assert format_timestamp_vtt(0.0) == "00:00:00.000"

    # 75.42 giây = 1 phút 15 giây 420 ms
    assert format_timestamp_srt(75.42) == "00:01:15,420"
    assert format_timestamp_vtt(75.42) == "00:01:15.420"

    # 3661.105 giây = 1 giờ 1 phút 1 giây 105 ms
    assert format_timestamp_srt(3661.105) == "01:01:01,105"
    assert format_timestamp_vtt(3661.105) == "01:01:01.105"


def test_audio_mastering_pipeline():
    """Kiểm tra chuỗi TikTok Mastering (-14 LUFS, presence EQ, de-esser)."""
    mastering = AudioMastering()

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_wav = os.path.join(tmp_dir, "input.wav")
        output_mp3 = os.path.join(tmp_dir, "mastered_output.mp3")

        # Tạo file WAV PCM âm thanh mẫu
        wav_bytes = create_minimal_wav_bytes(duration_sec=3.0)
        with open(input_wav, "wb") as f:
            f.write(wav_bytes)

        res_path = mastering.master_tiktok(
            input_audio_path=input_wav,
            output_audio_path=output_mp3,
            target_lufs=-14.0,
            presence_boost_db=3.5,
            tempo_factor=1.10,
            bitrate="192k",
        )

        assert os.path.exists(res_path)
        assert os.path.getsize(res_path) > 0
        assert res_path.endswith(".mp3")


def test_voice_adapter_profile_resolution():
    """Kiểm tra VoiceAdapter tự động tìm kiếm đúng thư mục voice vault."""
    store = ProjectStore("soc-nho-tv")
    adapter = VoiceAdapter(store)

    profile_path = adapter.resolve_voice_profile("soc-nho")
    assert profile_path is not None
    assert profile_path.exists()
    assert (profile_path / "profile.json").exists()


def test_voice_adapter_synthesis():
    """Kiểm tra tổng hợp giọng nói tiếng Việt thực tế và lưu vào ProjectStore."""
    async def _test():
        store = ProjectStore("soc-nho-tv")
        adapter = VoiceAdapter(store)

        text = "Xin chào các bạn nhỏ, mình là Sóc Nhỏ Bi TV đây nè!"
        artifact = await adapter.synthesize(
            text=text,
            voice_id="soc-nho",
            tempo=1.10,
            node_id="test_voice_node",
            run_id="run_voice_test",
        )

        assert isinstance(artifact, Artifact)
        assert artifact.kind == ArtifactKind.AUDIO
        assert artifact.mime in ["audio/mpeg", "audio/mp3"]
        assert artifact.size > 0
        assert artifact.meta.duration is not None and artifact.meta.duration > 0

        # Kiểm tra file vật lý tồn tại trong kho deduplicated của store
        physical_file = store.project_dir / artifact.uri
        assert physical_file.exists()
        assert physical_file.stat().st_size == artifact.size

        return artifact

    artifact = asyncio.run(_test())
    assert artifact is not None


def test_caption_adapter_transcription_and_generation():
    """Kiểm tra tách phụ đề Whisper từ tệp âm thanh thực tế."""
    async def _test():
        store = ProjectStore("soc-nho-tv")
        voice_adapter = VoiceAdapter(store)
        caption_adapter = CaptionAdapter(store, model_size="tiny")

        # 1. Sinh audio ngắn
        text = "Sóc Nhỏ thích ăn hạt dẻ."
        audio_art = await voice_adapter.synthesize(
            text=text,
            voice_id="soc-nho",
            node_id="voice_src",
            run_id="run_cap_test",
        )

        # 2. Tách phụ đề
        sub_art = await caption_adapter.generate_captions(
            audio_source=audio_art,
            node_id="caption_node",
            run_id="run_cap_test",
            language="vi",
        )

        assert isinstance(sub_art, Artifact)
        assert sub_art.kind == ArtifactKind.CAPTIONS
        assert sub_art.size > 0

        # Đọc nội dung file SRT được lưu
        srt_file = store.project_dir / sub_art.uri
        assert srt_file.exists()
        srt_content = srt_file.read_text(encoding="utf-8")

        # Kiểm tra cấu trúc SRT chuẩn
        assert "-->" in srt_content
        assert "00:00:" in srt_content

    asyncio.run(_test())


def test_end_to_end_voice_and_caption_dag():
    """Kiểm tra chạy đồ thị DAG thực tế kết nối: Text -> Voice TTS -> Captions."""
    async def _test():
        store = ProjectStore("soc-nho-tv")
        runner = GraphRunner(store=store)

        node_text = NodeInstance(
            id="node_input_text",
            type="text",
            params={"content": "Chào mừng các bạn đến với kênh Sóc Nhỏ TV!"},
        )
        node_voice = NodeInstance(
            id="node_tts",
            type="voice_tts",
            params={"voiceId": "soc-nho", "tempo": 1.10},
        )
        node_captions = NodeInstance(
            id="node_subtitles",
            type="captions",
            params={},
        )

        edges = [
            Edge(
                id="e1",
                source_node_id="node_input_text",
                source_port="text",
                target_node_id="node_tts",
                target_port="text",
            ),
            Edge(
                id="e2",
                source_node_id="node_tts",
                source_port="audio",
                target_node_id="node_subtitles",
                target_port="audio",
            ),
        ]

        graph = Graph(
            id="graph_voice_caption_pipeline",
            project_id="soc-nho-tv",
            nodes=[node_text, node_voice, node_captions],
            edges=edges,
            updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        # Chạy đồ thị với mock_mode = False để kích hoạt tool adapter thật!
        req = GraphRunRequest(
            project_id="soc-nho-tv",
            mode=RunMode.ALL,
            mock_mode=False,
        )

        summary = await runner.run(graph, req)

        assert summary.is_success is True
        assert len(summary.failed_nodes) == 0
        assert set(summary.executed_nodes) == {"node_input_text", "node_tts", "node_subtitles"}

        # Kiểm tra node Voice TTS có sinh Audio MP3
        voice_node = next(n for n in graph.nodes if n.id == "node_tts")
        assert voice_node.state == NodeState.COMPLETED
        assert voice_node.pinned_generation_id is not None

        # Kiểm tra node Captions có sinh SRT
        caption_node = next(n for n in graph.nodes if n.id == "node_subtitles")
        assert caption_node.state == NodeState.COMPLETED
        assert caption_node.pinned_generation_id is not None

    asyncio.run(_test())
