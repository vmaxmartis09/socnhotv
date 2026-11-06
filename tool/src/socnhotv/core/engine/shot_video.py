"""Shot Video Engine (G3 - Hợp đồng C4, C5).

Quản lý sinh clip video chuyển động lặp theo shot cho kịch bản tập hoạt hình:
1. Lựa chọn shot thông minh (maxClips, ưu tiên shot đầu cảnh, bài hát/cao trào, shot cuối).
2. Tích hợp nguồn clip linh hoạt (auto / manual / ai):
   - manual: chỉ dùng clip làm tay từ content/episodes/<ep>/clips/<shotId>.mp4
   - ai: gọi video provider
   - auto: ưu tiên clip làm tay, nếu không có mới gọi AI, AI lỗi thì giữ ảnh tĩnh
3. Caching theo shot (episodeId, shotId, model, prompt hash, image hash) tránh tốn credit khi chạy lại.
4. Xử lý lỗi an toàn (AI quota/auth error thì giữ nguyên ảnh, không làm gãy toàn bộ pipeline).
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from socnhotv.core.contracts.types import (
    Artifact,
    ArtifactKind,
    ArtifactProvenance,
)
from socnhotv.core.storage.project_store import ProjectStore

logger = logging.getLogger("socnhotv.core.shot_video")


def _compute_hash(text_or_bytes: str | bytes) -> str:
    """Tính SHA256 ngắn gọn 16 ký tự."""
    data = text_or_bytes.encode("utf-8") if isinstance(text_or_bytes, str) else text_or_bytes
    return hashlib.sha256(data).hexdigest()[:16]


def find_manual_clip(
    project_dir: Path,
    episode_id: Optional[str],
    shot_id: str,
) -> Optional[Path]:
    """Tìm clip làm tay theo hợp đồng C5:
    content/episodes/<episodeId>/clips/<shotId>.mp4
    hoặc data/projects/<id>/content/episodes/<episodeId>/clips/<shotId>.mp4.
    """
    if not episode_id or not shot_id:
        return None

    clean_shot = shot_id.strip()
    candidates = [
        project_dir / "content" / "episodes" / episode_id / "clips" / f"{clean_shot}.mp4",
        project_dir / "content" / "episodes" / episode_id / "clips" / f"{clean_shot.upper()}.mp4",
        project_dir / "content" / "episodes" / episode_id / "clips" / f"{clean_shot.lower()}.mp4",
    ]

    # Kiểm tra thêm đường dẫn tương đối trong repository
    for cand in candidates:
        if cand.is_file() and cand.stat().st_size > 0:
            return cand.resolve()

    return None


def select_shots_for_video(
    scenes: List[Dict[str, Any]],
    max_clips: int = 5,
    specified_shot_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Chọn tối đa max_clips shot để sinh video clip.
    Nếu người dùng chỉ định specified_shot_ids: chọn đúng danh sách đó.
    Nếu không: xếp thứ tự ưu tiên:
      1. Shot đầu của mỗi cảnh (sceneIndex mới)
      2. Shot cao trào / bài hát / bài tập thở
      3. Shot kết thúc tập (shot cuối)
      4. Các shot còn lại theo thứ tự kịch bản
    """
    if not scenes:
        return []

    if specified_shot_ids:
        target_ids = {str(sid).strip().lower() for sid in specified_shot_ids}
        selected = [sc for sc in scenes if str(sc.get("id") or sc.get("shotId") or "").lower() in target_ids]
        return selected[:max_clips]

    # Phân loại độ ưu tiên
    p1_first_in_scene: List[Dict[str, Any]] = []
    p2_highlight_song: List[Dict[str, Any]] = []
    p3_last_shot: List[Dict[str, Any]] = []
    p4_others: List[Dict[str, Any]] = []

    seen_scenes: Set[Any] = set()
    total = len(scenes)

    highlight_keywords = [
        "hát", "đồng dao", "núi lửa", "thở", "5 ngón tay", "thần chú", "khóc", "ôm", "bài học", "quay tít"
    ]

    for idx, sc in enumerate(scenes):
        sc_idx = sc.get("sceneIndex")
        is_first_of_scene = False
        if sc_idx is not None and sc_idx not in seen_scenes:
            seen_scenes.add(sc_idx)
            is_first_of_scene = True

        is_last = (idx == total - 1)

        text_content = (
            str(sc.get("dialogue") or "") + " "
            + str(sc.get("action") or "") + " "
            + str(sc.get("sfx") or "") + " "
            + str(sc.get("bgm") or "")
        ).lower()

        is_highlight = any(kw in text_content for kw in highlight_keywords)

        if is_first_of_scene:
            p1_first_in_scene.append(sc)
        elif is_highlight:
            p2_highlight_song.append(sc)
        elif is_last:
            p3_last_shot.append(sc)
        else:
            p4_others.append(sc)

    combined = p1_first_in_scene + p2_highlight_song + p3_last_shot + p4_others

    # Giữ thứ tự xuất hiện ban đầu trong video
    chosen_ids = {id(sc) for sc in combined[:max_clips]}
    return [sc for sc in scenes if id(sc) in chosen_ids]


def inject_manual_clips(
    scenes: List[Dict[str, Any]],
    project_dir: Path,
    episode_id: Optional[str],
) -> List[Dict[str, Any]]:
    """Tự động phát hiện và gán clip làm tay từ clips/<shotId>.mp4 vào scenes (Hợp đồng C5)."""
    if not episode_id:
        return scenes

    updated_scenes: List[Dict[str, Any]] = []
    for sc in scenes:
        sc_copy = dict(sc)
        shot_id = str(sc.get("id") or sc.get("shotId") or "")
        if not sc_copy.get("video") and shot_id:
            manual_file = find_manual_clip(project_dir, episode_id, shot_id)
            if manual_file:
                sc_copy["video"] = str(manual_file)
                sc_copy["videoSource"] = "manual"
                logger.info(f"Đã tự nhận clip làm tay cho shot {shot_id}: {manual_file}")
        updated_scenes.append(sc_copy)

    return updated_scenes


def clean_video_prompt(raw_prompt: str, target_duration_sec: float) -> str:
    """Điều chỉnh prompt video: thay thế '8-second' hoặc số giây cứng bằng thời lượng thực tế của model."""
    dur_str = f"{int(round(target_duration_sec))}-second"
    # Thay '8-second' hoặc '\d+-second'
    cleaned = re.sub(r"\b\d+-second\b", dur_str, raw_prompt, flags=re.IGNORECASE)
    return cleaned


class ShotVideoEngine:
    """Engine quản lý sinh video chuyển động lặp theo shot cho SocNhoTV."""

    def __init__(self, store: ProjectStore):
        self.store = store
        self.cache_dir = self.store.runs_dir / "cache" / "shot_videos"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.cache_dir / "manifest.json"
        self._cache_index: Dict[str, str] = self._load_cache_index()

    def _load_cache_index(self) -> Dict[str, str]:
        if self.manifest_path.is_file():
            try:
                return json.loads(self.manifest_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_cache_index(self) -> None:
        try:
            self.manifest_path.write_text(json.dumps(self._cache_index, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Không thể lưu cache index shot video: {e}")

    def make_cache_key(
        self,
        episode_id: Optional[str],
        shot_id: str,
        model: str,
        prompt: str,
        first_frame_hash: str,
    ) -> str:
        ep = episode_id or "common"
        prompt_h = _compute_hash(prompt)
        raw_key = f"{ep}:{shot_id}:{model}:{prompt_h}:{first_frame_hash}"
        return _compute_hash(raw_key)

    async def generate_per_shot_videos(
        self,
        scenes: List[Dict[str, Any]],
        provider: Any,
        episode_id: Optional[str] = None,
        max_clips: int = 5,
        specified_shot_ids: Optional[List[str]] = None,
        clip_source: str = "auto",
        model: str = "mock-video",
        target_duration_sec: float = 6.0,
        run_id: str = "run_default",
        progress_cb: Optional[Callable[[int, int, str], None]] = None,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Artifact]]:
        """Thực thi sinh video cho từng shot được chọn tuân thủ Hợp đồng C4, C5."""
        if not scenes:
            return [], []

        # 1. Quét clip làm tay trước
        scenes_with_manual = inject_manual_clips(scenes, self.store.project_dir, episode_id)

        # 2. Chọn shot
        target_shots = select_shots_for_video(
            scenes=scenes_with_manual,
            max_clips=max_clips,
            specified_shot_ids=specified_shot_ids,
        )

        target_ids = {id(sc) for sc in target_shots}
        total_target = len(target_shots)
        logger.info(f"Đã chọn {total_target} shot cho video_gen (clip_source={clip_source}, maxClips={max_clips})")

        out_scenes: List[Dict[str, Any]] = []
        video_artifacts: List[Artifact] = []

        clip_counter = 0

        for sc in scenes_with_manual:
            if cancel_event and cancel_event.is_set():
                logger.info("Quá trình sinh video theo shot bị hủy bởi người dùng.")
                break

            sc_out = dict(sc)
            shot_id = str(sc.get("id") or sc.get("shotId") or f"S_{len(out_scenes)+1:02d}")

            if id(sc) not in target_ids:
                # Shot này không nằm trong danh sách cần clip chuyển động -> giữ nguyên
                out_scenes.append(sc_out)
                continue

            clip_counter += 1
            if progress_cb:
                progress_cb(clip_counter, total_target, f"Đang xử lý Clip {clip_counter}/{total_target}: Shot {shot_id}")

            # Đã có clip làm tay từ trước
            if sc_out.get("video") and sc_out.get("videoSource") == "manual":
                logger.info(f"Shot {shot_id}: Tái sử dụng clip làm tay {sc_out['video']}")
                out_scenes.append(sc_out)
                continue

            # Nếu chỉ định manual nhưng chưa có clip
            manual_file = find_manual_clip(self.store.project_dir, episode_id, shot_id)
            if manual_file:
                sc_out["video"] = str(manual_file)
                sc_out["videoSource"] = "manual"
                out_scenes.append(sc_out)
                continue
            elif clip_source == "manual":
                logger.info(f"Shot {shot_id}: clip_source=manual nhưng không tìm thấy file, giữ ảnh tĩnh.")
                sc_out["video"] = None
                out_scenes.append(sc_out)
                continue

            # Nguồn AI (hoặc auto không có clip tay)
            img_val = sc.get("image") or sc.get("img") or sc.get("first_frame")
            img_path = str(img_val) if img_val else ""
            img_bytes = b""
            if img_path and os.path.isabs(img_path) and os.path.isfile(img_path):
                try:
                    img_bytes = Path(img_path).read_bytes()
                except Exception:
                    pass
            frame_hash = _compute_hash(img_bytes) if img_bytes else "no_frame"

            raw_prompt = str(sc.get("videoPrompt") or sc.get("action") or f"3D animation of shot {shot_id}")
            prompt = clean_video_prompt(raw_prompt, target_duration_sec)

            cache_key = self.make_cache_key(episode_id, shot_id, model, prompt, frame_hash)
            cached_rel_path = self._cache_index.get(cache_key)

            if cached_rel_path:
                cached_file = self.cache_dir / cached_rel_path
                if cached_file.is_file() and cached_file.stat().st_size > 0:
                    logger.info(f"Shot {shot_id}: Trúng cache ({cache_key}) -> Không gọi provider!")
                    sc_out["video"] = str(cached_file)
                    sc_out["videoSource"] = "ai"
                    sc_out["cached"] = True
                    out_scenes.append(sc_out)
                    continue

            # Gọi AI Provider
            try:
                vid_fn = getattr(provider, "generate_video", None)
                if not callable(vid_fn):
                    raise RuntimeError("Provider không hỗ trợ phương thức generate_video")

                art: Artifact = await vid_fn(
                    prompt=prompt,
                    first_frame_uri=img_path or None,
                    duration_sec=target_duration_sec,
                    aspect_ratio="16:9",
                    has_audio=False,
                    node_id="video_gen",
                    run_id=run_id,
                    model=model,
                    cancel_event=cancel_event,
                )

                # Lưu vào cache của engine
                cached_filename = f"{episode_id or 'ep'}_{shot_id}_{cache_key}.mp4"
                cached_dest = self.cache_dir / cached_filename
                
                # Trích xuất dữ liệu từ artifact
                art_file = self.store.project_dir / art.uri
                if art_file.is_file():
                    shutil.copy2(art_file, cached_dest)
                elif hasattr(art, "data") and art.data:
                    cached_dest.write_bytes(art.data)

                if cached_dest.is_file() and cached_dest.stat().st_size > 0:
                    self._cache_index[cache_key] = cached_filename
                    self._save_cache_index()
                    sc_out["video"] = str(cached_dest)
                else:
                    sc_out["video"] = str(art_file)

                sc_out["videoSource"] = "ai"
                video_artifacts.append(art)
                logger.info(f"Shot {shot_id}: Đã sinh thành công clip AI qua model {model}")

            except Exception as e:
                # Chiến lược tự thích ứng: AI lỗi (QUOTA, AUTH, network) -> Giữ ảnh tĩnh và cảnh báo
                err_msg = str(e)
                logger.warning(f"Shot {shot_id}: Lỗi sinh video AI ({err_msg}). Tự động giữ ảnh tĩnh.")
                sc_out["video"] = None
                sc_out["videoWarning"] = f"AI video error: {err_msg}"

            out_scenes.append(sc_out)

        return out_scenes, video_artifacts
