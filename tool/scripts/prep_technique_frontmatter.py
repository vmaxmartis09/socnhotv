#!/usr/bin/env python3
"""Standardize YAML front-matter across all 26 video craft technique cards.
Ensures every card has structured metadata for indexer, agent lookup, and QA.
"""
from pathlib import Path
import re
import yaml

TECHNIQUES_DIR = Path("data/shared/knowledge/video_craft/techniques")

CARDS_META = {
    "3-layer-knowledge-retention.md": {
        "id": "3-layer-knowledge-retention",
        "title": "3-Layer Knowledge Retention & Origin Traceability",
        "status": "in-studio",
        "build": "yes",
        "reproducible_with_our_stack": "yes",
        "needs": ["HyperFrames", "OmniVoice"],
        "implemented_in": [
            "tool/src/socnhotv/video/craft/lint.py",
            "data/shared/knowledge/video_craft/playbooks/depth-and-composition.md"
        ],
        "evidence_videos": ["seq_016"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["knowledge-base", "documentation", "architecture", "traceability", "zero-root-pollution"]
    },
    "360-turntable-catalog.md": {
        "id": "360-turntable-catalog",
        "title": "360 Turntable Catalog (Bàn Xoay Sản Phẩm 360 Độ)",
        "status": "knowledge",
        "build": "partial",
        "reproducible_with_our_stack": "partial (Cần quay sẵn video bàn xoay sản phẩm hoặc 3D model render loop)",
        "needs": ["Blender / 3D Model / Video quay sản phẩm thực tế"],
        "implemented_in": [],
        "evidence_videos": ["seq_007"],
        "confidence": "medium",
        "last_verified": "2026-11-04",
        "expires_at": "2027-11-04",
        "tags": ["product-catalog", "360-turntable", "e-commerce", "3d-rendering"]
    },
    "7-platform-automated-syndication-and-scope-locked-crm.md": {
        "id": "7-platform-automated-syndication-and-scope-locked-crm",
        "title": "7-Platform Automated Syndication & Scope-Locked CRM",
        "status": "knowledge",
        "build": "no",
        "reproducible_with_our_stack": "partial (Social scheduler hỗ trợ queue đa kênh; CRM webhook ngoài phạm vi video engine)",
        "needs": ["Social API", "CRM Webhook"],
        "implemented_in": ["tool/src/socnhotv/social/"],
        "evidence_videos": ["seq_020"],
        "confidence": "medium",
        "last_verified": "2026-11-04",
        "expires_at": "2027-11-04",
        "tags": ["social-syndication", "multi-platform", "crm", "automation"]
    },
    "camera-motion-choreography.md": {
        "id": "camera-motion-choreography",
        "title": "Camera Motion Choreography (Vũ Đạo Chuyển Động Camera 5 Cú Máy Kinh Điển)",
        "status": "in-studio",
        "build": "yes",
        "reproducible_with_our_stack": "yes",
        "needs": ["HyperFrames", "GSAP"],
        "implemented_in": [
            "tool/src/socnhotv/video/craft/camera.py",
            "data/shared/knowledge/video_craft/playbooks/camera-and-transitions.md"
        ],
        "evidence_videos": ["seq_006"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["camera", "motion-design", "cinematography", "hyperframes", "lookbook"]
    },
    "channel-style-cloning-template-pipeline.md": {
        "id": "channel-style-cloning-template-pipeline",
        "title": "Channel Style Cloning & Template Pipeline",
        "status": "knowledge",
        "build": "partial",
        "reproducible_with_our_stack": "yes (Định hình style thông qua template HyperFrames JSON + CSS)",
        "needs": ["HyperFrames", "Template Engine"],
        "implemented_in": ["tool/src/socnhotv/video/templates/"],
        "evidence_videos": ["seq_015"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "2027-11-04",
        "tags": ["template-pipeline", "style-cloning", "youtube-shorts", "branding"]
    },
    "cinematography-camera-mechanics-cheatsheet.md": {
        "id": "cinematography-camera-mechanics-cheatsheet",
        "title": "Cinematography & Camera Mechanics Cheatsheet",
        "status": "in-studio",
        "build": "yes",
        "reproducible_with_our_stack": "yes",
        "needs": ["HyperFrames GSAP", "Keyframes Adapter"],
        "implemented_in": [
            "tool/src/socnhotv/video/craft/camera.py",
            "data/shared/knowledge/video_craft/playbooks/camera-and-transitions.md"
        ],
        "evidence_videos": ["seq_014"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["camera-angles", "focal-length", "lens", "cinematography", "hyperframes"]
    },
    "confession-hook.md": {
        "id": "confession-hook",
        "title": "Confession Hook / Secret Reveal (Hook Thú Nhận Bí Mật Hậu Trường)",
        "status": "in-studio",
        "build": "yes",
        "reproducible_with_our_stack": "yes",
        "needs": ["HyperFrames", "OmniVoice"],
        "implemented_in": [
            "tool/src/socnhotv/video/craft/hooks.py",
            "data/shared/knowledge/video_craft/playbooks/hook-and-retention.md"
        ],
        "evidence_videos": ["seq_001"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["hook", "retention", "psychological", "tiktok-sales", "koc-review"]
    },
    "deterministic-web-to-video-rendering.md": {
        "id": "deterministic-web-to-video-rendering",
        "title": "Deterministic Web-to-Video Rendering Architecture",
        "status": "in-studio",
        "build": "yes",
        "reproducible_with_our_stack": "yes",
        "needs": ["HyperFrames Engine", "Chrome Headless", "FFmpeg"],
        "implemented_in": ["tool/src/socnhotv/video/hyperframes_engine.py"],
        "evidence_videos": ["seq_N03"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["hyperframes", "deterministic-render", "ffmpeg", "virtual-clock", "gsap"]
    },
    "dual-node-video-stitching.md": {
        "id": "dual-node-video-stitching",
        "title": "Dual-Node Video Stitching (Nối Đoạn Video 2 Đầu Bằng AI)",
        "status": "knowledge",
        "build": "no",
        "reproducible_with_our_stack": "partial (Cần mô hình video generation ngoài có API image-to-video/extend như Kling/Runway)",
        "needs": ["Kling AI / Runway Gen-3"],
        "implemented_in": [],
        "evidence_videos": ["seq_008"],
        "confidence": "medium",
        "last_verified": "2026-11-04",
        "expires_at": "2027-11-04",
        "tags": ["video-stitching", "outpainting", "generative-fill", "ai-video"]
    },
    "evergreen-shortform-foundations.md": {
        "id": "evergreen-shortform-foundations",
        "title": "Evergreen Shortform Foundations (Cấu Trúc Video Ngắn Thường Xanh)",
        "status": "in-studio",
        "build": "yes",
        "reproducible_with_our_stack": "yes",
        "needs": ["HyperFrames", "Lint"],
        "implemented_in": [
            "tool/src/socnhotv/video/craft/lint.py",
            "data/shared/knowledge/video_craft/playbooks/hook-and-retention.md"
        ],
        "evidence_videos": ["seq_011"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["retention", "loop-video", "shortform", "storytelling", "safe-zone"]
    },
    "first-comment-link-routing.md": {
        "id": "first-comment-link-routing",
        "title": "First-Comment Link Routing & Zero-Penalty Affiliate Funnel",
        "status": "in-studio",
        "build": "yes",
        "reproducible_with_our_stack": "yes",
        "needs": ["Social Publishing Engine", "Caption Templates"],
        "implemented_in": [
            "tool/src/socnhotv/social/publishing_templates.py",
            "data/shared/knowledge/video_craft/playbooks/affiliate-links-and-first-comment.md"
        ],
        "evidence_videos": ["seq_013"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["affiliate", "first-comment", "social-reach", "cta", "link-in-bio"]
    },
    "foreground-occlusion-spatial-depth-layering.md": {
        "id": "foreground-occlusion-spatial-depth-layering",
        "title": "Foreground Occlusion & 3-Layer Spatial Depth Partitioning",
        "status": "in-studio",
        "build": "yes",
        "reproducible_with_our_stack": "yes",
        "needs": ["HyperFrames", "GSAP Parallax", "Prompt Enrichment"],
        "implemented_in": [
            "tool/src/socnhotv/video/craft/depth.py",
            "data/shared/knowledge/video_craft/playbooks/depth-and-composition.md"
        ],
        "evidence_videos": ["seq_N08"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["cinematic-depth", "3-layer", "foreground-occlusion", "bokeh", "parallax"]
    },
    "frictionless-remix-workflow.md": {
        "id": "frictionless-remix-workflow",
        "title": "Frictionless Remix Workflow (Quy Trình Tái Chế B-Roll & Hook Không Ma Sát)",
        "status": "knowledge",
        "build": "partial",
        "reproducible_with_our_stack": "yes",
        "needs": ["Asset Library", "HyperFrames"],
        "implemented_in": ["tool/src/socnhotv/workspace/"],
        "evidence_videos": ["seq_005"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["remix", "b-roll", "batch-production", "workflow", "asset-reuse"]
    },
    "high-status-color-contrast.md": {
        "id": "high-status-color-contrast",
        "title": "High-Status Color Contrast (Bảng Màu Tương Phản Chuẩn Sang Trọng)",
        "status": "in-studio",
        "build": "yes",
        "reproducible_with_our_stack": "yes",
        "needs": ["HyperFrames CSS", "Lint"],
        "implemented_in": [
            "tool/src/socnhotv/video/craft/lint.py",
            "data/shared/knowledge/video_craft/playbooks/depth-and-composition.md"
        ],
        "evidence_videos": ["seq_016"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["color-palette", "contrast", "luxury-branding", "wcag", "aesthetic"]
    },
    "in-situ-koc-placement.md": {
        "id": "in-situ-koc-placement",
        "title": "In-Situ KOC Placement (Đặt Nhân Vật KOC Vào Bối Cảnh Đời Thực)",
        "status": "in-studio",
        "build": "yes",
        "reproducible_with_our_stack": "yes",
        "needs": ["Master DNA RGBA", "HyperFrames 3-layer"],
        "implemented_in": [
            "tool/src/socnhotv/video/craft/depth.py",
            "data/shared/knowledge/video_craft/playbooks/koc-review-and-sales.md"
        ],
        "evidence_videos": ["seq_002"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["koc-placement", "master-dna", "natural-lighting", "compositing"]
    },
    "local-comfyui-pipeline.md": {
        "id": "local-comfyui-pipeline",
        "title": "Local ComfyUI Pipeline For Generative B-Roll",
        "status": "knowledge",
        "build": "no",
        "reproducible_with_our_stack": "partial (Đòi hỏi GPU cục bộ chuyên dụng và cài ComfyUI riêng; hiện dự án ưu tiên Tier 0 local DNA + cloud fallback)",
        "needs": ["ComfyUI", "Local GPU"],
        "implemented_in": [],
        "evidence_videos": ["seq_009"],
        "confidence": "medium",
        "last_verified": "2026-11-04",
        "expires_at": "2027-11-04",
        "tags": ["comfyui", "local-gpu", "b-roll", "open-source-ai"]
    },
    "multi-agent-broll-orchestration.md": {
        "id": "multi-agent-broll-orchestration",
        "title": "Multi-Agent B-Roll Orchestration & Parallel Asset Generation",
        "status": "knowledge",
        "build": "partial",
        "reproducible_with_our_stack": "yes",
        "needs": ["Python asyncio", "AI Providers"],
        "implemented_in": ["tool/src/socnhotv/intelligence/"],
        "evidence_videos": ["seq_N05"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "2027-11-04",
        "tags": ["multi-agent", "orchestration", "parallel-gen", "b-roll"]
    },
    "niche-opportunity-index.md": {
        "id": "niche-opportunity-index",
        "title": "Niche Opportunity Index & Market Gap Discovery",
        "status": "knowledge",
        "build": "no",
        "reproducible_with_our_stack": "partial (Mô hình tính điểm thị trường bằng tay/kịch bản; ngoài core video engine)",
        "needs": ["Market Search Data"],
        "implemented_in": [],
        "evidence_videos": ["seq_010"],
        "confidence": "medium",
        "last_verified": "2026-11-04",
        "expires_at": "2027-11-04",
        "tags": ["market-research", "niche-index", "strategy", "ecommerce"]
    },
    "pre-publish-hook-retention-prediction.md": {
        "id": "pre-publish-hook-retention-prediction",
        "title": "Pre-Publish Hook Retention Prediction & Heuristic Scoring",
        "status": "in-studio",
        "build": "yes",
        "reproducible_with_our_stack": "yes",
        "needs": ["Python Heuristics", "Lint Engine"],
        "implemented_in": [
            "tool/src/socnhotv/video/craft/hooks.py",
            "tool/src/socnhotv/video/craft/lint.py",
            "data/shared/knowledge/video_craft/playbooks/hook-and-retention.md"
        ],
        "evidence_videos": ["seq_N04"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["hook-prediction", "retention-curve", "pre-flight-check", "heuristic-scoring"]
    },
    "rapid-montage-proof.md": {
        "id": "rapid-montage-proof",
        "title": "Rapid Montage Proof (Cắt Ghép Bằng Chứng Dồn Dập)",
        "status": "in-studio",
        "build": "yes",
        "reproducible_with_our_stack": "yes",
        "needs": ["HyperFrames", "GSAP rapid timeline"],
        "implemented_in": [
            "tool/src/socnhotv/video/craft/transitions.py",
            "data/shared/knowledge/video_craft/playbooks/camera-and-transitions.md"
        ],
        "evidence_videos": ["seq_003"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["montage", "proof-cut", "fast-paced", "retention", "social-proof"]
    },
    "split-canvas-lookbook.md": {
        "id": "split-canvas-lookbook",
        "title": "Split Canvas Lookbook (Khung Hình Chia Đôi / Chia Ba Lookbook)",
        "status": "knowledge",
        "build": "partial",
        "reproducible_with_our_stack": "yes",
        "needs": ["HyperFrames Layout"],
        "implemented_in": ["ai/skills/motion-mimic/"],
        "evidence_videos": ["seq_004"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["split-screen", "lookbook", "multi-tier", "visual-comparison"]
    },
    "sticker-cutout-doodle.md": {
        "id": "sticker-cutout-doodle",
        "title": "Sticker Cutout & Motion Doodle (Viền Sticker Trắng Cắt Rời & Nét Vẽ Hoạt Hình)",
        "status": "knowledge",
        "build": "partial",
        "reproducible_with_our_stack": "yes",
        "needs": ["HyperFrames SVG", "CSS drop-shadow"],
        "implemented_in": [],
        "evidence_videos": ["seq_006"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["sticker-cutout", "doodle", "motion-graphics", "2d-overlay"]
    },
    "transition-foresight-continuity.md": {
        "id": "transition-foresight-continuity",
        "title": "Transition Foresight & Motion Continuity (Chuyển Cảnh Tiên Liệu Hướng Chuyển Động)",
        "status": "in-studio",
        "build": "yes",
        "reproducible_with_our_stack": "yes",
        "needs": ["HyperFrames", "Python transition resolver"],
        "implemented_in": [
            "tool/src/socnhotv/video/craft/transitions.py",
            "data/shared/knowledge/video_craft/playbooks/camera-and-transitions.md"
        ],
        "evidence_videos": ["seq_N01"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["transition-foresight", "motion-continuity", "whip-pan", "match-cut", "smooth-pacing"]
    },
    "video-element-replacement.md": {
        "id": "video-element-replacement",
        "title": "Video Element Replacement & AI Inpainting (Thay Thế Vật Thể Trong Video)",
        "status": "knowledge",
        "build": "no",
        "reproducible_with_our_stack": "partial (Cần video inpainting model chuyên biệt)",
        "needs": ["Runway Gen-3 / Ebsynth"],
        "implemented_in": [],
        "evidence_videos": ["seq_008"],
        "confidence": "medium",
        "last_verified": "2026-11-04",
        "expires_at": "2027-11-04",
        "tags": ["inpainting", "element-replacement", "vfx", "generative-video"]
    },
    "virtual-influencer-paradox-storytelling.md": {
        "id": "virtual-influencer-paradox-storytelling",
        "title": "Virtual Influencer Paradox Storytelling & 4th Wall Break",
        "status": "in-studio",
        "build": "yes",
        "reproducible_with_our_stack": "yes",
        "needs": ["Script Generator", "OmniVoice"],
        "implemented_in": [
            "tool/src/socnhotv/video/craft/hooks.py",
            "data/shared/knowledge/video_craft/playbooks/hook-and-retention.md"
        ],
        "evidence_videos": ["seq_N07"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["virtual-influencer", "4th-wall-break", "storytelling", "paradox-hook", "emotional-connection"]
    },
    "walking-outfit-transition.md": {
        "id": "walking-outfit-transition",
        "title": "Walking Outfit Transition (Chuyển Đổi Trang Phục Theo Bước Chân)",
        "status": "knowledge",
        "build": "partial",
        "reproducible_with_our_stack": "yes",
        "needs": ["HyperFrames", "GSAP beat sync"],
        "implemented_in": [],
        "evidence_videos": ["seq_012"],
        "confidence": "high",
        "last_verified": "2026-11-04",
        "expires_at": "never",
        "tags": ["outfit-transition", "footstep-sync", "fashion-cut", "beat-sync"]
    }
}

def standardize_file(file_path: Path):
    filename = file_path.name
    meta = CARDS_META.get(filename)
    if not meta:
        print(f"Warning: No metadata mapped for {filename}")
        return

    content = file_path.read_text(encoding="utf-8")
    # If front-matter already exists, strip it
    if content.startswith("---\n"):
        parts = content.split("---\n", 2)
        if len(parts) >= 3:
            body = parts[2].lstrip()
        else:
            body = content
    else:
        body = content

    yaml_header = yaml.dump(meta, sort_keys=False, allow_unicode=True).strip()
    new_content = f"---\n{yaml_header}\n---\n\n{body}"
    file_path.write_text(new_content, encoding="utf-8")
    print(f"Standardized {filename}")

def main():
    count = 0
    for filename in sorted(CARDS_META.keys()):
        file_path = TECHNIQUES_DIR / filename
        if file_path.exists():
            standardize_file(file_path)
            count += 1
        else:
            print(f"Error: {file_path} not found")
    print(f"\nDone: {count}/26 cards standardized.")

if __name__ == "__main__":
    main()
