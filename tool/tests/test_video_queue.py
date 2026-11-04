from __future__ import annotations

import asyncio
import json
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from socnhotv.video.contracts import RenderRequest, submit_render, get_render
from socnhotv.video.queue import RenderQueue, get_render_queue
from socnhotv.workspace.paths import project_path


@pytest.mark.anyio
async def test_video_queue_multi_platform_render():
    queue = RenderQueue(max_parallel=2)
    project_id = "soc-nho-tv"

    req = RenderRequest(
        project_id=project_id,
        template_id="tiktok-sales-v1",
        platforms=["tiktok", "shorts", "youtube"],
        data={
            "scenes": [
                {"dialogue": "Scene 1", "image": "", "durationSec": 1.0}
            ],
            "title": "Test Multi Platform",
        },
        output_name="test_multi_out",
    )

    # Mock engine.render để không phải encode video thật
    def fake_render(bundle_dir, out_path, platform, **kwargs):
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(b"dummy_video_bytes")
        return Path(out_path)

    with patch.object(queue.engine, "render", side_effect=fake_render):
        job = queue.submit(req)
        assert job.status == "queued"

        # Chạy trực tiếp _process_job
        await queue._process_job(job)

        updated_job = queue.get(project_id, job.job_id)
        assert updated_job.status == "done"
        assert len(updated_job.outputs) == 3
        assert "tiktok" in updated_job.outputs
        assert "shorts" in updated_job.outputs
        assert "youtube" in updated_job.outputs

        # Kiểm tra file đã tạo
        for plat in ["tiktok", "shorts", "youtube"]:
            expected_file = project_path(project_id, "output", "test_multi_out", f"{plat}.mp4")
            assert expected_file.exists()


@pytest.mark.anyio
async def test_video_queue_cancel_job():
    queue = RenderQueue(max_parallel=2)
    project_id = "soc-nho-tv"

    req = RenderRequest(
        project_id=project_id,
        template_id="tiktok-sales-v1",
        platforms=["tiktok"],
        data={"scenes": [{"dialogue": "Cancel me", "durationSec": 1.0}]},
        output_name="test_cancel_out",
    )

    job = queue.submit(req)
    assert job.status == "queued"

    cancelled = queue.cancel(project_id, job.job_id)
    assert cancelled.status == "failed"
    assert "Cancelled" in (cancelled.error or "")

    # Gọi _process_job sẽ bỏ qua job đã bị cancel
    await queue._process_job(job)
    final_job = queue.get(project_id, job.job_id)
    assert final_job.status == "failed"


@pytest.mark.anyio
async def test_video_queue_auto_draft():
    queue = RenderQueue(max_parallel=2)
    project_id = "soc-nho-tv"

    req = RenderRequest(
        project_id=project_id,
        template_id="tiktok-sales-v1",
        platforms=["tiktok"],
        data={
            "scenes": [{"dialogue": "Auto draft", "durationSec": 1.0}],
            "auto_draft": True,
            "title": "Auto Draft Video",
            "caption": "#socnhotv #funny",
        },
        output_name="test_autodraft_out",
    )

    def fake_render(bundle_dir, out_path, platform, **kwargs):
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(b"dummy_video_bytes")
        return Path(out_path)

    with patch.object(queue.engine, "render", side_effect=fake_render):
        with patch("socnhotv.social.contracts.create_draft_post") as mock_draft:
            mock_draft.return_value = "post_123"
            job = queue.submit(req)
            await queue._process_job(job)

            updated_job = queue.get(project_id, job.job_id)
            assert updated_job.status == "done"

            mock_draft.assert_called_once()
            args, kwargs = mock_draft.call_args
            assert kwargs.get("project_id") == project_id or args[0] == project_id
            assert "output/test_autodraft_out/tiktok.mp4" in str(args) or "output/test_autodraft_out/tiktok.mp4" in str(kwargs)
