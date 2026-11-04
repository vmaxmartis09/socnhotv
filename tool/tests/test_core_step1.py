import pytest
import os
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

from socnhotv.core.contracts.types import (
    PortType,
    is_port_compatible,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
    NodeState,
)
from socnhotv.core.models_registry.registry import ModelRegistry
from socnhotv.core.nodes.registry import NodeRegistry
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root
from socnhotv.core.providers.mock_provider import MockProvider
from socnhotv.core.api.app import app


def test_port_compatibility():
    """Kiểm tra quy tắc tương thích cổng dữ liệu."""
    assert is_port_compatible(PortType.IMAGE, PortType.IMAGE) is True
    assert is_port_compatible(PortType.IMAGE, PortType.IMAGE_LIST) is True
    assert is_port_compatible(PortType.TEXT, PortType.TEXT) is True
    assert is_port_compatible(PortType.TEXT, PortType.IMAGE) is False
    assert is_port_compatible(PortType.VIDEO, PortType.AUDIO) is False


def test_node_registry_completeness():
    """Kiểm tra danh mục 13 node chuẩn + 3 node đơn giản (nhân vật từ ảnh, cảnh, chuyển cảnh) + các node mở rộng."""
    definitions = NodeRegistry.list_all()
    assert len(definitions) >= 16

    # Kiểm tra các node cốt lõi
    type_names = {d.type_name for d in definitions}
    expected = {
        "text", "image", "character", "script", "vision_analyze",
        "quality_check", "image_gen", "image_edit", "video_gen",
        "voice_tts", "captions", "hyperframes_render", "export",
        "character_image", "scene", "transition",
    }
    assert expected.issubset(type_names)


def test_models_registry_and_pricing():
    """Kiểm tra sổ model và tính toán chi phí ước tính."""
    registry = ModelRegistry.get_instance()
    models = registry.list_all()
    assert len(models) >= 7

    # Mock model miễn phí
    cost_mock = registry.estimate_cost("mock-image", {"n": 4})
    assert cost_mock == 0.0

    # Gemini Image ($0.03 / generation)
    cost_gemini = registry.estimate_cost("gemini-2.5-flash-image", {"n": 2})
    assert cost_gemini == 0.06

    # Veo Video ($0.15 / sec)
    cost_veo = registry.estimate_cost("google-veo-2", {"duration": 8.0})
    assert cost_veo == 1.20


def test_project_store_and_artifact_deduplication(tmp_path):
    """Kiểm tra lưu trữ artifact, tính mã băm sha256 và deduplication."""
    store = ProjectStore("test_project_temp", repo_root=tmp_path)

    data1 = b"HELLO_SOCNHOTV_PIXEL_DATA"
    prov1 = ArtifactProvenance(
        node_id="node_img_1",
        run_id="run_test",
        provider="mock",
        model="mock-v1",
        created_at="2026-11-03T00:00:00Z"
    )
    art1 = store.store_bytes(data1, "png", ArtifactKind.IMAGE, prov1)

    assert art1.id.startswith("art_")
    assert art1.hash.startswith("sha256:")
    assert art1.size == len(data1)

    # Lưu lại cùng dữ liệu -> cùng hash, không tạo file mới
    art2 = store.store_bytes(data1, "png", ArtifactKind.IMAGE, prov1)
    assert art1.hash == art2.hash
    assert art1.uri == art2.uri

    # Ghi nhận sổ chi phí
    store.record_cost_ledger("run_test", art1.id, 0.04, "test-model")
    ledger_file = store.runs_dir / "run_test" / "ledger.json"
    assert ledger_file.exists()


def test_mock_provider(tmp_path):
    """Kiểm tra sinh artifact giả lập từ MockProvider."""
    import asyncio

    async def _run():
        store = ProjectStore("test_mock_project", repo_root=tmp_path)
        provider = MockProvider(store)

        # Sinh ảnh mock
        images = await provider.generate_images("A baby squirrel Bi", aspect_ratio="9:16", n=2)
        assert len(images) == 2
        assert images[0].kind == ArtifactKind.IMAGE
        assert images[0].meta.aspect == "9:16"
        assert (store.project_dir / images[0].uri).exists()

        # Sinh video mock
        video = await provider.generate_video("Dolly camera", duration_sec=5.0, aspect_ratio="9:16")
        assert video.kind == ArtifactKind.VIDEO
        assert video.meta.duration == 5.0
        assert (store.project_dir / video.uri).exists()

        # Sinh giọng mock
        voice = await provider.speak_voice("Chào bạn, mình là Bi", voice_id="soc-nho")
        assert voice.kind == ArtifactKind.AUDIO
        assert voice.meta.duration is not None
        assert (store.project_dir / voice.uri).exists()

    asyncio.run(_run())


def test_fastapi_endpoints():
    """Kiểm tra các endpoints REST cơ bản của FastAPI."""
    client = TestClient(app)

    # 1. Healthcheck
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    # 2. Node types
    res_types = client.get("/node-types")
    assert res_types.status_code == 200
    assert len(res_types.json()) >= 16

    # 3. Models
    res_models = client.get("/models")
    assert res_models.status_code == 200
    assert len(res_models.json()) >= 7

    # 4. Projects
    res_projects = client.get("/projects")
    assert res_projects.status_code == 200
