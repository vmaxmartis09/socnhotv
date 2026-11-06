"""Node plugin nối Toolbox (tool/toolbox/tools/*) vào Studio (luồng I5).

Mỗi node bọc đúng một công cụ Toolbox, gọi như tiến trình con theo hợp đồng
`python run.py --in in.json --out out.json` bằng venv của chính công cụ (không import mã của tool).

Node            Công cụ        Vào -> Ra
--------------  -------------  ---------------------------------------------
bg_remove       bg-remove      image -> image (RGBA) + mask. Dùng được cho ảnh nhân vật
word_captions   stt-align      audio -> captions (SRT) + words (JSON từng từ)
scene_cut       scene-cut      video -> scenes (+ clip từng cảnh khi bật)
depth_layers    depth-layers   image -> bg / mid / fg (PNG) + depth
handdraw        handdraw       image -> video vẽ tay bảng trắng
voice_clone     voice-clone    audio mẫu -> voiceId (+ đọc thử). Cần consent_note

Công cụ chạy cục bộ, miễn phí (cost 0). Riêng `voice_clone` ghi vào kho giọng nên chế độ mock chỉ chạy dry_run.
Việc gọi `execute_toolbox_node` từ bộ chạy đồ thị cần một nhánh dispatch trong graph_runner (xem status/I5.md).
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactMeta,
    ArtifactProvenance,
    NodeDefinition,
    PortDefinition,
    PortType,
)

# tool/src/socnhotv/core/nodes/plugins/toolbox.py -> parents[5] = tool/
TOOLBOX_DIR = Path(os.environ.get("SOCNHOTV_TOOLBOX_DIR") or Path(__file__).resolve().parents[5] / "toolbox")
TOOLS_DIR = TOOLBOX_DIR / "tools"

#: node type -> mã công cụ Toolbox
NODE_TOOL: Dict[str, str] = {
    "bg_remove": "bg-remove",
    "word_captions": "stt-align",
    "scene_cut": "scene-cut",
    "depth_layers": "depth-layers",
    "handdraw": "handdraw",
    "voice_clone": "voice-clone",
}
TOOLBOX_NODE_TYPES = frozenset(NODE_TOOL)

DEFAULT_TIMEOUT_S = {"bg-remove": 300, "stt-align": 900, "scene-cut": 600, "depth-layers": 600, "handdraw": 600, "voice-clone": 1500}


class ToolboxError(RuntimeError):
    """Công cụ báo lỗi thật (không có file giả). `exit_code` theo hợp đồng Toolbox (2 thiếu phụ thuộc, 3 đầu vào sai)."""

    def __init__(self, tool_id: str, code: str, message: str, fix_hint: Optional[str] = None, exit_code: int = 1):
        super().__init__(f"[{tool_id}] {code}: {message}" + (f" — {fix_hint}" if fix_hint else ""))
        self.tool_id, self.code, self.message, self.fix_hint, self.exit_code = tool_id, code, message, fix_hint, exit_code


# --------------------------------------------------------------------------- chạy công cụ
def tool_python(tool_id: str) -> str:
    """Python của venv riêng công cụ; không có thì dùng Python hiện tại (tool chỉ dùng thư viện chuẩn vẫn chạy)."""
    base = TOOLS_DIR / tool_id / ".venv"
    for rel in ("bin/python", "Scripts/python.exe"):
        if (base / rel).exists():
            return str(base / rel)
    return sys.executable


def tool_available(tool_id: str) -> bool:
    return (TOOLS_DIR / tool_id / "run.py").exists()


def run_tool(tool_id: str, inputs: List[Path], params: Dict[str, Any], *, dry_run: bool = False,
             project: Optional[str] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
    """Chạy `tools/<id>/run.py`, trả nội dung out.json (ok=True). Lỗi thật -> ToolboxError."""
    run_py = TOOLS_DIR / tool_id / "run.py"
    if not run_py.exists():
        raise ToolboxError(tool_id, "TOOL_NOT_FOUND", f"Không thấy {run_py}", "Kiểm tra tool/toolbox/tools", 2)
    with tempfile.TemporaryDirectory(prefix=f"toolbox-{tool_id}-") as tmp:
        in_p, out_p = Path(tmp) / "in.json", Path(tmp) / "out.json"
        in_p.write_text(json.dumps({
            "params": params, "inputs": [str(p) for p in inputs], "project": project, "dry_run": dry_run,
        }, ensure_ascii=False), encoding="utf-8")
        try:
            proc = subprocess.run(
                [tool_python(tool_id), str(run_py), "--in", str(in_p), "--out", str(out_p)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=str(TOOLBOX_DIR.parent.parent), timeout=timeout or DEFAULT_TIMEOUT_S.get(tool_id, 600),
            )
        except subprocess.TimeoutExpired as e:
            raise ToolboxError(tool_id, "TIMEOUT", f"Quá thời gian chờ ({e.timeout}s)") from e
        if not out_p.exists():
            tail = " | ".join((proc.stderr or proc.stdout or "").strip().splitlines()[-3:])
            raise ToolboxError(tool_id, "NO_OUT_JSON", f"Công cụ thoát mã {proc.returncode} mà không ghi out.json: {tail}",
                               None, proc.returncode or 1)
        data = json.loads(out_p.read_text(encoding="utf-8"))
    if not data.get("ok"):
        err = data.get("error") or {}
        raise ToolboxError(tool_id, err.get("code", "TOOL_FAILED"), err.get("message", "không rõ"),
                           err.get("fix_hint"), proc.returncode or 1)
    return data


def _by_kind(result: Dict[str, Any]) -> Dict[str, List[Path]]:
    out: Dict[str, List[Path]] = {}
    for o in result.get("outputs", []):
        out.setdefault(o.get("kind", ""), []).append(Path(o["path"]))
    return out


# --------------------------------------------------------------------------- đầu vào/đầu ra Artifact
def _artifact_path(value: Any, store: Any) -> Optional[Path]:
    if isinstance(value, list):
        value = value[0] if value else None
    if value is None or value == "":
        return None
    if isinstance(value, Artifact):
        return Path(store.resolve_artifact_path(value))
    s = str(value)
    p = Path(s)
    if p.is_absolute() and p.exists():
        return p
    cand = Path(store.project_dir) / s.lstrip("/")
    return cand if cand.exists() else None


def _character_image(store: Any, char_id: str, index: int = 0) -> Optional[Path]:
    """Ảnh DNA gốc của nhân vật trong dự án (bỏ thư mục bắt đầu bằng '_')."""
    char_dir = Path(store.characters_dir) / char_id
    pngs = sorted(p for p in char_dir.glob("*.png")) if char_dir.exists() else []
    return pngs[index] if 0 <= index < len(pngs) else None


def _store_file(store: Any, path: Path, kind: ArtifactKind, node_id: str, run_id: str, tool_id: str,
                params: Dict[str, Any], meta: Optional[ArtifactMeta] = None, input_hashes: Optional[List[str]] = None) -> Artifact:
    prov = ArtifactProvenance(
        node_id=node_id, run_id=run_id, provider="toolbox", model=tool_id, params=params,
        input_hashes=input_hashes or [], cost_usd=0.0, created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    return store.store_bytes(data=Path(path).read_bytes(), ext=Path(path).suffix.lstrip(".") or "bin", kind=kind,
                             provenance=prov, meta=meta)


def _image_meta(path: Path) -> ArtifactMeta:
    try:
        from PIL import Image

        with Image.open(path) as im:
            return ArtifactMeta(width=im.width, height=im.height)
    except Exception:  # noqa: BLE001
        return ArtifactMeta()


def _need(path: Optional[Path], what: str, node_type: str) -> Path:
    if path is None:
        raise ValueError(f"Node '{node_type}' thiếu {what} — hãy nối cổng đầu vào hoặc điền tham số tương ứng.")
    return path


async def execute_toolbox_node(
    node_type: str,
    node_id: str,
    params: Dict[str, Any],
    resolved_inputs: Dict[str, Any],
    store: Any,
    run_id: str,
    is_mock: bool = True,
    runner: Callable[..., Dict[str, Any]] = run_tool,
) -> Tuple[Dict[str, Any], Optional[Artifact], float]:
    """Chạy một node Toolbox, trả (outputs, primary_artifact, cost_usd) đúng khuôn `_execute_node_handler`.

    `runner` để test thay bằng giả lập; mặc định gọi công cụ thật.
    """
    if node_type not in NODE_TOOL:
        raise KeyError(f"Không phải node Toolbox: {node_type}")
    tool_id = NODE_TOOL[node_type]
    p = {**(NODE_DEFAULTS.get(node_type) or {}), **(params or {})}
    outputs: Dict[str, Any] = {}
    primary: Optional[Artifact] = None

    def call(inp: List[Path], tp: Dict[str, Any], dry: bool = False) -> Dict[str, Any]:
        return runner(tool_id, inp, tp, dry_run=dry, project=getattr(store, "project_id", None))

    async def acall(inp: List[Path], tp: Dict[str, Any], dry: bool = False) -> Dict[str, Any]:
        return await asyncio.to_thread(call, inp, tp, dry)

    if node_type == "bg_remove":
        src = _artifact_path(resolved_inputs.get("image"), store)
        if src is None and p.get("characterId"):
            src = _character_image(store, str(p["characterId"]), int(p.get("imageIndex", 0)))
        src = _need(src, "ảnh đầu vào (cổng 'image') hoặc params.characterId có ảnh DNA", node_type)
        res = await acall([src], {"model": p["model"], "alpha_matting": bool(p["alpha_matting"])})
        k = _by_kind(res)
        if "cutout" not in k:
            raise ToolboxError(tool_id, "NO_OUTPUT", "Công cụ không trả ảnh cutout")
        img = _store_file(store, k["cutout"][0], ArtifactKind.IMAGE, node_id, run_id, tool_id,
                          {"model": p["model"], "source": src.name}, _image_meta(k["cutout"][0]))
        outputs["image"] = img
        if "mask" in k:
            outputs["mask"] = _store_file(store, k["mask"][0], ArtifactKind.IMAGE, node_id, run_id, tool_id,
                                          {"model": p["model"], "source": src.name, "role": "mask"}, _image_meta(k["mask"][0]))
        primary = img

    elif node_type == "word_captions":
        src = _need(_artifact_path(resolved_inputs.get("audio"), store), "audio đầu vào (cổng 'audio')", node_type)
        res = await acall([src], {"model_size": p["model_size"], "language": p["language"]})
        k = _by_kind(res)
        if "subtitles_srt" not in k or "word_timings" not in k:
            raise ToolboxError(tool_id, "NO_OUTPUT", "Công cụ không trả SRT hoặc thời gian từng từ")
        cap = _store_file(store, k["subtitles_srt"][0], ArtifactKind.CAPTIONS, node_id, run_id, tool_id,
                          {"model_size": p["model_size"], "language": p["language"]})
        words_doc = json.loads(k["word_timings"][0].read_text(encoding="utf-8"))
        words = [w for s in words_doc.get("segments", []) for w in s.get("words", [])]
        outputs["captions"] = cap
        outputs["words"] = json.dumps({"language": words_doc.get("language"), "duration": words_doc.get("duration"), "words": words},
                                      ensure_ascii=False)
        primary = cap

    elif node_type == "scene_cut":
        src = _need(_artifact_path(resolved_inputs.get("video"), store), "video đầu vào (cổng 'video')", node_type)
        res = await acall([src], {
            "threshold": float(p["threshold"]), "min_scene_s": float(p["min_scene_s"]),
            "export_clips": bool(p["export_clips"]), "aspect": p["aspect"], "max_scenes": int(p["max_scenes"]),
        })
        k = _by_kind(res)
        if "scenes_json" not in k:
            raise ToolboxError(tool_id, "NO_OUTPUT", "Công cụ không trả danh sách cảnh")
        doc = json.loads(k["scenes_json"][0].read_text(encoding="utf-8"))
        scenes = []
        for it in doc.get("scenes", []):
            sc = {
                "sceneNumber": it["index"], "title": f"Cảnh {it['index']}", "imagePrompt": "", "dialogue": "",
                "startSec": it["start"], "endSec": it["end"], "durationSec": it["duration"],
            }
            if it.get("clip"):
                sc["clip"] = it["clip"]
            scenes.append(sc)
        outputs["scenes"] = scenes
        outputs["report"] = f"{len(scenes)} cảnh / {doc.get('duration')}s (ngưỡng {p['threshold']})"

    elif node_type == "depth_layers":
        src = _artifact_path(resolved_inputs.get("image"), store)
        if src is None and p.get("characterId"):
            src = _character_image(store, str(p["characterId"]), int(p.get("imageIndex", 0)))
        src = _need(src, "ảnh đầu vào (cổng 'image')", node_type)
        res = await acall([src], {k_: p[k_] for k_ in ("fg_pct", "mid_pct", "feather", "max_side")})
        k = _by_kind(res)
        for name, kind in (("bg", "layer_bg"), ("mid", "layer_mid"), ("fg", "layer_fg"), ("depth", "depth")):
            if kind not in k:
                raise ToolboxError(tool_id, "NO_OUTPUT", f"Thiếu đầu ra {kind}")
            outputs[name] = _store_file(store, k[kind][0], ArtifactKind.IMAGE, node_id, run_id, tool_id,
                                        {"layer": name, "source": src.name}, _image_meta(k[kind][0]))
        primary = outputs["fg"]

    elif node_type == "handdraw":
        src = _need(_artifact_path(resolved_inputs.get("image"), store), "ảnh phác thảo nét đen nền trắng (cổng 'image')", node_type)
        res = await acall([src], {k_: p[k_] for k_ in ("duration_sec", "fps", "width", "height", "show_hand")})
        k = _by_kind(res)
        if "video" not in k:
            raise ToolboxError(tool_id, "NO_OUTPUT", "Công cụ không trả video")
        meta = ArtifactMeta(width=int(p["width"]), height=int(p["height"]), duration=float(p["duration_sec"]), fps=float(p["fps"]))
        vid = _store_file(store, k["video"][0], ArtifactKind.VIDEO, node_id, run_id, tool_id, {"source": src.name}, meta)
        outputs["video"] = vid
        primary = vid

    elif node_type == "voice_clone":
        sample = _need(_artifact_path(resolved_inputs.get("audio"), store), "mẫu giọng (cổng 'audio', 3.5–6s, một người nói)", node_type)
        name = str(p.get("name") or "").strip()
        if not name:
            raise ValueError("Node 'voice_clone' cần params.name (mã giọng dạng slug, ví dụ 'de-bong').")
        tp = {k_: p[k_] for k_ in ("name", "display_name", "consent_note", "dialect", "text", "duration", "verify", "verify_text") if p.get(k_) not in (None, "")}
        res = await acall([sample], tp, dry=is_mock)
        outputs["voice_id"] = name
        if is_mock:
            outputs["report"] = "mock: chưa clone (chỉ kiểm điều kiện); chạy thật để ghi vào kho giọng"
        else:
            k = _by_kind(res)
            if "voice_preview" in k:
                prev = _store_file(store, k["voice_preview"][0], ArtifactKind.AUDIO, node_id, run_id, tool_id, {"voice": name})
                outputs["preview"] = prev
                primary = prev
            outputs["report"] = f"đã clone '{name}' vào kho giọng"
    outputs["warnings"] = res.get("warnings", [])
    return outputs, primary, 0.0


# --------------------------------------------------------------------------- tham số mặc định
NODE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    # u2net: weights Apache-2.0; không dùng alpha_matting mặc định (chậm, dễ ăn viền ảnh hoạt hình)
    "bg_remove": {"model": "u2net", "alpha_matting": False, "characterId": "", "imageIndex": 0},
    "word_captions": {"model_size": "small", "language": "vi"},
    "scene_cut": {"threshold": 3.0, "min_scene_s": 1.0, "export_clips": False, "aspect": "keep", "max_scenes": 200},
    "depth_layers": {"fg_pct": 70, "mid_pct": 35, "feather": 3, "max_side": 1280, "characterId": "", "imageIndex": 0},
    # 9:16 an toàn TikTok; 540x960 để dựng nhanh, có thể nâng lên 1080x1920
    "handdraw": {"duration_sec": 5.0, "fps": 24, "width": 540, "height": 960, "show_hand": True},
    "voice_clone": {"name": "", "display_name": "", "consent_note": "", "dialect": "south", "duration": 4.5, "verify": True},
}


def register(registry: Any) -> None:
    """Đăng ký các node Toolbox vào NodeRegistry (menu 'Thêm node')."""
    P = PortDefinition

    registry.register(NodeDefinition(
        type_name="bg_remove", display_name="Tách nền ảnh", category="Structure",
        description="Tách nền ảnh thành PNG trong suốt + mặt nạ (rembg/u2net, chạy CPU). Nối ảnh nhân vật hoặc chọn nhân vật để có ảnh cắt sẵn, giữ nhất quán.",
        input_ports=[P(name="image", port_type=PortType.IMAGE, description="Ảnh cần tách nền (bỏ trống nếu chọn nhân vật)", required=False)],
        output_ports=[P(name="image", port_type=PortType.IMAGE, description="Ảnh đã tách nền (PNG RGBA)"),
                      P(name="mask", port_type=PortType.IMAGE, description="Mặt nạ alpha")],
        default_params=dict(NODE_DEFAULTS["bg_remove"]), mockable=False))

    registry.register(NodeDefinition(
        type_name="word_captions", display_name="Phụ đề từng từ", category="Audio",
        description="Nhận dạng lời và canh thời gian từng từ (faster-whisper, CPU). Ra phụ đề SRT và danh sách từ có mốc thời gian cho chữ karaoke.",
        input_ports=[P(name="audio", port_type=PortType.AUDIO, description="Giọng đọc / âm thanh")],
        output_ports=[P(name="captions", port_type=PortType.CAPTIONS, description="Phụ đề SRT"),
                      P(name="words", port_type=PortType.TEXT, description="JSON từng từ: word, start, end")],
        default_params=dict(NODE_DEFAULTS["word_captions"]), mockable=False))

    registry.register(NodeDefinition(
        type_name="scene_cut", display_name="Cắt cảnh video", category="Structure",
        description="Phát hiện điểm đổi cảnh trong video (PySceneDetect). Tuỳ chọn xuất clip từng cảnh để cắt Shorts từ tập dài.",
        input_ports=[P(name="video", port_type=PortType.VIDEO, description="Video cần tách cảnh")],
        output_ports=[P(name="scenes", port_type=PortType.SCENES, description="Danh sách cảnh: mốc bắt đầu, kết thúc, độ dài"),
                      P(name="report", port_type=PortType.TEXT, description="Tóm tắt số cảnh")],
        default_params=dict(NODE_DEFAULTS["scene_cut"]), mockable=False))

    registry.register(NodeDefinition(
        type_name="depth_layers", display_name="Tách lớp chiều sâu", category="Structure",
        description="Tách ảnh thành nền / trung cảnh / tiền cảnh (Depth Anything V2 Small, CPU) cho hiệu ứng parallax.",
        input_ports=[P(name="image", port_type=PortType.IMAGE, description="Ảnh cần tách lớp", required=False)],
        output_ports=[P(name="bg", port_type=PortType.IMAGE, description="Lớp nền (không lỗ hổng)"),
                      P(name="mid", port_type=PortType.IMAGE, description="Lớp trung + tiền cảnh (RGBA)"),
                      P(name="fg", port_type=PortType.IMAGE, description="Lớp tiền cảnh (RGBA)"),
                      P(name="depth", port_type=PortType.IMAGE, description="Bản đồ độ sâu (sáng = gần)")],
        default_params=dict(NODE_DEFAULTS["depth_layers"]), mockable=False))

    registry.register(NodeDefinition(
        type_name="handdraw", display_name="Vẽ tay bảng trắng", category="Generation",
        description="Biến ảnh phác thảo nét đen nền trắng thành video vẽ dần từng nét kèm bàn tay cầm bút (9:16, cần ffmpeg).",
        input_ports=[P(name="image", port_type=PortType.IMAGE, description="Ảnh nét đen trên nền trắng")],
        output_ports=[P(name="video", port_type=PortType.VIDEO, description="Video vẽ tay (MP4)")],
        default_params=dict(NODE_DEFAULTS["handdraw"]), mockable=False))

    registry.register(NodeDefinition(
        type_name="voice_clone", display_name="Clone giọng", category="Audio",
        description="Nhân bản giọng từ mẫu 3.5–6s vào kho giọng (OmniVoice). Bắt buộc ghi rõ mẫu của ai và đã được đồng ý. Không ghi đè giọng có sẵn; mock chỉ kiểm điều kiện.",
        input_ports=[P(name="audio", port_type=PortType.AUDIO, description="Mẫu giọng sạch, một người nói")],
        output_ports=[P(name="voice_id", port_type=PortType.TEXT, description="Mã giọng trong kho"),
                      P(name="preview", port_type=PortType.AUDIO, description="Câu đọc thử bằng giọng mới", required=False),
                      P(name="report", port_type=PortType.TEXT, description="Kết quả")],
        default_params=dict(NODE_DEFAULTS["voice_clone"]), mockable=False))
