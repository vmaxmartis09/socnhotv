"""Unit tests cho luồng H2: Nguồn video trả phí + đo thật (Veo 3.1 Fast, Kling v3 Pro, Seedance 1.0 Pro, Hailuo 02 Pro, Wan 2.2)."""
from __future__ import annotations

import asyncio
import base64
import json
import shutil
import sys
from pathlib import Path

import httpx
import pytest

from socnhotv.core.contracts.types import ArtifactKind
from socnhotv.core.models_registry.registry import ModelRegistry
from socnhotv.core.providers.errors import ProviderError, ProviderErrorKind
from socnhotv.core.providers.fal_provider import FalProvider
from socnhotv.core.providers.google_provider import GoogleProvider
from socnhotv.core.providers.spend_guard import SpendCapExceeded, SpendGuard
from socnhotv.core.storage.project_store import ProjectStore

FAKE_GEMINI_KEY = "AIzaSyTestVeo31FastKeyForUnitTests98765"
FAKE_FAL_KEY = "fal_live_key_12345:fal_secret_abcdef987654321"
FAKE_MP4_BYTES = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isomfakevideo"


@pytest.fixture
def tmp_store(tmp_path: Path) -> ProjectStore:
    return ProjectStore("soc-nho-tv", repo_root=tmp_path)


@pytest.fixture
def tmp_frame_file(tmp_path: Path) -> Path:
    frame_dir = tmp_path / "data" / "projects" / "soc-nho-tv" / "characters" / "soc_nho"
    frame_dir.mkdir(parents=True, exist_ok=True)
    frame = frame_dir / "soc_nho_01.png"
    # Header PNG 1x1
    frame.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return frame


def test_models_registry_has_all_five_video_models():
    """Kiểm tra ModelRegistry chứa đủ 5 model video mới của luồng H2."""
    reg = ModelRegistry.get_instance()
    expected_models = [
        ("google-veo-3.1-fast", "google", "veo-3.1-fast-generate-preview", 0.12),
        ("fal-kling-v3-pro", "fal", "fal-ai/kling-video/v3/pro/image-to-video", 0.14),
        ("fal-seedance-1.0-pro", "fal", "fal-ai/bytedance/seedance/v1/pro/image-to-video", 0.12),
        ("fal-hailuo-02-pro", "fal", "fal-ai/minimax/hailuo-02/pro/image-to-video", 0.08),
        ("fal-wan-2.2", "fal", "wan/v2.6/image-to-video", 0.05),
    ]

    for key, provider, model_id, min_cost_per_sec in expected_models:
        spec = reg.get(key)
        assert spec is not None, f"Thiếu model {key} trong registry"
        assert spec.provider == provider
        assert spec.model_id == model_id
        assert spec.kind == "video"
        assert spec.tier == "paid"
        assert spec.supports_reference is True
        assert spec.pricing.cost_per_second == pytest.approx(min_cost_per_sec, abs=1e-3)
        assert len(spec.durations_sec) > 0


def test_google_veo_3_1_fast_image_to_video_mock_transport(
    tmp_store: ProjectStore, tmp_frame_file: Path, tmp_path: Path
):
    """Kiểm tra gọi Veo 3.1 Fast image-to-video qua mock transport."""
    async def _run():
        submitted_requests = []

        def mock_handler(request: httpx.Request) -> httpx.Response:
            url_str = str(request.url)
            submitted_requests.append({"url": url_str, "method": request.method})

            if "predictLongRunning" in url_str:
                body = json.loads(request.content)
                instance = body["instances"][0]
                assert "image" in instance
                assert "bytesBase64Encoded" in instance["image"]
                assert body["parameters"]["aspectRatio"] == "16:9"
                assert body["parameters"]["durationSeconds"] == 5
                return httpx.Response(200, json={"name": "operations/test-veo-op-12345", "done": False})

            if "operations/test-veo-op-12345" in url_str:
                return httpx.Response(
                    200,
                    json={
                        "name": "operations/test-veo-op-12345",
                        "done": True,
                        "response": {
                            "generateVideoResponse": {
                                "generatedSamples": [
                                    {"video": {"uri": "https://storage.googleapis.com/test-bucket/veo.mp4"}}
                                ]
                            }
                        },
                    },
                )

            if "veo.mp4" in url_str:
                return httpx.Response(200, content=FAKE_MP4_BYTES)

            return httpx.Response(404, text="Not found")

        transport = httpx.MockTransport(mock_handler)
        guard = SpendGuard(tmp_path / "runs", cap_usd=5.0)
        provider = GoogleProvider(
            store=tmp_store,
            guard=guard,
            key=FAKE_GEMINI_KEY,
            poll_interval_sec=0.01,
            transport=transport,
        )

        art = await provider.generate_video(
            prompt="Sóc Bi vẫy tay tươi cười ở nhà cây",
            first_frame_uri="characters/soc_nho/soc_nho_01.png",
            duration_sec=5.0,
            aspect_ratio="16:9",
            model="google-veo-3.1-fast",
        )

        assert art.kind == ArtifactKind.VIDEO
        assert art.meta.width == 1920
        assert art.meta.height == 1080
        assert art.meta.duration == 5.0
        assert art.provenance.provider == "google"
        assert art.provenance.model == "veo-3.1-fast-generate-preview"
        assert art.provenance.cost_usd == pytest.approx(0.60, abs=1e-3)
        assert guard.spent() == pytest.approx(0.60, abs=1e-3)

    asyncio.run(_run())


def test_fal_kling_v3_pro_image_to_video_mock_transport(
    tmp_store: ProjectStore, tmp_frame_file: Path, tmp_path: Path
):
    """Kiểm tra gọi fal.ai Kling v3 Pro image-to-video qua mock transport."""
    async def _run():
        submitted_bodies = []

        def mock_handler(request: httpx.Request) -> httpx.Response:
            url_str = str(request.url)

            if request.method == "POST" and "kling-video/v3/pro/image-to-video" in url_str:
                body = json.loads(request.content)
                submitted_bodies.append(body)
                assert "start_image_url" in body or "image_url" in body
                assert body["duration"] == "5"
                assert body["generate_audio"] is True
                return httpx.Response(
                    200,
                    json={
                        "status_url": "https://queue.fal.run/test-status",
                        "response_url": "https://queue.fal.run/test-response",
                    },
                )

            if "test-status" in url_str:
                return httpx.Response(200, json={"status": "COMPLETED"})

            if "test-response" in url_str:
                return httpx.Response(
                    200,
                    json={"video": {"url": "https://fal.media/files/kling_pro.mp4"}},
                )

            if "kling_pro.mp4" in url_str:
                return httpx.Response(200, content=FAKE_MP4_BYTES)

            return httpx.Response(404, text="Not found")

        transport = httpx.MockTransport(mock_handler)
        guard = SpendGuard(tmp_path / "runs", cap_usd=5.0)
        provider = FalProvider(
            store=tmp_store,
            guard=guard,
            key=FAKE_FAL_KEY,
            poll_interval_sec=0.01,
            transport=transport,
        )

        art = await provider.generate_video(
            prompt="Sóc Bi vẫy tay ở nhà cây",
            first_frame_uri="characters/soc_nho/soc_nho_01.png",
            duration_sec=5.0,
            aspect_ratio="16:9",
            has_audio=True,
            model="fal-kling-v3-pro",
        )

        assert art.kind == ArtifactKind.VIDEO
        assert art.meta.width == 1920
        assert art.meta.height == 1080
        assert art.provenance.provider == "fal"
        assert art.provenance.model == "fal-ai/kling-video/v3/pro/image-to-video"
        assert art.provenance.cost_usd > 0

    asyncio.run(_run())


def test_fal_hailuo_and_seedance_and_wan_parameters(
    tmp_store: ProjectStore, tmp_frame_file: Path, tmp_path: Path
):
    """Kiểm tra tham số payload riêng của Hailuo 02 Pro, Seedance 1.0 Pro và Wan 2.2."""
    async def _run():
        recorded_endpoints = {}

        def mock_handler(request: httpx.Request) -> httpx.Response:
            url_str = str(request.url)
            if request.method == "POST":
                endpoint = url_str.replace("https://queue.fal.run/", "")
                body = json.loads(request.content)
                recorded_endpoints[endpoint] = body
                return httpx.Response(
                    200,
                    json={
                        "status_url": f"https://queue.fal.run/status-{len(recorded_endpoints)}",
                        "response_url": f"https://queue.fal.run/resp-{len(recorded_endpoints)}",
                    },
                )

            if "status-" in url_str:
                return httpx.Response(200, json={"status": "COMPLETED"})

            if "resp-" in url_str:
                return httpx.Response(
                    200,
                    json={"video": {"url": "https://fal.media/sample.mp4"}},
                )

            if "sample.mp4" in url_str:
                return httpx.Response(200, content=FAKE_MP4_BYTES)

            return httpx.Response(404)

        transport = httpx.MockTransport(mock_handler)
        guard = SpendGuard(tmp_path / "runs", cap_usd=5.0)
        provider = FalProvider(
            store=tmp_store,
            guard=guard,
            key=FAKE_FAL_KEY,
            poll_interval_sec=0.01,
            transport=transport,
        )

        # 1. Hailuo 02 Pro
        await provider.generate_video(
            prompt="Bi cười vui vẻ",
            first_frame_uri="characters/soc_nho/soc_nho_01.png",
            duration_sec=6.0,
            model="fal-hailuo-02-pro",
        )
        hailuo_payload = recorded_endpoints.get("fal-ai/minimax/hailuo-02/pro/image-to-video")
        assert hailuo_payload is not None
        assert hailuo_payload.get("prompt_optimizer") is True
        assert "image_url" in hailuo_payload

        # 2. Seedance 1.0 Pro
        await provider.generate_video(
            prompt="Camera tracking Bi",
            first_frame_uri="characters/soc_nho/soc_nho_01.png",
            duration_sec=5.0,
            model="fal-seedance-1.0-pro",
            has_audio=True,
        )
        seedance_payload = recorded_endpoints.get("fal-ai/bytedance/seedance/v1/pro/image-to-video")
        assert seedance_payload is not None
        assert seedance_payload.get("duration") == "5"
        assert seedance_payload.get("generate_audio") is True

        # 3. Wan 2.2
        await provider.generate_video(
            prompt="Bi nhảy lò cò",
            first_frame_uri="characters/soc_nho/soc_nho_01.png",
            duration_sec=5.0,
            model="fal-wan-2.2",
        )
        wan_payload = recorded_endpoints.get("wan/v2.6/image-to-video")
        assert wan_payload is not None
        assert wan_payload.get("duration") == "5"
        assert "image_url" in wan_payload

    asyncio.run(_run())


def test_spend_guard_strictly_blocks_over_five_dollars(tmp_path: Path):
    """SpendGuard chặn tuyệt đối nếu chi phí vượt quá $5.00."""
    guard = SpendGuard(tmp_path / "runs", cap_usd=5.00)
    guard.reserve(2.63, "5 models bench")
    assert guard.spent() == pytest.approx(2.63, abs=1e-3)

    # Đặt lệnh thứ 2 vượt quá $5
    with pytest.raises(SpendCapExceeded):
        guard.reserve(2.50, "vượt trần $5")


def test_video_bench_script_cli_modes(tmp_path: Path):
    """Kiểm tra CLI scripts/bench/video_bench.py ở các chế độ."""
    import subprocess

    bench_script = Path(__file__).resolve().parents[2] / "scripts" / "bench" / "video_bench.py"
    assert bench_script.exists()

    # 1. Chế độ --check-keys
    res_check = subprocess.run(
        [sys.executable, str(bench_script), "--check-keys"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "TỔNG CHI PHÍ DỰ KIẾN: $2.630 USD" in res_check.stdout
    assert "Trần: $5.00" in res_check.stdout

    # 2. Chế độ an toàn: không có --confirm-paid -> exit code 2
    res_safe = subprocess.run(
        [sys.executable, str(bench_script)],
        capture_output=True,
        text=True,
    )
    assert res_safe.returncode == 2
    assert "CHÚ Ý BẢO VỆ CHI PHÍ" in res_safe.stdout

    # 3. Chế độ --mock chạy thành công $0
    out_dir = tmp_path / "bench_out"
    res_mock = subprocess.run(
        [
            sys.executable,
            str(bench_script),
            "--mock",
            "--models",
            "fal-wan-2.2",
            "fal-hailuo-02-pro",
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "SUCCESS (MOCK)" in res_mock.stdout
    assert (out_dir / "benchmark_results.json").exists()
