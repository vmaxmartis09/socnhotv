"""Chạy THẬT một template v2: slot + giọng + ảnh -> bundle HyperFrames -> MP4 + báo cáo trung thực (I4).

Tại sao có tệp này: node `template_render` của Studio đã đăng ký nhưng bộ chạy graph chưa có nhánh thực thi
(rơi vào nhánh chung "Generic execution" -> ảnh mock). Các MP4 `preview.mp4` cũ được dựng bằng script
Windows từ dữ liệu mẫu, không đi qua Studio. Module này là đường chạy thật duy nhất, dùng được từ:
- node `template_render` (khi chủ sở hữu graph_runner nối vào — xem status/I4.md, mục "Yêu cầu"),
- CLI `data/shared/templates/_engine/run_template.py`,
- test `tests/test_i4_template_runner.py`.

Không gọi nguồn trả phí. Giọng do bên gọi truyền vào (`voice_audio`); không có giọng -> video im lặng và
báo cáo ghi rõ `audio.present = False`.
"""
from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from socnhotv.video.fallback_ffmpeg import get_audio_duration
from socnhotv.video.hyperframes_engine import HyperFramesEngine
from socnhotv.video.platforms import get_platform
from socnhotv.video.templates.compose import compose_template
from socnhotv.video.templates.loader import get_template, get_template_dir

logger = logging.getLogger("socnhotv.video.templates.runner")


@dataclass
class TemplateRunReport:
    template_id: str
    platform: str
    ok: bool = False
    mp4: Optional[str] = None
    contact_sheet: Optional[str] = None
    engine: str = "none"  # "hyperframes" | "ffmpeg_fallback" | "none"
    width: int = 0
    height: int = 0
    duration_sec: float = 0.0
    size_bytes: int = 0
    has_audio_stream: bool = False
    render_sec: float = 0.0
    slots_from_user: List[str] = field(default_factory=list)
    slots_from_sample: List[str] = field(default_factory=list)
    audio_source: str = "none"  # "voice_audio" | "template_sample_asset" | "none"
    assets_from_user: List[str] = field(default_factory=list)
    assets_from_template: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _ffprobe(path: Path) -> Dict[str, Any]:
    exe = shutil.which("ffprobe")
    if not exe:
        return {}
    r = subprocess.run(
        [exe, "-v", "error", "-show_entries", "format=duration,size", "-show_entries",
         "stream=codec_type,width,height", "-of", "json", str(path)],
        capture_output=True, text=True, timeout=60,
    )
    try:
        return json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        return {}


def _contact_sheet(ffmpeg: str, mp4: Path, out_jpg: Path, duration: float, cols: int = 6) -> bool:
    fps = max(0.5, cols / max(duration, 0.5))
    r = subprocess.run(
        [ffmpeg, "-y", "-i", str(mp4), "-vf", f"fps={fps:.4f},scale=240:-1,tile={cols}x1",
         "-frames:v", "1", "-q:v", "3", str(out_jpg)],
        capture_output=True, text=True, timeout=120,
    )
    return r.returncode == 0 and out_jpg.exists()


def align_words(audio: Path, language: str = "vi", model_size: str = "small") -> List[Dict[str, Any]]:
    """Mốc từng từ của giọng thật bằng faster-whisper (cục bộ, miễn phí; cùng model với tool stt-align)."""
    from faster_whisper import WhisperModel

    import numpy as np

    # Tự giải mã bằng ffmpeg -> float32 16 kHz mono: tránh lỗi PyAV của faster-whisper trên môi trường này
    # ("open() got an unexpected keyword argument 'metadata_errors'").
    pcm = subprocess.run(
        [shutil.which("ffmpeg") or "ffmpeg", "-v", "error", "-i", str(audio), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
        capture_output=True, check=True, timeout=120,
    ).stdout
    samples = np.frombuffer(pcm, dtype=np.float32)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(samples, language=language, word_timestamps=True)
    words: List[Dict[str, Any]] = []
    for seg in segments:
        for w in seg.words or []:
            t = (w.word or "").strip()
            if t:
                words.append({"w": t, "start": round(float(w.start), 3), "end": round(float(w.end), 3)})
    return words


def text_on_timings(text: str, heard: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Đặt các từ của KỊCH BẢN (đúng chính tả) lên khoảng thời gian Whisper nghe được.

    Whisper nhỏ nghe sai nhiều từ trên giọng nhân bản (I4: "Baskin Roboy" cho "Bass Pro"), nên chỉ dùng mốc
    đầu/cuối của nó, chia đều theo độ dài chữ cho các từ đã biết. Không có mốc -> trả về rỗng (không bịa).
    """
    toks = text.split()
    if not toks or not heard:
        return []
    t0, t1 = heard[0]["start"], heard[-1]["end"]
    weights = [max(len(t), 2) for t in toks]
    total = float(sum(weights))
    out: List[Dict[str, Any]] = []
    cur = t0
    for tok, wgt in zip(toks, weights):
        dur = (t1 - t0) * wgt / total
        out.append({"w": tok, "start": round(cur, 3), "end": round(cur + dur, 3)})
        cur += dur
    return out


def chunk_words(words: List[Dict[str, Any]], per_chunk: int = 5) -> List[Dict[str, Any]]:
    """Gom từ thành các cụm phụ đề; cụm hiện đến lúc cụm sau bắt đầu (không chồng nhau)."""
    chunks: List[Dict[str, Any]] = []
    groups = [words[i:i + per_chunk] for i in range(0, len(words), per_chunk)]
    for i, grp in enumerate(groups):
        start = grp[0]["start"]
        end = groups[i + 1][0]["start"] if i + 1 < len(groups) else grp[-1]["end"] + 0.3
        chunks.append({"start": start, "end": round(end, 3), "words": grp})
    return chunks

def run_template(
    template_id: str,
    out_dir: Path,
    slots: Optional[Dict[str, Any]] = None,
    platform: Optional[str] = None,
    voice_audio: Optional[Path | str] = None,
    asset_files: Optional[Dict[str, Path | str]] = None,
    words: Optional[List[Dict[str, Any]]] = None,
    voice_text: Optional[str] = None,
    quality: str = "draft",
    timeout_sec: int = 600,
) -> TemplateRunReport:
    """Dựng MP4 thật từ template.

    Args:
        template_id: vd. 'shorts-fact-v1'.
        out_dir: thư mục đầu ra (bundle + MP4 + contact sheet). Bên gọi chọn, không ghi vào data/projects thật.
        slots: giá trị slot do người dùng/flow cung cấp. Slot thiếu sẽ lấy `sample.data.json` và được báo cáo.
        platform: id nền tảng (mặc định `template.default_platform`).
        voice_audio: tệp thoại thật. Có thì ghi đè `assets/voiceover.mp3` của template.
        voice_text: lời thoại gốc đã đọc; có thì phụ đề dùng đúng chữ này (không dùng chữ Whisper nghe).
        words: mốc từng từ [{w,start,end}] cho template có phụ đề karaoke; thiếu thì tự căn bằng Whisper từ voice_audio.
        asset_files: {tên tệp trong assets/: đường dẫn nguồn}, vd {"product.png": "/x/y.png"}.
        quality: draft | looks | delivery (draft = rẻ nhất, đủ để kiểm).
    """
    out_dir = Path(out_dir).resolve()
    tmpl = get_template(template_id)
    t_dir = get_template_dir(template_id)
    plat_id = platform or tmpl.default_platform or "tiktok"
    rep = TemplateRunReport(template_id=template_id, platform=plat_id)
    t0 = time.time()
    try:
        if tmpl.platforms and plat_id not in tmpl.platforms:
            rep.warnings.append(f"Nền tảng '{plat_id}' không nằm trong danh sách của template: {tmpl.platforms}")
        preset = get_platform(plat_id)
        rep.width, rep.height = preset.width, preset.height

        # --- slot: người dùng > mẫu, ghi lại slot nào lấy từ mẫu
        sample: Dict[str, Any] = {}
        sample_file = t_dir / "sample.data.json"
        if sample_file.exists():
            sample = json.loads(sample_file.read_text(encoding="utf-8"))
        user = {k: v for k, v in (slots or {}).items() if v is not None}  # "" = người dùng chủ động để trống, không lấy chữ mẫu
        data = {**sample, **user}
        rep.slots_from_user = sorted(user)
        rep.slots_from_sample = sorted(k for k in sample if k not in user)
        if rep.slots_from_sample:
            rep.warnings.append("Slot lấy từ sample.data.json (không phải dữ liệu người dùng): " + ", ".join(rep.slots_from_sample))

        # --- bundle
        bundle = out_dir / "bundle"
        if bundle.exists():
            shutil.rmtree(bundle)
        (bundle / "assets").mkdir(parents=True)
        src_assets = t_dir / "assets"
        if src_assets.is_dir():
            for f in src_assets.iterdir():
                if f.is_file():
                    shutil.copy2(f, bundle / "assets" / f.name)
                    rep.assets_from_template.append(f.name)
        for name, src in (asset_files or {}).items():
            src = Path(src)
            if not src.is_file():
                raise FileNotFoundError(f"Tệp asset '{name}' không tồn tại: {src}")
            shutil.copy2(src, bundle / "assets" / name)
            if name in rep.assets_from_template:
                rep.assets_from_template.remove(name)
            rep.assets_from_user.append(name)

        voice_path: Optional[Path] = None
        if voice_audio:
            voice_path = Path(voice_audio)
            if not voice_path.is_file():
                raise FileNotFoundError(f"voice_audio không tồn tại: {voice_path}")
            shutil.copy2(voice_path, bundle / "assets" / "voiceover.mp3")
            rep.audio_source = "voice_audio"
            if "voiceover.mp3" in rep.assets_from_template:
                rep.assets_from_template.remove("voiceover.mp3")
        elif (bundle / "assets" / "voiceover.mp3").exists():
            rep.audio_source = "template_sample_asset"
            rep.warnings.append("Không có voice_audio: dùng voiceover.mp3 mẫu đóng gói sẵn trong template (không phải lời của slot).")
        else:
            rep.warnings.append("Không có giọng: video im lặng.")

        # Template có phụ đề karaoke (dùng data.word_chunks): mốc từ phải khớp GIỌNG THẬT, không dùng mốc đóng gói sẵn.
        if "word_chunks" in (t_dir / "composition.html.j2").read_text(encoding="utf-8"):
            if words is None and voice_path is not None:
                heard = align_words(voice_path)
                if voice_text:
                    words = text_on_timings(voice_text, heard)
                    rep.warnings.append(
                        f"Phụ đề: chữ từ voice_text ({len(words)} từ), mốc đầu/cuối từ Whisper; thời điểm từng từ là ước lượng theo độ dài chữ."
                    )
                else:
                    words = heard
                    rep.warnings.append(f"Phụ đề: {len(words)} từ do Whisper nghe (có thể sai chính tả vì không có voice_text).")
            if words:
                data["word_chunks"] = chunk_words(words)
            else:
                data["word_chunks"] = []
                rep.warnings.append("Template có phụ đề nhưng không có giọng/mốc từ: KHÔNG có phụ đề.")

        sample_assets = [n for n in rep.assets_from_template if n not in ("gsap.min.js", "voiceover.mp3")]
        if sample_assets:
            rep.warnings.append("Asset mẫu đóng gói trong template (không phải của người dùng): " + ", ".join(sorted(sample_assets)))

        html = compose_template(
            template_id, data, platform=preset,
            voice_audio_path=(bundle / "assets" / "voiceover.mp3") if rep.audio_source != "none" else None,
            total_duration=None,
        )
        (bundle / "index.html").write_text(html, encoding="utf-8")

        # Kiểm trước: mọi `assets/...` composition tham chiếu phải có trong bundle. Thiếu -> báo rõ TÊN tệp thay vì
        # để HyperFrames chết giữa chừng ("VIDEO_SOURCE_UNRENDERABLE"). Ví dụ I4: whiteboard.mp4 (handdraw),
        # source.mp4 (video nguồn của người dùng), scene_bg.mp4 (cảnh nền) không có sẵn trong template.
        needed = sorted(set(re.findall(r'src="assets/([^"]+)"', html)))
        missing = [n for n in needed if not (bundle / "assets" / n).is_file()]
        if missing:
            raise FileNotFoundError(
                f"Template '{template_id}' cần tệp assets chưa được cung cấp: {', '.join(missing)} "
                f"(truyền qua asset_files={{tên: đường dẫn}}; template không đóng gói sẵn các tệp này)."
            )
        (bundle / "hyperframes.json").write_text(
            json.dumps({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
                        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}}),
            encoding="utf-8")

        engine = HyperFramesEngine()
        chk = engine.check(bundle)
        if isinstance(chk, dict) and chk.get("ok") is False:
            rep.warnings.append("hyperframes check: " + json.dumps(chk, ensure_ascii=False)[:400])

        out_dir.mkdir(parents=True, exist_ok=True)
        mp4 = out_dir / f"{template_id}_{plat_id}.mp4"
        tr = time.time()
        engine.render(bundle, mp4, platform=preset, quality=quality, timeout_sec=timeout_sec,
                      require_hyperframes=True, log_file=out_dir / "render.log")
        rep.render_sec = round(time.time() - tr, 2)
        rep.engine = engine.last_engine
        rep.mp4 = str(mp4)

        probe = _ffprobe(mp4)
        for s in probe.get("streams", []):
            if s.get("codec_type") == "video":
                rep.width, rep.height = int(s.get("width", 0)), int(s.get("height", 0))
            if s.get("codec_type") == "audio":
                rep.has_audio_stream = True
        rep.duration_sec = round(float(probe.get("format", {}).get("duration", 0) or 0), 2)
        rep.size_bytes = int(probe.get("format", {}).get("size", 0) or 0)
        sheet = out_dir / f"{template_id}_{plat_id}_contact.jpg"
        if _contact_sheet(engine.ffmpeg, mp4, sheet, rep.duration_sec):
            rep.contact_sheet = str(sheet)
        rep.ok = rep.size_bytes > 0 and rep.engine == "hyperframes"
    except Exception as e:  # noqa: BLE001 - báo cáo lỗi thật, không nuốt
        rep.error = f"{type(e).__name__}: {e}"
        logger.exception("run_template %s lỗi", template_id)
    finally:
        (out_dir).mkdir(parents=True, exist_ok=True)
        (out_dir / "report.json").write_text(json.dumps(rep.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        rep.render_sec = rep.render_sec or round(time.time() - t0, 2)
    return rep
