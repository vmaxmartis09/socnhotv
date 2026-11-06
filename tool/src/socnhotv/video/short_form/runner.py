from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Dict, Optional

from socnhotv.core.contracts.types import GraphRunRequest, RunMode
from socnhotv.core.engine.graph_runner import GraphRunner
from socnhotv.core.providers.mock_provider import MockProvider
from socnhotv.core.providers.router import ProviderRouter
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root
from socnhotv.video.short_form.generator import generate_short_video_script
from socnhotv.video.short_form.graph import build_short_video_graph
from socnhotv.video.short_form.types import ShortVideoConfig, ShortVideoResult

logger = logging.getLogger(__name__)


def probe_video(video_path: Path) -> Dict[str, Any]:
    """Kiểm tra tệp MP4 kết quả bằng ffprobe."""
    if not video_path.is_file():
        return {"exists": False, "error": f"Tệp không tồn tại: {video_path}"}

    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "stream=codec_type,width,height,duration,r_frame_rate",
            "-show_entries", "format=duration,size,bit_rate",
            "-of", "json",
            str(video_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        meta = json.loads(res.stdout)

        video_stream = next((s for s in meta.get("streams", []) if s.get("codec_type") == "video"), {})
        audio_stream = next((s for s in meta.get("streams", []) if s.get("codec_type") == "audio"), {})
        format_info = meta.get("format", {})

        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        duration = float(format_info.get("duration", video_stream.get("duration", 0.0)))
        size_bytes = int(format_info.get("size", video_path.stat().st_size))

        return {
            "exists": True,
            "path": str(video_path),
            "width": width,
            "height": height,
            "duration": round(duration, 2),
            "size_bytes": size_bytes,
            "has_video": bool(video_stream),
            "has_audio": bool(audio_stream),
            "is_tiktok_9_16": (width == 1080 and height == 1920),
        }
    except Exception as e:
        return {
            "exists": True,
            "path": str(video_path),
            "size_bytes": video_path.stat().st_size,
            "error": f"Lỗi ffprobe: {e}",
        }


def check_audio_volume(video_path: Path) -> Dict[str, Any]:
    """Kiểm tra âm lượng video bằng ffmpeg volumedetect để đảm bảo không im lặng."""
    try:
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",
            "-filter:a", "volumedetect",
            "-f", "null",
            "-",
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stderr = res.stderr
        mean_vol = None
        max_vol = None
        for line in stderr.splitlines():
            if "mean_volume:" in line:
                mean_vol = float(line.split("mean_volume:")[1].replace("dB", "").strip())
            elif "max_volume:" in line:
                max_vol = float(line.split("max_volume:")[1].replace("dB", "").strip())

        is_silent = (mean_vol is not None and mean_vol <= -50.0)
        return {
            "mean_volume_db": mean_vol,
            "max_volume_db": max_vol,
            "is_silent": is_silent,
            "has_sound": not is_silent and (mean_vol is not None),
        }
    except Exception as e:
        return {"error": str(e), "has_sound": False}


async def run_short_video_pipeline(
    config: ShortVideoConfig,
    store: Optional[ProjectStore] = None,
    provider: Optional[Any] = None,
    run_policy: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Thực thi toàn bộ luồng tạo video ngắn từ 1 ý tưởng và đo lường thời gian thực tế.
    
    Quy trình:
    1. Sinh kịch bản & phân bổ shots (generator.py)
    2. Dựng đồ thị Graph (graph.py)
    3. Chạy qua GraphRunner
    4. Đo thời gian sinh kịch bản, dựng HyperFrames và tổng thời gian
    5. Kiểm định kết quả video bằng ffprobe và volumedetect
    """
    t_start = time.perf_counter()

    # 1. Sinh kịch bản
    t_script_0 = time.perf_counter()
    script_result = generate_short_video_script(config)
    t_script = time.perf_counter() - t_script_0

    # 2. Xây dựng đồ thị
    graph = build_short_video_graph(config, script_result)

    # 3. Chuẩn bị Store & Provider
    if store is None:
        repo_root = get_repo_root()
        store = ProjectStore(project_id=config.project_id, repo_root=repo_root)

    if provider is None:
        # Nếu chưa truyền provider, sử dụng ProviderRouter hoặc MockProvider an toàn
        try:
            from socnhotv.core.providers import KeyVault, SpendGuard
            guard = SpendGuard(cap_usd=5.0)
            vault = KeyVault()
            provider = ProviderRouter(store=store, spend_guard=guard, key_vault=vault)
        except Exception:
            provider = MockProvider(store=store)

    runner = GraphRunner(store=store, provider=provider)

    # 4. Thực thi đồ thị
    t_exec_0 = time.perf_counter()
    run_req = GraphRunRequest(
        project_id=config.project_id,
        graph=graph,
        mode=RunMode.ALL,
        confirm_paid_run=False,
        run_policy=run_policy or {
            "image": "mock" if config.mode == "static" else "real",
            "video": "off" if config.mode == "static" else "real",
            "voice": "local",
            "text": "mock",
        },
    )

    summary = await runner.run(graph, run_req)
    t_exec = time.perf_counter() - t_exec_0
    t_total = time.perf_counter() - t_start

    # 5. Xác định tệp video xuất
    slug = config.output_slug or "short-video"
    output_dir = getattr(store, "output_dir", store.project_dir / "output")
    target_mp4 = output_dir / slug / f"{slug}.mp4"
    if not target_mp4.exists():
        # Tìm fallback nếu file export đặt tên khác
        cand = list((output_dir / slug).glob("*.mp4"))
        if cand:
            target_mp4 = cand[0]

    # 6. Kiểm định chất lượng
    probe_info = probe_video(target_mp4)
    volume_info = check_audio_volume(target_mp4)

    return {
        "success": target_mp4.exists(),
        "slug": slug,
        "video_path": str(target_mp4),
        "target_duration_sec": config.target_duration_sec,
        "actual_duration_sec": probe_info.get("duration"),
        "shots_count": len(script_result.shots),
        "mode": config.mode,
        "metrics": {
            "script_gen_time_sec": round(t_script, 3),
            "execution_time_sec": round(t_exec, 3),
            "total_time_sec": round(t_total, 3),
        },
        "probe": probe_info,
        "volume": volume_info,
        "cost_estimate": script_result.cost_estimate,
        "summary": summary.model_dump() if hasattr(summary, "model_dump") else str(summary),
    }
