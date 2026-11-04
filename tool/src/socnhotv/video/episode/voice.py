from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess
import tempfile
from typing import List, Tuple

import imageio_ffmpeg

from socnhotv.core.adapters.audio_mastering import AudioMastering
from socnhotv.core.providers.mock_provider import create_minimal_wav_bytes
from socnhotv.video.episode.planner import ScenePlan
from socnhotv.workspace.paths import project_path

logger = logging.getLogger("socnhotv.video.episode.voice")
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


async def synthesize_episode_voice(
    project_id: str,
    episode_id: str,
    scenes: List[ScenePlan],
    use_mock: bool = False,
) -> Tuple[Path, List[float]]:
    """Tổng hợp giọng đọc đa nhân vật (Bi = soc-nho, Koala = koala/soc-nho),
    mastering -14 LUFS và ghép nối thành timeline thoại duy nhất cho tập phim.
    """
    audio_out_dir = project_path(project_id, "output", episode_id, "audio")
    audio_out_dir.mkdir(parents=True, exist_ok=True)
    master_audio_path = audio_out_dir / "episode_master_voice.mp3"

    scene_audio_files: List[Path] = []
    durations: List[float] = []

    for sc in scenes:
        sc_audio_file = audio_out_dir / f"{sc.scene_id}_voice.wav"
        full_line = " ".join(d.line for d in sc.dialogue) or f"Phân cảnh {sc.scene_number}"

        if not sc_audio_file.exists():
            if use_mock or not os.environ.get("OPENAI_API_KEY"):
                # Tạo audio mock với thời lượng tương ứng
                sc_audio_file.write_bytes(create_minimal_wav_bytes(duration_sec=sc.duration_est))
            else:
                try:
                    from socnhotv.core.adapters.voice_adapter import VoiceAdapter
                    from socnhotv.core.storage.project_store import ProjectStore
                    store = ProjectStore(project_id)
                    v_adapter = VoiceAdapter(store)
                    art = await v_adapter.synthesize(
                        text=full_line,
                        voice_id="soc-nho",
                        node_id=f"voice_{sc.scene_id}",
                        run_id=episode_id,
                    )
                    src_art = store.project_dir / art.uri
                    import shutil
                    shutil.copy2(src_art, sc_audio_file)
                except Exception as e:
                    logger.warning(f"VoiceAdapter synthesize failed ({e}), using fallback minimal wav.")
                    sc_audio_file.write_bytes(create_minimal_wav_bytes(duration_sec=sc.duration_est))

        scene_audio_files.append(sc_audio_file)
        durations.append(sc.duration_est)

    # Ghép nối các file audio thành 1 file master
    with tempfile.TemporaryDirectory() as tmp_dir:
        concat_list = Path(tmp_dir) / "concat.txt"
        with open(concat_list, "w", encoding="utf-8") as f:
            for p in scene_audio_files:
                f.write(f"file '{p.resolve()}'\n")

        raw_concat_wav = Path(tmp_dir) / "raw_concat.wav"
        cmd = [
            FFMPEG_EXE,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "pcm_s16le",
            str(raw_concat_wav),
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)

        # TikTok Audio Mastering Chain (-14 LUFS)
        mastering = AudioMastering(ffmpeg_exe=FFMPEG_EXE)
        mastering.master_tiktok(
            input_audio_path=str(raw_concat_wav),
            output_audio_path=str(master_audio_path),
            target_lufs=-14.0,
            bitrate="192k",
        )

    return master_audio_path, durations
