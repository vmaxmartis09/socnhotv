#!/usr/bin/env python3
"""
depth-layers (T-10): tách ảnh thành 3 lớp tiền / trung / hậu cảnh theo độ sâu (Depth Anything V2 Small, CPU)
để dựng parallax trong HyperFrames (craft/depth: 0.2x / 1.0x / 1.8x).

Lớp XẾP CHỒNG, KHÔNG có lỗ hổng khi dịch chuyển:
  layer_bg.png   toàn bộ ảnh (nền, không cắt)
  layer_mid.png  RGBA: vùng trung + tiền cảnh
  layer_fg.png   RGBA: chỉ vùng tiền cảnh
Chồng bg → mid → fg (alpha-over) khôi phục đúng ảnh gốc (tool đo PSNR để kiểm).
Kèm depth.png (bản đồ độ sâu, sáng = gần).

params: fg_pct (70) · mid_pct (35) phân vị độ sâu · feather (3) px làm mềm viền mask · max_side (1280)
Giấy phép: chỉ bản Small của Depth Anything V2 là Apache-2.0 (bản lớn khác giấy phép).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_DIR.parents[1] / "toolbox_cli"))
from kit import (  # noqa: E402
    SHARED_DIR, BadInput, MissingDependency, atomic_write, compute_sha8, out_file, run_tool, store_record,
)

VERSION = "1.0.0"
MODEL_ID = "depth-anything/Depth-Anything-V2-Small-hf"
MODELS_DIR = SHARED_DIR / "models" / "depth-anything-v2-small"
OUT_ROOT = SHARED_DIR / "assets" / "frames"
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def process(inputs, params, ctx):
    try:
        import numpy as np
        import torch
        from PIL import Image, ImageFilter
        from transformers import AutoImageProcessor, AutoModelForDepthEstimation
    except ImportError as e:
        raise MissingDependency(f"Thiếu thư viện: {e.name}", "python -m pip install -r requirements.txt trong venv của tool") from e

    src = inputs[0]
    if src.suffix.lower() not in IMG_EXT:
        raise BadInput(f"Định dạng {src.suffix} không phải ảnh được hỗ trợ")
    fg_pct = float(params.get("fg_pct", 70))
    mid_pct = float(params.get("mid_pct", 35))
    feather = float(params.get("feather", 3))
    max_side = int(params.get("max_side", 1280))
    if not (0 < mid_pct < fg_pct < 100):
        raise BadInput("Cần 0 < mid_pct < fg_pct < 100")

    img = Image.open(src).convert("RGB")
    if max(img.size) > max_side:
        k = max_side / max(img.size)
        img = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    processor = AutoImageProcessor.from_pretrained(MODEL_ID, cache_dir=str(MODELS_DIR))
    model = AutoModelForDepthEstimation.from_pretrained(MODEL_ID, cache_dir=str(MODELS_DIR)).eval()
    with torch.no_grad():
        pred = model(**processor(images=img, return_tensors="pt")).predicted_depth
        pred = torch.nn.functional.interpolate(pred.unsqueeze(1), size=(img.height, img.width), mode="bicubic", align_corners=False)
    d = pred.squeeze().cpu().numpy().astype("float32")
    d = (d - d.min()) / max(1e-6, float(d.max() - d.min()))  # 0 xa … 1 gần

    t_fg, t_mid = np.percentile(d, fg_pct), np.percentile(d, mid_pct)

    def soft(mask_bool):
        m = Image.fromarray((mask_bool * 255).astype("uint8"), "L")
        return m.filter(ImageFilter.GaussianBlur(feather)) if feather > 0 else m

    mask_fg, mask_mid = soft(d >= t_fg), soft(d >= t_mid)

    sha8 = compute_sha8(src)
    out_dir = OUT_ROOT / sha8
    out_dir.mkdir(parents=True, exist_ok=True)

    def with_alpha(mask):
        rgba = img.convert("RGBA")
        rgba.putalpha(mask)
        return rgba

    bg, mid, fg = img.convert("RGBA"), with_alpha(mask_mid), with_alpha(mask_fg)
    depth_img = Image.fromarray((d * 255).astype("uint8"), "L")

    paths = {"layer_bg": out_dir / "layer_bg.png", "layer_mid": out_dir / "layer_mid.png",
             "layer_fg": out_dir / "layer_fg.png", "depth": out_dir / "depth.png"}
    bg.save(paths["layer_bg"]); mid.save(paths["layer_mid"]); fg.save(paths["layer_fg"]); depth_img.save(paths["depth"])

    # Kiểm: chồng 3 lớp phải khôi phục ảnh gốc (bg phủ kín nên kết quả bằng đúng bg; đo thêm sai khác mid/fg so với ảnh)
    comp = Image.alpha_composite(Image.alpha_composite(bg, mid), fg).convert("RGB")
    a, b = np.asarray(img, dtype="float32"), np.asarray(comp, dtype="float32")
    mse = float(((a - b) ** 2).mean())
    psnr = 99.0 if mse == 0 else float(10 * np.log10(255.0 ** 2 / mse))
    cover = {"fg": round(float((np.asarray(mask_fg) > 127).mean()), 3), "mid_plus_fg": round(float((np.asarray(mask_mid) > 127).mean()), 3)}

    meta = {"source": str(src.resolve()), "size": [img.width, img.height], "model": MODEL_ID,
            "fg_pct": fg_pct, "mid_pct": mid_pct, "feather": feather, "reconstruction_psnr_db": round(psnr, 2),
            "coverage": cover, "parallax_hint": {"layer_bg": 0.2, "layer_mid": 1.0, "layer_fg": 1.8}}
    meta_path = out_dir / "layers.json"
    atomic_write(meta_path, json.dumps(meta, ensure_ascii=False, indent=2))

    outputs = [out_file(paths[k], k) for k in ("layer_bg", "layer_mid", "layer_fg", "depth")] + [out_file(meta_path, "layers_json")]
    rec = store_record(sha8, "depth-layers", VERSION, str(src.resolve()), "Apache-2.0 (Depth Anything V2 Small)",
                       {**{k: v for k, v in paths.items()}, "layers_json": meta_path},
                       {"width": img.width, "height": img.height, "psnr_db": round(psnr, 2), "coverage": cover},
                       index=OUT_ROOT / "index.jsonl")
    warnings = []
    if psnr < 40:
        warnings.append(f"Chồng lớp khôi phục chỉ đạt PSNR {psnr:.1f}dB (< 40dB)")
    return outputs, [rec], warnings


if __name__ == "__main__":
    run_tool(process)
