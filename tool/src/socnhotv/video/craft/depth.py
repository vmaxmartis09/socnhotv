"""3-Layer Spatial Depth Engine: Prompt Enrichment and HyperFrames Parallax.

Eliminates the "Flat AI" effect by strictly partitioning space into 3 layers:
- Layer 1: Foreground Occlusion (out-of-focus optical bokeh, floating particles)
- Layer 2: Midground In-Focus Subject (Master DNA character, scale-locked)
- Layer 3: Atmospheric Background (cinematic haze, soft depth of field)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional

CHARACTER_DNA_PROMPTS = {
    "soc_nho": (
        "master character soc_nho (a cute 100cm cartoon squirrel with fluffy striped tail, "
        "large expressive warm hazel eyes, adorable soft velvet ears, standing at 100cm scale), "
        "wearing a tiny explorer acorn satchel, natural rim lighting, sharp in-focus 8k"
    ),
    "koala": (
        "master character doctor koala (a gentle 150cm anthropomorphic koala with round fuzzy ears, "
        "wearing spectacles and a neat beige vest, standing at 150cm scale), friendly wise expression"
    ),
    "gobi_koc": (
        "Vietnamese female fashion KOC, natural glowing skin, modern chic casual outfit, "
        "confident warm smile, sharp in-focus studio portraiture"
    )
}

ENVIRONMENT_DEPTH_PROMPTS = {
    "forest": {
        "foreground": "softly blurred sunlit oak leaves and floating golden pollen flakes in the extreme foreground, out-of-focus optical bokeh",
        "background": "lush ancient forest softly receding into morning atmospheric mist, warm golden sunbeams through pine canopy, deep focal falloff"
    },
    "rainbow_sky": {
        "foreground": "translucent shimmering rainbow raindrops catching sunlight in extreme close-up, soft circular camera lens bokeh",
        "background": "soft pastel sky with a magnificent curved vibrant rainbow fading gently into distant fluffy cumulus clouds"
    },
    "studio_indoor": {
        "foreground": "soft edge of a modern indoor potted plant leaf slightly blurring the bottom corner, shallow depth of field",
        "background": "cozy modern Scandinavian interior, warm ambient background lighting, soft furniture blur"
    }
}

@dataclass
class EnrichedPrompt:
    foreground_prompt: str
    midground_prompt: str
    background_prompt: str
    combined_prompt: str

def enrich_3layer_prompt(
    action_or_core: str,
    character_key: str = "soc_nho",
    environment_key: str = "forest"
) -> EnrichedPrompt:
    """Enriches a base action prompt into a 3-layer spatial prompt preserving character DNA."""
    char_desc = CHARACTER_DNA_PROMPTS.get(character_key, CHARACTER_DNA_PROMPTS["soc_nho"])
    env_data = ENVIRONMENT_DEPTH_PROMPTS.get(environment_key, ENVIRONMENT_DEPTH_PROMPTS["forest"])

    fg = env_data["foreground"]
    mid = f"{char_desc}, {action_or_core}"
    bg = env_data["background"]

    combined = (
        f"[Foreground]: {fg}. "
        f"[Midground]: {mid}. "
        f"[Background]: {bg}. "
        f"Cinematic 3-layer spatial composition, shot on 50mm f/1.4 lens, 9:16 vertical."
    )

    return EnrichedPrompt(
        foreground_prompt=fg,
        midground_prompt=mid,
        background_prompt=bg,
        combined_prompt=combined
    )

def build_3layer_html_composition(
    bg_asset_url: str,
    mid_asset_url: str,
    fg_asset_url: Optional[str] = None,
    duration_sec: float = 5.0,
    width: int = 1080,
    height: int = 1920,
    title_text: str = ""
) -> str:
    """Builds a deterministic, seekable HyperFrames HTML5/CSS/GSAP 3-layer composition."""
    # If no separate foreground asset is provided, generate a floating bokeh particle overlay via CSS
    fg_markup = (
        f'<img src="{fg_asset_url}" class="layer layer-fg" alt="foreground" />'
        if fg_asset_url
        else '<div class="layer layer-fg-bokeh"></div>'
    )

    title_markup = (
        f'<div class="scene-title-badge">{title_text}</div>'
        if title_text
        else ""
    )

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width={width}, height={height}">
  <title>HyperFrames 3-Layer Spatial Depth</title>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      width: {width}px;
      height: {height}px;
      overflow: hidden;
      background: #000;
      position: relative;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    .stage {{
      position: absolute;
      width: 100%;
      height: 100%;
      perspective: 1000px;
      overflow: hidden;
    }}
    .layer {{
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      will-change: transform;
    }}
    /* Layer 3: Background */
    .layer-bg {{
      object-fit: cover;
      transform: scale(1.15) translate(0px, 0px);
      filter: blur(2px) brightness(0.9);
      z-index: 10;
    }}
    /* Layer 2: Midground Character (DNA RGBA) */
    .layer-mid {{
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 20;
    }}
    .character-img {{
      max-width: 85%;
      max-height: 85%;
      object-fit: contain;
      filter: drop-shadow(0 20px 30px rgba(0,0,0,0.6));
    }}
    /* Layer 1: Foreground Bokeh / Occlusion */
    .layer-fg-bokeh {{
      position: absolute;
      width: 100%; height: 100%;
      background: radial-gradient(circle at 15% 20%, rgba(255, 230, 150, 0.45) 0%, transparent 18%),
                  radial-gradient(circle at 85% 75%, rgba(255, 255, 255, 0.35) 0%, transparent 22%),
                  radial-gradient(circle at 25% 85%, rgba(255, 200, 100, 0.3) 0%, transparent 15%);
      pointer-events: none;
      z-index: 30;
      filter: blur(8px);
    }}
    .layer-fg {{
      object-fit: cover;
      pointer-events: none;
      z-index: 30;
      filter: blur(6px);
    }}
    .scene-title-badge {{
      position: absolute;
      top: 140px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(15, 23, 42, 0.85);
      color: #FFF;
      padding: 16px 32px;
      border-radius: 9999px;
      font-size: 32px;
      font-weight: 700;
      letter-spacing: 0.5px;
      border: 1px solid rgba(255, 255, 255, 0.2);
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      z-index: 40;
    }}
  </style>
</head>
<body>
  <div class="stage" id="stage">
    <img src="{bg_asset_url}" class="layer layer-bg" id="bgLayer" alt="background" />
    <div class="layer layer-mid" id="midLayer">
      <img src="{mid_asset_url}" class="character-img" id="charImg" alt="character" />
    </div>
    {fg_markup}
    {title_markup}
  </div>

  <script>
    // Deterministic GSAP Timeline for HyperFrames Virtual Clock
    const tl = gsap.timeline({{ paused: true }});
    const dur = {duration_sec};

    // Parallax motion: Background moves slowly, Midground reacts naturally, Foreground drifts fast
    tl.fromTo("#bgLayer", 
      {{ scale: 1.15, x: -30, y: -15 }}, 
      {{ scale: 1.18, x: 30, y: 15, duration: dur, ease: "power1.inOut" }}, 0
    );

    tl.fromTo("#midLayer", 
      {{ scale: 0.98, y: 10 }}, 
      {{ scale: 1.02, y: -10, duration: dur, ease: "sine.inOut" }}, 0
    );

    tl.fromTo(".layer-fg-bokeh, .layer-fg", 
      {{ x: -60, y: -30 }}, 
      {{ x: 80, y: 40, duration: dur, ease: "none" }}, 0
    );

    window.__timeline = tl;
    window.__duration = dur;
  </script>
</body>
</html>"""
    return html
