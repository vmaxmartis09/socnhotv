from __future__ import annotations

import time
from typing import Any, Dict, List

from socnhotv.core.contracts.types import Edge, Graph, NodeInstance, NodeState
from socnhotv.video.short_form.types import ShortVideoConfig, ShortVideoResult


SHORT_VIDEO_PRESET_ID = "short-video-preset"
SHORT_VIDEO_PRESET_NAME = "Video ngắn (30–90s)"


def build_short_video_graph(
    config: ShortVideoConfig,
    result: ShortVideoResult,
) -> Graph:
    """Xây dựng đồ thị Graph đầy đủ chuẩn Core Engine cho Video ngắn.
    
    Bao gồm 7 node tuần tự:
    1. n_script (Kịch bản): mode="paste" chứa kịch bản chia shot đã format
    2. n_cast (Dàn diễn viên): sinh giọng thoại OmniVoice + nạp ảnh DNA
    3. n_quality (Kiểm định): duyệt chính sách nội dung an toàn
    4. n_keyframes (Keyframe theo shot): sinh ảnh tĩnh theo từng shot
    5. n_video (Video theo shot):
       - Chế độ 'static': clipSource='manual', maxClips=0 ($0)
       - Chế độ 'ai_clip': clipSource='auto', perShot=True, model=video_model
    6. n_render (Dựng HyperFrames): Safe Zone TikTok 9:16, camera presets, BGM ducking
    7. n_export (Xuất video): tự động xuất file vào output/<slug>/<slug>.mp4
    """
    slug = config.output_slug or "short-video"
    is_static = (config.mode == "static")
    platform = "tiktok" if config.aspect_ratio == "9:16" else "youtube"

    specs = [
        {
            "id": "n_script",
            "type": "script",
            "x": 60,
            "y": 160,
            "name": "Kịch bản video ngắn",
            "params": {
                "mode": "paste",
                "rawScript": result.raw_script,
                "targetSceneCount": len(result.shots),
                "targetDurationSec": result.total_duration_sec,
                "text": config.prompt,
                "slug": slug,
            },
            "hint": f"Kịch bản ngắn {len(result.shots)} shot ({result.total_duration_sec:.1f}s)",
        },
        {
            "id": "n_cast",
            "type": "cast",
            "x": 420,
            "y": 40,
            "name": "Dàn diễn viên",
            "params": {
                "speak": {"enabled": True},
                "include": [config.character_id],
                "voiceOverrides": {config.character_id: "soc-nho"},
                "onMissingVoice": "stop",
            },
            "hint": f"Nhân vật {config.character_name} & giọng OmniVoice",
        },
        {
            "id": "n_quality",
            "type": "quality_check",
            "x": 420,
            "y": 320,
            "name": "Kiểm định chính sách",
            "params": {
                "blockOnFail": True,
                "policyAutoScan": True,
            },
            "hint": "Cổng kiểm soát an toàn ngôn từ",
        },
        {
            "id": "n_keyframes",
            "type": "image_gen",
            "x": 780,
            "y": 160,
            "name": "Keyframe theo shot",
            "params": {
                "model": config.image_model,
                "aspectRatio": config.aspect_ratio,
                "resolution": "1080p",
                "n": 1,
                "prompt": "",
            },
            "hint": "Tạo ảnh 3-layer depth tham chiếu DNA",
        },
        {
            "id": "n_video",
            "type": "video_gen",
            "x": 1140,
            "y": 160,
            "name": "Video theo shot",
            "params": {
                "model": config.video_model if not is_static else "mock-video",
                "perShot": True,
                "maxClips": 0 if is_static else min(config.max_clips, len(result.shots)),
                "shotIds": [],
                "clipSource": "manual" if is_static else "auto",
                "durationSec": 5.0,
                "aspectRatio": config.aspect_ratio,
                "hasAudio": False,
            },
            "hint": "Chế độ ảnh tĩnh ($0)" if is_static else f"Clip AI ({config.video_model})",
        },
        {
            "id": "n_render",
            "type": "hyperframes_render",
            "x": 1500,
            "y": 160,
            "name": f"Dựng HyperFrames {config.aspect_ratio}",
            "params": {
                "aspectRatio": config.aspect_ratio,
                "platform": platform,
                "template": "tiktok_safe_zone",
                "templateId": "tiktok_safe_zone",
                "requireHyperFrames": True,
                "timing": "script",
                "gapSec": 0.35,
                "titleBadge": "SÓC NHỎ TV • SHORT",
            },
            "hint": "Render HTML5/GSAP chuẩn Safe Zone",
        },
        {
            "id": "n_export",
            "type": "export",
            "x": 1860,
            "y": 160,
            "name": "Xuất video ngắn",
            "params": {
                "platforms": [platform],
                "outputSlug": slug,
                "outputFileName": f"{slug}.mp4",
            },
            "hint": f"Xuất: output/{slug}/{slug}.mp4",
        },
    ]

    wires: List[tuple[str, str, str, str]] = [
        ("n_script", "lines", "n_cast", "lines"),
        ("n_script", "scenes", "n_cast", "scenes"),
        ("n_script", "scenes", "n_quality", "scenes"),
        ("n_script", "lines", "n_quality", "text"),
        ("n_script", "scenes", "n_keyframes", "scenes"),
        ("n_cast", "reference_images", "n_keyframes", "references"),
        ("n_keyframes", "scenes", "n_video", "scenes"),
        ("n_video", "scenes", "n_render", "scenes"),
        ("n_cast", "voice", "n_render", "voice_clips"),
        ("n_quality", "pass_fail", "n_render", "gate"),
        ("n_render", "video", "n_export", "video"),
    ]

    nodes: List[NodeInstance] = []
    for s in specs:
        nodes.append(
            NodeInstance(
                id=s["id"],
                type=s["type"],
                position={"x": float(s["x"]), "y": float(s["y"])},
                params={**s["params"], "_customName": s["name"]},
                state=NodeState.IDLE,
                is_stale=False,
                ui={"hint": s.get("hint", "")},
            )
        )

    edges: List[Edge] = []
    for src, sp, dst, dp in wires:
        edges.append(
            Edge(
                id=f"e_{src}_{sp}__{dst}_{dp}",
                source_node_id=src,
                source_port=sp,
                target_node_id=dst,
                target_port=dp,
            )
        )

    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return Graph(
        id=f"graph_short_{slug}",
        projectId=config.project_id,
        name=f"Video Ngắn: {config.prompt[:30]}",
        nodes=nodes,
        edges=edges,
        updatedAt=now_iso,
    )
