"""Bộ kiểm thử hợp đồng Bước 5 Core:
- Provider thật: Google Gemini/Veo & fal.ai Queue (dùng httpx.MockTransport phản hồi ghi sẵn, không tốn phí mạng)
- Khóa chi tiêu đa tầng SpendGuard (trần dự án, trần 24h, trần MCP/Agent)
- Kho khóa API KeyVault & che khóa redact_secrets
- Bộ định tuyến đa nhà cung cấp ProviderRouter & dừng ngay không retry lỗi CONTENT_BLOCKED/AUTH
- Ước tính giá (/estimate) & cổng xác nhận chi phí trước khi chạy (confirmPaidRun -> HTTP 409)
"""
from __future__ import annotations

import asyncio
import base64
import importlib
import json
import os
import stat
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx
import pytest
from fastapi.testclient import TestClient

app_module = importlib.import_module("socnhotv.core.api.app")
from socnhotv.core.contracts.types import (
    ArtifactKind,
    Edge,
    Graph,
    GraphRunRequest,
    NodeInstance,
    NodeState,
    RunMode,
)
from socnhotv.core.engine.graph_runner import GraphRunner
from socnhotv.core.providers import (
    FalProvider,
    GoogleProvider,
    KeyVault,
    ProviderError,
    ProviderErrorKind,
    ProviderRouter,
    SpendCapExceeded,
    SpendGuard,
    classify_http_error,
    redact_secrets,
)
from socnhotv.core.providers.mock_provider import create_minimal_png_bytes
from socnhotv.core.storage.project_store import ProjectStore

FAKE_GEMINI_KEY = "AIzaSyD9TestKeyForUnitTestsOnly987654321"
FAKE_FAL_KEY = "fal_live_key_id_12345:fal_secret_value_abcdef98765"
FAKE_MP4_BYTES = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isomfakevideodata"


@pytest.fixture
def isolated_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ProjectStore:
    """Tạo ProjectStore cô lập hoàn toàn trong tmp_path để không ghi rác vào data/ thật."""
    proj_root = tmp_path / "data" / "projects" / "test-step5"
    for sub in ("assets", "runs", "output", "characters"):
        (proj_root / sub).mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("socnhotv.core.storage.project_store.get_repo_root", lambda: tmp_path)
    return ProjectStore("test-step5")


def test_secret_redaction_and_error_classification():
    """Kiểm tra bộ lọc che khóa API và phân loại lỗi HTTP retryable / non-retryable."""
    raw_msg = (
        f"Request failed with Authorization: Key {FAKE_FAL_KEY}, "
        f"header x-goog-api-key={FAKE_GEMINI_KEY}, url https://x.test?key={FAKE_GEMINI_KEY} "
        "and Bearer sk-proj-supersecret1234567890"
    )
    cleaned = redact_secrets(raw_msg, extra_secrets=[FAKE_FAL_KEY, FAKE_GEMINI_KEY])
    assert FAKE_GEMINI_KEY not in cleaned
    assert FAKE_FAL_KEY not in cleaned
    assert "sk-proj-supersecret1234567890" not in cleaned
    assert "***REDACTED***" in cleaned

    err_401 = classify_http_error("google", 401, f"Invalid key {FAKE_GEMINI_KEY}", [FAKE_GEMINI_KEY])
    assert err_401.kind == ProviderErrorKind.AUTH
    assert err_401.retryable is False
    assert FAKE_GEMINI_KEY not in str(err_401)

    err_429_rate = classify_http_error("fal", 429, "Too many requests per minute, slow down")
    assert err_429_rate.kind == ProviderErrorKind.TRANSIENT
    assert err_429_rate.retryable is True

    err_429_quota = classify_http_error("fal", 429, "Exhausted balance / insufficient credit")
    assert err_429_quota.kind == ProviderErrorKind.QUOTA
    assert err_429_quota.retryable is False

    err_safety = classify_http_error("google", 400, "Request rejected by safety policy filter")
    assert err_safety.kind == ProviderErrorKind.CONTENT_BLOCKED
    assert err_safety.retryable is False

    err_503 = classify_http_error("google", 503, "Backend temporarily unavailable")
    assert err_503.kind == ProviderErrorKind.TRANSIENT
    assert err_503.retryable is True


def test_google_provider_contract_images_edit_video_text_and_refund(isolated_store: ProjectStore):
    """Kiểm tra toàn diện hợp đồng GoogleProvider bằng phản hồi ghi sẵn (0 gọi mạng thật)."""

    async def _run():
        png_bytes = create_minimal_png_bytes(320, 568)
        png_b64 = base64.b64encode(png_bytes).decode("ascii")
        ref_rel = "assets/ref_soc_nho.png"
        (isolated_store.project_dir / ref_rel).write_bytes(png_bytes)

        poll_counter = {"count": 0}
        force_401 = {"enabled": False}

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers.get("x-goog-api-key") == FAKE_GEMINI_KEY
            url = str(request.url)

            if force_401["enabled"]:
                return httpx.Response(401, text=f"API key invalid: {FAKE_GEMINI_KEY}")

            if ":generateContent" in url:
                payload = json.loads(request.content.decode("utf-8"))
                gen_cfg = payload.get("generationConfig", {})
                if "IMAGE" in gen_cfg.get("responseModalities", []):
                    return httpx.Response(
                        200,
                        json={
                            "candidates": [
                                {
                                    "content": {
                                        "parts": [
                                            {"inlineData": {"mimeType": "image/png", "data": png_b64}}
                                        ]
                                    }
                                }
                            ]
                        },
                    )
                return httpx.Response(
                    200,
                    json={
                        "candidates": [
                            {
                                "content": {
                                    "parts": [
                                        {
                                            "text": json.dumps(
                                                {
                                                    "scenes": [
                                                        {
                                                            "sceneNumber": 1,
                                                            "imagePrompt": "Bi cười tươi",
                                                            "videoPrompt": "Zoom chậm",
                                                            "dialogue": "Xin chào các bạn!",
                                                            "durationSec": 6.0,
                                                        }
                                                    ]
                                                },
                                                ensure_ascii=False,
                                            )
                                        }
                                    ]
                                }
                            }
                        ]
                    },
                )

            if ":predictLongRunning" in url:
                return httpx.Response(200, json={"name": "operations/veo-op-123", "done": False})

            if "operations/veo-op-123" in url:
                poll_counter["count"] += 1
                if poll_counter["count"] < 2:
                    return httpx.Response(200, json={"name": "operations/veo-op-123", "done": False})
                return httpx.Response(
                    200,
                    json={
                        "name": "operations/veo-op-123",
                        "done": True,
                        "response": {
                            "generateVideoResponse": {
                                "generatedSamples": [
                                    {"video": {"uri": "https://generativelanguage.googleapis.com/v1beta/files/v123"}}
                                ]
                            }
                        },
                    },
                )

            if "/files/v123" in url:
                return httpx.Response(200, content=FAKE_MP4_BYTES, headers={"Content-Type": "video/mp4"})

            return httpx.Response(404, text="Not mocked")

        guard = SpendGuard(isolated_store.runs_dir, cap_usd=10.0)
        provider = GoogleProvider(
            store=isolated_store,
            guard=guard,
            key=FAKE_GEMINI_KEY,
            poll_interval_sec=0.01,
            transport=httpx.MockTransport(handler),
        )

        # 1. Tạo ảnh kèm ảnh tham chiếu
        imgs = await provider.generate_images(
            prompt="Sóc Nhỏ Bi đứng trước nhà cây",
            references=[ref_rel],
            aspect_ratio="9:16",
            n=1,
            node_id="n_img",
            run_id="r1",
            model="gemini-2.5-flash-image",
        )
        assert len(imgs) == 1
        assert imgs[0].kind == ArtifactKind.IMAGE
        assert imgs[0].provenance.provider == "google"
        assert (isolated_store.project_dir / imgs[0].uri).exists()

        # 2. Sửa ảnh (image.edit)
        edited = await provider.edit_image(
            image_uri=imgs[0].uri,
            prompt="Đổi nền sang phòng khám Bác sĩ Koala",
            node_id="n_edit",
            run_id="r1",
        )
        assert edited.kind == ArtifactKind.IMAGE

        # 3. Sinh video Veo (submit -> poll 2 vòng -> tải MP4)
        vid = await provider.generate_video(
            prompt="Camera dolly vào Sóc Nhỏ Bi",
            first_frame_uri=imgs[0].uri,
            duration_sec=5.0,
            aspect_ratio="9:16",
            node_id="n_vid",
            run_id="r1",
            model="google-veo-2",
        )
        assert vid.kind == ArtifactKind.VIDEO
        assert poll_counter["count"] == 2
        assert (isolated_store.project_dir / vid.uri).read_bytes() == FAKE_MP4_BYTES

        # 4. Hủy giữa chừng khi đang poll Veo
        poll_counter["count"] = 0
        cancel_ev = asyncio.Event()
        cancel_ev.set()
        with pytest.raises(ProviderError) as exc_cancel:
            await provider.generate_video(
                prompt="Clip bị hủy",
                duration_sec=5.0,
                node_id="n_cancel",
                run_id="r1",
                model="google-veo-2",
                cancel_event=cancel_ev,
            )
        assert exc_cancel.value.kind == ProviderErrorKind.CANCELLED

        # 5. Sinh JSON kịch bản có cấu trúc
        tc = await provider.text_complete(
            system="Biên kịch",
            prompt="Tách 1 cảnh",
            schema={"type": "OBJECT"},
        )
        assert isinstance(tc.get("scenes"), list)
        assert tc["scenes"][0]["dialogue"] == "Xin chào các bạn!"

        # 6. Lỗi 401 phải hoàn lại tiền dự phòng (refund) và che khóa API
        spent_before = guard.spent()
        force_401["enabled"] = True
        with pytest.raises(ProviderError) as exc_auth:
            await provider.generate_images(prompt="Test 401", n=1, node_id="n_401")
        assert exc_auth.value.kind == ProviderErrorKind.AUTH
        assert FAKE_GEMINI_KEY not in str(exc_auth.value)
        assert guard.spent() == pytest.approx(spent_before, abs=1e-4)

    asyncio.run(_run())


def test_fal_provider_contract_queue_flux_kling_and_cancel(isolated_store: ProjectStore):
    """Kiểm tra toàn diện hợp đồng FalProvider: hàng đợi FLUX, Kontext, Kling v3 và hủy qua cancel_url."""

    async def _run():
        png_bytes = create_minimal_png_bytes(320, 568)
        frame_rel = "assets/first_frame.png"
        (isolated_store.project_dir / frame_rel).write_bytes(png_bytes)

        queue_polls = {"count": 0}
        cancelled_urls: List[str] = []
        captured_bodies: List[Dict[str, Any]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            method = request.method.upper()

            if "cdn.fal.media" not in url:
                assert request.headers.get("Authorization") == f"Key {FAKE_FAL_KEY}"

            if method == "PUT" and "/cancel" in url:
                cancelled_urls.append(url)
                return httpx.Response(200, json={"status": "CANCELLED"})

            if method == "POST" and "queue.fal.run/" in url:
                body = json.loads(request.content.decode("utf-8"))
                captured_bodies.append({"url": url, "body": body})
                req_kind = "video" if "kling" in url else "image"
                return httpx.Response(
                    200,
                    json={
                        "request_id": f"req_{req_kind}_001",
                        "status_url": f"https://queue.fal.run/requests/req_{req_kind}_001/status",
                        "response_url": f"https://queue.fal.run/requests/req_{req_kind}_001",
                        "cancel_url": f"https://queue.fal.run/requests/req_{req_kind}_001/cancel",
                    },
                )

            if method == "GET" and url.endswith("/status"):
                queue_polls["count"] += 1
                if queue_polls["count"] == 1:
                    return httpx.Response(200, json={"status": "IN_QUEUE"})
                return httpx.Response(200, json={"status": "COMPLETED"})

            if method == "GET" and "requests/req_image_001" in url:
                return httpx.Response(
                    200,
                    json={
                        "images": [
                            {
                                "url": "https://cdn.fal.media/out_flux.png",
                                "width": 1080,
                                "height": 1920,
                                "content_type": "image/png",
                            }
                        ],
                        "seed": 42,
                    },
                )

            if method == "GET" and "requests/req_video_001" in url:
                return httpx.Response(
                    200,
                    json={"video": {"url": "https://cdn.fal.media/out_kling.mp4"}},
                )

            if url == "https://cdn.fal.media/out_flux.png":
                return httpx.Response(200, content=png_bytes)

            if url == "https://cdn.fal.media/out_kling.mp4":
                return httpx.Response(200, content=FAKE_MP4_BYTES)

            return httpx.Response(404, text=f"Unhandled {method} {url}")

        guard = SpendGuard(isolated_store.runs_dir, cap_usd=10.0)
        fal = FalProvider(
            store=isolated_store,
            guard=guard,
            key=FAKE_FAL_KEY,
            poll_interval_sec=0.01,
            transport=httpx.MockTransport(handler),
        )

        # 1. FLUX tạo ảnh
        imgs = await fal.generate_images(
            prompt="Lookbook thời trang studio",
            aspect_ratio="9:16",
            n=1,
            seed=42,
            node_id="fal_img",
            model="fal-flux-schnell",
        )
        assert len(imgs) == 1
        assert imgs[0].provenance.provider == "fal"
        assert imgs[0].provenance.cost_usd == pytest.approx(0.003, abs=1e-4)

        # 2. Kling v3 tạo video từ khung đầu (data URI)
        queue_polls["count"] = 0
        vid = await fal.generate_video(
            prompt="Người mẫu xoay nhẹ trước ống kính",
            first_frame_uri=frame_rel,
            duration_sec=5.0,
            aspect_ratio="9:16",
            has_audio=False,
            node_id="fal_vid",
            model="fal-kling-v3-std",
        )
        assert vid.kind == ArtifactKind.VIDEO
        assert vid.provenance.provider == "fal"
        assert vid.provenance.cost_usd == pytest.approx(0.42, abs=1e-4)
        kling_call = next(c for c in captured_bodies if "kling-video" in c["url"])
        assert kling_call["body"]["start_image_url"].startswith("data:image/png;base64,")
        assert kling_call["body"]["duration"] == "5"

        # 3. Hủy job trên hàng đợi fal.ai gọi PUT cancel_url
        cancel_ev = asyncio.Event()
        cancel_ev.set()
        with pytest.raises(ProviderError) as exc_cancel:
            await fal.generate_video(
                prompt="Hủy job",
                duration_sec=5.0,
                node_id="fal_cancel",
                model="fal-kling-v3-std",
                cancel_event=cancel_ev,
            )
        assert exc_cancel.value.kind == ProviderErrorKind.CANCELLED
        assert len(cancelled_urls) == 1

    asyncio.run(_run())


def test_spend_guard_multitier_caps(tmp_path: Path):
    """Kiểm tra khóa chi tiêu 3 tầng: trần dự án, trần 24h, và trần riêng cho MCP/Agent."""
    now = 1_800_000_000.0
    guard = SpendGuard(
        tmp_path,
        cap_usd=5.0,
        daily_cap_usd=3.0,
        mcp_cap_usd=1.0,
    )

    # Khoản chi cách đây 2 ngày (tính vào tổng dự án, KHÔNG tính vào 24h)
    guard.reserve(1.50, "cũ 2 ngày trước", source="api", now_ts=now - 172800)
    assert guard.spent() == pytest.approx(1.50)
    assert guard.spent_24h(now_ts=now) == pytest.approx(0.0)

    # MCP chỉ được chi tối đa $1.00 / 24h
    guard.reserve(0.80, "mcp_job_1", source="mcp", now_ts=now)
    with pytest.raises(SpendCapExceeded, match="MCP/Agent"):
        guard.reserve(0.30, "mcp_job_2", source="mcp", now_ts=now)

    # Nhưng giao diện người dùng (source="api") vẫn chi tiếp được trong trần ngày $3.00
    guard.reserve(1.80, "ui_job_1", source="api", now_ts=now)
    assert guard.spent_24h(now_ts=now) == pytest.approx(2.60)

    # Vượt trần 24h ($2.60 + $0.50 > $3.00)
    with pytest.raises(SpendCapExceeded, match="24h"):
        guard.reserve(0.50, "ui_job_over_daily", source="api", now_ts=now)


def test_key_vault_and_api_keys_endpoints_never_leak_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Kiểm tra KeyVault lưu .env.local quyền 0600 và API /settings/api-keys không bao giờ lộ khóa."""
    saved_mem = dict(KeyVault._memory_keys)
    saved_upd = dict(KeyVault._updated_at)
    KeyVault._memory_keys.clear()
    KeyVault._updated_at.clear()

    for env_k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "FAL_KEY", "OPENAI_API_KEY", "REPLICATE_API_TOKEN"):
        monkeypatch.delenv(env_k, raising=False)

    vault = KeyVault(repo_root=tmp_path, persist_local=True)
    monkeypatch.setattr(app_module, "get_key_vault", lambda: vault)

    try:
        client = TestClient(app_module.app)

        # Khóa giữ chỗ hoặc quá ngắn phải bị từ chối HTTP 400
        bad_res = client.post(
            "/settings/api-keys",
            json={"provider": "gemini", "apiKey": "your_api_key_here"},
        )
        assert bad_res.status_code == 400

        # Lưu khóa hợp lệ
        ok_gemini = client.post(
            "/settings/api-keys",
            json={"provider": "gemini", "apiKey": FAKE_GEMINI_KEY},
        )
        assert ok_gemini.status_code == 200
        assert ok_gemini.json()["configured"] is True
        assert FAKE_GEMINI_KEY not in ok_gemini.text

        ok_fal = client.post(
            "/settings/api-keys",
            json={"provider": "fal", "apiKey": FAKE_FAL_KEY},
        )
        assert ok_fal.status_code == 200
        assert FAKE_FAL_KEY not in ok_fal.text

        # Kiểm tra tệp .env.local có quyền 0600
        env_local = tmp_path / ".env.local"
        assert env_local.exists()
        mode = stat.S_IMODE(os.stat(env_local).st_mode)
        if os.name != 'nt':
            assert mode == 0o600

        # Kiểm tra GET /settings/api-keys và GET /providers không bao giờ trả khóa
        st_res = client.get("/settings/api-keys")
        assert st_res.status_code == 200
        assert FAKE_GEMINI_KEY not in st_res.text
        assert FAKE_FAL_KEY not in st_res.text
        prov_map = {p["provider"]: p["configured"] for p in st_res.json()["providers"]}
        assert prov_map["gemini"] is True
        assert prov_map["fal"] is True

        prov_res = client.get("/providers")
        assert prov_res.status_code == 200
        assert FAKE_GEMINI_KEY not in prov_res.text
        assert FAKE_FAL_KEY not in prov_res.text
    finally:
        KeyVault._memory_keys.clear()
        KeyVault._memory_keys.update(saved_mem)
        KeyVault._updated_at.clear()
        KeyVault._updated_at.update(saved_upd)


def test_multi_provider_dag_and_non_retryable_stop(isolated_store: ProjectStore):
    """Chạy DAG kết hợp Google (tạo ảnh) -> fal.ai (tạo video Kling) và kiểm tra dừng ngay khi bị chặn an toàn."""

    async def _run():
        png_bytes = create_minimal_png_bytes(320, 568)
        png_b64 = base64.b64encode(png_bytes).decode("ascii")

        def google_handler(req: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "candidates": [
                        {"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": png_b64}}]}}
                    ]
                },
            )

        def fal_handler(req: httpx.Request) -> httpx.Response:
            url = str(req.url)
            if req.method == "POST":
                return httpx.Response(
                    200,
                    json={
                        "request_id": "r_dag",
                        "status_url": "https://queue.fal.run/requests/r_dag/status",
                        "response_url": "https://queue.fal.run/requests/r_dag",
                    },
                )
            if url.endswith("/status"):
                return httpx.Response(200, json={"status": "COMPLETED"})
            if url.endswith("/r_dag"):
                return httpx.Response(200, json={"video": {"url": "https://cdn.fal.media/dag.mp4"}})
            return httpx.Response(200, content=FAKE_MP4_BYTES)

        guard = SpendGuard(isolated_store.runs_dir, cap_usd=10.0)
        google_prov = GoogleProvider(
            isolated_store, guard=guard, key=FAKE_GEMINI_KEY, transport=httpx.MockTransport(google_handler)
        )
        fal_prov = FalProvider(
            isolated_store,
            guard=guard,
            key=FAKE_FAL_KEY,
            poll_interval_sec=0.01,
            transport=httpx.MockTransport(fal_handler),
        )
        router = ProviderRouter(
            store=isolated_store,
            guard=guard,
            mock_mode=False,
            providers={"google": google_prov, "fal": fal_prov},
        )

        graph = Graph(
            id="g_multi_prov",
            project_id=isolated_store.project_id,
            nodes=[
                NodeInstance(
                    id="n_img_google",
                    type="image_gen",
                    params={"prompt": "Sóc Nhỏ Bi ở rừng thông", "model": "gemini-2.5-flash-image", "n": 1},
                ),
                NodeInstance(
                    id="n_vid_fal",
                    type="video_gen",
                    params={"prompt": "Bi vẫy tay chào", "model": "fal-kling-v3-std", "durationSec": 5.0},
                ),
            ],
            edges=[
                Edge(
                    id="e_img_to_vid",
                    source_node_id="n_img_google",
                    source_port="image",
                    target_node_id="n_vid_fal",
                    target_port="first_frame",
                )
            ],
            updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        runner = GraphRunner(store=isolated_store, provider=router)
        summary = await runner.run(
            graph,
            GraphRunRequest(
                project_id=isolated_store.project_id,
                mode=RunMode.ALL,
                mock_mode=False,
                confirm_paid_run=True,
            ),
        )
        assert summary.is_success is True
        assert summary.executed_nodes == ["n_img_google", "n_vid_fal"]
        assert summary.total_cost_usd > 0.40

        # Kiểm tra không retry vô ích khi gặp lỗi CONTENT_BLOCKED (non-retryable)
        safety_calls = {"count": 0}

        def blocked_handler(req: httpx.Request) -> httpx.Response:
            safety_calls["count"] += 1
            return httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}})

        blocked_google = GoogleProvider(
            isolated_store, guard=guard, key=FAKE_GEMINI_KEY, transport=httpx.MockTransport(blocked_handler)
        )
        blocked_router = ProviderRouter(
            store=isolated_store, guard=guard, mock_mode=False, providers={"google": blocked_google}
        )
        blocked_graph = Graph(
            id="g_blocked",
            project_id=isolated_store.project_id,
            nodes=[
                NodeInstance(
                    id="n_blocked",
                    type="image_gen",
                    params={"prompt": "Blocked test", "model": "gemini-2.5-flash-image"},
                )
            ],
            edges=[],
            updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        summary_blocked = await GraphRunner(store=isolated_store, provider=blocked_router).run(
            blocked_graph,
            GraphRunRequest(
                project_id=isolated_store.project_id,
                mode=RunMode.ALL,
                mock_mode=False,
                max_retries=4,
            ),
        )
        assert summary_blocked.is_success is False
        assert safety_calls["count"] == 1  # Chỉ gọi đúng 1 lần, không retry lãng phí!
        assert blocked_graph.nodes[0].state == NodeState.FAILED

    asyncio.run(_run())


def test_estimate_endpoint_and_confirm_paid_run_gate(
    isolated_store: ProjectStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Kiểm tra POST /estimate và cổng xác nhận confirmPaidRun (HTTP 409 trước khi tốn tiền thật)."""
    saved_mem = dict(KeyVault._memory_keys)
    KeyVault._memory_keys.clear()
    vault = KeyVault(repo_root=tmp_path, persist_local=False)
    vault.set_key("gemini", FAKE_GEMINI_KEY)
    vault.set_key("fal", FAKE_FAL_KEY)
    monkeypatch.setattr(app_module, "get_key_vault", lambda: vault)

    try:
        client = TestClient(app_module.app)
        graph_payload = {
            "id": "g_est",
            "projectId": "test-step5",
            "name": "Estimate Gate Test",
            "nodes": [
                {
                    "id": "n_img",
                    "type": "image_gen",
                    "params": {"prompt": "Bi đánh răng", "model": "gemini-2.5-flash-image", "n": 2},
                    "inputs": {},
                    "position": {"x": 0, "y": 0},
                    "state": "idle",
                    "generations": [],
                },
                {
                    "id": "n_vid",
                    "type": "video_gen",
                    "params": {"prompt": "Bi cười", "model": "fal-kling-v3-std", "durationSec": 5},
                    "inputs": {},
                    "position": {"x": 300, "y": 0},
                    "state": "idle",
                    "generations": [],
                },
            ],
            "edges": [
                {
                    "id": "e1",
                    "sourceNodeId": "n_img",
                    "sourcePort": "image",
                    "targetNodeId": "n_vid",
                    "targetPort": "first_frame",
                }
            ],
            "updatedAt": "2026-11-03T12:00:00Z",
        }

        # 1. Gọi /estimate ở chế độ thật
        est_res = client.post(
            "/projects/test-step5/estimate",
            json={"graph": graph_payload, "mode": "all", "mockMode": False},
        )
        assert est_res.status_code == 200
        est = est_res.json()
        assert est["requiresConfirmation"] is True
        assert est["missingApiKeys"] == []
        assert est["totalEstimatedCostUsd"] == pytest.approx(0.06 + 0.42, abs=1e-4)
        assert len(est["nodesToExecute"]) == 2

        # 2. Gọi /run với mockMode=False nhưng CHƯA truyền confirmPaidRun=True -> phải bị chặn 409!
        unconfirmed = client.post(
            "/projects/test-step5/run",
            json={"graph": graph_payload, "mode": "all", "mockMode": False, "confirmPaidRun": False},
        )
        assert unconfirmed.status_code == 409
        body_409 = unconfirmed.json()
        assert "estimate" in body_409
        assert body_409["estimate"]["totalEstimatedCostUsd"] == pytest.approx(0.48, abs=1e-4)

        # 3. Khi truyền confirmPaidRun=True -> cho phép chạy qua ProviderRouter (mock HTTP)
        png_bytes = create_minimal_png_bytes(320, 568)
        png_b64 = base64.b64encode(png_bytes).decode("ascii")

        def mock_router_factory(store, guard, vault, mock_mode, fallback_to_mock, source):
            g_prov = GoogleProvider(
                store,
                guard=guard,
                key=FAKE_GEMINI_KEY,
                transport=httpx.MockTransport(
                    lambda _r: httpx.Response(
                        200,
                        json={
                            "candidates": [
                                {"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": png_b64}}]}}
                            ]
                        },
                    )
                ),
            )
            f_prov = FalProvider(
                store,
                guard=guard,
                key=FAKE_FAL_KEY,
                poll_interval_sec=0.01,
                transport=httpx.MockTransport(
                    lambda r: httpx.Response(
                        200,
                        json={"video": {"url": "https://cdn.fal.media/ok.mp4"}}
                        if r.method == "POST"
                        else None,
                        content=FAKE_MP4_BYTES if r.method == "GET" else None,
                    )
                ),
            )
            return ProviderRouter(
                store=store, guard=guard, vault=vault, mock_mode=False, providers={"google": g_prov, "fal": f_prov}
            )

        monkeypatch.setattr(app_module, "ProviderRouter", mock_router_factory)
        confirmed = client.post(
            "/projects/test-step5/run",
            json={"graph": graph_payload, "mode": "all", "mockMode": False, "confirmPaidRun": True},
        )
        assert confirmed.status_code == 200
        assert confirmed.json()["isSuccess"] is True
    finally:
        KeyVault._memory_keys.clear()
        KeyVault._memory_keys.update(saved_mem)
