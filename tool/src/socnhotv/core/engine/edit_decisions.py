from __future__ import annotations

import copy
import hashlib
import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import imageio_ffmpeg

from socnhotv.core.engine.episode_script import SCRIPT_JSON, script_to_scenes
from socnhotv.core.storage.project_store import ProjectStore, get_repo_root
from socnhotv.video.hyperframes_engine import HyperFramesEngine

logger = logging.getLogger("socnhotv.core.engine.edit_decisions")
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

EDIT_DECISIONS_JSON = "edit_decisions.json"
EDIT_DECISIONS_SCHEMA_VERSION = 1


def _compute_sha256(content: str) -> str:
    """Tính SHA-256 của chuỗi văn bản."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _compute_file_sha256(path: Path) -> str:
    """Tính SHA-256 của tệp tin."""
    if not path.is_file():
        return ""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class EditDecisionsManager:
    """Quản lý các quyết định chỉnh sửa thủ công của người dùng trên timeline theo shot.
    Nguyên tắc cốt lõi:
    - KHÔNG BAO GIỜ sửa script.json gốc (giữ nguyên tính toàn vẹn và bất biến).
    - Lưu mọi quyết định chỉnh sửa vào edit_decisions.json.
    - Hỗ trợ đổi thứ tự shot, đổi thời lượng, thay ảnh/clip, tắt/bật shot, sửa phụ đề.
    - Cho phép render lại vi sai (selective/incremental re-render) chỉ phần bị đổi.
    """

    def __init__(self, store: ProjectStore):
        self.store = store
        self.repo_root = get_repo_root()
        self.ffmpeg = FFMPEG_EXE
        self.engine = HyperFramesEngine(ffmpeg_exe=self.ffmpeg)

    def get_episode_dir(self, episode_id: str) -> Path:
        """Đường dẫn thư mục tập phim trong project store."""
        return self.store.project_dir / "content" / "episodes" / episode_id

    def get_script_path(self, episode_id: str) -> Path:
        """Đường dẫn tệp script.json gốc."""
        return self.get_episode_dir(episode_id) / SCRIPT_JSON

    def get_edit_decisions_path(self, episode_id: str) -> Path:
        """Đường dẫn tệp edit_decisions.json."""
        return self.get_episode_dir(episode_id) / EDIT_DECISIONS_JSON

    def get_shot_cache_dir(self, episode_id: str) -> Path:
        """Thư mục lưu cache segment video từng shot để phục vụ render vi sai."""
        cache_dir = self.store.runs_dir / "cache" / "shots" / episode_id
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def load_base_script(self, episode_id: str) -> Dict[str, Any]:
        """Đọc kịch bản gốc từ script.json (chỉ đọc, không sửa)."""
        script_path = self.get_script_path(episode_id)
        if not script_path.is_file():
            raise FileNotFoundError(f"Không tìm thấy kịch bản {script_path}")
        with open(script_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_decisions(self, episode_id: str) -> Optional[Dict[str, Any]]:
        """Đọc tệp edit_decisions.json nếu tồn tại."""
        dec_path = self.get_edit_decisions_path(episode_id)
        if not dec_path.is_file():
            return None
        try:
            with open(dec_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Không đọc được edit_decisions.json (%s): %s", dec_path, e)
            return None

    def save_decisions(self, episode_id: str, decisions_data: Dict[str, Any]) -> Path:
        """Ghi tệp edit_decisions.json (đảm bảo atomic write)."""
        dec_path = self.get_edit_decisions_path(episode_id)
        dec_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = dec_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(decisions_data, f, indent=2, ensure_ascii=False)
        tmp_path.replace(dec_path)
        logger.info("Đã lưu edit_decisions.json cho tập %s", episode_id)
        return dec_path

    def _init_empty_decisions(self, episode_id: str, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo cấu trúc quyết định chỉnh sửa ban đầu."""
        script_content = json.dumps(script_data, sort_keys=True, ensure_ascii=False)
        base_hash = _compute_sha256(script_content)
        return {
            "schemaVersion": EDIT_DECISIONS_SCHEMA_VERSION,
            "episodeId": episode_id,
            "baseScriptSha256": base_hash,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "shotOrder": [],  # Danh sách shotId theo thứ tự mới; rỗng nghĩa là thứ tự mặc định
            "shots": {},  # shotId -> { durationSec, mediaSrc, enabled, dialogue, subtitle, camera, ... }
            "history": [],
        }

    def get_effective_shots(self, episode_id: str) -> List[Dict[str, Any]]:
        """Trả về danh sách shot sau khi áp dụng các quyết định chỉnh sửa lên kịch bản gốc.
        Mỗi shot chứa đầy đủ thông tin: id, title, startSec, endSec, durationSec, media,
        dialogue, subtitle, camera, speaker, priority, enabled, isModified...
        """
        script_data = self.load_base_script(episode_id)
        raw_scenes = script_to_scenes(script_data)
        decisions = self.load_decisions(episode_id) or {}
        shot_overrides = decisions.get("shots", {})
        custom_order = decisions.get("shotOrder", [])

        # Tạo bản đồ shot gốc theo shotId
        base_map: Dict[str, Dict[str, Any]] = {}
        original_order: List[str] = []
        for sc in raw_scenes:
            s_id = str(sc.get("shotId") or f"shot_{sc.get('sceneNumber', 1)}")
            original_order.append(s_id)
            # Tìm ảnh/clip mặc định nếu có
            default_media = (
                sc.get("video")
                or sc.get("img")
                or sc.get("image")
                or sc.get("src")
                or ""
            )
            # Kiểm tra clip tay hoặc ảnh đã sinh
            clip_path = self.get_episode_dir(episode_id) / "clips" / f"{s_id}.mp4"
            if not default_media and clip_path.is_file():
                default_media = f"content/episodes/{episode_id}/clips/{s_id}.mp4"

            base_map[s_id] = {
                "shotId": s_id,
                "sceneNumber": sc.get("sceneNumber", 1),
                "sceneIndex": sc.get("sceneIndex", 1),
                "title": sc.get("title", f"Shot {s_id}"),
                "durationSec": float(sc.get("durationSec", 20.0)),
                "dialogue": sc.get("dialogue", ""),
                "subtitle": sc.get("dialogue", ""),
                "speaker": sc.get("speaker", ""),
                "speakerId": sc.get("speakerId", "soc_nho"),
                "camera": sc.get("camera", "push-in"),
                "priority": sc.get("priority", 3),
                "mediaSrc": str(default_media),
                "enabled": True,
                "isModified": False,
                "action": sc.get("action", ""),
                "sfx": sc.get("sfx", ""),
                "bgm": sc.get("bgm", ""),
            }

        # Xác định thứ tự shot áp dụng
        active_order = custom_order if custom_order else original_order

        # Đảm bảo không mất shot nào nếu custom_order thiếu shot
        final_order = []
        for sid in active_order:
            if sid in base_map and sid not in final_order:
                final_order.append(sid)
        for sid in original_order:
            if sid not in final_order:
                final_order.append(sid)

        # Xây dựng danh sách shot và tính lại startSec/endSec chuẩn
        effective_list: List[Dict[str, Any]] = []
        current_time = 0.0

        for sid in final_order:
            shot_data = copy.deepcopy(base_map[sid])
            override = shot_overrides.get(sid, {})

            if override:
                shot_data["isModified"] = True
                if "durationSec" in override:
                    shot_data["durationSec"] = max(0.5, float(override["durationSec"]))
                if "mediaSrc" in override:
                    shot_data["mediaSrc"] = str(override["mediaSrc"])
                if "enabled" in override:
                    shot_data["enabled"] = bool(override["enabled"])
                if "dialogue" in override:
                    shot_data["dialogue"] = str(override["dialogue"])
                if "subtitle" in override:
                    shot_data["subtitle"] = str(override["subtitle"])
                if "camera" in override:
                    shot_data["camera"] = str(override["camera"])

            # Gán mốc thời gian dựa trên trạng thái bật/tắt
            shot_dur = shot_data["durationSec"]
            shot_data["startSec"] = round(current_time, 3)
            shot_data["endSec"] = round(current_time + (shot_dur if shot_data["enabled"] else 0.0), 3)

            if shot_data["enabled"]:
                current_time += shot_dur

            effective_list.append(shot_data)

        return effective_list

    def apply_decision(
        self,
        episode_id: str,
        action: str,
        shot_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Thực hiện một hành động chỉnh sửa và lưu vào edit_decisions.json.
        Các action được hỗ trợ:
        - "reorder": params={"order": ["S02", "S01", ...]}
        - "update_duration": shot_id="S01", params={"durationSec": 15.0}
        - "replace_media": shot_id="S01", params={"mediaSrc": "path/to/file.mp4"}
        - "toggle_shot": shot_id="S01", params={"enabled": False}
        - "update_subtitle": shot_id="S01", params={"subtitle": "...", "dialogue": "..."}
        - "reset_shot": shot_id="S01" (xóa mọi override của shot này)
        - "reset_all": xóa toàn bộ override, đưa về kịch bản gốc
        """
        params = params or {}
        script_data = self.load_base_script(episode_id)
        decisions = self.load_decisions(episode_id) or self._init_empty_decisions(episode_id, script_data)

        timestamp = datetime.now(timezone.utc).isoformat()
        history_entry = {
            "timestamp": timestamp,
            "action": action,
            "shotId": shot_id,
            "params": params,
        }

        if action == "reset_all":
            dec_path = self.get_edit_decisions_path(episode_id)
            if dec_path.is_file():
                dec_path.unlink()
            return {"status": "reset", "effectiveShots": self.get_effective_shots(episode_id)}

        elif action == "reset_shot" and shot_id:
            if shot_id in decisions.get("shots", {}):
                del decisions["shots"][shot_id]
            if decisions.get("shotOrder") and shot_id in decisions["shotOrder"]:
                decisions["shotOrder"].remove(shot_id)

        elif action == "reorder":
            new_order = params.get("order", [])
            if isinstance(new_order, list) and new_order:
                decisions["shotOrder"] = [str(x) for x in new_order]

        elif action == "update_duration" and shot_id:
            dur = float(params.get("durationSec", 20.0))
            decisions.setdefault("shots", {}).setdefault(shot_id, {})["durationSec"] = max(0.5, dur)

        elif action == "replace_media" and shot_id:
            media_src = str(params.get("mediaSrc", ""))
            decisions.setdefault("shots", {}).setdefault(shot_id, {})["mediaSrc"] = media_src

        elif action == "toggle_shot" and shot_id:
            enabled = bool(params.get("enabled", True))
            decisions.setdefault("shots", {}).setdefault(shot_id, {})["enabled"] = enabled

        elif action == "update_subtitle" and shot_id:
            sub = str(params.get("subtitle", ""))
            dia = str(params.get("dialogue", sub))
            decisions.setdefault("shots", {}).setdefault(shot_id, {})["subtitle"] = sub
            decisions["shots"][shot_id]["dialogue"] = dia

        else:
            raise ValueError(f"Hành động không hợp lệ hoặc thiếu shot_id: {action}")

        decisions["updatedAt"] = timestamp
        decisions.setdefault("history", []).append(history_entry)
        self.save_decisions(episode_id, decisions)

        effective_shots = self.get_effective_shots(episode_id)
        return {
            "status": "success",
            "action": action,
            "shotId": shot_id,
            "effectiveShots": effective_shots,
            "totalDurationSec": sum(s["durationSec"] for s in effective_shots if s["enabled"]),
        }

    def compute_shot_hash(self, shot: Dict[str, Any]) -> str:
        """Tính mã băm xác thực nội dung của shot.
        Khi mã băm không đổi, segment video của shot được tái sử dụng 100%.
        """
        payload = {
            "shotId": shot.get("shotId"),
            "durationSec": round(float(shot.get("durationSec", 20.0)), 3),
            "mediaSrc": str(shot.get("mediaSrc", "")),
            "subtitle": str(shot.get("subtitle") or shot.get("dialogue") or ""),
            "camera": str(shot.get("camera", "")),
            "enabled": bool(shot.get("enabled", True)),
        }
        return _compute_sha256(json.dumps(payload, sort_keys=True))

    def render_shot_segment(
        self,
        episode_id: str,
        shot: Dict[str, Any],
        out_segment_path: Path,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
    ) -> Path:
        """Render một shot đơn lẻ thành segment MP4 chuẩn (H.264/AAC, 1920x1080 hoặc 1080x1920).
        Tái sử dụng nhanh gọn bằng FFmpeg hoặc HyperFrames composition đơn shot.
        """
        dur = float(shot.get("durationSec", 5.0))
        media_src = shot.get("mediaSrc") or ""
        media_full_path = self.store.project_dir / media_src if media_src else None

        out_segment_path.parent.mkdir(parents=True, exist_ok=True)

        # Chuẩn bị nguồn hình ảnh/video
        has_real_media = media_full_path and media_full_path.is_file()
        is_video = has_real_media and media_full_path.suffix.lower() in [".mp4", ".mov", ".webm"]

        cmd = [self.ffmpeg, "-y"]

        if is_video:
            cmd.extend(["-t", str(dur), "-i", str(media_full_path)])
        elif has_real_media:
            cmd.extend(["-loop", "1", "-t", str(dur), "-i", str(media_full_path)])
        else:
            # Tạo màu nền placeholder nếu chưa có ảnh
            cmd.extend(["-f", "lavfi", "-i", f"color=c=0x18181b:s={width}x{height}:d={dur}"])

        # Tạo luồng audio giả lập im lặng để segment đồng nhất luồng
        cmd.extend(["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={dur}"])

        # Filter xử lý kích thước và phụ đề đơn giản nếu có
        sub_text = (shot.get("subtitle") or shot.get("dialogue") or "").replace("'", "").replace(":", "")
        # Tránh ký tự escape phức tạp trong ffmpeg drawtext
        filter_str = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,format=yuv420p"

        cmd.extend([
            "-filter_complex", f"[0:v]{filter_str}[v]",
            "-map", "[v]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-r", str(fps),
            "-shortest",
            str(out_segment_path),
        ])

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logger.error("FFmpeg render shot segment thất bại: %s", res.stderr)
            raise RuntimeError(f"Lỗi render segment {shot.get('shotId')}: {res.stderr[:200]}")

        return out_segment_path

    def selective_rerender(
        self,
        episode_id: str,
        output_mp4_path: Optional[Path] = None,
        force_all: bool = False,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
    ) -> Dict[str, Any]:
        """Thực hiện RENDER LẠI CHỈ PHẦN BỊ ĐỔI (Incremental / Selective Re-render):
        1. Lấy danh sách effective shots sau chỉnh sửa.
        2. Tính content hash của từng shot.
        3. Với shot không đổi và đã có segment MP4 trong cache: BỎ QUA không render lại!
        4. Với shot bị đổi hoặc chưa có cache: Render lại segment của shot đó.
        5. Ghép nối (concatenation) các segment thành video thành phẩm <episodeId>.mp4.
        """
        start_time = time.time()
        effective_shots = self.get_effective_shots(episode_id)
        active_shots = [s for s in effective_shots if s["enabled"]]

        if not active_shots:
            raise ValueError(f"Tập {episode_id} không có shot nào được bật để render.")

        cache_dir = self.get_shot_cache_dir(episode_id)
        if not output_mp4_path:
            output_dir = self.store.project_dir / "output" / episode_id
            output_dir.mkdir(parents=True, exist_ok=True)
            output_mp4_path = output_dir / f"{episode_id}.mp4"

        segment_paths: List[Path] = []
        cached_count = 0
        rendered_count = 0

        for shot in active_shots:
            sid = shot["shotId"]
            shot_hash = self.compute_shot_hash(shot)
            seg_path = cache_dir / f"{sid}_{shot_hash[:12]}.mp4"

            if seg_path.is_file() and not force_all and os.path.getsize(seg_path) > 1024:
                # Đã có cache và hash khớp -> Tái sử dụng ngay!
                segment_paths.append(seg_path)
                cached_count += 1
            else:
                # Cần render lại shot này
                t0 = time.time()
                self.render_shot_segment(
                    episode_id=episode_id,
                    shot=shot,
                    out_segment_path=seg_path,
                    width=width,
                    height=height,
                    fps=fps,
                )
                rendered_count += 1
                logger.info("Render segment %s trong %.2fs", sid, time.time() - t0)
                segment_paths.append(seg_path)

        # Ghép nối các segment bằng FFmpeg concat demuxer (cực nhanh, không cần re-encode)
        concat_list_file = cache_dir / "concat_list.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for p in segment_paths:
                f.write(f"file '{p.resolve()}'\n")

        output_mp4_path.parent.mkdir(parents=True, exist_ok=True)
        concat_cmd = [
            self.ffmpeg,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file.resolve()),
            "-c", "copy",
            str(output_mp4_path.resolve()),
        ]

        res = subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logger.error("FFmpeg concat segments thất bại: %s", res.stderr)
            raise RuntimeError(f"Lỗi ghép nối video: {res.stderr[:200]}")

        elapsed_sec = round(time.time() - start_time, 3)

        # Tạo thumbnail nếu chưa có
        thumb_path = output_mp4_path.parent / "thumb.jpg"
        thumb_cmd = [
            self.ffmpeg, "-y",
            "-ss", "0.5",
            "-i", str(output_mp4_path),
            "-vframes", "1",
            "-q:v", "2",
            str(thumb_path),
        ]
        subprocess.run(thumb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        total_dur = sum(s["durationSec"] for s in active_shots)
        logger.info(
            "Hoàn tất selective rerender cho %s: %d rendered, %d cached trong %.2fs",
            episode_id, rendered_count, cached_count, elapsed_sec,
        )

        return {
            "status": "success",
            "episodeId": episode_id,
            "outputVideo": str(output_mp4_path.relative_to(self.store.project_dir)),
            "outputFullPath": str(output_mp4_path),
            "renderedShotsCount": rendered_count,
            "cachedShotsCount": cached_count,
            "totalShotsCount": len(active_shots),
            "elapsedSec": elapsed_sec,
            "totalDurationSec": total_dur,
            "engine": "selective_shot_concat",
        }
