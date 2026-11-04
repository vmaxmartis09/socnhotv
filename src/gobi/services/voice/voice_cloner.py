"""Voice Vault: clone giọng từ video/mp3 một lần, đọc kịch bản nhiều lần.

Engine mặc định OmniVoice; dự phòng edge-tts (vi-VN-HoaiMyNeural, rate +5%, pitch +2Hz).
"""

import asyncio
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from gobi.services.voice.audio_mastering import AudioMastering
from gobi.services.voice.audio_preprocessor import AudioPreprocessor
from gobi.services.voice.omnivoice_engine import OmniVoiceEngine

PROJECT_ROOT = Path(__file__).resolve().parents[4]
_shared_vault = PROJECT_ROOT / "data" / "shared" / "voice_vault"
DEFAULT_PROFILES_DIR = _shared_vault if _shared_vault.exists() else (PROJECT_ROOT / "assets" / "voice_vault")
OUTPUT_DIR = PROJECT_ROOT / "output"

# Câu mặc định cho file preview của mọi giọng. Sửa theo thương hiệu dự án.
DEFAULT_CLONED_GREETING = "Xin chào, mình là Sóc Nhỏ TV đây nè, chúc cả nhà một ngày thật vui!"

EDGE_VOICE = "vi-VN-HoaiMyNeural"


def split_sentences(text: str, max_chars: int = 220) -> List[str]:
    """Tách theo câu để giữ ngữ điệu; câu quá dài thì cắt ở dấu phẩy."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?…])\s+|\n+", text) if p.strip()]
    out: List[str] = []
    for p in parts:
        while len(p) > max_chars:
            cut = p.rfind(",", 0, max_chars)
            cut = cut if cut > 40 else p.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            out.append(p[:cut + 1].strip())
            p = p[cut + 1:].strip()
        if p:
            out.append(p)
    return out or [text.strip()]


class VoiceCloner:
    def __init__(self, profiles_dir=DEFAULT_PROFILES_DIR, whisper_model: str = "base"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.preprocessor = AudioPreprocessor(whisper_model=whisper_model)
        self.mastering = AudioMastering()
        self.engine = OmniVoiceEngine()

    def get_profile(self, profile_id: str) -> Dict[str, Any]:
        pj = self.profiles_dir / profile_id / "profile.json"
        if not pj.exists():
            raise FileNotFoundError(f"Không có giọng '{profile_id}' trong Voice Vault ({pj})")
        return json.loads(pj.read_text(encoding="utf-8"))

    def create_profile(
        self,
        media_path: str,
        profile_id: str,
        speaker_name: Optional[str] = None,
        dialect: str = "north",
        style: str = "default",
        custom_transcript: Optional[str] = None,
        target_duration: float = 4.5,
    ) -> Dict[str, Any]:
        folder = self.profiles_dir / profile_id
        folder.mkdir(parents=True, exist_ok=True)
        print(f"\n== TẠO SOUND PROFILE: {profile_id} ==")

        prep = self.preprocessor.process_media(
            media_path, str(folder), target_duration=target_duration, custom_transcript=custom_transcript
        )
        transcript = prep["transcript"]
        (folder / "reference_transcript.txt").write_text(transcript, encoding="utf-8")

        source_preview = folder / "source_original_preview.mp3"
        self.mastering.master_tiktok_koc(prep["ref_slice_wav"], str(source_preview), tempo_factor=1.0, presence_boost_db=2.5)

        meta = {
            "profile_id": profile_id,
            "speaker_name": speaker_name or profile_id,
            "dialect": dialect,
            "style": style,
            "engine": "omnivoice",
            "duration": prep["duration"],
            "transcript": transcript,
            "default_greeting": DEFAULT_CLONED_GREETING,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "files": {
                "prompt": "omnivoice_prompt.pt",
                "ref_slice": "reference_clean_slice.wav",
                "transcript": "reference_transcript.txt",
                "full_clean": "raw_extracted_clean.wav",
                "source_preview": "source_original_preview.mp3",
                "cloned_sample": "cloned_default_sample.mp3",
            },
        }
        (folder / "profile.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

        self.engine.create_prompt(str(folder), prep["ref_slice_wav"], transcript)

        cloned_sample = folder / "cloned_default_sample.mp3"
        self.speak(profile_id, DEFAULT_CLONED_GREETING, str(cloned_sample), master=True, tempo_factor=1.0)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_preview, OUTPUT_DIR / f"{profile_id}_source_original_preview.mp3")
        shutil.copy2(cloned_sample, OUTPUT_DIR / f"{profile_id}_cloned_default_sample.mp3")
        print(f"\n[+] Profile xong: {folder / 'profile.json'}")
        print(f"    Source gốc : {OUTPUT_DIR / (profile_id + '_source_original_preview.mp3')}")
        print(f"    Clone mẫu  : {OUTPUT_DIR / (profile_id + '_cloned_default_sample.mp3')}")
        return meta

    def speak(
        self,
        profile_id: str,
        new_script: str,
        output_path: str,
        engine: str = "omnivoice",
        master: bool = True,
        tempo_factor: float = 1.10,
    ) -> str:
        self.get_profile(profile_id)
        out = Path(output_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        raw = out.with_name(f"_raw_{profile_id}_{out.stem}.wav")
        sentences = split_sentences(new_script)

        done = False
        if engine == "omnivoice":
            try:
                print(f"[OmniVoice] {profile_id}: {len(sentences)} câu")
                self.engine.synthesize(str(self.profiles_dir / profile_id), sentences, str(raw))
                done = True
            except Exception as e:
                print(f"[!] OmniVoice lỗi, chuyển sang edge-tts: {e}")
        if not done:
            raw = raw.with_suffix(".mp3")
            self._edge_tts(" ".join(sentences), str(raw))

        if master:
            self.mastering.master_tiktok_koc(str(raw), str(out), tempo_factor=tempo_factor)
        else:
            shutil.copy2(raw, out)
        raw.unlink(missing_ok=True)
        print(f"[OK] {out}")
        return str(out)

    @staticmethod
    def _edge_tts(text: str, out_path: str) -> None:
        import edge_tts

        async def run():
            await edge_tts.Communicate(text, voice=EDGE_VOICE, rate="+5%", pitch="+2Hz").save(out_path)

        asyncio.run(run())

    def clone_and_speak(self, media_path: str, new_script: str, output_path: str, profile_id: Optional[str] = None, engine: str = "omnivoice") -> str:
        """Clone + đọc một lệnh. Không có profile_id thì dùng thư mục tạm, không lưu vào vault."""
        if profile_id:
            self.create_profile(media_path, profile_id)
            return self.speak(profile_id, new_script, output_path, engine=engine)
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_cloner = VoiceCloner(profiles_dir=tmp, whisper_model=self.preprocessor.whisper_model_name)
            tmp_cloner.create_profile(media_path, "_oneshot")
            return tmp_cloner.speak("_oneshot", new_script, output_path, engine=engine)

    def list_profiles(self) -> List[Dict[str, Any]]:
        rows = []
        for p in sorted(self.profiles_dir.iterdir()) if self.profiles_dir.exists() else []:
            pj = p / "profile.json"
            if p.is_dir() and pj.exists():
                d = json.loads(pj.read_text(encoding="utf-8"))
                d["_dir"] = str(p)
                rows.append(d)
        return rows
