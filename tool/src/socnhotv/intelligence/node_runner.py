"""Studio Node Runner for Intelligence capabilities.

Executes `channel_insight`, `blueprint_analyze`, `script_from_blueprint`, and `compliance_check`
nodes, returning execution outputs compatible with Studio canvas ports and artifacts.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from socnhotv.intelligence.analyzer import analyze_video
from socnhotv.intelligence.channel_analyze import analyze_channel
from socnhotv.intelligence.channel_ingest import generate_channel_id, ingest_channel, ingest_user_channel_data
from socnhotv.intelligence.compliance import check_and_clean_script
from socnhotv.intelligence.contracts import (
    load_channel_blueprint,
    load_video_blueprint,
)
from socnhotv.intelligence.products import get_product, list_products
from socnhotv.intelligence.script_gen import GeneratorType, generate_complete_script

logger = logging.getLogger(__name__)


def execute_intel_node(
    project_id: str,
    node_type: str,
    params: Optional[Dict[str, Any]] = None,
    inputs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute an intelligence node by type with resolved inputs and parameters."""
    p = params or {}
    inp = inputs or {}

    if node_type == "channel_insight":
        channel_url = str(inp.get("channel_url") or p.get("channel_url") or "").strip()
        user_videos = inp.get("user_videos") or p.get("user_videos")
        channel_name = str(inp.get("channel_name") or p.get("channel_name") or "").strip()

        if user_videos and isinstance(user_videos, list):
            # 1. Ingest user-provided data directly
            meta = ingest_user_channel_data(
                project_id=project_id,
                channel_url=channel_url or f"https://custom/{channel_name or 'user_channel'}",
                channel_name=channel_name or "Kênh người dùng cung cấp",
                raw_videos=user_videos,
            )
            analysis = analyze_channel(project_id, meta["id"])
        elif channel_url:
            # 2. Scrape public channel via yt-dlp
            max_videos = int(p.get("max_videos", 50))
            meta = ingest_channel(project_id, channel_url, max_videos=max_videos, download_top_n=0)
            analysis = analyze_channel(project_id, meta["id"])
        else:
            raise ValueError("Node 'channel_insight' yêu cầu 'channel_url' hoặc 'user_videos' của kênh.")

        bp = analysis.get("blueprint", {})
        pillars = analysis.get("pillars", [])
        stats = analysis.get("stats", {})

        summary_md = (
            f"### Phân tích Kênh: {analysis.get('channel_meta', {}).get('name', 'N/A')}\n"
            f"- **Trạng thái**: {analysis.get('data_label', 'DỮ LIỆU THẬT')}\n"
            f"- **Tổng video phân tích**: {stats.get('total_videos', 0)}\n"
            f"- **Lượt xem trung vị (Median Views)**: {stats.get('median_views', 0):,}\n"
            f"- **Lượt xem trung bình (Avg Views)**: {stats.get('avg_views', 0):,}\n"
            f"- **Thời lượng trung bình**: {stats.get('avg_duration_s', 0)} giây\n"
            f"- **Tỷ lệ Shorts/Longs**: {stats.get('shorts_ratio', 0) * 100:.0f}% Shorts / {stats.get('longs_ratio', 0) * 100:.0f}% Video dài\n"
            f"- **Nhịp đăng**: {stats.get('upload_cadence', 'N/A')}\n"
            f"- **Pillars chính**: {', '.join([pi['name'] for pi in pillars[:3]])}\n"
            f"- **Giữ chân**: {stats.get('retention_note', 'Không có số liệu bịa đặt')}\n"
        )

        return {
            "blueprint": json.dumps(bp, ensure_ascii=False, indent=2),
            "pillars": json.dumps(pillars, ensure_ascii=False, indent=2),
            "summary": summary_md,
            "raw_analysis": analysis,
        }

    elif node_type == "blueprint_analyze":
        source_id = str(inp.get("video") or inp.get("source_id") or p.get("source_id") or "").strip()
        if not source_id:
            raise ValueError("Node 'blueprint_analyze' yêu cầu đầu vào 'video' hoặc 'source_id'.")

        bp = analyze_video(project_id, source_id)
        return {
            "blueprint": bp.model_dump_json(indent=2),
            "pacing_cuts_per_10s": bp.pacing_cuts_per_10s,
            "suggested_template_id": bp.suggested_template_id or "koc-review-v1",
            "hook": bp.hook,
            "cta": bp.cta,
            "beats_count": len(bp.beats),
            "data_label": bp.data_label,
        }

    elif node_type == "script_from_blueprint":
        bp_raw = inp.get("blueprint") or p.get("blueprint")
        blueprint = None
        if isinstance(bp_raw, str) and bp_raw.strip():
            try:
                # Try parse as JSON
                bp_dict = json.loads(bp_raw)
                from socnhotv.intelligence.contracts import VideoBlueprint
                blueprint = VideoBlueprint(**bp_dict)
            except Exception:
                # Try load as blueprint_id
                blueprint = load_video_blueprint(project_id, bp_raw.strip())

        # Select product
        product_id = str(inp.get("product_id") or p.get("product_id") or "").strip()
        product = get_product(project_id, product_id) if product_id else None

        if not product:
            prods = list_products(project_id)
            if prods:
                product = prods[0]
            else:
                from socnhotv.intelligence.products import Product, save_product
                product = save_product(
                    project_id,
                    Product(
                        id=f"prod_demo_{project_id}",
                        name="[MẪU] Sản phẩm Trải nghiệm KOC",
                        brand="SocNho Brand",
                        price=199000,
                        usp=["Tiện dụng", "Thiết kế thông minh"],
                        pain_points=["Bất tiện hàng ngày"],
                        compliance_notes="[MẪU] Sản phẩm demo tự động",
                    ),
                )

        character_name = str(inp.get("character") or p.get("character_name") or "LyLy").strip()
        voice_id = str(p.get("voice_id") or "soc-nho").strip()
        gen_type: GeneratorType = p.get("generator_type", "koc_review")

        res = generate_complete_script(
            project_id=project_id,
            product=product,
            generator_type=gen_type,
            blueprint=blueprint,
            character_name=character_name,
            voice_id=voice_id,
        )

        return {
            "script": json.dumps(res["lines"], ensure_ascii=False, indent=2),
            "full_text": res["full_text"],
            "render_request": json.dumps(res["render_request"], ensure_ascii=False, indent=2),
            "template_id": res["template_id"],
            "compliance_warnings": res["compliance_warnings"],
            "hook_lab": res["hook_lab"],
        }

    elif node_type == "compliance_check":
        text = str(inp.get("text") or p.get("text") or "").strip()
        is_affiliate = bool(p.get("is_affiliate", True))
        c_res = check_and_clean_script(text, is_affiliate=is_affiliate)

        return {
            "clean_text": c_res.modified_text,
            "passed": c_res.passed,
            "warnings": c_res.warnings,
            "violations": [v.model_dump() for v in c_res.violations],
            "disclosure_added": c_res.disclosure_added,
        }

    else:
        raise ValueError(f"Loại node không xác định trong intelligence node runner: '{node_type}'")
