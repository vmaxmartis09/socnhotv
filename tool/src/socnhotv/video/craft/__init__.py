"""Video Craft Toolkit for Studio & HyperFrames Automation.

Exports:
- Hook Lab: generate_hook_variants, score_hook
- 3-Layer Spatial Depth: enrich_3layer_prompt, build_3layer_html_composition
- Transition Foresight: resolve_transition, build_rapid_montage_gsap
- Camera Presets: get_camera_preset, build_camera_gsap_snippet
- Creative QA / Lint: lint_script, lint_caption, lint_composition
"""
from __future__ import annotations

from socnhotv.video.craft.hooks import (
    score_hook,
    generate_hook_variants,
    HookScore,
    HookVariant,
    HookLabResult,
)
from socnhotv.video.craft.depth import (
    enrich_3layer_prompt,
    build_3layer_html_composition,
    EnrichedPrompt,
)
from socnhotv.video.craft.transitions import (
    resolve_transition,
    build_rapid_montage_gsap,
    MotionVector,
    TransitionDecision,
)
from socnhotv.video.craft.camera import (
    get_camera_preset,
    build_camera_gsap_snippet,
    CameraPreset,
    CAMERA_PRESETS,
)
from socnhotv.video.craft.lint import (
    lint_script,
    lint_caption,
    lint_composition,
    Issue,
    LintReport,
)

__all__ = [
    "score_hook",
    "generate_hook_variants",
    "HookScore",
    "HookVariant",
    "HookLabResult",
    "enrich_3layer_prompt",
    "build_3layer_html_composition",
    "EnrichedPrompt",
    "resolve_transition",
    "build_rapid_montage_gsap",
    "MotionVector",
    "TransitionDecision",
    "get_camera_preset",
    "build_camera_gsap_snippet",
    "CameraPreset",
    "CAMERA_PRESETS",
    "lint_script",
    "lint_caption",
    "lint_composition",
    "Issue",
    "LintReport",
]
