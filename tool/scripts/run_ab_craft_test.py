#!/usr/bin/env python3
"""Run Internal A/B Test comparing Vanilla Video vs Craft-Optimized Video.

Topic: "Vì sao cầu vồng có nhiều màu?"
- Version A (Vanilla): Flat 2D, greeting hook, static cuts, no camera move, no depth.
- Version B (Craft): Hook Lab confession hook, 3-layer spatial parallax, push-right transition, push-in camera.

Renders both, extracts 12-frame contact sheets, and runs Creative QA Lint on both.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from socnhotv.core.adapters.hyperframes_adapter import HyperFramesAdapter
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root
from socnhotv.video.craft.lint import lint_script, lint_composition
from socnhotv.video.craft.hooks import score_hook, generate_hook_variants
from socnhotv.video.craft.depth import build_3layer_html_composition
from socnhotv.video.craft.transitions import resolve_transition, MotionVector

REPO_ROOT = get_repo_root()
AB_DIR = REPO_ROOT / "data" / "shared" / "templates" / "_techniques" / "ab_comparison"
AB_DIR.mkdir(parents=True, exist_ok=True)

BG_IMG = REPO_ROOT / "data" / "projects" / "soc-nho-tv" / "content" / "episodes" / "soc-nho-sau-rang" / "scenes" / "canh_01.jpg"
DNA_IMG = REPO_ROOT / "data" / "projects" / "soc-nho-tv" / "characters" / "soc_nho" / "soc_nho_01.png"
VOICE_AUDIO = REPO_ROOT / "output" / "preflight_voice.mp3"

def run_ab_test():
    store = ProjectStore("soc-nho-tv")
    adapter = HyperFramesAdapter(store)

    # 1. Version A: Vanilla
    script_a = "Xin chào các bạn, hôm nay mình xin chia sẻ vì sao cầu vồng có nhiều màu."
    lint_a = lint_script(script_a, duration_sec=5.0)
    hook_score_a = score_hook(script_a)

    dir_a = AB_DIR / "version_a_vanilla"
    dir_a.mkdir(parents=True, exist_ok=True)
    (dir_a / "assets").mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(BG_IMG, dir_a / "assets" / "bg.jpg")
    shutil.copy2(DNA_IMG, dir_a / "assets" / "char.png")
    shutil.copy2(VOICE_AUDIO, dir_a / "assets" / "voiceover.mp3")

    html_a = """<!DOCTYPE html>
<html><body style="margin:0;width:1080px;height:1920px;background:#000;">
  <img src="assets/bg.jpg" style="width:100%;height:100%;object-fit:cover;" />
  <img src="assets/char.png" style="position:absolute;bottom:300px;left:50%;transform:translateX(-50%);max-height:800px;" />
  <div style="position:absolute;top:50px;left:50px;color:#FFF;font-size:28px;">Xin chào các bạn...</div>
</body></html>"""
    (dir_a / "index.html").write_text(html_a, encoding="utf-8")
    (dir_a / "hyperframes.json").write_text(json.dumps({"width":1080,"height":1920,"fps":30,"duration":5.0}))
    mp4_a = dir_a / "vanilla.mp4"
    adapter.render(dir_a, mp4_a, fps=30)

    # 2. Version B: Craft Optimized
    hook_b_res = generate_hook_variants("Vì sao cầu vồng có nhiều màu?", character="soc-nho")
    script_b = f"{hook_b_res.selected_hook}\nÁnh sáng trắng đi qua giọt mưa bị tán sắc thành 7 màu rực rỡ!\nBình luận màu bạn thích nhất nhé!"
    lint_b = lint_script(script_b, duration_sec=5.0)
    hook_score_b = score_hook(hook_b_res.selected_hook)

    dir_b = AB_DIR / "version_b_craft"
    dir_b.mkdir(parents=True, exist_ok=True)
    (dir_b / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy2(BG_IMG, dir_b / "assets" / "bg.jpg")
    shutil.copy2(DNA_IMG, dir_b / "assets" / "char.png")
    shutil.copy2(VOICE_AUDIO, dir_b / "assets" / "voiceover.mp3")

    html_b = build_3layer_html_composition(
        bg_asset_url="assets/bg.jpg",
        mid_asset_url="assets/char.png",
        duration_sec=5.0,
        title_text="CẦU VỒNG 7 MÀU"
    )
    (dir_b / "index.html").write_text(html_b, encoding="utf-8")
    (dir_b / "hyperframes.json").write_text(json.dumps({"width":1080,"height":1920,"fps":30,"duration":5.0}))
    mp4_b = dir_b / "craft_optimized.mp4"
    adapter.render(dir_b, mp4_b, fps=30)

    # 3. Extract 12-frame contact sheets for visual inspection
    ffmpeg = adapter.ffmpeg
    sheet_a = dir_a / "contact_sheet_12frames.jpg"
    sheet_b = dir_b / "contact_sheet_12frames.jpg"
    
    # 12 frames extracted across 5 seconds (every ~0.4s) into a 4x3 tile grid
    cmd_sheet_a = [
        ffmpeg, "-y", "-i", str(mp4_a),
        "-vf", "fps=2.4,scale=270:480,tile=4x3",
        "-frames:v", "1", str(sheet_a)
    ]
    subprocess.run(cmd_sheet_a, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cmd_sheet_b = [
        ffmpeg, "-y", "-i", str(mp4_b),
        "-vf", "fps=2.4,scale=270:480,tile=4x3",
        "-frames:v", "1", str(sheet_b)
    ]
    subprocess.run(cmd_sheet_b, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    report = {
        "topic": "Vì sao cầu vồng có nhiều màu?",
        "version_a_vanilla": {
            "hook": script_a,
            "hook_score": hook_score_a.total_score,
            "hook_penalties": hook_score_a.penalties,
            "lint_passed": lint_a.passed,
            "lint_errors": lint_a.error_count,
            "lint_warnings": lint_a.warning_count,
            "mp4_file": str(mp4_a),
            "contact_sheet": str(sheet_a)
        },
        "version_b_craft": {
            "hook": hook_b_res.selected_hook,
            "hook_score": hook_score_b.total_score,
            "hook_bonuses": hook_score_b.bonuses,
            "lint_passed": lint_b.passed,
            "lint_errors": lint_b.error_count,
            "lint_warnings": lint_b.warning_count,
            "mp4_file": str(mp4_b),
            "contact_sheet": str(sheet_b)
        }
    }

    report_path = AB_DIR / "ab_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ A/B test completed successfully. Report saved to {report_path}")
    print(f"   Version A Score: {hook_score_a.total_score}/100, Lint Passed: {lint_a.passed}")
    print(f"   Version B Score: {hook_score_b.total_score}/100, Lint Passed: {lint_b.passed}")

if __name__ == "__main__":
    run_ab_test()
