"""
GOBI SOCIAL — RÁP CÁC CLIP GOOGLE FLOW THÀNH VIDEO HOÀN CHỈNH QUA HYPERFRAMES
==============================================================================
Dùng SAU KHI Claude đã tạo xong từng clip ngắn (~8s) bằng EGO Lite/Google Flow
và tải về máy. Script này: sinh giọng Gô Bi cho từng cảnh (Voice Vault), nối
các clip video thật theo đúng thứ tự (KHÔNG Ken-Burns ảnh tĩnh, KHÔNG overlay
chữ/tag nào — chỉ hình ảnh + giọng thuần theo đúng yêu cầu), ép đồng nhất
khuôn mặt Gô Bi (face-swap cục bộ từ chính ảnh gốc `lyly_master_portrait.png`
của cô ấy — KHÔNG phải ghép lên người mẫu thật — để sửa hiện tượng Flow tự
"trôi" mặt nhẹ giữa các lần generate), xoá watermark AI góc dưới-phải của
Google Flow/Veo, ghi `_flow_manifest.json` (job_id, prompt, nguồn clip từng
cảnh) để không lẫn giữa các job, rồi lưu vào đúng job folder + cập nhật
product.json để Dashboard tự hiện qua SSE.

Dùng thủ công (không wire vào Dashboard/API) — Claude tự chạy mỗi khi xử lý
xong 1 Brief từ Dashboard.

Cách dùng: sửa SCENES + JOB_DIR + PRODUCT_NAME bên dưới rồi chạy:
    .venv/bin/python scripts/flow_ai/assemble_flow_scenes.py
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path("/Volumes/Data/gobi-social")
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from gobi.services.media.hyperframes_engine import HyperFramesEngine  # noqa: E402
from gobi.services.voice.voice_cloner import VoiceCloner  # noqa: E402


def generate_lookbook_html(
    scenes: List[Dict[str, Any]], duration: float, product_name: str, voiceover_relpath: str
) -> str:
    """
    HTML nhiều cảnh VIDEO thật nối tiếp nhau — KHÔNG overlay chữ/tag nào cả
    (bỏ theo yêu cầu: không cần ghim text cố định, chỉ giữ hình ảnh + giọng,
    đúng như video TikTok tham khảo không có overlay). `product_name` chỉ còn
    dùng để đặt tên hiển thị, không render ra khung hình.
    Các <video> cảnh luôn `muted`, giọng Gô Bi đến từ <audio id="voiceover-audio">
    riêng — đúng pattern track-index đã dùng ở generate_html_composition(), để
    adapter render mux đúng audio vào video cuối.
    """
    video_blocks = []
    current_time = 0.0
    for idx, sc in enumerate(scenes):
        video_blocks.append(f"""
    <video id="vid-{idx}" class="clip scene-video"
           src="{sc['video_relpath']}"
           playsinline muted
           data-start="{current_time:.3f}"
           data-duration="{sc['duration']:.3f}"
           data-track-index="1"></video>""")
        current_time += sc["duration"]

    return f"""<!doctype html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Gobi Social - Flow Lookbook</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
      #root {{ width: 100%; height: 100%; position: relative; overflow: hidden; }}
      .scene-video {{
        position: absolute; top: 0; left: 0;
        width: 1080px; height: 1920px; object-fit: cover;
      }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{duration:.3f}" data-width="1080" data-height="1920">
      {"".join(video_blocks)}
      <audio id="voiceover-audio"
             src="{voiceover_relpath}"
             data-start="0"
             data-duration="{duration:.3f}"
             data-volume="1.0"
             data-track-index="4"></audio>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>"""


def concat_audio(audio_paths: List[Path], output_path: Path) -> Path:
    concat_list = output_path.parent / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in audio_paths:
            f.write(f"file '{p.resolve()}'\n")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list), "-c:a", "libmp3lame", "-q:a", "2", str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return output_path


def _enforce_gobi_identity(src: Path, dest: Path, avatar_path: Path) -> None:
    """
    Ép đồng nhất khuôn mặt Gô Bi: face-swap TỪ CHÍNH ảnh gốc `avatar_path`
    (lyly_master_portrait.png) LÊN clip Flow đã tạo (đã là "Gô Bi" nhưng mặt
    có thể trôi nhẹ giữa các lần generate). KHÔNG áp dụng cho ảnh/clip của
    người mẫu thật — khác hẳn lần thử ghép mặt lên người thật đã bị từ chối.
    """
    import cv2
    import insightface
    from insightface.app import FaceAnalysis

    FACESWAP_PROVIDERS = ["CoreMLExecutionProvider", "CPUExecutionProvider"]
    swapper_model_path = str(PROJECT_ROOT / "models" / "weights" / "inswapper_128.onnx")

    app = FaceAnalysis(name="buffalo_l", providers=FACESWAP_PROVIDERS)
    app.prepare(ctx_id=0, det_size=(320, 320))
    swapper = insightface.model_zoo.get_model(swapper_model_path, providers=FACESWAP_PROVIDERS)

    avatar_img = cv2.imread(str(avatar_path))
    avatar_faces = app.get(avatar_img)
    if not avatar_faces:
        raise ValueError(f"Không tìm thấy khuôn mặt trong avatar: {avatar_path}")
    source_face = avatar_faces[0]

    cap = cv2.VideoCapture(str(src))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    temp_video = dest.parent / f"_{dest.stem}_idlock_raw.mp4"
    writer = cv2.VideoWriter(str(temp_video), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        faces = app.get(frame)
        if faces:
            primary = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            frame = swapper.get(frame, primary, source_face, paste_back=True)
        writer.write(frame)
    cap.release()
    writer.release()

    cmd = ["ffmpeg", "-y", "-i", str(temp_video), "-c:v", "libx264", "-preset", "fast", "-crf", "18", str(dest)]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    temp_video.unlink(missing_ok=True)


def _dewatermark_and_trim(
    src: Path, dest: Path, start_frac: float, end_frac: float, width: int = 1080, height: int = 1920
) -> None:
    """
    Cắt bỏ watermark AI (góc dưới-phải, icon sparkle ✦ của Google Flow/Veo) bằng
    cách crop 82% khung hình từ góc trên-trái rồi scale lại full-frame (zoom nhẹ,
    không lộ dấu vết). Đồng thời trim theo [start_frac, end_frac] của clip gốc để
    tạo 2 sub-cut nhanh/cảnh thay vì phát nguyên 8s — khớp nhịp cắt nhanh (~2s/cảnh)
    của video tham khảo thay vì nhịp chậm (8s/cảnh) trước đây. Bỏ audio gốc của
    clip (-an) vì giọng Gô Bi đến từ track voiceover riêng.
    """
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(src)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True,
    )
    clip_duration = float(probe.stdout.strip())
    start = clip_duration * start_frac
    seg_duration = clip_duration * (end_frac - start_frac)
    cmd = [
        "ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", str(src), "-t", f"{seg_duration:.3f}",
        "-vf", f"crop=iw*0.82:ih*0.82:0:0,scale={width}:{height}",
        "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18", str(dest),
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def assemble(
    job_dir: Path,
    scenes: List[Dict[str, str]],
    product_name: str,
    voice_profile_id: str = "voice-fm-lyly",
    character: str = "gobi_lyly",
    job_id: str | None = None,
    character_avatar_path: Path | None = None,
    enforce_identity: bool = True,
) -> Path:
    """
    scenes: [{"clip_path": "/abs/path/clip0.mp4", "voiceover_text": "..."}, ...] theo đúng thứ tự.
    job_id: dùng để ghi vào _flow_manifest.json (mặc định tự tách từ tên job_dir,
        vd "7694350317697142037_ao_len..." -> "7694350317697142037") — tránh lẫn
        clip giữa các job khi cùng nằm trong ~/Downloads.
    enforce_identity: True (mặc định) -> chạy face-swap cục bộ TỪ CHÍNH ảnh gốc
        character_avatar_path (lyly_master_portrait.png) LÊN clip Flow đã tạo,
        ép đồng nhất khuôn mặt Gô Bi giữa các clip (sửa hiện tượng Flow tự "trôi"
        mặt nhẹ mỗi lần generate). KHÔNG liên quan đến face-swap lên người mẫu
        thật (đã bị từ chối ở job trước).
    """
    job_dir = Path(job_dir)
    job_id = job_id or job_dir.name.split("_")[0]
    character_avatar_path = character_avatar_path or (PROJECT_ROOT / "assets" / "characters" / "lyly_master_portrait.png")
    work_dir = job_dir / "_flow_assembly"
    work_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = work_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    hf_engine = HyperFramesEngine(PROJECT_ROOT)
    cloner = VoiceCloner()

    print(f"[*] Sinh giọng {voice_profile_id} cho {len(scenes)} cảnh...")
    audio_paths: List[Path] = []
    scene_durations: List[float] = []
    scenes_for_html: List[Dict[str, Any]] = []
    manifest_scenes: List[Dict[str, Any]] = []

    for idx, sc in enumerate(scenes):
        audio_out = work_dir / f"voice_{idx:02d}.mp3"
        cloner.speak(
            profile_id=voice_profile_id,
            new_script=sc["voiceover_text"],
            output_path=str(audio_out),
            engine="omnivoice",
        )
        audio_paths.append(audio_out)
        duration = hf_engine.get_audio_duration(audio_out)
        scene_durations.append(duration)
        print(f"    - cảnh {idx}: {duration:.1f}s — \"{sc['voiceover_text'][:50]}...\"")

        # Tách clip 8s gốc thành 2 sub-cut (45%/55% thời lượng cảnh) để tăng nhịp
        # cắt (giống nhịp quay/dựng tự nhiên của video tham khảo), đồng thời xoá
        # watermark AI góc dưới-phải qua _dewatermark_and_trim().
        src_clip = Path(sc["clip_path"])

        if enforce_identity:
            print(f"    - cảnh {idx}: ép đồng nhất khuôn mặt Gô Bi...")
            idlocked_clip = assets_dir / f"clip{idx:02d}_idlocked.mp4"
            _enforce_gobi_identity(src_clip, idlocked_clip, character_avatar_path)
            src_clip = idlocked_clip

        cut_a = assets_dir / f"clip{idx:02d}a.mp4"
        cut_b = assets_dir / f"clip{idx:02d}b.mp4"
        _dewatermark_and_trim(src_clip, cut_a, 0.05, 0.45)
        _dewatermark_and_trim(src_clip, cut_b, 0.55, 0.95)

        dur_a = duration * 0.45
        dur_b = duration - dur_a
        scenes_for_html.append({"video_relpath": f"assets/{cut_a.name}", "duration": dur_a})
        scenes_for_html.append({"video_relpath": f"assets/{cut_b.name}", "duration": dur_b})
        manifest_scenes.append({
            "scene_index": idx,
            "voiceover_text": sc["voiceover_text"],
            "original_clip_source": str(Path(sc["clip_path"])),
            "identity_locked": enforce_identity,
            "duration_seconds": round(duration, 2),
        })

    total_duration = sum(scene_durations)
    final_audio = assets_dir / "voiceover_full.mp3"
    concat_audio(audio_paths, final_audio)
    print(f"[✓] Giọng xong, tổng {total_duration:.1f}s, {len(scenes_for_html)} sub-cut (nhịp cắt nhanh)")

    html_content = generate_lookbook_html(
        scenes_for_html, total_duration, product_name, f"assets/{final_audio.name}"
    )
    (work_dir / "index.html").write_text(html_content, encoding="utf-8")
    hf_config = {
        "id": work_dir.name, "fps": 30, "width": 1080, "height": 1920,
        "duration": total_duration, "entry": "index.html"
    }
    (work_dir / "hyperframes.json").write_text(json.dumps(hf_config, indent=2), encoding="utf-8")
    print(f"[✓] Composition HyperFrames đã tạo tại {work_dir}")

    final_video_path = job_dir / "generated_video.mp4"
    print("[*] Đang render video cuối cùng...")
    render_res = hf_engine.render_project(project_dir=work_dir, output_file=final_video_path)
    print(f"[✓] Render xong: {render_res}")

    product_json_path = job_dir / "product.json"
    if product_json_path.exists():
        prod_data = json.loads(product_json_path.read_text(encoding="utf-8"))
    else:
        prod_data = {}
    prod_data["status"] = "DA_LAM_VIDEO"
    prod_data["video_type"] = "talking_head"
    prod_data["generated_video_at"] = datetime.now().isoformat()
    prod_data["generated_via"] = "google_flow_ego_lite"
    product_json_path.write_text(json.dumps(prod_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[✓] Đã cập nhật {product_json_path} (status=DA_LAM_VIDEO)")

    manifest_path = job_dir / "_flow_manifest.json"
    manifest = {
        "job_id": job_id,
        "product_name": product_name,
        "character": character,
        "voice_profile_id": voice_profile_id,
        "generated_at": datetime.now().isoformat(),
        "output_video": str(final_video_path),
        "scenes": manifest_scenes,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[✓] Đã ghi {manifest_path} (job_id={job_id}) — tra cứu clip nào thuộc job nào")

    return final_video_path


if __name__ == "__main__":
    # === SỬA CÁC GIÁ TRỊ NÀY CHO ĐÚNG JOB ĐANG XỬ LÝ ===
    JOB_DIR = PROJECT_ROOT / "data/products/1737777058633123730_navie_quan_short_kaki_orina_cap_thap_vien_ren"
    PRODUCT_NAME = "NAVIE - Quần short kaki ORINA"
    VOICE_PROFILE = "voice-fm-lyly"

    SCENES = [
        # {"clip_path": "/abs/path/to/downloaded/clip_hook.mp4", "voiceover_text": "..."},
    ]

    if not SCENES:
        print("[!] Chưa điền SCENES — sửa file này trước khi chạy, hoặc import assemble() để gọi trực tiếp.")
        sys.exit(1)

    assemble(JOB_DIR, SCENES, PRODUCT_NAME, VOICE_PROFILE)
